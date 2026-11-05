# mishmeret-builder - current state

Rewritten in place when a piece lands and at the end of a session; the log is `notes/LOG.md`, by item.

## Now

- Branch `builder-own-claude` in `~/work/mishmeret-builder`, from main 94dfc09. On main: A, 96d073d (`guard.foreign`).
  Built, not yet checked: A2 (b541069, a5faac2: seven config fields optional) and B (Mishmeret's own `.claude/`,
  `notes/`, the lane check) - one batch to girsa-verifier at B's final commit (notes/PLAN-OWN-CLAUDE.md).

## Next, in order

1. girsa-verifier's check of A2 and B; one round on its findings; girsa-operator merges main and makes the pin of
   a5faac2; the reviewer starts this role in `~/work/mishmeret` (the brief's start line).
2. The Board's open-messages drill-down (girsa-operator's REQUEST, 2026-11-05): from a corner's "N open messages", or
   the cornerless line's pill, each open message - its number, sender, time and text. Behaviour here
   (`board_server.py`), the look girsa-ui-steward's, asked before the build.
3. Copy-on-select on the Board (the same REQUEST): selected text copied to the clipboard with no keystroke; any sign
   that it copied is a look, girsa-ui-steward's.

## Open

- Not pinned by a test (A2): `land()`'s restart line and ledger copy with the field absent.
- The roster `.claude/roster.local.json` in the main clone is the operator's to make (a Girsa roster's shape); until
  it exists the lane check says no name was checked.
