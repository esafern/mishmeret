---
name: mishmeret-status-report
description: Mishmeret's general procedure for the reviewer's big picture of a project run with Mishmeret - what is left in each piece and what is next, the loose ends, who waits on whom, and what waits on the reviewer - read from the project's config, its records and read-only counts; any role, when the reviewer asks; the project's own skill, if it has one, holds its particulars (its products, its releases).
---

Shipped with Mishmeret (`mishmeret/skills/`), linked into the project's `.claude/skills/` by `agents.sh` from the
commit the project pins. It reads records and runs read-only counts; it changes nothing and proposes nothing new.

**Read, in the same turn as the report** (each name is a field of the project's `.claude/mishmeret.json`):
1. The status file, `sizes.status_file`; every role's state file, `sizes.state_files`; the logs, `start_reads.logs` -
   each role's now, next, open and waiting lines. A newer state file beats an older status file on the same point,
   and the report says which it used.
2. What is LEFT, where it is written: the plan of each piece in flight, its case and its review; the latest log item's
   findings not fixed.
3. The Board, `board_dir`: `board.py list --open`, and each role's corner, its last `status` record.
4. The counts, run then: main against origin (`git rev-list --count origin/main..main`, said "not fetched" unless
   fetched in that turn); branches not merged; worktrees and whether a session runs in each; the project's
   `mishmeret_commit` against Mishmeret's main; the suite's size from `pytest --collect-only -q`, never a grep.

**The report, the reviewer's questions first:**
1. Each piece in flight: how much is left to land it - plan, review, build, check, merge, push - each by its record.
2. What is next, and its size: an estimate labeled as the role's, with the pace it rests on and what would make it
   wrong.
3. Loose ends and technical debt: open lines, review findings left for a later touch, tests red or skipped,
   housekeeping (commits not pushed, branches merged and not deleted).
4. Now: each role's piece, and who waits on whom - a role waiting on an idle one, or a corner older than its role's
   last commit, named first.
5. What waits on the reviewer: each item, why it is theirs, what happens on their answer, its Board item or path.

**The rules:**
- Every count is copied with its source named, or run in that turn with its command named; a sentence of absence
  likewise.
- An estimate is a number with its basis; never a date no record holds. A list of what each role does is not an
  answer to "how much is left".
- It ends by naming what it rests on and what it did not check. The full report goes on the Board (`board.py qa`); the
  pane gets the answers in short and the Board's link.
