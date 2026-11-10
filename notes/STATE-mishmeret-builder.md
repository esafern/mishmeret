# mishmeret-builder - current state

Rewritten in place when a piece lands and at the end of a session; the log is `notes/LOG.md`, by item.

## Built, on main (8738b21, not pushed; each verified by girsa-verifier, merged by girsa-operator)

- c1963d1: A (`guard.foreign`), A2 (seven config fields optional) and B (Mishmeret's own `.claude/`, `notes/`, the
  lane check) (notes/PLAN-OWN-CLAUDE.md). The Board on 8451 runs from the main clone.
- 59178bf: the open-messages drill-down (notes/PLAN-OPEN-MESSAGES.md).
- 8f6771d, 31ac716: copy-on-select and its LOW round (notes/PLAN-COPY-SELECT.md).
- 8738b21: the start scripts with no project named (notes/PLAN-START-SCRIPTS.md) - a run with no MISHMERET_CONFIG
  stops; the Go keeps the shim's mark; every role launched with the config dropped.
- Girsa's pin bumps to these are girsa-builder's (Girsa Board #172, #195); the first project's stopgap `env -u
  MISHMERET_CONFIG -u MISHMERET_AS` can go after its roles' next restart through its own scripts, once bumped.

## Now

- Finishing a session, by day and by night (notes/PLAN-FINISH.md; the first project's Board #183, A; the log's M05):
  the plan is written, nothing built. `~/work/mishmeret-builder` on `builder-finish`, main plus the plan's commit.
- Waiting, live: girsa-architect's answers to the plan's questions 1 and 2, girsa-ui-steward's to 3 (the page's
  words), girsa-verifier's review of the plan. To resume: read the plan; if no answer is in this session's messages,
  send the three again.

## Next, in order

1. Build the plan's three parts, a commit each: the word (config `night.finish_command`, `board.py finished`, the
   page), the night run's end without a Go, the Stop hook and `agents.sh --next`. Then girsa-verifier's check at the
   last commit, girsa-operator's merge, and the commit id to girsa-operator (it takes its `/land` pointer down after
   the pin moves; the first project's config and settings change at that bump - the plan's last section but one).
2. Not given as work (girsa-operator, 2026-11-10): a Board state for a session busy only with its own background task
   (`board_server.py`'s busy-to-idle rule, `board.py`'s `shown_state`) - size it; build on the reviewer's word.

## Open

- Not pinned by a test (A2): `land()`'s restart line and ledger copy with the field absent.
- The 5 s refresh redraws the corners, so a focused pill loses its focus then (page-wide; girsa-ui-steward: leave it).
- Copy-on-select measured in headless Chromium alone, not Safari or Firefox; the focused-box rule acts only where a
  browser targets what is under the pointer (not Chromium), so no test here can show it red alone.
- The live tmux server of the first project holds an unmarked config until it ends; the roles' clean restart is the
  reviewer's.
