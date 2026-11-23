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

- ON MAIN ff94f3f (girsa-operator's merges; 12 ahead of origin, not pushed - the reviewer's word in its pane): the
  known gaps' seven (M15) with dc30cc2, the lane check's half; the pi plan (654a562, 0600059); Mishmeret's own skills,
  status-report and guard-measure, VERIFIED, guard-measure's two LOWs fixed (5bccb49). The first project pins
  075f49a; its pin bump is girsa-verifier's first.
- THE CLASSIFICATION (notes/PLAN-GIT-CLASSIFICATION.md; M17; the first project's #302 A), branch
  `builder-git-classification` from main ff94f3f: the plan at this commit, measured on a prototype in the scratchpad
  (cls/mishmeret/role_guard.py; rule 45's files in r45c/). Waiting: girsa-verifier's review, girsa-architect on its
  two departures; then the build.
- THE PI PLAN (notes/PLAN-PI-ROLE.md; M16): girsa-verifier READY on three conditions - its LOW 1 (an edit's and a
  write's text to the time rule), LOW 2 (the extension calls the project's own hook, `.claude/hooks/role_guard.py`
  through the shim, not the guard beside it), NOTE 1 measured (pass every argument of bash's execute through, ctx
  among them; the cwd run equals the cwd judged). With NOTE 2 (a config naming `runner` lands with its pin bump) and
  NOTE 3 (`--no-extensions` in agents.sh's line). The first project's #303 answered A: a guarded pi role lands there.
  The prototype stays in the scratchpad (pi-proto/); the plan's appendix holds the extension.
- Done with, to delete: every merged `builder-*` branch.
- To resume: `git -C ~/work/mishmeret log --oneline -3`; `git -C ~/work/mishmeret-builder status -sb`; the Board.

## Next, in order

1. THE CLASSIFICATION: the review, its findings, the build (the prototype's code, with tests and mutate.py), rule 45.
2. PI: the plan revised on the review's conditions, NOTE 1 measured, then the build.
3. THE SKILLS SHIPPED TO EVERY PROJECT (the reviewer's "Both" and "all of the above"): a plan - status-report made
   general, landing, sessions, push and pin - its first measure how a project, and a pi role (`--skill PATH`), takes
   a pinned skill.

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
