# Plan: the guard alone - a project's config with only what the guard reads

## The case

The reviewer, 2026-11-25, in mishmeret-builder's pane, on using Mishmeret for a new project: "the citation normalizer
project is small and currently single-agent, so this may be too much process for that - but that also makes it
easier to experiment on, correct? and the guards are still useful for a single-agent", then "yes, plan the guard-only
minimal config piece". And, while it was planned: "references to claude should go - files with claude names -
renamed" (design questions 5 and 6).

Today a project cannot take the guard alone. `config.load` wants 21 of the config's 24 top-level fields - the Board's
folder, port and page order, the tmux session and its settings, Claude Code's transcripts folder, the agent files, the
launchd prefix, the night run's knobs, the reports' tables, the landing's - and each role's drawing keys (short name,
tmux colour, the page's two colours, corner, pane), whatever the project uses; and the guard sends every `git commit`
and every landing `git merge` in the project through `land.py`, which brings the lane check, the gate and the Board's
hold. The guard itself reads only the operator, each role's name and worktrees, and the `guard` table (and
`land.planned` and `tmux_session`, each only in a message or for the tmux rule).

THE PROJECT, read (the citation normalizer, `~/work/sefaria-citation-normalizer`): 57 commits, 86 files, one agent,
its own lessons file; no `.claude/` but a `settings.local.json`; one transcript in Claude Code's folder, one in pi's.
ON ITS RECORD (the guard-measure skill's extract.py, 2026-11-25): 380 distinct commands, every one with no role, every
one run in its main clone.

THE MEASURE, a prototype on a scratch copy of main 43a9d97's `mishmeret/` (the change below), its config a scratch
copy of the normalizer's tree (an APFS clone, its own `.git`) holding six fields - `repository`,
`mishmeret_commit`, `project`, one role by name, `operator`, `guard.foreign` (the first project, the Mishmeret
checkout, and `~/work/rav-shvat-blog`) - and the 380 commands' folder read as that copy:
- EACH MODULE under it: the guard, the time check, `expiring` and the draft check load; the Board, its server, its
  hook, the status line, land.py and the three reports each stop with one sentence naming the part it needs ("this
  project's config has no board part (board_dir, board_port, page_order, budget) - the Board (board.py) needs it");
  the session modules load and refuse at their entry; `config.py --shell` (the session scripts' read) names the
  sessions part. The prototype's first run found the loader reading `land.server` through an absent `land`: fixed.
- THE RECORD, judged as the project's operator (rule 45's decide.py): 7 of 380 refused, faults 0 - 5 writes into
  `~/work/rav-shvat-blog` (`git -C ... checkout --` of a shared file, two `add`s and two commits vendoring the shared
  dialect layer there: refused because the measure's config names it foreign - design question 4), 1 `git stash`
  (the shared-stash rule), 1 `git push origin --delete <a branch>` (the operator's push never deletes; the
  reviewer's own command). No commit refused: with no landing part, git commits as it is.
- AS IT RAN, with no role: 34 of 380 refused - 10 pushes (pushing is the operator's), 18 writes in the main clone
  (`commit` 7, `add` 6, `switch` 2, `pull`, `checkout`, `update-ref`), the 5 into `rav-shvat-blog` and the stash.
  So the agent starts as its role (design question 2).
- RULE 45, the first project's 170,908 and Mishmeret's 1,815, by role, main's guard against the prototype with each
  full config: each newly refused 0, newly let through 0, faults 0. Main's side is the hook piece's run at e8cfcb0,
  whose `role_guard.py` and `config.py` are main 43a9d97's byte for byte (`git diff`, 0 lines).
The scripts and decision files: this session's scratchpad, guardonly/ (cmds-normalizer.jsonl, cmds-norm-copy.jsonl,
norm-*.jsonl, r45-*.jsonl; the copy `norm/` and its config).

GIRSA-ARCHITECT'S ANSWER (the first project's design-study/MISHMERET-GUARD-ONLY-ARCHITECT.md at 7501436fb, written
before any review of this plan; it read the prototype):
- Q1, parts - with two changes. A part is what ONE reader needs together: the reports share no field (`size_report`
  reads `sizes` alone, `start_reading_report` `start_reads`, `effort_report` `effort` with `agent_files`), so three
  parts of one field each. And one home for "who needs which part": not `need()` at each reader with a test's list
  beside them (the rule in two copies), but `load()` returning a config whose read of a field of an absent part raises
  that part's sentence, naming the reading module; `"x" in cfg` asks whether a part is there. Measured there: every
  config read in the prototype goes through `load()` (22 call sites), none copies it into a plain dict.
- Q2, started as its role: no role judged as the single role would make an unset variable mean the operator in one
  kind of project; the 34 of 380 the README's measured cost of forgetting it.
- Q3, agreed: without the landing part THROUGH_LAND has nothing to bring.
- Its view on 5 and 6 (the reviewer's): the split is right. The config's path has one home already, the project's
  shim; `config.path()`'s own default is a second copy, to go once the runs that reach it with no MISHMERET_CONFIG
  are counted (not yet). "Who is this session" - land.py, board.py and finish_hook.py read CLAUDE_CODE_AGENT, pi_guard
  sets it, the Bash guard reads the payload's `agent_type` - becomes one function in the runner adapter (Claude Code's
  variable for Claude Code, MISHMERET_ROLE for pi). The README says only what the code reads that day: this piece
  lands the config's new home, or its README keeps `.claude/mishmeret.json` until the move. The move's size in the
  first project: `.claude/mishmeret.json` 208 times in 107 files, `.claude/hooks/` 153 in 62, `.claude/board/` 98 in
  41, the shim 51 in 35, CLAUDE_CODE_AGENT 90 in 39.
BUILT INTO THE PROTOTYPE AND MEASURED AGAIN: the six parts and the reading object (`config.Config`), the seven `need`
calls gone (their modules as main's again). Under the minimal config each module loads or stops at its first read
with its part's sentence naming itself ("...has no board part (board_dir, board_port, page_order, budget) - board.py
needs it"; land.py, size_report.py, start_reading_report.py, effort_report.py each its own; `--shell` the session
scripts). The suite on the prototype with its full placeholder config: 179, of which 174 pass and 5 are the rule
they test, changed - four of a field missing refused by its old words (`board_port`, `budget`, a role's `tmux`, and
`guard.trees`, now optional) and the optional-fields test, whose loop pops `land` before `land.ledger`.

## The change

1. THE PARTS, each all its fields or none (`config.PARTS`): the Board (`board_dir`, `board_port`, `page_order`,
   `budget`), the sessions (`tmux_session`, `tmux_conf`, `claude_projects`, `agent_files`, `launchd_prefix`,
   `state_dir`, `night`), `sizes`, `start_reads`, `effort`, and the landing (`land`). A part half given is refused at
   load. A role's drawing keys are required only with the Board or the sessions. `guard.fallback_roots`, `trees`,
   `retired_remotes` and `checks` each optional, absent read as none. What is left required: `repository`,
   `mishmeret_commit`, `project`, `roles` (each a name), `operator`, `guard`.
2. `config.Config`, what `load()` returns: a read (`[]` or `.get`) of a field of an absent part raises a ConfigError
   naming the part's fields and the module that read it - PARTS the one list of who needs what, no reader meeting a
   KeyError; `"x" in cfg` asks whether a part is there (the guard's tmux session so). A module that must not begin
   work reads its part first (`--shell`: `tmux_session`).
3. THE GUARD with no landing part: `git commit` and a landing `git merge` are not sent through land.py (THROUGH_LAND
   and the operator's OPERATOR_THROUGH_LAND empty); every other rule as it is. With no sessions part the tmux rule
   still refuses the live server's `kill-server` (it holds every project's sessions), and names no roles' session.
4. THE README: a project that takes the guard alone - its config's six fields, the shim and `.claude/hooks/
   role_guard.py`, the `PreToolUse` hook in `.claude/settings.json`, one agent file so the session starts as its
   role (or pi's `--role` with `pi_guard.ts`) - and what the guard then refuses, and the cost of starting it with no
   role (34 of the normalizer's 380). In the names the code reads that day: `.claude/mishmeret.json` until the move
   (girsa-architect's view on Q6), or the new home if the reviewer's answer to Q5 and Q6 brings it into this piece.

Not in this piece: setting the normalizer up (its own repository, the reviewer's or its session's step, the files
in item 4); the names (design questions 5 and 6, a piece of their own); a part's reader that loads and then refuses
deeper (the session modules: their entry points, measured, say why).

## Design questions (to girsa-architect, answered at 7501436fb, the plan's head; 4 to 6 the reviewer's, asked)

1. PARTS, all or none, not each field optional: a Board with a port and no folder is no Board, and a field left out
   by mistake would read as "off". My recommendation: parts.
2. THE SINGLE AGENT IS THE OPERATOR, started as its role: it works in the main clone, which only the operator
   changes. A session with no role stays refused what every role but the operator is (34 of the 380 would be). Or
   a project with one role judges a session with no role as that role. My recommendation: started as its role - one
   agent file, no second rule.
3. NO LANDING PART, NO LAND.PY: commits and merges as git makes them; the check-status, push, foreign, config, refs
   and time rules stay. My recommendation: so.
4. FOR THE NORMALIZER (the reviewer's): is `~/work/rav-shvat-blog` foreign to it? Its record holds deliberate work
   there - the shared dialect layer vendored into it, two commits. And `git stash` (the shared-stash rule, 1 on its
   record): kept for one agent? My recommendation: not foreign (its agent commits there by design), the stash rule
   kept.
5. THE NAMES (the reviewer: "references to claude should go - files with claude names - renamed"). Mishmeret's own
   that can be: the config's home `.claude/mishmeret.json`, the shims and scripts in `.claude/hooks/`, `.claude/
   land.py`, `.claude/board/`, the field `claude_projects`, and CLAUDE_CODE_AGENT as the role variable Mishmeret reads
   (pi_guard.ts sets it for pi). Claude Code's own cannot: `.claude/settings.json`, `.claude/agents/`, `.claude/
   skills/`, `CLAUDE.md`, the variables it sets, its transcripts folder - those go behind one runner's adapter, as
   pi's are in pi_guard.ts. My recommendation: `.mishmeret/` for the config and the shims, a `transcripts` field per
   runner, `MISHMERET_ROLE` set by each runner's start (Claude Code's read from its own variable in one place).
6. WHEN: the normalizer starts in the names chosen, so they come first or with this piece; moving the first project and
   Mishmeret itself is a piece of its own (every shim, the settings' hook paths, the config's path - a read of the
   old place until both pins move past it, its removal named). My recommendation: settle the names now, this piece
   writes the README in them, the move a piece of its own.

## Files

- mishmeret/config.py (PARTS, Config, the checks with a part absent, `--shell`)
- mishmeret/role_guard.py (no landing part; the guard table's four keys; the tmux rule's session by membership)
- tests/test_config.py (the four refusals' words, the optional-fields test by parts), tests/test_guard.py,
  tests/conftest.py (a minimal placeholder project beside the full one)
- README.md (the guard alone)
- notes/PLAN-GUARD-ONLY.md, notes/LOG.md, notes/STATE-mishmeret-builder.md

## Tests (each rule red with it taken out: mutate.py)

- The minimal config loads; each part half given refused; a role's drawing keys required with the Board or the
  sessions, not without.
- Every module under the minimal config: loads, or stops at its read with its part's sentence naming itself - each
  module imported, PARTS the one list (girsa-architect's Q1: no second list to keep in step); a read by `.get` raises
  as `[]` does; `"x" in cfg` does not.
- The guard under the minimal config: `git commit` and `git merge` in the main clone let through to the operator;
  the push, foreign, stash, check-status and tmux rules as with a full config.
- The full configs unchanged: rule 45 by role on both records (above).
