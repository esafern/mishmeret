// Mishmeret's role guard for a role run by pi (notes/PLAN-PI-ROLE.md). pi runs no Claude Code hook, has no --agent
// and sets no CLAUDE_CODE_AGENT: its 2026-11-22 session in the first project's main clone ran unguarded, and landed
// by setting that variable in its own commands. Loaded by agents.sh with `pi --no-extensions -e <this file>`, never
// from a project's .pi/extensions/ (which loads only once the project is trusted).
//
// - THE ROLE is `--role`, fixed at start; agents.sh sets `--name` to the same (girsa-architect's Q1: a rename must
//   not change what the guard judges). None given: judged as no role.
// - EVERY CALL GOES TO THE PROJECT'S OWN HOOK, as Claude Code runs it: `python3 <project>/.claude/hooks/role_guard.py`
//   with CLAUDE_PROJECT_DIR the folder pi started in (girsa-verifier's LOW 2 - one path to the guard, the commit the
//   checkout pins). bash as Bash; write as Write with its content; an edit as one Edit per edit, with its old and
//   new text (its LOW 1 - the time rule reads them). Exit 0 runs the call; anything else - a refusal, a fault, a
//   timeout, no hook - blocks it with the guard's words.
// - `read` passes by name, as Claude Code's hook lets Read through; any other tool is blocked, its name in the reason
//   (girsa-architect's Q3: a later pi's tool, or another extension's that writes).
// - bash is pi's own, with CLAUDE_CODE_AGENT (the role) put in each call's environment after the inherited one
//   (Q2), every argument of execute passed through - pi's ctx among them (girsa-verifier's NOTE 1: with four,
//   the call lost PI_SESSION_ID and the session's cwd).
import { spawnSync } from "node:child_process";
import { join, resolve } from "node:path";
import { createBashTool } from "@earendil-works/pi-coding-agent";

const PROJECT = process.cwd();
const HOOK = join(PROJECT, ".claude", "hooks", "role_guard.py");
const PASS = new Set(["read"]);

function judged(event: object): string | null {
  const r = spawnSync("python3", [HOOK], { input: JSON.stringify(event), encoding: "utf-8", timeout: 20000,
                                           env: { ...process.env, CLAUDE_PROJECT_DIR: PROJECT } });
  if (r.status === 0) return null;
  return (r.stderr || "").trim() ||
    `refused by the role guard's pi extension: the guard gave no answer (exit ${r.status}${r.error ? ", " + r.error.message : ""}) - nothing runs`;
}

function events(name: string, input: any, cwd: string): object[] | null {
  if (name === "bash") return [{ tool_name: "Bash", tool_input: { command: input.command } }];
  const file_path = resolve(cwd, input.path ?? "");
  if (name === "write") return [{ tool_name: "Write", tool_input: { file_path, content: input.content ?? "" } }];
  if (name === "edit") {
    const edits = Array.isArray(input.edits) ? input.edits : [{ oldText: input.oldText, newText: input.newText }];
    return (edits.length ? edits : [{}]).map((e: any) => (
      { tool_name: "Edit", tool_input: { file_path, old_string: e.oldText ?? "", new_string: e.newText ?? "" } }));
  }
  return null;
}

export default function (pi: any) {
  pi.registerFlag("role", { description: "the Mishmeret role this session runs as", type: "string", default: "" });
  const role = () => pi.getFlag("role") || "";
  const bash = createBashTool(PROJECT, {
    spawnHook: ({ command, cwd, env }: any) => ({ command, cwd, env: { ...env, CLAUDE_CODE_AGENT: role() } }),
  });
  pi.registerTool({ ...bash, execute: (...args: any[]) => (bash.execute as any)(...args) });
  pi.on("tool_call", async (event: any, ctx: any) => {
    try {
      if (PASS.has(event.toolName)) return;
      const each = events(event.toolName, event.input || {}, ctx.cwd);
      if (each === null) {
        return { block: true, reason: `refused by the role guard's pi extension: \`${event.toolName}\` is a tool it ` +
                                      "does not know - only read, bash, edit and write run" };
      }
      const base = { cwd: ctx.cwd, hook_event_name: "PreToolUse", ...(role() ? { agent_type: role() } : {}) };
      for (const e of each) {
        const why = judged({ ...base, ...e });
        if (why) return { block: true, reason: why };
      }
    } catch (e: any) {
      return { block: true, reason: `refused by the role guard's pi extension: it failed (${e?.message ?? e}) - nothing runs` };
    }
  });
}
