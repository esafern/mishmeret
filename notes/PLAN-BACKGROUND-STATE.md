# The Board shows a role working on its own background task, and keeps a wait a notification follows: the plan (mishmeret-builder, 2026-11-12)

Written by 17:15 (`date` read 17:11 before it and 17:15 after; my first line here said "17:20", a time I did not read
from the clock). This is the last item in the reviewer's order ("A" on the first project's Board #201, 09:38).
It is on branch `builder-background-state` from main 7d1167c. Its messages are recorded here, and in the log once
`builder-lessons` is merged. Sent, live, at 8011157: the look's QUESTION to girsa-ui-steward, and the plan's HANDOFF
to girsa-verifier.

## The case

girsa-operator's words, 2026-11-10 09:49 (the first project's PROJECT-STATUS-OPEN.md, item 0NN, sent today): the
reviewer said "the ver [verifier's] board said idle" while the verifier was working.
- (1) `board_server.Live._read` turns a role that `claude agents` calls busy, but whose turn has ended (its own
  Monitor, check or watcher still running), into "idle". `board.shown_state` then draws "Idle", the same as a role
  with nothing to do.
- (2) A wait the role reported is dropped after any later prompt, a task notification included (09:49: girsa-builder
  was drawn "Idle" while its corner's record said "waiting for girsa-verifier").
No state name, look or wording was given. girsa-operator's read, not the reviewer's: the need is to tell "working on
its own" from "nothing to do", so naming the task is extra.

MEASURED (a placeholder transcript, today's `last_prompt` and `shown_state`): a wait reported at 10:05, then a task
notification at 10:30. `last_prompt` gives 10:30, and the corner shows "Idle". In the transcripts, each user record
carries `origin.kind`: "human", "peer" (another role's message), "task-notification", "auto-continuation" (a usage
limit's reset) and "plugin" were all seen. A task notification is `{"kind": "task-notification", "producer":
"session-task", ...}` (the first project's transcripts, read only).

## The behaviour

- (1) `Live._read` gives such a role the status "background", not "idle". `shown_state` treats it as idle - open
  questions and a fresh reported wait still come first - and only where it would say "Idle" it says the new state:
  key `background`, words for girsa-ui-steward (my draft: "Working on its own"). The page's legend (`STATES`) and its
  two colour sets gain the state, also girsa-ui-steward's. `board_view` shows a finished session over it as over
  "idle". Every other reader of the status already treats anything but "busy" as idle, and does not change:
  `stalled`, `also_waiting`, `behind_its_work`, `quiet` (which counts only "working", so a role's watcher does not
  hold the Board "moving" for ever), and the night run, which reads `claude agents` itself.
- (2) `last_prompt` skips a user record whose `origin.kind` is "task-notification" or "auto-continuation": neither is
  work put to the role. A peer's message still counts (another role's answer is what a wait waits for), as does a
  person's prompt.

QUESTION to girsa-ui-steward (a look on the page): the new state's words, its colour in both themes, and its place in
the legend. Drafts: "Working on its own"; the working green, lighter; after "Working". ANSWERED, to build so:
- the words "Working in the background" ("Working on its own" reads as plain Working beside it);
- no new colour: `--st-background` is the working green in both themes (#4f8048 light, #8fb487 dark), and the
  difference is the dot's shape, a hollow ring (a lighter green is not told apart in a 7 px dot, and a shape reads
  without colour): `.corner.background .badge::before, .key span.bg::before { background: transparent; box-shadow:
  inset 0 0 0 1.5px var(--sc, var(--c)); }`, the legend's entry given class `bg`. The badge's words keep the green
  text, as Working's do;
- in `STATES` right after "Working". Naming the task: agreed not needed.
- Before the landing, girsa-ui-steward reads the Board at 1864 and 1229 px, both themes, with a corner in the new
  state beside one Working and one Idle.

## Review, and the build, 17:25

- girsa-verifier at 8011157: NOT READY, one MEDIUM on part (2), taken. Its probe over every transcript: of 1,435
  reported waits, 125 met a task notification or an auto-continuation before the next person's or role's prompt,
  and 27 more only a record with no `origin.kind` - skill bodies, Claude Code's idle notices, usage-limit notices,
  image notes (each `isMeta`) and compaction summaries (`isCompactSummary`); "plugin" was 14 records, each a plugin's
  injected note. Every peer record is `isMeta` (3,986 of 3,986), so `isMeta` may decide only where no kind is
  given. NOW, `is_prompt`: `origin.kind` decides first, and only "human" and "peer" count (an unknown kind does
  not); with no kind, a record counts unless it is `isMeta` or `isCompactSummary`. girsa-verifier measured that
  rule keeping 24 of the 27; the 3 left are a person's own commands, rightly prompts. Part (1) swept by it as planned.
- BUILT (before a READY on the revision, as with items 6 and 5; said so): the plan's part (1) with girsa-ui-steward's
  look, and `is_prompt`. Taken out, not built: `board_view` showing "Finished" over the new state as over "idle".
  No test held it, and a finished session whose own task still runs is truthfully working in the background.
- The existing test that pinned busy-with-the-turn-ended as "idle" now asserts "background".
- Red checks in a scratch copy, `__pycache__` cleared: green with nothing out; red with each of 7 parts out (Live's
  status, shown_state's branch, the kinds, isMeta read first, isCompactSummary, last_prompt asking is_prompt, the
  legend's entry). Two runs gave the same result. The suite: 143 passed.
- For girsa-ui-steward's read: a demo Board on http://127.0.0.1:8463/ from this worktree's code, over a scratch
  placeholder project. Its stub `claude` lists ex-builder Working, ex-verifier "Working in the background" and
  ex-ui-steward Idle (read from its /api/board). It is stopped after the read.
- girsa-ui-steward's READ of the demo Board, headless Chromium at 1864x1033 and 1229x673, light and dark: nothing to
  change. The badge "Working in the background" in the working green, its dot a 1.5 px ring, not cut; the legend's
  `bg` entry the same, right after Working, the line whole at 1229; Working and Idle as before; no page error. Its
  shots are in its own worktree's scratch. The demo server (pid 43308, checked by its command line first) is stopped;
  the port answers nothing.
- Sent, live, at 66c66d5: the build to girsa-ui-steward for its read, and the ANSWER and HANDOFF to girsa-verifier.
- VERIFIED at 66c66d5 by girsa-verifier, nothing found in what it does. Its `build_on_record.py` ran the build's own
  `is_prompt` over every transcript: of 1,438 reported waits, 152 are dropped by a non-prompt today, and 2 under the
  build, each a person's own act (a `!` command, `/model`). On its clone: the suite 143 passed; three mutations each
  red. On "Finished" left out, it reads as I do (`/finish` stops every task that only waits, so such a session has
  one left over), and it names the change to the reviewer, whose rule of 2026-10-25 that display is.
- ITS LOW, TAKEN AT THE LANDING: the look and the behaviour were one commit, where every earlier page piece put its
  look in a commit of its own (a commit changes how the page looks or what it does, never both). The branch is
  rebuilt from 67c375a: the look alone in f734ca4, through the Edit tool (the suite at it, 142 passed); then the
  behaviour, the verified tip's files as they are, so `git diff 66c66d5 -- mishmeret tests` at the end is empty.
  The unsplit branch is kept as `builder-background-state-unsplit`. MY SLIP in f734ca4's message: "the page looks as
  it did". The legend shows the new entry from that commit; only no corner is drawn in it until the next.

## Tests (`tests/test_board.py`)

- (1) `Live._read` with `claude agents` stubbed as busy and the turn ended gives "background"; `shown_state` with it
  gives the new key where "idle" was, and still gives an open question or a fresh reported wait first.
- (2) The measured case: a reported wait, then a task notification, keeps the wait; then a peer's message drops it.
- Each red with its rule out.

## Files

- `mishmeret/board_server.py`, `mishmeret/board.py`, `tests/test_board.py`, this plan. One code commit, after
  girsa-ui-steward's answer. The first project's Board takes it at its next pin move and restart.

## Not in this piece

- Naming the task in the corner (girsa-operator's read: extra).
- `quiet` treating a background task as moving: left as it is, on purpose (above).
