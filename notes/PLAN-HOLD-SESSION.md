# Plan: the Board's hold, by session

## The case

girsa-operator's REQUEST, 2026-11-13, on the reviewer's night directive (the first project's
design-study/NIGHT-QUEUE-2026-11-12-OPERATOR.md:52-53): "the Board's hold kept by role name, so a second session of one
role ends the first's hold". The record: no instance found yet in the first project's Board messages (a search for a
hold ended by another session of its role); asked of girsa-operator. Until it answers, this is a path in the code:

- `board.hold` refuses another ROLE's hold, but takes one over its own role's without a word; `board.release` frees
  main for any session naming that role (board.py:308-327).
- Prototype (`hold_proto.py`, a scratch Board, two sessions of mishmeret-operator told apart by
  `CLAUDE_CODE_SESSION_ID`): session A `hold` - rc 0; session B `hold` - rc 0, "main held"; session B `release` - rc
  0, "main released", while A's landing would still be under way. The record: hold (A's), hold (B's), release.
- What tells two sessions apart, measured in this session (Claude Code 2.1.323): `CLAUDE_CODE_SESSION_ID`, the
  session's own id (its transcript's name), and `CLAUDE_PID`, its live claude process - both in every command's
  environment, so land.py's own `board.py hold` and `release` inherit them.

## The change

1. A hold records its session and process (`CLAUDE_CODE_SESSION_ID`, `CLAUDE_PID`) when they are set.
2. `hold`: main held by the same role from another session whose process is alive is refused, as another role's is
   ("main is held by ROLE's other session SID since TS (WHY) - wait for its release"); from a session whose process is
   gone, taken over and said; from the same session, or with no session on either side (the night run, a terminal),
   as today.
3. `release`: the same three cases - another live session's hold refused; a gone session's freed and said; the same
   session's, or no session known, as today (so the reviewer's own terminal still frees a hold by hand).

## Files

- mishmeret/board.py, tests/test_board.py
- notes/PLAN-HOLD-SESSION.md, notes/LOG.md, notes/STATE-mishmeret-builder.md

## Tests (each rule's test shown red with the rule taken out)

1. Two sessions of one role: B's hold and B's release refused while A's process is alive; A's own release taken.
2. A's process gone (a process id that runs nothing): B takes the hold over, and the line says so; B may release it.
3. No session on either side: as today (a hold, a re-hold, a release by role).
4. A hold's record carries its session and process.

## For the first project

Nothing in its config. land.py's hold and release run with the session's own variables, so a landing holds as its
session; a hold taken before the pin bump has no session and is judged by role, as today.

## Not in this piece

The page showing which session holds (a look: girsa-ui-steward's); a hold's expiry by time.
