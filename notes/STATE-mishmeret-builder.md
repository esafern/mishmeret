# mishmeret-builder - current state

Rewritten in place when a piece lands and at the end of a session; the log is `notes/LOG.md`, by item.

## Built, on main (main 4715362, 8 ahead of origin; each verified by girsa-verifier, merged by girsa-operator)

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
  the guard-measure skill measures by role (`each`). The skill's 4 files under `--because` "Your word, --because
  (Recommended)".

## Now

- No piece is open. Main 4715362 is 8 ahead of origin: its push is the reviewer's word in girsa-operator's pane.
- THE FIRST PROJECT'S PIN BUMP (075f49a to main), girsa-verifier first, brings: the seven's refusals, the
  classification, the pi guard (`runner: pi` with the bump), the shipped skills, and the protected refs. Its own
  steps: the `.gitignore` line for `.claude/skills/mishmeret-*` below its `!.claude/skills/` un-ignore; its `landing`
  and `operator-sessions` cut to its particulars; its config's `guard.refs` (`known-good`, `alpha-rc*`, `demo-good`)
  and `roles[].worktrees`, landing with the bump; and girsa-verifier's NOTE 4 - the older-worktree landing run on the
  bump's patch before it lands (an older pin refuses the two fields).
- To resume: `git -C ~/work/mishmeret log --oneline -3`; `git -C ~/work/mishmeret-builder status -sb`; the Board, and
  a watcher (`board.py wait <id>`) on any Board item a piece waits on. A code round on girsa-verifier's findings goes
  back to it once before LANDED-READY.

## Next, in order

1. Git's `reference-transaction` hook, a piece of its own (girsa-architect, the first project's 350e01e37): main's
   branch and `guard.refs` guarded by the ref, whatever writes it; its four measured points in PLAN-PROTECTED-REFS's
   head (read the ref's own value; no landing mark; one function for both callers; the escapes to close).

## Open

- girsa-verifier's LOW on 075f49a: PREFIX and TMUX_PREFIX are two copies of one pattern (they differ by `env -u`).
- The piped-check rule does not read a check inside a substitution after another word (`echo $(pytest | tail)`).
- A GIT_INDEX_FILE set from a variable is taken as temporary (114 such on the record): the classification's cost.
- A shell write through a link into a pin meets no file-target rule (as for any pinned file).
- `export GIT_DIR=<main>/.git` before git is not read by `_git_trees`, so by no rule built on it (girsa-verifier's
  NOTE 1 on the protected-refs plan); the file tools' edits into another role's worktree are not refused.
- eval of a variable or a substitution (`X='git reset --hard'; eval "$X"`, `eval $(echo git ...)`) is not read
  (girsa-verifier's NOTE on 6bb1caf): the record's 10 such are none git; a same-command variable could go through
  `_expand`.
- A branch checked out nowhere (a role's parked branch) is no one's; a protected branch checked out a second time
  before the rule is moved by a commit there (PLAN-PROTECTED-REFS's named costs).
- Not measured: a pi session whose folder differs from its start folder; pi and the shipped skills on Windows and Linux;
  a skill's link changed under a running session.
- Not run live: the night and morning runs as changed (stubs only). The session scripts are macOS-only.
- A `!` command the reviewer types bypasses the hook (2026-11-12).
- A required config key cannot be added or renamed: Mishmeret pins itself (M05).
- Not pinned by a test (A2): `land()`'s restart line and ledger copy with the field absent.
- The 5 s refresh redraws the corners, so a focused pill loses focus (girsa-ui-steward: leave it).
- The first project's older worktree `...-mishmeret`: unused (told girsa-operator, #307); its removal is #307's.
