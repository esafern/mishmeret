# Plan: the Board's hold, by session

## The case

girsa-operator's REQUEST, 2026-11-13, on the reviewer's night directive (the first project's
design-study/NIGHT-QUEUE-2026-11-12-OPERATOR.md:52-53): "the Board's hold kept by role name, so a second session of one
role ends the first's hold". THE RECORD (girsa-operator's ANSWER; the first project's PROJECT-STATUS-OPEN.md:4456,
item 0NE, 2026-11-08): "15:34: the Antigravity operator's release ended mine of 15:28 mid-gate" - girsa-operator in
Claude Code held main for a gate; a second session running as girsa-operator outside Claude Code, with no
`CLAUDE_CODE_SESSION_ID`, released "its" hold and freed the first's. Board #168 A there since forbids such a session
any hold, so the same path today needs two Claude Code sessions of one role (a restart, a resumed pane beside a live
one) - or any command run with no session, which is what the 11-08 release was. The path in the code:

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
2. ONE RULE FOR BOTH, `hold` and `release`, on a hold of the same role: a hold whose session's process is ALIVE is
   that session's alone - another session, AND A COMMAND WITH NO SESSION (the 11-08 release), is refused ("main is held
   by ROLE's session SID since TS (WHY), its process alive - release it from that session"); a hold whose session's
   process is gone is taken over or freed, and said; a hold with no session (the night run's, a terminal's, one taken
   before the pin bump) is judged by role, as today; the holding session itself, as today. A live session's hold left
   behind (a land.py killed outright while its session lives on) is freed from that session - by the reviewer too, as
   `! python3 .claude/board/board.py release --role ROLE` in its pane, which runs with that session's variables.

## Files

- mishmeret/board.py, tests/test_board.py
- notes/PLAN-HOLD-SESSION.md, notes/LOG.md, notes/STATE-mishmeret-builder.md

## Tests (each rule's test shown red with the rule taken out)

1. Two sessions of one role: B's hold and B's release refused while A's process is alive; A's own release taken.
2. A command with no session against A's live hold: its hold and its release refused (the 11-08 case).
3. A's process gone (a process id that runs nothing): B, or a command with no session, takes the hold over or frees
   it, and the line says so.
4. No session on either side: as today (a hold, a re-hold, a release by role).
5. A hold's record carries its session and process.

## For the first project

Nothing in its config. land.py's hold and release run with the session's own variables, so a landing holds as its
session; a hold taken before the pin bump has no session and is judged by role, as today.

## Not in this piece

The page showing which session holds (a look: girsa-ui-steward's); a hold's expiry by time.
