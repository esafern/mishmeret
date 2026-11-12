# Mishmeret's lessons file: the plan (mishmeret-builder, 2026-11-12)

Written 09:20, revised 09:22 (`date`). ACCEPTED by girsa-verifier at 5142cbe, with nothing found: its own run of
`split.py` remakes all three drafts byte for byte. Built 09:37. This is girsa-operator's REQUEST, on the reviewer's answer to the first project's Board #182
(2026-11-11 23:36): "B - Also the six borderline: 50 move". The request and the drafts sit outside both repositories,
in the first project's copies folder (`~/work/girsa-copies/lessons-split-2026-11-10/`, where
`REQUEST-to-mishmeret-builder.txt` is the request). The plan and the build may go ahead. THE LANDING WAITS: first the
reviewer reads the six borderline lessons' Mishmeret wording and examples (girsa-operator's of 2026-11-12, in that
folder's `BEFORE-AFTER.md`; girsa-operator tells me when), then girsa-verifier checks it, then girsa-operator merges it
and moves the first project's pin (#155 B).

## The case

- The general lessons, how any session checks, tests and reports, leave the first project's `LESSONS.md` for a
  file in Mishmeret. Every role of a project run with Mishmeret then reads both: the project's own file and
  Mishmeret's, at the commit the project pins. The first project's file after the split (the draft
  `GIRSA-LESSONS.after.md`) keeps each moved lesson's number and name and points to
  `~/work/mishmeret/.pins/<that commit>/LESSONS.md`. That fixes this file's place and name.
- The text is the draft `MISHMERET-LESSONS.draft.md`: 50 lessons, each cited by name (no numbers), each with one
  example from no project in particular. The reviewer saw 44 of them (option A) with their examples. The other six
  (NO DERIVED GROUND TRUTH, FUZZY IS NOT A POSITION, EVERY ANCHOR HAS A GAP, EVERY PART NOT PART ONE, APPLYING HAS
  SIDE EFFECTS, THE PROBE THAT CANNOT SEE) they saw by name and rule only.

## The behaviour

- `LESSONS.md` at the repository's top: the draft byte for byte, in its 14:26 version (19,059 bytes, sha256
  624b7510ff2f0d7e...). That version changes one example from the 09:22 one (18,917 bytes, fa3308a4f17964e4...). The
  reviewer asked of WRITE THE ENUMERATION DOWN's Do: "what happens when a new place is added later?" As written,
  nothing catches it, since the test checks only the list. My wording, now in girsa-operator's draft word for word:
  a second test that finds every place holding the name on its own and fails on one the list lacks. It is still the
  reviewer's to accept. The opening paragraph stays the draft's. It already says what the file is, that a lesson's
  name is its id, and that a project keeps its own lessons in its own file and points here for these.
- ANSWERED by girsa-operator (09:22): "labelled" (in THE SAMPLE THAT SELECTED ITSELF) is now "labeled", changed in
  the draft itself and its three drafts remade from its `split.py`. The reviewer asked for American spelling
  (2026-11-12). Read here: "labelled" 0 times, "labeled" at line 105, one byte fewer.
- `README.md`: one bullet, so that the public page names the file: "`LESSONS.md`: the rules every session of a
  project run with Mishmeret works by, cited by name; a project's roles read it at the commit the project pins,
  beside the project's own lessons."
- `notes/BRIEF-mishmeret-builder.md`: START READS gains `LESSONS.md`, because Mishmeret is itself run with
  Mishmeret, so its rules bind this role too. The cost: 18,918 bytes more at every start.

## The measure (the draft, read from the copies folder by a script in scratch; nothing in the repository written)

- Lane check: the lane check's own patterns (`.claude/lane_check.py`'s `forbidden()`, with the main clone's roster
  read, and `PERSONAL_ADDRESS`) found 0 hits in the draft, and no personal address. The draft is ASCII only.
- Names: 50, all unique. Each is one of the 50 names that the draft `GIRSA-LESSONS.after.md` marks "in Mishmeret's
  lessons", and none is missing.
- Spelling: one British form, "labelled" (the script's candidates, read by eye: called, calling, labelled,
  otherwise, raised, your).
- Size: 18,918 bytes, as the request says. In the 09:22 version, 18,917.

## Files

- `LESSONS.md` (new), `README.md`, `notes/BRIEF-mishmeret-builder.md`. This is one notes commit (`land.py commit
  mishmeret-builder notes`, `--doc-only`: every file is a `.md`), on branch `builder-lessons` from main.
- Not changed: anything in `.claude/`, which is the operator's (the lane check refuses it from this role).
  girsa-operator agrees (09:22) that `sizes.files` should list `LESSONS.md`. The limit proposed: 25,000 bytes, about
  a third above its 18,917, with its overflow going to "a new lesson file, by the reviewer's word". The config edit
  is the operator's own commit.

## Not in this piece

- Mishmeret's code still cites the first project's numbers for four moved lessons: `land.py:7` (60),
  `config.py:13` and `config.py:25` (21, 47), and `board.py:189`, `board.py:224`, `board_server.py:374` and
  `role_usage.py:130` (59). Those numbers mean nothing to a reader of this public repository. Citing them by name
  would be a code piece of its own, on the reviewer's word. girsa-operator put it to the reviewer, as a line of
  the first project's Board #201.
- The first project's side (its `LESSONS.md`, its start reads, the pin) is girsa-operator's, after this lands.
- I did not run `split.py`. girsa-verifier ran it on a copy, and it remakes the draft byte for byte.
