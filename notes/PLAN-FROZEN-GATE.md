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
   CHOSEN (girsa-architect, the first project's design-study/MISHMERET-FROZEN-GATE-ARCHITECT.md, 76974084): A gates
   what the review servers run; B's trigger is a stand-in (Lesson 41) that would drop the live rulings whenever a ruling
   is recorded beside any uncommitted note - one such note is in that main tree now. The reset's reason (the copy
   carries the main clone's index) does not bite: outside a commit in progress the main tree's index is HEAD's, and
   land.py refuses to start a commit over a staged one. ITS TWO CHANGES, taken: the red's sentence, where the copy
   held uncommitted tracked files, names them - "read against these, the main tree's own, before it is yours" - in
   place of "the fix is yours" alone; and the cost as measured: what the landing gate reads in place there is mostly
   the operator's documents (the status pair, START_HERE.md, WRITING.md, LANE-PATHS.md, LANES.md, the finish
   commands - its file and lines), not only code. A KNOWN GAP (its own): a tracked file a running job writes, other
   than the ledger - the first project's vision verdict cache - is copied as it stands, mid-write if a paid run is in
   flight; the ledger's compare does not cover it (paid runs are rare and announced).
   girsa-verifier's read (the first project's 2b7998c1, before girsa-architect's): A. Measured there in A's form: a
   copy of its main clone taken whole at 6d688ffa, `land.py gate --tree <copy>`, exit 0, 1978 passed, 14 xfailed. ITS
   LOW 1, taken: one `cp -c -R` copies file by file, so an Apply writing during it could leave a book file cloned
   before its write beside a ledger cloned after its append - so after the clone, EVERY tracked file that differs from
   HEAD in either tree, and the ledger, is compared between the copy and the main tree; a difference refuses, as the
   ledger's check does today. Its LOW 2: the line names nothing when the main tree is clean.
B. HEAD'S OWN PAIR: when the live ledger and another tracked file both differ from HEAD, the copy keeps HEAD's own
   ledger, and the line says the live rulings were not gated. Its cost: the live rulings are not gated whenever main
   holds an uncommitted Apply - the case the live ledger was put in for (girsa-architect's Q4 on the landing script).

## Files

- mishmeret/land.py (`_frozen_gate`), tests/test_guard.py
- notes/PLAN-FROZEN-GATE.md, notes/LOG.md, notes/STATE-mishmeret-builder.md

## Tests (each rule's test shown red with the rule taken out)

1. A main clone holding an uncommitted Apply (placeholders): the gate after a landing green, and its line naming the
   uncommitted file; red as today with the reset put back. A red over an uncommitted file: its sentence names the file
   and "read against these, the main tree's own, before it is yours"; a red over none says "the fix is yours", as now.
2. The ledger, or an uncommitted tracked file, changed between the clone and the check: refused. A clean main tree:
   the line names nothing. Mutations: the line's list taken from the copy instead of the main tree; the compare
   limited to the ledger.
3. The existing landing test (the frozen copy holds the live rulings file) unchanged and green.

## For the first project

None in its config; at its pin bump the after-landing gate gates the main tree as it stands. A red there with an
uncommitted Apply then reads as that Apply's or the landing's, never the pairing's.

## Not in this piece

The Board's hold by session (girsa-operator's next item).
