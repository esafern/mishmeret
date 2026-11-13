# mishmeret-builder - current state

Rewritten in place when a piece lands and at the end of a session; the log is `notes/LOG.md`, by item.

## Built, on main (main b303f6c; origin at 8818221, the reviewer's push pending; each verified by girsa-verifier, merged by girsa-operator)

- c1963d1 (Mishmeret's own `.claude/`; PLAN-OWN-CLAUDE), 59178bf (open messages), 8f6771d and 31ac716
  (copy-on-select), 8738b21 (the start scripts with no project named) - each plan in notes/.
- 51499da, 7b9c6e0: finishing a session, by day and by night (notes/PLAN-FINISH.md; the log's M05) - the two finish
  commands from the config, `board.py finished`, the night run ending with no Go, the Stop hook `finish_hook.py`
  and `agents.sh --next`.
- f33aad3, 529af0a, b8dac60: an escaped quote inside a string no longer turns the role guard off
  (notes/PLAN-GUARD-MASK.md; the log's M06; girsa-verifier: HIGH).
- 21cb9ba: the operator's push refused for a force or a delete in any form (M07 item 4; notes/PLAN-PUSH-FORMS.md).
- db17aac (with db7b0ff, 828abdc): the guard sees git after a shell keyword, behind its own options and written
  quoted; every tree git may use, every cd in order, a cd quoted, optioned or by pushd (M07 item 1;
  notes/PLAN-GUARD-KEYWORDS.md). The first project's pin is febf285 (#206 A; girsa-verifier checks the bump).
- 1137c12: land.py ended by a stop's SIGTERM, or SIGHUP, releases the hold and leaves nothing staged (M07 item 6).
- d7c97bc: the Board's first answers asked at once parse each landed session once (M07 item 5).
- 5aa9a0a: a subagent is judged as no role (M07 item 2; the reviewer's "No role (c)").
- f734ca4 (the look), febf285: the Board draws a role working on its own background task "Working in the background",
  and keeps a reported wait past a notification (notes/PLAN-BACKGROUND-STATE.md).
- f87e3ce (girsa-operator's 8818221 adds its `sizes.files` limit, 25,000 bytes): `LESSONS.md`, from girsa-operator's
  draft of 18:43, byte for byte (notes/PLAN-LESSONS.md; the log's M08; the reviewer's "go then push when done").
  Merged by girsa-operator; girsa-verifier's check at f87e3ce is not recorded in this repository - ask it if needed.
- d6a8ce7, 090253c (with girsa-operator's f7c7d1d, the lane check's half): the seven fixes of my audit - a relayed
  answer keeps the page's rule; the commit message scanned; a role's session writes to the Board as itself; one
  alert function; a code commit names its tests (or `none`); the config docs; `landed` gone (notes/PLAN-AUDIT-FIXES.md;
  the log's M09). Suite 147 passed. At the first project's pin bump (girsa-builder's; girsa-operator keeps the
  notes): its briefs gain `--tests`/`none` and the relay's `--change`.
- a24377d, 6039283: what expires - expiring.py and the Board's /expiring.ics (notes/PLAN-EXPIRING.md; the log's M10).
  Main e1f9195. For the first project: its pin bump with no `expiring` rows, the five rows later; the reviewer
  subscribes once to http://127.0.0.1:8450/expiring.ics (On My Mac, alerts kept). The token lapses 2026-11-17 13:49 UTC.
- fd2178e, 159ea56: the land.py race (notes/PLAN-LAND-RACE.md; the log's M11) - a refused main-tree commit unstages
  its own names alone; one lock on the main tree for a main-tree commit's and a landing's git steps. Main 668eea0.
- e63b4a2: the gate after a code landing takes the main tree whole, a file moved during the copy refused, the main
  tree's uncommitted files named (notes/PLAN-FROZEN-GATE.md; the log's M12). Main 81759f8.
- c8af403: the Board's hold is its session's while its process runs (the same id and start); another session and a
  command with no session refused; a gone session's taken over (notes/PLAN-HOLD-SESSION.md; the log's M13). Main
  b303f6c. Every piece of this session protects the first project only after its pin bump (its Board #215, with the
  reviewer); the lock and the hold fully once every tree's pin passes them.

## Now

- No piece is open. Main b303f6c, suite 155 passed; origin at 8818221 - the push is the reviewer's word, through
  girsa-operator.
- Done with, to delete: every `builder-*` branch but `builder-state-2026-11-13` (this file's commit, to merge).
- To resume: `git -C ~/work/mishmeret log --oneline -3`; `git -C ~/work/mishmeret-builder status -sb`; the Board.

## Next, in order

Nothing more is given.

Not given: the code's citations of the first project's lesson numbers; M07's smaller items; role_guard.py's header
sentence on subagents (girsa-verifier's LOW, for its next touch).

## Open
- Not run live: the night run and the morning run as changed (behind stubs only); the hook under the first project's
  shim. Mishmeret's own config names neither finish command and its settings no Stop hook - it has no role in tmux.
- Not run on Linux: `agents.sh --next` (osascript, BSD `find -mmin`, tmux) - the sessions' scripts are macOS-only.
- The guard's mask, not checked: `$"..."` and a backtick string (girsa-verifier's forms hold them, no test here);
  the piped-check refusals and the Edit and Write side under an escaped quote.
- The guard, not in M07 items 1 and 4 (their plans' "Not in this piece"): two `-C`s, `cd -`, a bare `cd`, a cd or
  git option through a variable, a force from git's config or an alias, a `case` pattern's `)`. A `!` command the
  reviewer types bypasses the hook (the reviewer's own run, 2026-11-12), so a delete refused to the operator runs that way.
- A required config key cannot be added or renamed: Mishmeret pins itself (the log's M05).
- Not pinned by a test (A2): `land()`'s restart line and ledger copy with the field absent.
- The 5 s refresh redraws the corners, so a focused pill loses its focus then (page-wide; girsa-ui-steward: leave it).
- Copy-on-select measured in headless Chromium alone; the page's new words too.
- The first project's older worktree of this work (`...-mishmeret`) is finished with; its removal is the reviewer's.

The session is ready to clear.
