# mishmeret-builder - current state

Rewritten in place when a piece lands and at the end of a session; the log is `notes/LOG.md`, by item.

## Built, on main

- c1963d1: A (`guard.foreign`), A2 (seven config fields optional) and B (Mishmeret's own `.claude/`, `notes/`, the
  lane check), each verified by girsa-verifier (notes/PLAN-OWN-CLAUDE.md). The Board on 8451 runs from the main clone
  (girsa-operator, on the reviewer's Girsa Board #160 A).

## Now

- The open-messages drill-down (notes/PLAN-OPEN-MESSAGES.md), branch `builder-open-messages` in
  `~/work/mishmeret-builder`, from main c1963d1. The prototype is in the tree, uncommitted (`board_server.py`,
  `tests/test_board.py`: 21 passed). Waiting on girsa-ui-steward's look (four questions) and girsa-verifier's review
  of the plan; then the build, committed, and girsa-verifier's check at its final commit.

## Next, in order

1. Copy-on-select on the Board (girsa-operator's REQUEST, item 3; the reviewer, 2026-11-05: "girsa board should
   auto-copy highlighted text inthe c-b [clipboard]"): selected text copied with no keystroke; any sign that it
   copied is a look, girsa-ui-steward's.

## Open

- Not pinned by a test (A2): `land()`'s restart line and ledger copy with the field absent.
