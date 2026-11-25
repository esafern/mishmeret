# mishmeret-builder - current state

Rewritten in place when a piece lands and at the end of a session; the log is `notes/LOG.md`, by item.

## Built, on main (main 2327b0d, not pushed; each verified by girsa-verifier, merged by girsa-operator)

- To 2026-11-24 (M01-M19): own `.claude/`, open messages, copy-on-select, the start scripts, finishing a session, the
  guard's mask, M07's items, `LESSONS.md`, the audit's fixes, /expiring.ics, the land.py race, the frozen gate, the
  hold by session, the known gaps (fifteen), Mishmeret's own skills, git's classification, a role run by pi, the
  shipped skills.
- 70a6ffe-4715362: a ref judged by the repository, not the folder (PLAN-PROTECTED-REFS; M20).
- 44485c3, 43a9d97: the Board's tab icon, mem on slate (PLAN-FAVICON; M22; the first project's #249 B).
- 40c167e-3016e2b (code 94cd205): git's reference-transaction hook (PLAN-REF-HOOK; M21) - main forward any role's,
  back, deleted or linked the operator's; `guard.refs` refs and replacements their owners'; run as installed;
  `guard.main` naming main for both callers, land.py refusing another; the Bash guard refusing what moves the hooks.
- 2327b0d: the guard alone (PLAN-GUARD-ONLY; M23; Board #3435, #3447) - config.PARTS, each all or none, a read of an
  absent part raising its sentence naming the reader; no landing part, no land.py; the config at
  `.mishmeret/config.json` (else `.claude/mishmeret.json`); config.session_role, MISHMERET_ROLE else
  CLAUDE_CODE_AGENT, for the environment's readers (the Bash guard's role still `agent_type` alone); `transcripts` by
  runner for `claude_projects`. Old names read until both pins and configs pass them.

## Now

- No piece in build. Main's push is the reviewer's word, in girsa-operator's pane.
- Branch `builder-guard-only`: 8edec6d (the check into the plan) and this state, notes for girsa-operator to merge;
  delete the branch once merged (`git branch -D` after `merge-base --is-ancestor` with main).
- The first project's bump to 2327b0d: girsa-operator's (it said so, 2026-11-25), with `ref_hook.py --install` run
  again after it (girsa-verifier's NOTE 1: a hook installed earlier passes CLAUDE_CODE_AGENT alone).
- The normalizer's setup is its own, not this lane (the plan's head): `norm-builder` and an operator, rav-shvat-blog
  foreign, its tags the operator's - `stage` and `prod` exact (the reviewer), `beta-rc*`; others suggested (M24).
- To resume: `git -C ~/work/mishmeret log --oneline -3`; `git -C ~/work/mishmeret-builder status -sb`; the Board, and a
  watcher on any Board item a piece waits on.

## Next, in order

1. The terminal adapter (the reviewer: "small terminal adapter"): tmux's verbs behind one module (WezTerm on macOS,
   Linux and Windows; headless RPC later); with it, if wanted, a session started by MISHMERET_ROLE with no agent file
   (girsa-architect's Q7: measured on a top-level start and a nested one first).
2. The move to the names in the first project and Mishmeret itself (every shim, the settings' hook paths, the configs'
   `transcripts`), then the old names' removal once both pins pass - its own piece. The first project's share:
   `.claude/mishmeret.json` 208 times in 107 files, CLAUDE_CODE_AGENT 90 in 39 (girsa-architect, 7501436fb).
3. Answered in this pane, not yet planned: the runner adapter (Claude Code's specifics in one module, pi first-class:
   its transcripts, the finish on `agent_end`); Gemini CLI as a third runner (M23: its hooks read); Mishmeret's
   reviews and Board items in its own repository.

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
- At the next touch of role_usage.py (:3, :28) and role_sessions.py (:9): their docstrings say claude_projects
  (girsa-verifier's NIT 1 on 2327b0d).
- A config kept outside its project's tree guards another folder (`config.root()`, its folder's parent) and leaves the
  project unguarded, unsaid - pre-existing; the README says so.
- Not measured: a pi session whose folder differs from its start folder; pi and the shipped skills on Windows and Linux.
- Not run live: the night and morning runs as changed (stubs only). The session scripts are macOS-only.
- A `!` command the reviewer types bypasses the hook (2026-11-12).
- A required config key cannot be added or renamed: Mishmeret pins itself (M05).
- Not pinned by a test (A2): `land()`'s restart line and ledger copy with the field absent.
- The 5 s refresh redraws the corners, so a focused pill loses focus (girsa-ui-steward: leave it).
- The first project's older worktree `...-mishmeret`: unused (told girsa-operator, #307); its removal is #307's.
