# mishmeret-builder - current state

Rewritten in place when a piece lands and at the end of a session; the log is `notes/LOG.md`, by item.

## Built, on main (main 3016e2b, 7 ahead of origin; each verified by girsa-verifier, merged by girsa-operator)

- To 2026-11-24 (M01-M19): own `.claude/`, open messages, copy-on-select, the start scripts, finishing a session, the
  guard's mask, M07's items, `LESSONS.md`, the audit's fixes, /expiring.ics, the land.py race, the frozen gate, the
  hold by session, the known gaps (fifteen), Mishmeret's own skills, git's classification, a role run by pi, the
  shipped skills.
- 70a6ffe-4715362: a ref judged by the repository, not the folder (PLAN-PROTECTED-REFS; M20).
- 44485c3, 43a9d97: the Board's tab icon, mem on slate (PLAN-FAVICON; M22; the first project's #249 B).
- 40c167e-3016e2b (code 94cd205): git's reference-transaction hook (PLAN-REF-HOOK; M21) - main forward any role's,
  back, deleted or linked the operator's; `guard.refs` refs and replacements their owners'; run as installed;
  `guard.main` naming main for both callers, land.py refusing another; the Bash guard refusing what moves the hooks.

## Now

- No piece in build. Main's push is the reviewer's word, in girsa-operator's pane.
- THE GUARD ALONE (PLAN-GUARD-ONLY, branch `builder-guard-only` at af2cd60, from 43a9d97): the plan with
  girsa-architect's answer (parts, each what one reader needs; a read of an absent part raising its sentence). Waits on
  the reviewer's questions 4-6 (is `~/work/rav-shvat-blog` foreign to the citation normalizer; the stash rule for one
  agent; the names - asked in this pane 2026-11-25), then girsa-verifier's review. Its prototype was in this session's
  scratchpad (guardonly/proto): the plan names each change. Rebase the branch on main before the build.
- The first project's bump to 3016e2b or later: its steps sent to girsa-builder, who forwarded them to girsa-operator
  (Board #3378) - in the first project the pin bump is girsa-operator's, not girsa-builder's as the brief says. In
  girsa-verifier's NOTE 1 order: the pin, then `guard.main` with its own branch's name, the older-worktree landing,
  then `ref_hook.py --install`.
- To resume: `git -C ~/work/mishmeret log --oneline -3`; `git -C ~/work/mishmeret-builder status -sb` (branch
  `builder-state-2026-11-25`: delete it once merged); the Board, and a watcher on any Board item a piece waits on.

## Next, in order

1. The guard alone, its build after the reviewer's answers and the review: config PARTS and `Config`, the guard with
   no landing part; with it the hook's NIT 1 (config.py's `LAND ={`) and NOTE 2 (a script can detach the main clone:
   landings refused till re-attached) in the README.
2. The names (the reviewer: "references to claude should go"), if the answer makes it its own piece: Mishmeret's own
   `.claude/` paths, `claude_projects`, CLAUDE_CODE_AGENT as its role variable; Claude Code's own behind one adapter.
3. Asked by the reviewer and answered in this pane, not yet planned: pi as first-class (a runner adapter, pi's
   transcripts read, the finish hook on pi's `agent_end`, the role written in pi's session); a terminal adapter over
   tmux's verbs (WezTerm on macOS, Linux and Windows; headless RPC later); Mishmeret's reviews and Board items in its
   own repository.

## Open

- girsa-verifier's LOW on 075f49a: PREFIX and TMUX_PREFIX are two copies of one pattern (they differ by `env -u`).
- The piped-check rule does not read a check inside a substitution after another word (`echo $(pytest | tail)`).
- A GIT_INDEX_FILE set from a variable is taken as temporary (114 such on the record): the classification's cost.
- No shell write is read by path: into a pin, the main tree, or the main clone's `.git/` (past the ref hook too).
- `export GIT_DIR=<main>/.git` before git is not read by `_git_trees`; the file tools' edits into another role's
  worktree are not refused; eval of a variable or a substitution is not read.
- A branch checked out nowhere is no one's. In the ref hook: an operator's subagent has the operator's rights; a tag
  made on origin elsewhere fails a non-owner's plain fetch; Linux, Windows and reftable unmeasured.
- The guard-measure skill's mutate.py copies `.claude/skills/` alone; the hook's tests need `.claude/`'s shim helper
  and land.py (the build ran a scratch copy): the operator's lane.
- The Board's `--waiting-for` takes this config's roles alone: a wait on a first-project role cannot be shown.
- At the next touch of mishmeret/skills/mishmeret-landing/SKILL.md: its line 8 names `.claude/land.py`, Mishmeret's own.
- At the next touch of tests/test_board.py: the favicon test quotes the reviewer as typed, "needfavicons [need
  favicons]" (girsa-verifier's NIT on 43a9d97).
- Not measured: a pi session whose folder differs from its start folder; pi and the shipped skills on Windows and Linux.
- Not run live: the night and morning runs as changed (stubs only). The session scripts are macOS-only.
- A `!` command the reviewer types bypasses the hook (2026-11-12).
- A required config key cannot be added or renamed: Mishmeret pins itself (M05).
- Not pinned by a test (A2): `land()`'s restart line and ledger copy with the field absent.
- The 5 s refresh redraws the corners, so a focused pill loses focus (girsa-ui-steward: leave it).
- The first project's older worktree `...-mishmeret`: unused (told girsa-operator, #307); its removal is #307's.
