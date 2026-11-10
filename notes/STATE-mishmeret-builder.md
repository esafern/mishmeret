# mishmeret-builder - current state

Rewritten in place when a piece lands and at the end of a session; the log is `notes/LOG.md`, by item.

## Built, on main (8738b21, not pushed; each verified by girsa-verifier, merged by girsa-operator)

- c1963d1: A (`guard.foreign`), A2 (seven config fields optional) and B (Mishmeret's own `.claude/`, `notes/`, the
  lane check) (notes/PLAN-OWN-CLAUDE.md). The Board on 8451 runs from the main clone.
- 59178bf: the open-messages drill-down (notes/PLAN-OPEN-MESSAGES.md).
- 8f6771d, 31ac716: copy-on-select and its LOW round (notes/PLAN-COPY-SELECT.md).
- 8738b21: the start scripts with no project named (notes/PLAN-START-SCRIPTS.md).

## Now

- Finishing a session, by day and by night (notes/PLAN-FINISH.md, revised; the first project's Board #183 A and the
  reviewer's "add finish-and-exit"; the log's M05): BUILT on `builder-finish` in `~/work/mishmeret-builder` -
  51499da, checked by girsa-verifier (the code holds; one MEDIUM, a missing test leg), and the commit after it, that
  leg. The suite: 138 passed.
- The role guard's escaped-quote fault (girsa-verifier: HIGH): FIXED on `builder-guard-mask`, from main - ede5952 and
  0cff45c (notes/PLAN-GUARD-MASK.md). That branch does not touch this file or the log.
- Waiting, live: girsa-verifier's word on the leg's commit and its check of 0cff45c; then girsa-operator's merges,
  whichever is verified first, the other rebased after it (notes only should collide). To resume: `git -C
  ~/work/mishmeret-builder log --oneline -3 builder-finish builder-guard-mask`; if no VERIFIED is in this session's
  messages, send each HANDOFF again with its commit's id.

## Next, in order

1. After the merge: the commit's id to girsa-operator (its `/land` pointer comes down after the pin moves) and to
   girsa-verifier (its older-worktree check at the pin bump); girsa-ui-steward asked to be told when the words reach
   the live Board. The first project's side is the plan's section of that name: two config fields, the Stop hook in
   its settings through a shim, its command files calling `board.py finished`.
2. Not given as work (girsa-operator, 2026-11-10): a Board state for a session busy only with its own background task
   (`board_server.py`'s busy-to-idle rule, `board.py`'s `shown_state`) - size it; build on the reviewer's word.

## Open

- `board.py landed`, the old name, is still taken: it goes once the first project's command files call `finished`.
- Until `builder-guard-mask` is merged and the first project's pin moves to it, every role's guard is turned off for
  the rest of a command by a string holding an escaped quote.
- Not run live: the night run and the morning run as changed (behind stubs only); the hook under the first project's
  shim. Mishmeret's own config names neither finish command and its settings no Stop hook - it has no role in tmux.
- Not run on Linux: `agents.sh --next` (osascript, BSD `find -mmin`, tmux) - the sessions' scripts are macOS-only.
- A required config key cannot be added or renamed: Mishmeret pins itself (the log's M05).
- Not pinned by a test (A2): `land()`'s restart line and ledger copy with the field absent.
- The 5 s refresh redraws the corners, so a focused pill loses its focus then (page-wide; girsa-ui-steward: leave it).
- Copy-on-select measured in headless Chromium alone; the page's new words too.
- The live tmux server of the first project holds an unmarked config until it ends; the roles' clean restart is the
  reviewer's.
