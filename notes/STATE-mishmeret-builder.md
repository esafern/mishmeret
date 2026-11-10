# mishmeret-builder - current state

Rewritten in place when a piece lands and at the end of a session; the log is `notes/LOG.md`, by item.

## Built, on main (7b9c6e0, not pushed; each verified by girsa-verifier, merged by girsa-operator)

- c1963d1: A (`guard.foreign`), A2 (seven config fields optional) and B (Mishmeret's own `.claude/`, `notes/`, the
  lane check) (notes/PLAN-OWN-CLAUDE.md). The Board on 8451 runs from the main clone.
- 59178bf: the open-messages drill-down (notes/PLAN-OPEN-MESSAGES.md).
- 8f6771d, 31ac716: copy-on-select and its LOW round (notes/PLAN-COPY-SELECT.md).
- 8738b21: the start scripts with no project named (notes/PLAN-START-SCRIPTS.md).
- 51499da, 7b9c6e0: finishing a session, by day and by night (notes/PLAN-FINISH.md; the log's M05) - the two finish
  commands from the config, `board.py finished`, the night run ending with no Go, the Stop hook `finish_hook.py`
  and `agents.sh --next`. The first project's side at its pin bump (girsa-operator's, girsa-builder's; the plan's
  section of that name): two `night` config fields, the Stop hook in its settings through a shim, its command files
  calling `board.py finished`; girsa-verifier owes three checks there.

## Now

- The role guard's escaped-quote fault (girsa-verifier: HIGH; notes/PLAN-GUARD-MASK.md; the log's M06): FIXED on
  `builder-guard-mask` in `~/work/mishmeret-builder`, rebased over main 7b9c6e0 - f33aad3, 529af0a, b8dac60, then
  this notes commit. girsa-verifier's one round (a MEDIUM, a LOW) is answered in b8dac60. The suite: 139 passed.
- Waiting, live: girsa-verifier's VERIFIED on it, then girsa-operator's merge. To resume: `git -C
  ~/work/mishmeret-builder log --oneline -5`; if no VERIFIED is in this session's messages, send girsa-verifier the
  branch's last commit id again.

## Next, in order

1. After that merge: its commit id to girsa-operator for the first project's pin (one bump can take both pieces).
   girsa-ui-steward asked to be told when the page's "Finished" reaches the live Board.
2. Not given as work (girsa-operator, 2026-11-10): a Board state for a session busy only with its own background task
   (`board_server.py`'s busy-to-idle rule, `board.py`'s `shown_state`) - size it; build on the reviewer's word.

## Open

- Until `builder-guard-mask` is merged and the first project's pin moves to it, every role's guard is turned off for
  the rest of a command by a string holding an escaped quote.
- `board.py landed`, the old name, is still taken: it goes once the first project's command files call `finished`.
- Not run live: the night run and the morning run as changed (behind stubs only); the hook under the first project's
  shim. Mishmeret's own config names neither finish command and its settings no Stop hook - it has no role in tmux.
- Not run on Linux: `agents.sh --next` (osascript, BSD `find -mmin`, tmux) - the sessions' scripts are macOS-only.
- The guard's mask, not checked: `$"..."` and a backtick string (girsa-verifier's forms hold them, no test here);
  the piped-check refusals and the Edit and Write side under an escaped quote.
- A required config key cannot be added or renamed: Mishmeret pins itself (the log's M05).
- Not pinned by a test (A2): `land()`'s restart line and ledger copy with the field absent.
- The 5 s refresh redraws the corners, so a focused pill loses its focus then (page-wide; girsa-ui-steward: leave it).
- Copy-on-select measured in headless Chromium alone; the page's new words too.
- The live tmux server of the first project holds an unmarked config until it ends; the roles' clean restart is the
  reviewer's.
