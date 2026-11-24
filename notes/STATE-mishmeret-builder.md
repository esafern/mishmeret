# mishmeret-builder - current state

Rewritten in place when a piece lands and at the end of a session; the log is `notes/LOG.md`, by item.

## Built, on main (main e7c1c6d, 9 ahead of origin; each verified by girsa-verifier, merged by girsa-operator)

- To 2026-11-13 (M01-M13): own `.claude/`, open messages, copy-on-select, the start scripts, finishing a session, the
  guard's mask, M07's items, `LESSONS.md`, the audit's fixes, /expiring.ics, the land.py race, the frozen gate, the
  hold by session.
- b01f7d0, 075f49a, f2126a1: the known gaps' first eight (PLAN-KNOWN-GAPS; M14). The first project pins 075f49a.
- 977295f, e5a4d40, 958474f, dc30cc2: the known gaps' seven (PLAN-KNOWN-GAPS-SEVEN; M15).
- 7c48fea, 7203f57, 59f84a2, 5bccb49: Mishmeret's own skills, status-report and guard-measure (M16).
- f49111a, 6575743, fa53cb2: git's command list as a classification (PLAN-GIT-CLASSIFICATION; M17; #302 A).
- 654a562, 0600059, 7d6e9ad, 7cbe089: a role run by pi (PLAN-PI-ROLE; M18; #303 A).
- 137ff68, ec8c031, 89cba8b: skills shipped to every project (PLAN-SHIPPED-SKILLS; M19).
- 70a6ffe-4715362 (build 110415f, round 6bb1caf): a ref judged by the repository, not the folder (PLAN-PROTECTED-REFS;
  M20; the first project's #304 A, #310 A) - main's branch the operator's, `guard.refs` refs their owners', a role's
  worktree and its branch the role's and the operator's; a git write in another role's worktree refused, a session
  with no role too (the reviewer's "Refuse it"); git in a function's body, eval, trap and coproc read by every rule;
  the guard-measure skill measures by role (`each`).

## Now

- No piece is open. Main e7c1c6d is 9 ahead of origin: its push is the reviewer's word in girsa-operator's pane.
- THE FIRST PROJECT'S PIN BUMP to e7c1c6d: girsa-verifier is checking it (the first project's #3247; its CHECK.md under
  design-study/step5-verification/pin-e7c1c6d-2026-11-24/). It lands in two steps (push-and-pin's step 3): as one
  patch an older worktree's landing holds main, its old config.py refusing `roles[].worktrees`. It brings the seven,
  the classification, the pi guard, the shipped skills and the protected refs, with its own steps (the `.gitignore`
  line for `.claude/skills/mishmeret-*`, its `landing` and `operator-sessions` cut, `guard.refs` and
  `roles[].worktrees` in its config). The first project's work, not mine.
- To resume: `git -C ~/work/mishmeret log --oneline -3`; `git -C ~/work/mishmeret-builder status -sb` (branch
  `builder-state-2026-11-24`, merged: delete it at the next branch); the Board, and a watcher (`board.py wait <id>`)
  on any Board item a piece waits on. A code round on girsa-verifier's findings goes back to it once before
  LANDED-READY.

## Next, in order

1. Git's `reference-transaction` hook, a piece of its own (girsa-architect, the first project's
   design-study/MISHMERET-PROTECTED-REFS-ARCHITECT.md, "Follow-up", at 350e01e37): main's branch and `guard.refs`
   guarded by the ref, whatever writes it. Its four measured points are in PLAN-PROTECTED-REFS's head: the hook reads
   the ref's own value (`update-ref <ref> <older>` hands it zeros); main needs no landing mark (a deletion or a move to
   a non-descendant refused to all but the operator); one function of who may move which ref, called by the Bash guard
   and by the hook; the escapes the Bash guard closes (`core.hooksPath` by `-c`, `GIT_CONFIG_*` or the config; the
   role variable unset before git). Its measure is a live run of every ref update the roles make, with the hook
   installed - not rule 45's replay. Plan first, with design questions to girsa-architect.

## Open

- girsa-verifier's LOW on 075f49a: PREFIX and TMUX_PREFIX are two copies of one pattern (they differ by `env -u`).
- The piped-check rule does not read a check inside a substitution after another word (`echo $(pytest | tail)`).
- A GIT_INDEX_FILE set from a variable is taken as temporary (114 such on the record): the classification's cost.
- A shell write through a link into a pin meets no file-target rule (as for any pinned file).
- `export GIT_DIR=<main>/.git` before git is not read by `_git_trees`, so by no rule built on it; the file tools'
  edits into another role's worktree are not refused.
- eval of a variable or a substitution (`X='git reset --hard'; eval "$X"`) is not read: the record's 10 such are none
  git; a same-command variable could go through `_expand`.
- A branch checked out nowhere is no one's; a protected branch checked out a second time before the rule is moved by a
  commit there.
- At the next touch of mishmeret/skills/mishmeret-landing/SKILL.md (girsa-verifier's NOTE on the bump): its line 8
  names `.claude/land.py`, Mishmeret's own path; a project's comes from its config or its own skill.
- Not measured: a pi session whose folder differs from its start folder; pi and the shipped skills on Windows and Linux;
  a skill's link changed under a running session.
- Not run live: the night and morning runs as changed (stubs only). The session scripts are macOS-only.
- A `!` command the reviewer types bypasses the hook (2026-11-12).
- A required config key cannot be added or renamed: Mishmeret pins itself (M05).
- Not pinned by a test (A2): `land()`'s restart line and ledger copy with the field absent.
- The 5 s refresh redraws the corners, so a focused pill loses focus (girsa-ui-steward: leave it).
- The first project's older worktree `...-mishmeret`: unused (told girsa-operator, #307); its removal is #307's.

The session is ready to clear.
