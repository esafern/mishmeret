# mishmeret-builder - current state

Rewritten in place when a piece lands and at the end of a session; the log is `notes/LOG.md`, by item.

## Built, on main (main 57b87b2, origin's main at it; each verified by girsa-verifier, merged by girsa-operator)

- To 2026-11-24 (M01-M19), by the log. 70a6ffe-4715362: a ref judged by the repository (M20). 43a9d97: the Board's
  tab icon (M22). 94cd205: git's reference-transaction hook (M21) - main forward any role's, else the operator's;
  `guard.refs` refs and replacements their owners'; `guard.main`.
- 2327b0d: the guard alone (PLAN-GUARD-ONLY; M23) - config.PARTS, each all or none, an absent part's read raising its
  sentence; no landing part, no land.py; the config at `.mishmeret/config.json` (else `.claude/mishmeret.json`);
  config.session_role, MISHMERET_ROLE else CLAUDE_CODE_AGENT (the Bash guard's role still `agent_type`);
  `transcripts` for `claude_projects`. Old names read until both pins and configs pass them.

## Now

- THE TERMINAL ADAPTER (PLAN-TERMINAL-ADAPTER, branch `builder-terminal-adapter` from main 57b87b2): BUILT at
  2c44f21 (M25, M27) - its guard part 654db02 and 52c04a8 (girsa-verifier's plan review, READY on LOW 1, taken); term.sh,
  the config's `terminal`, the scripts through it; 22 of 22 on private tmux and WezTerm servers; suite 205; rule 45
  1 and 6, named costs. NEXT: girsa-verifier's check at the final commit, then girsa-operator's merge. Windows the
  reviewer's own run. The measures' files: session aa55e80c's scratchpad, ta/ (gone if cleared: the plan's head).
- A PROJECT'S SETUP (PLAN-PROJECT-SETUP, branch `builder-project-setup` from main 57b87b2, the plan at 5937c48; M26):
  girsa-architect agreed (332c2fdb1); girsa-verifier READY on MEDIUM 1 (`guard.foreign` written with `~`, and a test
  that no written file holds the home folder). Its build next, after the adapter's check. THE NORMALIZER SET UP that
  night by the prototype (girsa-operator: its 165f8dc, not pushed); norm-builder runs under pi by its line with the
  pin's pi_guard.ts. This branch's log and state stay on the adapter's.
- Main's push is the reviewer's word, in girsa-operator's pane.
- The first project's bump to 2327b0d: girsa-operator's (it said so, 2026-11-25), with `ref_hook.py --install` run
  again after it (girsa-verifier's NOTE 1: a hook installed earlier passes CLAUDE_CODE_AGENT alone).
- To resume: `git -C ~/work/mishmeret log --oneline -3`; `git -C ~/work/mishmeret-builder status -sb`; the Board, and a
  watcher on any Board item a piece waits on.

## Next, in order

1. The terminal adapter's check and merge (above); then the setup's build. If wanted, a session started by
   MISHMERET_ROLE with no agent file (measured top-level and nested first).
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

The session is ready to clear.
