# Mishmeret's own .claude/: the plan (mishmeret-builder, 2026-11-05)

Written 14:22, revised 14:46 (`date`). On Board #156 B (this builder builds Mishmeret's own `.claude/`) and #153 B
(girsa-architect's MISHMERET-BUILDER-ROLE-PLAN-ARCHITECT.md, the guard's gap closed hard first). Its design questions
answered by girsa-architect (MISHMERET-OWN-CLAUDE-ARCHITECT.md, in Girsa); reviewed by girsa-verifier
(step5-verification/mishmeret-own-claude-2026-11-05/REVIEW.md, in Girsa): ACCEPTED with the conditions folded in below.

## The case

- A Mishmeret session wrote into Girsa: d87aa497 (through Girsa's `land.py`), 74437404, and 952cf591 (in another
  role's worktree). The guard kept a session out of a listed tree's MAIN clone only (`is_main_tree`: `git_dir ==
  common`); every worktree was open.
- Mishmeret had no `.claude/`, so a Mishmeret session ran Girsa's hooks and config, as a Girsa role.

## Pieces

- **A, `guard.foreign`** - built and VERIFIED, on main at 96d073d: a repository no role changes in its main clone or any
  worktree (one git common dir), the operator too - a git verb that changes a tree, `land.py commit|land` there, a file
  tool's write. Not covered, as for the main tree: a shell write, `git worktree add`, `git branch`.
- **A2, seven fields optional** - b541069, a5faac2 (with A's LOW 1): `python`, `drafts`, `guard.homes`,
  `guard.precommit`, `guard.foreign`, `land.ledger`, `land.server`. Absent, each reader takes it as off, no default
  (girsa-architect's answer 3; `guard.foreign` on girsa-verifier's recommendation, so a project's pin bump needs no new
  field). Not pinned by a test: `land()`'s restart line and ledger copy with the field absent.
- **B, `.claude/`** - below.

## B: the files

- `.claude/mishmeret.json`: pinned to a5faac2 (on main before B merges). Roles `mishmeret-builder` (a corner on the
  Board at 8451, `~/work/mishmeret-board`; no tmux), `mishmeret-operator` (the config's operator, no session) and
  `mishmeret-verifier` (`land.verifier` must name a role; girsa-verifier does the work). `guard.trees`
  `["~/work/mishmeret"]` (its pins guarded: `pin_of` reads TREES); `guard.foreign` Girsa's main clone and its corpus
  root (`~/work/sefer-digitization-pipeline`, `~/work/hashorashim` - its own git, which the first does not reach).
  None of the seven optional fields.
- `.claude/mishmeret_shim.py`: Girsa's, the one bootstrap copy (README), its map of Girsa's retired variable names
  dropped.
- `.claude/settings.json`: the guard (PreToolUse on Bash, Edit, Write, NotebookEdit), the Board hook, the status line.
- Shims: `.claude/hooks/role_guard.py`, `board_hook.py`, `statusline.py`; `.claude/board/board.py`, `board_server.py`;
  `.claude/land.py`.
- `.claude/agents/mishmeret-builder.md`: Girsa's builder's tools, opus, high; its first message names the brief.
- `.claude/lanes.txt` and `.claude/lane_check.py` (about 60 lines): `ROLE may|not PATTERN` rows (fnmatch; a path is
  the role's when a `may` matches and no `not` does), no role name in the code. The builder: everything but
  `.claude/` - so its own settings never reach main through a merge (girsa-architect's condition to answer 1).
  `--doc-only`: every path a `.md`. `--because`: reported, passes. `--range` and `--plan`: refused (no one runs
  `land.py land` here; the operator merges). AND, on every commit (girsa-verifier's condition, Mishmeret being
  PUBLIC): no personal address, no name or address from the local roster, no home folder in an added line - the
  roster `.claude/roster.local.json` in the MAIN clone (gitignored; the shape of a Girsa roster, `{"reviewers": {id:
  {"display", "email"}}}`), its absence said in the report. One place: this check.
- `notes/`: the builder's records - this plan, its brief (`BRIEF-mishmeret-builder.md`), its state file
  (`STATE-mishmeret-builder.md`, 6,000 bytes) and its log (`LOG.md`), to the public standard: roles, never names;
  paths with `~`.
- `.gitignore`: `.claude/roster.local.json`.
- `tests/test_own_project.py`: the repository's own config loads; the lane check refuses `.claude/` to the builder and
  passes elsewhere, `--doc-only`, `--range` refused, the personal scan on a placeholder roster.

## Starting it

`cd ~/work/mishmeret && env -u MISHMERET_CONFIG -u MISHMERET_AS claude --agent mishmeret-builder --name
mishmeret-builder` - in the MAIN clone (answer 1), whose `.claude/` only the operator writes; the builder works in
`~/work/mishmeret-builder`. `env -u`: a terminal that carries Girsa's MISHMERET_CONFIG would otherwise run Girsa's
config here (the shim keeps a value set by hand). Its commits: `<a Python with pytest> .claude/land.py commit
mishmeret-builder code|notes -F MSG FILES... --tests "..."` - the guard refuses a plain `git commit` in its own
project (THROUGH_LAND).

## After

girsa-verifier checks A2 and B at B's final commit; girsa-operator merges Mishmeret main and makes the pin of a5faac2,
then the reviewer starts the builder. Girsa's bumps are girsa-builder's (Board #155 B). Next for this builder
(girsa-operator's REQUEST): the Board's open-messages drill-down, then copy-on-select - each look girsa-ui-steward's.
