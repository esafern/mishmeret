# mishmeret-builder - current state

Rewritten in place when a piece lands and at the end of a session; the log is `notes/LOG.md`, by item.

## Built, on main

- c1963d1: A (`guard.foreign`), A2 (seven config fields optional) and B (Mishmeret's own `.claude/`, `notes/`, the
  lane check), each verified by girsa-verifier (notes/PLAN-OWN-CLAUDE.md). The Board on 8451 runs from the main clone.
- 59178bf: the open-messages drill-down (notes/PLAN-OPEN-MESSAGES.md), verified.
- 8f6771d: copy-on-select (notes/PLAN-COPY-SELECT.md; the look 24d0246), and the drill-down's LOW test 9c9fa8b,
  verified; merged by girsa-operator, not pushed; Board 8451 restarted at it. Girsa's pin bump is girsa-builder's.

## Now

- girsa-verifier's LOW 1 on 8f6771d, one round: branch `builder-copy-pins` in `~/work/mishmeret-builder`, from
  8f6771d, its tip the round's one commit (the test pins the answer's box and the left button; `button, a` dropped
  from the target rule, measured). Waiting on girsa-verifier's check at the tip; then girsa-operator merges.

## Next, in order

1. None queued: ask girsa-operator for the next Mishmeret work.

## Open

- Not pinned by a test (A2): `land()`'s restart line and ledger copy with the field absent.
- The 5 s refresh redraws the corners, so a focused pill loses its focus then (page-wide; girsa-ui-steward: leave it).
- Copy-on-select measured in headless Chromium alone, not Safari or Firefox; the focused-box rule acts only where a
  browser targets what is under the pointer (not Chromium), so no test here can show it red alone.
