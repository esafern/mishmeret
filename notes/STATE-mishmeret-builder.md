# mishmeret-builder - current state

Rewritten in place when a piece lands and at the end of a session; the log is `notes/LOG.md`, by item.

## Built, on main (main f031698 = origin; each verified by girsa-verifier, merged by girsa-operator)

- c1963d1 (own `.claude/`), 59178bf (open messages), 8f6771d, 31ac716 (copy-on-select), 8738b21 (start scripts).
- 51499da, 7b9c6e0: finishing a session by day and by night (PLAN-FINISH; M05).
- f33aad3, 529af0a, b8dac60: an escaped quote no longer turns the guard off (PLAN-GUARD-MASK; M06).
- 21cb9ba (push forms), db17aac (git after a keyword, behind options, quoted; every cd), 1137c12 (land.py on a
  signal), d7c97bc (the Board's first answers), 5aa9a0a (a subagent is no role), f734ca4 and febf285 (working in
  the background) - M07's items (M08).
- f87e3ce: `LESSONS.md` (PLAN-LESSONS; M08).
- d6a8ce7, 090253c (with girsa-operator's f7c7d1d): my audit's seven fixes (PLAN-AUDIT-FIXES; M09).
- a24377d, 6039283: what expires, /expiring.ics (PLAN-EXPIRING; M10). The first project's five rows are in
  (girsa-operator's 607e871a there); the reviewer subscribes once (On My Mac, alerts kept).
- fd2178e, 159ea56: the land.py race (PLAN-LAND-RACE; M11). e63b4a2: the gate takes the main tree whole
  (PLAN-FROZEN-GATE; M12). c8af403: the Board's hold is its session's (PLAN-HOLD-SESSION; M13).
- The first project pins f031698 (f00c256a there); every tree of it that lands pins it (girsa-operator, 2026-11-13).

- b01f7d0, 075f49a, f2126a1: the known gaps' first eight (notes/PLAN-KNOWN-GAPS.md; M14). Item 1 (HIGH, found while
  measuring): a quoted word in git's options or before git hid the command from every rule. Also items 2, 7, 8, 11-14
  and 16. Verified at 075f49a; main f2126a1 = origin (pushed). The first project pins 075f49a (its #224 A).

## Now

- THE KNOWN GAPS' SEVEN (notes/PLAN-KNOWN-GAPS-SEVEN.md; M15): VERIFIED at 958474f, merged by girsa-operator (main
  958474f, then its dc30cc2, the lane check's half). Not pushed (main 5 ahead of origin: the reviewer's word in
  girsa-operator's pane). The first project's pin bump next, girsa-verifier first; it pins 075f49a.
- ONE BRANCH, `builder-own-skills`, on main dc30cc2: the pi plan (654a562, revised at this commit on girsa-architect's
  78c32beb answer), and Mishmeret's own skills - status-report (7c48fea, 7203f57; its first report Mishmeret's Board
  Q&A #1) and guard-measure (59f84a2, its scripts and tests/test_guard_measure.py). `builder-pi-role` is its first
  commit only.
- Waiting: girsa-verifier's check of the two skills and review of the pi plan (one HANDOFF). Then the skills go to
  girsa-operator; the pi build follows on this branch. The prototype stays in the scratchpad (pi-proto/: guard.ts,
  guard2.ts, fake.ts, fake_server.py); the plan's appendix holds the extension.
- Waiting on the reviewer: the first project's #303 (may a guarded pi role land there); the push of Mishmeret's main
  (its word in girsa-operator's pane).
- Waiting on the reviewer: the first project's Board #302 (the eight git writers in no verb set). With its answer, item
  6a's list becomes the classification (each name in a verb set or in a named set that changes nothing; a test red on
  a name in neither).
- Done with, to delete: every merged `builder-*` branch.
- To resume: `git -C ~/work/mishmeret log --oneline -3`; `git -C ~/work/mishmeret-builder status -sb`; the Board;
  #302 in the first project's Board record (`~/work/girsa-board/board.jsonl`).

## Next, in order

1. PI: girsa-verifier's review, then the build (the reviewer: "before the skills do the plan and design question").
2. THE SKILLS SHIPPED TO EVERY PROJECT (the reviewer's "Both" and "all of the above"): a plan - status-report made
   general, landing, sessions, push and pin - its first measure how a project, and a pi role (`--skill PATH`), takes
   a pinned skill.
3. Item 6a's classification, on #302's answer.

## Open

- girsa-verifier's LOW on 075f49a: PREFIX and TMUX_PREFIX are two copies of one pattern (they differ by `env -u`).
- The piped-check rule does not read a check inside a substitution after another word (`echo $(pytest | tail)`),
  on f031698 too.
- Not run live: the night and morning runs as changed (stubs only). Not run on Linux: the session scripts (macOS-only).
- A `!` command the reviewer types bypasses the hook (2026-11-12).
- A required config key cannot be added or renamed: Mishmeret pins itself (M05).
- Not pinned by a test (A2): `land()`'s restart line and ledger copy with the field absent.
- The 5 s refresh redraws the corners, so a focused pill loses focus (girsa-ui-steward: leave it).
- Copy-on-select measured in headless Chromium alone.
- The first project's older worktree `...-mishmeret` is finished with; its removal is the reviewer's.

The session is ready to clear.
