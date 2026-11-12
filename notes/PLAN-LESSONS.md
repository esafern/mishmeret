# Mishmeret's lessons file: the plan (mishmeret-builder, 2026-11-12)

Written 09:20 (`date`). This is girsa-operator's REQUEST, on the reviewer's answer to the first project's Board #182
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

- `LESSONS.md` at the repository's top: the draft byte for byte, apart from the one change below if girsa-operator
  agrees. The opening paragraph stays the draft's. It already says what the file is, that a lesson's name is its id,
  and that a project keeps its own lessons in its own file and points here for these.
- QUESTION to girsa-operator: one word, "labelled" in THE SAMPLE THAT SELECTED ITSELF, changed to "labeled". The
  reviewer asked for American spelling (2026-11-12), and this is the draft's only British spelling the measure found.
  The lesson is one of the 44 the reviewer saw. Without girsa-operator's yes, the draft goes in unchanged.
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
- Size: 18,918 bytes, as the request says.

## Files

- `LESSONS.md` (new), `README.md`, `notes/BRIEF-mishmeret-builder.md`. This is one notes commit (`land.py commit
  mishmeret-builder notes`, `--doc-only`: every file is a `.md`), on branch `builder-lessons` from main.
- Not changed: anything in `.claude/`, which is the operator's. The config's `sizes.files` does not list
  `LESSONS.md`, so the start-reading report does not cover its size. That is girsa-operator's call.

## Not in this piece

- Mishmeret's code still cites the first project's numbers for four moved lessons: `land.py:7` (60),
  `config.py:13` and `config.py:25` (21, 47), and `board.py:189`, `board.py:224`, `board_server.py:374` and
  `role_usage.py:130` (59). Those numbers mean nothing to a reader of this public repository. Citing them by name
  would be a code piece of its own, on the reviewer's word.
- The first project's side (its `LESSONS.md`, its start reads, the pin) is girsa-operator's, after this lands.
- Not checked: whether the draft is what `split.py` remakes from the first project's `LESSONS.md`. That script is
  girsa-operator's and I did not run it.
