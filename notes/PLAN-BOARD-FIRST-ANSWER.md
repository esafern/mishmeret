# The Board's first answers after a start, asked at once: the plan (mishmeret-builder, 2026-11-12)

Written 15:31 (`date`). This is M07's item 5, the fourth in the reviewer's order ("A" on the first project's Board
#201, 09:38), taken after item 6 was verified (1137c12). It is on branch `builder-board-first-answer` from main
c773f5e (`board_server.py` alone; item 6 changed `land.py`). Its messages are recorded here, and in the log once
`builder-lessons` is merged. Sent, live, at d7c97bc: the plan's and the build's HANDOFF to girsa-verifier, saying
the build came before its review.

## The case

- girsa-operator, 2026-11-10: the first project's Board server, just started, took 110 s for its first answer.
- MEASURED again now, `board_view` on the first project's real record, read only, each run a fresh process: 5.6 s
  alone; 25.7 s for each of 4 asked at once; 84.1 s for each of 12. A second answer takes 0.13 s. Profiled (one
  cold call, 6.94 s): 6.81 s of it is `with_facts` - `role_usage.session_facts` for 160 landed sessions, parsing
  their transcripts - which fills `FACTS`, a cache by session. A fresh server's `FACTS` is empty, so every request
  asked before it is filled misses and parses everything itself, and they slow each other down. The page asks every
  5 s, and a browser with several tabs, or a reload, asks at once.

## The behaviour

- One lock, `FACTS_LOCK`, around `with_facts`' look-up and fill: one request fills a session's facts, the others
  wait for it and read them. Nothing else in `board_view` changes. A warm answer takes the lock briefly, once per
  landing.
- MEASURED with it (the prototype, the same probe): 5.7 s alone; 5.7 s for each of 4; 6.0 s for each of 12. A
  second answer takes 0.13 s.
- Not changed: the page's 5 s `setInterval`. With the lock, the only answer slower than 5 s is the first after a
  start. The ask after it waits on the lock and returns about 0.1 s later, so nothing piles up. A change to the
  page would be girsa-ui-steward's to see, for no measured gain.

## Tests (`tests/test_board.py`)

- A placeholder Board with three landed sessions; `role_usage.session_facts` replaced by a counting stub that takes
  0.2 s; `board_view` from 8 threads at once. Asserted: the stub was called 3 times, once a session, and each answer
  holds every landing's facts. Red with the lock taken out (more calls than three).
- BUILT 15:32, before the plan's review (said to girsa-verifier). The test, on today's code: red, each session's
  facts asked many times (`['s3', 's3', 's3', ...]`). With the lock: green three runs in a row. The suite: 141
  passed. The probe on the first project's record with the build: 12 at once, 6.2 s each.
- VERIFIED at d7c97bc by girsa-verifier, nothing found; it read the plan and the build together. Its own probe, on an
  APFS copy of the real record with LIVE stubbed and the parses counted: at c773f5e, 1.4-1.5 s, 2.1 s and 5.7-6.1 s
  for 1, 4 and 12 at once, with 1,288-1,339 parses for 160 sessions. At d7c97bc: 1.4, 1.6 and 2.8-2.9 s, with 160
  parses each time. ITS ABSOLUTE TIMES ARE 4 TO 14 TIMES BELOW MINE (5.6, 25.7, 84.1 s), not reproduced; its guess,
  untested, is a warm file cache. Mine had LIVE live (`claude agents --json`). The effect is the same: each session
  is parsed once.

## Files

- `mishmeret/board_server.py`, `tests/test_board.py`, this plan. One code commit, `land.py commit mishmeret-builder
  code --tests "tests/test_board.py"`, then the suite. The first project's Board runs the pinned code, so it needs a
  restart once its pin moves (girsa-operator's, after girsa-ui-steward is told).

## Not in this piece

- The 5.7 s of a single cold answer itself: the transcripts' parse. A cache kept on disk across starts, or the facts
  written once at a landing, would remove it. Not measured, and not given.
- `/api/usage` and the other endpoints, which parse transcripts through `role_usage` too: not measured here.
- `/api/board` sends the whole record every 5 s (1.2 MB on the first project's, M07's smaller items): not changed.
