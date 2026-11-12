# The Board shows a role working on its own background task, and keeps a wait a notification follows: the plan (mishmeret-builder, 2026-11-12)

Written 17:20 (`date`). This is the last item in the reviewer's order ("A" on the first project's Board #201, 09:38).
It is on branch `builder-background-state` from main 7d1167c. Its messages are recorded here, and in the log once
`builder-lessons` is merged.

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
the legend. Drafts: "Working on its own"; the working green, lighter; after "Working".

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
