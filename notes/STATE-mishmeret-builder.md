# mishmeret-builder - current state

Rewritten in place when a piece lands and at the end of a session; the log is `notes/LOG.md`, by item.

## Built, on main (main 9b979d3, 1 ahead of origin; each verified by girsa-verifier, merged by girsa-operator)

- To 2026-11-13 (M01-M13): own `.claude/`, open messages, copy-on-select, the start scripts, finishing a session, the
  guard's mask, M07's items, `LESSONS.md`, the audit's fixes, /expiring.ics, the land.py race, the frozen gate, the
  hold by session.
- b01f7d0, 075f49a, f2126a1: the known gaps' first eight (PLAN-KNOWN-GAPS; M14). The first project pins 075f49a.
- 977295f, e5a4d40, 958474f, dc30cc2: the known gaps' seven (PLAN-KNOWN-GAPS-SEVEN; M15) - two -C, cd -/popd, a case
  arm, git's own verb list and the config writes closed, a quoted verb; dc30cc2 is girsa-operator's lane check half.
- 7c48fea, 7203f57 (status-report), 59f84a2, 5bccb49 (guard-measure, its scripts): Mishmeret's own skills (M16).
- f49111a, 6575743, fa53cb2: git's command list as a classification (PLAN-GIT-CLASSIFICATION; M17; the first
  project's #302 A) - the eight writers refused where reset --hard is, 181 names in four sets.
- 654a562, 0600059, 7d6e9ad, 7cbe089: a role run by pi (PLAN-PI-ROLE; M18; #303 A) - mishmeret/pi_guard.ts, the
  config's `runner`, agents.sh's pi line.
- 137ff68, ec8c031, 89cba8b: skills shipped to every project (PLAN-SHIPPED-SKILLS; M19) - mishmeret/skills/, agents.sh's
  links, pi's `--skill`, the drift test.

## Now

- OPEN: #304 A on `builder-protected-refs` (notes/PLAN-PROTECTED-REFS.md, M20) - BUILT (110415f), VERIFIED but for
  LOWs 1-2 and NOTEs 1-2, fixed in one round (6bb1caf); with girsa-operator to land, under the `--because` words the
  skill's 4 files carry. #310 A; the reviewer's "Refuse it" (a session with no role in a role's worktree). The scratch scripts and decision files: this session's scratchpad, refs304/ (the HANDOFF names
  them). The guard-measure skill now measures by role (`each`).
- Main 9b979d3 (the notes on the first project's rewritten ids) is 1 ahead of origin: its push is the reviewer's word.
- THE FIRST PROJECT'S PIN BUMP (075f49a to main), girsa-verifier first, brings: the seven's refusals, the
  classification (girsa-builder's 3 measured writes refused), the pi guard (`runner: pi` named with the bump, then
  #303 A), and the shipped skills - with its own steps: its `.gitignore` line for `.claude/skills/mishmeret-*` below
  its `!.claude/skills/` un-ignore, and its `landing` and `operator-sessions` cut to its particulars.
- Every old builder branch is deleted (2026-11-23): 37 merged by `git branch -d`; and, on the reviewer's "delete",
  four whose content had landed under other ids (`git branch -D`; tips 7e0e8b3, 3bc9c49, 96454a1, 4b9133b), each read
  first.
- THE PIN BUMP, girsa-verifier's NOTE 4 on this piece: run the older-worktree landing on the bump's patch before it
  lands (an older pin refuses the config's `guard.refs` and `roles[].worktrees`).
- To resume: `git -C ~/work/mishmeret log --oneline -3`; `git -C ~/work/mishmeret-builder status -sb`; the Board, and
  a watcher (`board.py wait <id>`) on any Board item a piece waits on.

## Next, in order

1. #304: girsa-verifier's check of the build, its findings fixed in one round, girsa-operator's merge.
2. Git's `reference-transaction` hook, a piece of its own (girsa-architect, the first project's 350e01e37: main's branch
   and `guard.refs` by the ref, whatever writes it; its four measured points in the plan's head).

## Open

- girsa-verifier's LOW on 075f49a: PREFIX and TMUX_PREFIX are two copies of one pattern (they differ by `env -u`).
- The piped-check rule does not read a check inside a substitution after another word (`echo $(pytest | tail)`).
- A GIT_INDEX_FILE set from a variable is taken as temporary (114 such on the record, the scratch-index pattern): the
  classification's accepted cost.
- A shell write through a link into a pin meets no file-target rule (as for any pinned file; girsa-verifier's NOTE 3).
- `export GIT_DIR=<main>/.git` before git is not read by `_git_trees`, so by no rule built on it (girsa-verifier's
  NOTE 1 on the protected-refs plan); the file tools' edits into another role's worktree are not refused.
- Not measured: a pi session whose folder differs from its start folder; pi and the shipped skills on Windows and Linux;
  a skill's link changed under a running session.
- Not run live: the night and morning runs as changed (stubs only). The session scripts are macOS-only.
- A `!` command the reviewer types bypasses the hook (2026-11-12).
- A required config key cannot be added or renamed: Mishmeret pins itself (M05).
- Not pinned by a test (A2): `land()`'s restart line and ledger copy with the field absent.
- The 5 s refresh redraws the corners, so a focused pill loses focus (girsa-ui-steward: leave it).
- The first project's older worktree `...-mishmeret`: unused (told girsa-operator, #307); its removal is #307's.
