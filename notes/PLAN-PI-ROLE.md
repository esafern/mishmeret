# Plan: a role run by pi

## The case

The reviewer, 2026-11-23, in mishmeret-builder's pane: "i recently experimented with running pi instead of claude
code as a builder. it does not have a command line option for agent but it does have name", then, on this plan's
outline: "before the skills do the plan and design question".

Mishmeret takes a session's role from Claude Code in two places. The guard reads the hook input's `agent_type` (the
`--agent` a session was started with). land.py and board.py read `CLAUDE_CODE_AGENT`, which Claude Code sets in its
bash tool's environment. The guard runs only because Claude Code fires a PreToolUse hook. pi (1.6.0 on this machine)
has none of these: no `--agent`, no Claude Code hooks, and no variable.

THE RECORD (read 2026-11-23): pi's three sessions on this machine (`~/.pi/agent/sessions`). No pi extension is
installed (`pi list`: none; no `~/.pi/agent/extensions`, no project `.pi/`), so no rule saw any of their tool calls.
- One ran in the first project's main clone on 2026-11-22: 96 tool calls (bash 51, read 32, edit 12, write 1). It
  worked as that project's operator. It edited main-tree files and committed through land.py, naming the role by
  putting `CLAUDE_CODE_AGENT=<operator>` in its commands. Judged by the guard at e5a4d40 under that project's config:
  as its operator, 5 refused, each for setting that variable; as its builder, 20 refused (the main-tree edits and the
  writes, and land.py naming the operator). What it committed is not checked here.
- Two ran in `~/work`: 8 tool calls, none refused.
So a pi role runs unguarded today, and it lands only by naming its role in a variable any command can set.

THE MEASURE, a prototype in the scratchpad: no model called, nothing outside the scratchpad written. A scripted
provider (an OpenAI-compatible fake server on 127.0.0.1, registered by a second extension) gave pi fixed tool calls.
They ran in a throwaway project whose own config guards it, so a failure could touch only scratch files. The
prototype extension, about 30 lines, put each bash, edit and write call to role_guard.py as Claude Code's PreToolUse
event. That is `tool_name` Bash/Edit/Write; `tool_input` `{command}`, or `{file_path}` with pi's `path` resolved
against the cwd; `cwd`; and `agent_type`, the role. It blocked the call on any exit but 0. Measured:
- `--role ex-builder` (a flag the extension registers) and `--name ex-builder` both reach it at `session_start`.
- `echo` ran. `git push origin main` and a write into the project's main tree were blocked; pi gave the model the
  guard's words as the tool's result, and the file was not written.
- With no `--role`: judged as no role, so the push and the write were refused.
- With the guard's path missing: every call was blocked (fail closed).
- A replacement bash tool with a spawn hook (pi's `createBashTool`) gave each call `CLAUDE_CODE_AGENT=ex-builder`, and
  the guard still judged that bash. pi also gives every bash call `PI_SESSION_ID`. pi's tools here: read, bash, edit,
  write.
- A launcher cannot set the variable instead: this session's own guard refused the prototype's first launch line
  (`CLAUDE_CODE_AGENT=... pi ...`), and agents.sh is a script the guard reads.
- From pi's docs (extensions.md): an `-e PATH` extension loads under `--no-extensions`; a project's `.pi/extensions/`
  loads only after the project is trusted.

Not in this piece, and why (each listed in the README as what a pi role lacks):
- The reports and night-run steps that read Claude Code's transcripts (`claude_projects`): role_sessions, role_usage,
  the status line, keepalive_due, the night run's context check, and `agents.sh --resume`. pi keeps its own sessions
  in another format; a pi role is not in them.
- The finish hook: the finish sentence, and `agents.sh --next` after it. A pi role is cleared and started again by
  hand.
- SendMessage and ListAgents: Claude Code's, between its own sessions. A pi role is reached through the Board's
  `send` and `inbox`.
- Skills: pi reads `.agents/skills/` or `--skill PATH`, not `.claude/skills/`. That belongs to the skills piece, next.

## The change

1. `mishmeret/pi_guard.ts`, the extension, loaded by `-e` from the pinned tree (never from `.pi/extensions/`, which
   loads only once the project is trusted):
   - It registers `--role` (design question 1).
   - On `tool_call`, for bash, edit and write, it runs the role_guard.py beside it in the same tree with the event
     above. On any exit but 0, a timeout (20 s) or a fault, it blocks with the guard's words. Other tools pass, as
     Claude Code's hook lets Read through.
   - It replaces bash with pi's own bash, adding `CLAUDE_CODE_AGENT` (the role) through the spawn hook (design
     question 2).
2. agents.sh: a role whose config entry names `"runner": "pi"` (an OPTIONAL role key; absent means claude) is
   started as `pi --name R --role R -e <the tree>/mishmeret/pi_guard.ts`, plus `--thinking X` for the agent file's
   effort, `--append-system-prompt` with the agent file's body, and the brief's line as its first message. It is
   started fresh: no `--resume` for a pi role.
3. config.py: `runner` in ROLE_KEYS, OPTIONAL, `claude` or `pi`; any other value refused.
4. README: "A role run by pi" - how it is started, what guards it, and the four things it lacks (above).

## Design questions (to girsa-architect)

1. THE ROLE: a flag the extension registers (`--role`, fixed at start), or `--name`, as the reviewer suggests?
   `--name` is also the session's display name, and `/name` or an extension's `setSessionName` can rename the
   session mid-way; the guard would follow the new name. My recommendation: `--role` for the guard, with agents.sh
   setting `--name` to the same, as it does for claude.
2. THE ROLE FOR land.py AND board.py:
   (a) the extension sets `CLAUDE_CODE_AGENT` in each bash call's environment (measured above). One name, and the
       guard's rule on commands unchanged.
   (b) a second variable that land.py and board.py also read. The guard would then have to refuse a command setting
       it too.
   My recommendation: (a).
3. THE SCOPE: the guard, the role and the start only, with the README naming what a pi role lacks - or should one of
   the four (the transcript reports, resume, the finish hook, messages) come in this piece?
4. THE TESTS: the extension's test needs pi itself (the prototype's fake provider, in a throwaway project). Skipped
   where pi is not installed, as the browser tests are without Playwright? Then on a machine without pi the
   extension is tested by nothing.

## Files

- mishmeret/pi_guard.ts (new)
- mishmeret/agents.sh, mishmeret/config.py
- tests/test_pi_role.py (new; the fake provider and server under tests/), tests/test_sessions.py (agents.sh's pi line,
  with a stub `pi`), tests/test_config.py (ROLE_KEYS), tests/conftest.py (the stub `pi` first on PATH)
- README.md
- notes/PLAN-PI-ROLE.md, notes/LOG.md, notes/STATE-mishmeret-builder.md

## Tests (each rule's test shown red with it taken out)

- The extension under pi with the fake provider, in a throwaway project:
  - a push and a main-tree write blocked, and the guard's words in the tool's result;
  - `echo` run;
  - no `--role` judged as no role;
  - a missing guard blocking every call;
  - `CLAUDE_CODE_AGENT` in bash's environment equal to `--role`;
  - an edit (pi's `path`) resolved against the cwd.
- agents.sh with a stub `pi`: a `runner: pi` role's line holds `-e`, `--role` and `--name`; a claude role's line is
  unchanged; `--resume` starts the pi role fresh.
- config: `runner` absent, `claude` or `pi` accepted; any other value refused.

## For the first project

Nothing in its config until it names a role `runner: pi`. Until then a pi session there runs unguarded, as the
2026-11-22 one did: the reviewer's to know before the next run.

## Appendix: the prototype extension, as measured

Loaded as `pi -p --no-extensions -e fake.ts -e guard.ts --provider fake --model fake-chat --role ex-builder`,
with MISHMERET_GUARD naming role_guard.py and MISHMERET_CONFIG the throwaway project's config (the build reads
the guard beside the extension instead). The fake provider and server stay in the builder's scratchpad.

```typescript
// The pi prototype of Mishmeret's role guard: every bash, edit and write call is put to role_guard.py
// ($MISHMERET_GUARD) as Claude Code's PreToolUse event would be, the role from --role; exit 0 runs it, anything else
// (a refusal, a fault, a timeout) blocks it with the guard's words. What it saw is appended to $PROTO_LOG.
import { spawnSync } from "node:child_process";
import { appendFileSync } from "node:fs";
import { resolve } from "node:path";
import { createBashTool } from "@earendil-works/pi-coding-agent";

const TOOLS: Record<string, [string, (i: any, cwd: string) => any]> = {
  bash: ["Bash", (i) => ({ command: i.command })],
  edit: ["Edit", (i, cwd) => ({ file_path: resolve(cwd, i.path) })],
  write: ["Write", (i, cwd) => ({ file_path: resolve(cwd, i.path) })],
};
const log = (x: any) => appendFileSync(process.env.PROTO_LOG || "/dev/null", JSON.stringify(x) + "\n");

export default function (pi: any) {
  pi.registerFlag("role", { description: "the Mishmeret role this session runs as", type: "string", default: "" });
  // the role into each bash call's environment, as Claude Code sets it: land.py and board.py read it
  const bash = createBashTool(process.cwd(), {
    spawnHook: ({ command, cwd, env }: any) => ({ command, cwd, env: { ...env, CLAUDE_CODE_AGENT: pi.getFlag("role") || "" } }),
  });
  pi.registerTool({ ...bash, execute: (id: any, params: any, signal: any, onUpdate: any) => bash.execute(id, params, signal, onUpdate) });
  pi.on("session_start", (_e: any, ctx: any) => {
    log({ start: true, role: pi.getFlag("role"), name: pi.getSessionName?.(), cwd: ctx.cwd });
  });
  pi.on("tool_call", async (event: any, ctx: any) => {
    const t = TOOLS[event.toolName];
    if (!t) return;
    const role = pi.getFlag("role") || "";
    const hook = { tool_name: t[0], tool_input: t[1](event.input, ctx.cwd), cwd: ctx.cwd,
                   hook_event_name: "PreToolUse", ...(role ? { agent_type: role } : {}) };
    const r = spawnSync("python3", [process.env.MISHMERET_GUARD || "/missing/role_guard.py"],
                        { input: JSON.stringify(hook), encoding: "utf-8", timeout: 20000 });
    log({ tool: event.toolName, input: event.input, status: r.status, stderr: (r.stderr || "").slice(0, 200) });
    if (r.status === 0) return;
    return { block: true, reason: (r.stderr || "").trim() || `the role guard gave no answer (exit ${r.status}) - nothing runs` };
  });
}
```
