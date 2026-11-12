# mishmeret-builder - current state

Rewritten in place when a piece lands and at the end of a session; the log is `notes/LOG.md`, by item.

## Built, on main (code as of db17aac, notes to c773f5e; origin at 158993f, the reviewer's push pending; each verified by girsa-verifier, merged by girsa-operator)

- c1963d1: A (`guard.foreign`), A2 (seven config fields optional) and B (Mishmeret's own `.claude/`, `notes/`, the
  lane check) (notes/PLAN-OWN-CLAUDE.md). The Board on 8451 runs from the main clone.
- 59178bf: the open-messages drill-down (notes/PLAN-OPEN-MESSAGES.md).
- 8f6771d, 31ac716: copy-on-select and its LOW round (notes/PLAN-COPY-SELECT.md).
- 8738b21: the start scripts with no project named (notes/PLAN-START-SCRIPTS.md).
- 51499da, 7b9c6e0: finishing a session, by day and by night (notes/PLAN-FINISH.md; the log's M05) - the two finish
  commands from the config, `board.py finished`, the night run ending with no Go, the Stop hook `finish_hook.py`
  and `agents.sh --next`.
- f33aad3, 529af0a, b8dac60: an escaped quote inside a string no longer turns the role guard off
  (notes/PLAN-GUARD-MASK.md; the log's M06; girsa-verifier: HIGH).
- 21cb9ba: the operator's push refused for a force or a delete in any form (M07 item 4; notes/PLAN-PUSH-FORMS.md).
- db17aac (with db7b0ff, 828abdc): the guard sees git after a shell keyword, behind its own options and written
  quoted; every tree git may use, every cd in order, a cd quoted, optioned or by pushd (M07 item 1;
  notes/PLAN-GUARD-KEYWORDS.md). The first project's pin is db17aac. The suite at db17aac: 140 passed.

## Now

- THE LESSONS FILE (notes/PLAN-LESSONS.md; the log's M08): girsa-operator's REQUEST, on the reviewer's "B - Also
  the six borderline: 50 move" (the first project's Board #182). `LESSONS.md` at the top, from the draft in
  `~/work/girsa-copies/lessons-split-2026-11-10/`, now its 14:26 version (19,059 bytes; one example changed on the
  reviewer's question). BUILT on branch `builder-lessons`, rebased on main c773f5e: the plan was accepted by
  girsa-verifier, and the suite passed (140). The LANDING WAITS for the reviewer's read of the six borderline
  lessons and of the changed example (girsa-operator tells me), then girsa-verifier's check at the final commit,
  then girsa-operator's merge with its `sizes.files` entry and the pin.
- To resume: `git -C ~/work/mishmeret log --oneline -3`; `git -C ~/work/mishmeret-builder status -sb` (on
  `builder-lessons`); the log's M08.

## Next, in order

GIVEN (the reviewer's "A" on the first project's Board #201, 09:38, 2026-11-12), one plan at a time, each checked
by girsa-verifier before the next; plans go to girsa-operator. Items 4 and 1 are done. The log's M07 has each:

1. M07's item 6: `land.py` ended by a signal (a tool's time limit) runs no `finally`, so the Board's hold and the
   staged names stay. Reasoned, not run. NEXT: its plan, on a new branch from main.
2. M07's item 5: the Board's slow first answer - each request builds the whole answer itself (5.0 s alone, 68.5 s
   for 12 at once); one lock around the build, and the page not asking again while it waits.
3. M07's item 2 (a subagent's type judged as the role), and the Board state for a session busy only with its own
   background task (`board_server.py`'s busy-to-idle rule, `board.py`'s `shown_state`).

Not given: the code's citations of the first project's lesson numbers; M07's smaller items.

## Open

- `board.py landed`, the old name, is still taken: the first project's tracked files no longer call it (M07).
- Not run live: the night run and the morning run as changed (behind stubs only); the hook under the first project's
  shim. Mishmeret's own config names neither finish command and its settings no Stop hook - it has no role in tmux.
- Not run on Linux: `agents.sh --next` (osascript, BSD `find -mmin`, tmux) - the sessions' scripts are macOS-only.
- The guard's mask, not checked: `$"..."` and a backtick string (girsa-verifier's forms hold them, no test here);
  the piped-check refusals and the Edit and Write side under an escaped quote.
- The guard, not in M07 items 1 and 4 (their plans' "Not in this piece"): two `-C`s, `cd -`, a bare `cd`, a cd or
  git option through a variable, a force from git's config or an alias, a `case` pattern's `)`. A `!` command the
  reviewer types bypasses the hook (the reviewer's own run, 2026-11-12), so a delete refused to the operator runs that way.
- A required config key cannot be added or renamed: Mishmeret pins itself (the log's M05). The README still says
  every field is required; seven are optional since A2 and two more since M05 - not corrected.
- Not pinned by a test (A2): `land()`'s restart line and ledger copy with the field absent.
- The 5 s refresh redraws the corners, so a focused pill loses its focus then (page-wide; girsa-ui-steward: leave it).
- Copy-on-select measured in headless Chromium alone; the page's new words too.
- The first project's older worktree of this work (`...-mishmeret`) is finished with; its removal is the reviewer's.
