# mishmeret-builder - current state

Rewritten in place when a piece lands and at the end of a session; the log is `notes/LOG.md`, by item.

## Built, on main (main 8818221 = origin/main, pushed; each verified by girsa-verifier, merged by girsa-operator)

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
  notes/PLAN-GUARD-KEYWORDS.md). The first project's pin is febf285 (#206 A; girsa-verifier checks the bump).
- 1137c12: land.py ended by a stop's SIGTERM, or SIGHUP, releases the hold and leaves nothing staged (M07 item 6).
- d7c97bc: the Board's first answers asked at once parse each landed session once (M07 item 5).
- 5aa9a0a: a subagent is judged as no role (M07 item 2; the reviewer's "No role (c)").
- f734ca4 (the look), febf285: the Board draws a role working on its own background task "Working in the background",
  and keeps a reported wait past a notification (notes/PLAN-BACKGROUND-STATE.md).
- f87e3ce (girsa-operator's 8818221 adds its `sizes.files` limit, 25,000 bytes): `LESSONS.md`, from girsa-operator's
  draft of 18:43, byte for byte (notes/PLAN-LESSONS.md; the log's M08; the reviewer's "go then push when done").
  Merged by girsa-operator; girsa-verifier's check at f87e3ce is not recorded in this repository - ask it if needed.

## Now

- THE SEVEN AUDIT FIXES (notes/PLAN-AUDIT-FIXES.md; the log's M09; the reviewer's "fix 1 through 7"): branch
  `builder-audit-fixes`, rebased on main f7c7d1d (girsa-operator's commit of the lane check's half, from
  notes/PLAN-AUDIT-FIXES-LANE-CHECK.md). Plan reviewed (girsa-verifier, the first project's 3a321c10;
  girsa-architect's f6f25c9c). BUILT at d6a8ce7, 147 passed, 9 of 9 rules red without them, both halves run
  together. Waiting: girsa-verifier's check at the branch's final commit, then girsa-operator's merge and pin. At the first
  project's pin bump (girsa-builder's): the demo operator's and steward's briefs gain `--tests` and `none`; the
  operator's the relay with `--change`.
- `builder-lessons` and `builder-background-state-unsplit` (a backup before a split) are merged or done with; they
  can be deleted. `builder-state-after-lessons` (96454a1) is inside `builder-audit-fixes`.
- To resume: `git -C ~/work/mishmeret log --oneline -3`; `git -C ~/work/mishmeret-builder status -sb`; the Board;
  girsa-verifier's and girsa-operator's answers, live; the log's M09.

## Next, in order

1. girsa-demo-operator's REQUEST, the reviewer's words: track tokens, secrets and other things that expire, and set
   calendar alerts - the items from the project's config, never Girsa's names in code. Its cases (the log's M09):
   the hosting MCP token (its JWT's `exp`, now 2026-11-17 13:49 UTC; the alert follows each renewal), the Board
   stats fetch's Claude login (2026-12-07), two TLS certificates (2027-01-15), the domain (not known). The
   reviewer's to decide: which calendar, how far ahead.
2. girsa-operator's REQUEST (the night directive): `_frozen_gate` red while an Apply is uncommitted in the main tree
   (the first project's Board #495).
3. girsa-operator's REQUEST: the Board's hold kept by role name, so a second session of one role ends the first's.

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
