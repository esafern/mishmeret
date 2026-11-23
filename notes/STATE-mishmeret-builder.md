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

- ON MAIN 367380a (girsa-operator's merges; 4 ahead of origin - main pushed since on the reviewer's word): the known
  gaps' seven (M15), Mishmeret's own skills (M16), and git's command list as a classification (M17; the first
  project's #302 A), VERIFIED. The first project pins 075f49a; its pin bump is girsa-verifier's first, after the
  classification's LOW 1 fix lands.
- Branch `builder-git-classification` at this commit, on main 367380a:
  - fa53cb2, the classification's LOW 1 (an index named by a command substitution), with girsa-verifier;
  - 7cbe089, A ROLE RUN BY PI built (notes/PLAN-PI-ROLE.md; M18; its plan READY on three conditions, all built;
    170 passed; 14 rules red). Waiting: girsa-verifier's check at this commit.
  The pi prototype and rule 45's files stay in the scratchpad (pi-proto/, r45c/).
- Waiting on the reviewer: the first project's Board #304 (refs judged by the repository, and the found writers), a
  later piece.
- Done with, to delete: every merged `builder-*` branch.
- To resume: `git -C ~/work/mishmeret log --oneline -3`; `git -C ~/work/mishmeret-builder status -sb`; the Board.

## Next, in order

1. girsa-verifier's check of fa53cb2 and of the pi build; its findings in one round; then girsa-operator's merge.
2. THE SKILLS SHIPPED TO EVERY PROJECT (the reviewer's "Both" and "all of the above"): a plan - status-report made
   general, landing, sessions, push and pin - its first measure how a project, and a pi role (`--skill PATH`), takes
   a pinned skill.
3. #304, when the reviewer answers it.

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
