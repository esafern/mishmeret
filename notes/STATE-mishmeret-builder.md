# mishmeret-builder - current state

Rewritten in place when a piece lands and at the end of a session; the log is `notes/LOG.md`, by item.

## Built, on main

- c1963d1: A (`guard.foreign`), A2 (seven config fields optional) and B (Mishmeret's own `.claude/`, `notes/`, the
  lane check), each verified by girsa-verifier (notes/PLAN-OWN-CLAUDE.md). The Board on 8451 runs from the main clone.
- 59178bf: the open-messages drill-down (notes/PLAN-OPEN-MESSAGES.md; the look 4e1ac02, the behaviour 59178bf),
  verified; merged by girsa-operator, not pushed. Girsa's pin bump to it is girsa-builder's.

## Now

- Copy-on-select (notes/PLAN-COPY-SELECT.md), branch `builder-copy-select` in `~/work/mishmeret-builder`, from
  59178bf. Built: 9c9fa8b (girsa-verifier's LOW 1 on 59178bf, the `#qa-N` link's test), 24d0246 (the sign's look),
  and the behaviour at the branch's tip (the mouse-up listener, its LOW 1 on the plan, the test; suite 107 passed).
  Waiting on girsa-verifier's check at the tip; then girsa-operator merges main.

## Next, in order

1. None queued after copy-on-select: ask girsa-operator for the next Mishmeret work.

## Open

- Not pinned by a test (A2): `land()`'s restart line and ledger copy with the field absent.
- The 5 s refresh redraws the corners, so a focused pill loses its focus then (page-wide; girsa-ui-steward: leave it).
