# Plan: the gate after a code landing, over an uncommitted Apply

## The case

girsa-operator's REQUEST, 2026-11-13, on the reviewer's night directive: "`_frozen_gate` is red while an Apply is
uncommitted in the main tree (Girsa Board #495)". The first project's Board messages (read there, read only):
- #495, girsa-verifier, 2026-11-08: two after-landing gates went red on
  `test_no_candidate_re_raises_a_word_an_applied_decision_already_settled` (8 and 24 candidates) and passed minutes
  later on a copy of the main tree. Reproduced there with `_frozen_gate`'s own steps: the copy reset to HEAD, then the
  live `review_decisions.jsonl` copied in - FAILS; with HEAD's own ledger - PASSES. The main tree held girsa-operator's
  uncommitted Apply (the book's files modified, 5 apply_event rows in the live ledger): `_frozen_gate` pairs the live
  ledger with HEAD's files, which predate those rows. "Until then a red on that test while the main tree holds an
  uncommitted Apply is this, not the landing - and a real red there reads the same."
- #1086, girsa-verifier, 2026-11-12: a second test, `KeyError: '65a443f03887'`, the same class (an uncommitted Apply's
  title corrections); "It goes green once girsa-operator commits that Apply."

Prototype (`frozen_proto.py`, scratch; the placeholder project; a gate test that every applied ruling is in the
book): a main clone with an uncommitted Apply (the ledger's apply row and the book file it wrote). Its own tests in the
main tree: 2 passed. `_frozen_gate` as it is: RED (1 failed). The same copy taken whole - no reset, no ledger copied
over it: 2 passed.

The first project's main tree now: one tracked file uncommitted (an `.md`); its ledger as committed. So the false red
needs both the ledger and a book file to differ from HEAD - an Apply not yet committed.

## The change (recommended: A; the design question to girsa-architect)

A. THE COPY TAKEN WHOLE: `_frozen_gate` gates the main tree as it stands - the files the review server serves, its
   live ledger with the book files that ledger was applied to, a consistent pair by construction. The reset to HEAD
   and the ledger's copy go; the check that the ledger did not change while it was copied stays, as the copy's ledger
   compared with the live one after the clone. The gate's line names the tracked files that differ from HEAD (an
   uncommitted Apply, an operator's note), so a red is read against them. Code: about 8 lines less, 3 more.
   Its cost: an uncommitted code edit in the main tree (the operator's, which it lands as a commit the same day) is
   gated with the landing; the line names it.
B. HEAD'S OWN PAIR: when the live ledger and another tracked file both differ from HEAD, the copy keeps HEAD's own
   ledger, and the line says the live rulings were not gated. Its cost: the live rulings are not gated whenever main
   holds an uncommitted Apply - the case the live ledger was put in for (girsa-architect's Q4 on the landing script).

## Files

- mishmeret/land.py (`_frozen_gate`), tests/test_guard.py
- notes/PLAN-FROZEN-GATE.md, notes/LOG.md, notes/STATE-mishmeret-builder.md

## Tests (each rule's test shown red with the rule taken out)

1. A main clone holding an uncommitted Apply (placeholders): the gate after a landing green, and its line naming the
   uncommitted file; red as today with the reset put back.
2. The ledger changed while copied: refused, as today.
3. The existing landing test (the frozen copy holds the live rulings file) unchanged and green.

## For the first project

None in its config; at its pin bump the after-landing gate gates the main tree as it stands. A red there with an
uncommitted Apply then reads as that Apply's or the landing's, never the pairing's.

## Not in this piece

The Board's hold by session (girsa-operator's next item).
