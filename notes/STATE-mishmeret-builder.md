# mishmeret-builder - current state

Rewritten in place when a piece lands and at the end of a session; the log is `notes/LOG.md`, by item.

## Built, on main (code as of dd3bcdb, notes after it; not pushed; each verified by girsa-verifier, merged by girsa-operator)

- c1963d1: A (`guard.foreign`), A2 (seven config fields optional) and B (Mishmeret's own `.claude/`, `notes/`, the
  lane check) (notes/PLAN-OWN-CLAUDE.md). The Board on 8451 runs from the main clone.
- 59178bf: the open-messages drill-down (notes/PLAN-OPEN-MESSAGES.md).
- 8f6771d, 31ac716: copy-on-select and its LOW round (notes/PLAN-COPY-SELECT.md).
- 8738b21: the start scripts with no project named (notes/PLAN-START-SCRIPTS.md).
- 51499da, 7b9c6e0: finishing a session, by day and by night (notes/PLAN-FINISH.md; the log's M05) - the two finish
  commands from the config, `board.py finished`, the night run ending with no Go, the Stop hook `finish_hook.py`
  and `agents.sh --next`.
- f33aad3, 529af0a, b8dac60: an escaped quote inside a string no longer turns the role guard off
  (notes/PLAN-GUARD-MASK.md; the log's M06; girsa-verifier: HIGH). The suite at dd3bcdb: 139 passed.

## Now

- No piece is in work. The first project's pin is dd3bcdb since its main e955b2cf (girsa-operator's step 1 of 2:
  the pin, the finish hook's shim and Stop hook). Its step 2 - `night.finish_command`, `night.finish_exit_command`
  in its config - waits until every worktree there is at or past e955b2cf; its command files calling `board.py
  finished` are its builder's. girsa-verifier owes three checks there (the hook under the shim, the two fields, an
  older worktree's landing). The first project's Board was restarted on the pin: its page says "Finished"
  (girsa-ui-steward told, live, 17:41).
- To resume: `git -C ~/work/mishmeret log --oneline -3`; `git -C ~/work/mishmeret-builder status -sb`; ask
  girsa-operator, live, for the next work.

## Next, in order

1. A FINDING to trace, girsa-operator's, live, 2026-11-10 (the first project's status item 0NN, 17:40 there): the
   first project's Board server, restarted on the pin dd3bcdb, took 110 s for its first GET `/api/board` (1,232,472
   bytes, curl's own time), the second 0.39 s; three reads of its own with a 10-20 s limit got no byte meanwhile
   though the server's log printed 200 for each - the page would stand empty that long. Not traced, not reproduced
   here: measure it on a placeholder project first (what the first answer builds; whether a request waits on it).
2. Not given as work (girsa-operator, 2026-11-10): a Board state for a session busy only with its own background task
   (`board_server.py`'s busy-to-idle rule, `board.py`'s `shown_state`) - size it; build on the reviewer's word.

## Open

- `board.py landed`, the old name, is still taken: it goes once the first project's command files call `finished`.
- Not run live: the night run and the morning run as changed (behind stubs only); the hook under the first project's
  shim. Mishmeret's own config names neither finish command and its settings no Stop hook - it has no role in tmux.
- Not run on Linux: `agents.sh --next` (osascript, BSD `find -mmin`, tmux) - the sessions' scripts are macOS-only.
- The guard's mask, not checked: `$"..."` and a backtick string (girsa-verifier's forms hold them, no test here);
  the piped-check refusals and the Edit and Write side under an escaped quote.
- With the fix pinned, a command that passed only because an escaped quote hid it is refused: that is the fix.
- A required config key cannot be added or renamed: Mishmeret pins itself (the log's M05). The README still says
  every field is required; seven are optional since A2 and two more since M05 - not corrected.
- Not pinned by a test (A2): `land()`'s restart line and ledger copy with the field absent.
- The 5 s refresh redraws the corners, so a focused pill loses its focus then (page-wide; girsa-ui-steward: leave it).
- Copy-on-select measured in headless Chromium alone; the page's new words too.
- The first project's older worktree of this work (`...-mishmeret`) is finished with; its removal is the reviewer's.
