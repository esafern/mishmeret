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
  writes, and land.py naming the operator). Its commits, by girsa-architect's reading: 2e221b3c, 53391f88 and
  479aff88, re-checked by girsa-operator afterwards (0d723b2c) and verified by girsa-verifier (that project's Board
  #2757); two of the three carry no role prefix or co-author line.
- Two ran in `~/work`: 8 tool calls, none refused.
So a pi role runs unguarded today, and it lands only by naming its role in a variable any command can set.

GIRSA-ARCHITECT'S ANSWER to the four design questions (the first project's
design-study/MISHMERET-PI-ROLE-ARCHITECT.md at 79b449f5), all taken:
- Q1: `--role`, fixed at start, with `--name` set to the same: the guard judges an identity a rename cannot change.
- Q2: (a). One name; the spawn hook writes the role after the inherited environment, so one the launching shell carried
  is overwritten; a command's own setting is refused already (SETS_AGENT).
- Q3: the scope as planned, with one change: the extension names the tools that pass (`read`) and blocks any other
  tool it does not know, its name in the reason - a later pi's tool, or another extension's that writes, would
  otherwise run unguarded. 0 such calls on the record.
- Q4: acceptable, on two conditions. The test skips only where `pi` is not on PATH, and says why. agents.sh refuses to
  start a `runner: pi` role when the extension file it names is missing - a case nothing measured in pi itself.
- The README names pi on Windows and Linux as unmeasured.
- For the first project: its Board #168 A (a session run outside Claude Code only hands off) binds it. Whether a
  guarded pi role may commit and land there is the reviewer's, on its Board #303. Mishmeret's build does not wait on
  it: the extension guards a pi role either way. ANSWERED A by the reviewer, 2026-11-23 18:50 (in this session at
  18:46: "yes may commit"): once the extension has landed and been verified, a `runner: pi` role commits and lands as
  any role does; #168 A binds only sessions with no guard.

GIRSA-VERIFIER'S REVIEW (the first project's design-study/step5-verification/mishmeret-pi-role-plan-2026-11-23/
REVIEW.md, on 0600059): READY on three conditions, each taken below.
- LOW 1: an edit's and a write's text reach the time rule. The prototype gave Edit and Write `{file_path}` alone, and
  the time rule reads Edit's old_string/new_string and Write's content. pi's records: 12 of 12 edits are
  `{path, edits: [{oldText, newText}]}`, the write `{path, content}`.
- LOW 2: one path to the guard (DON'T REINVENT THE WHEEL). Claude Code runs the project's own hook,
  `python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/role_guard.py"`, whose shim runs the guard of the commit the checkout's
  config pins. "The role_guard.py beside" the extension is the tree agents.sh loaded it from, once, at start: in a
  worktree whose branch bumps the pin, a pi role would be judged by other code than a Claude Code role there.
- NOTE 1, measured since (the prototype, its replacement bash): passing four of execute's five arguments drops pi's
  `ctx`. Bash then ran with no `PI_SESSION_ID`; passing every argument through, it had it. The cwd bash ran in equalled
  the session's in both runs, but there they are the same folder; a run where they differ is the build's test.
- NOTE 2: a config naming `runner` is refused by any pin older than this build (config.py checks role keys exactly).
  This piece adds it to no config; the step that first names a role `runner: pi` lands with its project's pin bump.
- NOTE 3: agents.sh's line passes `--no-extensions`, as the prototype ran: by pi's docs `-e` still loads, and no other
  extension's bash can then replace the guarded one.

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

THE BUILD (7cbe089): the change below, with its tests; suite 170 passed.
- Under pi itself (tests/test_pi_role.py, two runs and a third with no hook):
  - each refusal's words reached the model;
  - the time rule saw a write's content and each of an edit's edits, and blocked the edit whole;
  - bash ran in the folder the guard judged, with pi's session id, and with CLAUDE_CODE_AGENT the role over the
    `ex-operator` pi was started with;
  - every judged call went through the throwaway project's own hook, CLAUDE_PROJECT_DIR the folder pi started in.
- 14 rules each RED with it taken out, over a passing baseline (mutate.py; the extension's nine, agents.sh's three,
  config.py's two).
- role_guard.py is unchanged, so rule 45 has nothing to compare. The guard judges `bash agents.sh` the same with the
  new script as with main's.

## The change

1. `mishmeret/pi_guard.ts`, the extension, loaded by `-e` from the pinned tree (never from `.pi/extensions/`, which
   loads only once the project is trusted):
   - It registers `--role` (Q1).
   - On `tool_call`, for bash, edit and write, it runs the project's own hook, as Claude Code does:
     `python3 <the project>/.claude/hooks/role_guard.py`, with CLAUDE_PROJECT_DIR set to the project - the folder pi
     was started in, as Claude Code takes the folder a session starts in (LOW 2). The event: Bash `{command}`;
     Write `{file_path, content}`; and an edit as one Edit `{file_path, old_string, new_string}` for each of its edits,
     the call blocked if any is refused (LOW 1). On any exit but 0, a timeout (20 s) or a fault, it blocks with the
     guard's words.
   - `read` passes, by name, as Claude Code's hook lets Read through. Any other tool is blocked, its name in the reason
     (Q3).
   - It replaces bash with pi's own bash, adding `CLAUDE_CODE_AGENT` (the role) through the spawn hook, after the
     inherited environment (Q2), and passing every argument of `execute` through, pi's `ctx` among them (NOTE 1).
2. agents.sh: a role whose config entry names `"runner": "pi"` (an OPTIONAL role key; absent means claude) is
   started as `pi --no-extensions --name R --role R -e <the tree>/pi_guard.ts` (NOTE 3), plus `--thinking X` for the
   agent file's effort, `--append-system-prompt` with the agent file's body, and the brief's line as its first
   message. `<the tree>` is the one agents.sh itself runs from, the pin its project's shim names; which guard judges
   is the project's hook (LOW 2), not that tree. It is started fresh: no `--resume` for a pi role. When the extension
   file is missing, it starts nothing for that role and says why (Q4).
3. config.py: `runner` in ROLE_KEYS, OPTIONAL, `claude` or `pi`; any other value refused.
4. README: "A role run by pi" - how it is started, what guards it, the four things it lacks (above), and that pi on
   Windows and Linux is unmeasured.

## Design questions (to girsa-architect; answered at 79b449f5, the plan's head)

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
- tests/test_pi_role.py and tests/pi/ (new: the fake provider, its server, a tool the extension does not know),
  tests/test_sessions.py (agents.sh's pi line, behind the stub tmux that records what is typed - no stub `pi` needed,
  so tests/conftest.py is unchanged), tests/test_config.py (ROLE_KEYS)
- README.md
- notes/PLAN-PI-ROLE.md, notes/LOG.md, notes/STATE-mishmeret-builder.md

## Tests (each rule's test shown red with it taken out)

- The extension under pi with the fake provider, in a throwaway project; skipped only where `pi` is not on PATH, the
  skip saying so (Q4):
  - a push and a main-tree write blocked, and the guard's words in the tool's result;
  - `echo` run;
  - no `--role` judged as no role;
  - a missing guard blocking every call;
  - `CLAUDE_CODE_AGENT` in bash's environment equal to `--role`, over one the launching shell carried;
  - an edit (pi's `path`) resolved against the cwd;
  - a tool the extension does not know blocked, its name in the reason (registered by a test extension);
  - LOW 1: a write naming a time ahead of the clock blocked by the time rule; an edit whose second edit names one
    blocked whole;
  - LOW 2: the guard reached through the throwaway project's own `.claude/hooks/role_guard.py` (its shim, recording
    that it ran), with CLAUDE_PROJECT_DIR the folder pi started in;
  - NOTE 1: the folder bash ran in equals the cwd the guard judged, and PI_SESSION_ID is set (the sign `ctx` arrived).
- agents.sh with a stub `pi`: a `runner: pi` role's line holds `--no-extensions`, `-e`, `--role` and `--name`; a
  claude role's line is unchanged; `--resume` starts the pi role fresh; a missing extension file starts nothing for
  that role.
- config: `runner` absent, `claude` or `pi` accepted; any other value refused.

## For the first project

Nothing in its config until it names a role `runner: pi`, with its pin bump to this build (NOTE 2). Until then a pi
session there runs unguarded, as the 2026-11-22 one did, and its Board #168 A binds it: a session run outside Claude
Code only hands off. After it, a guarded pi role commits and lands as any role does (#303 A).

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
