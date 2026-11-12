# Plan: the seven fixes of my audit of 2026-11-12

## The case

The reviewer, 2026-11-12, in my pane, on my whole-repository audit: "fix 1 through 7". Each finding, its measure on a
prototype (scratch files only), and - from girsa-verifier's review (the first project's
design-study/step5-verification/mishmeret-audit-fixes-plan-2026-11-13/REVIEW.md, 3a321c10) - its record:

1. `board.py answer` (the relay of an answer the reviewer gave in a pane) skips the page's rule. Prototype: on a
   scratch Board item #1 answered A took `answer 1 --answer B` with no word, and withdrawn #2 took an answer event.
   Record: four relays on the first project's live Board went over an item already answered (#13, #33, #92 twice);
   the record tells a relay only by its note's wording.
2. The lane check, this PUBLIC repository's only scan for personal details, never reads the commit message.
   Prototype in a scratch repository: today's lane check with a message holding this machine's home folder, exit 0,
   PASS; one reading the message from `MISHMERET_COMMIT_MESSAGE`, exit 1, FAIL; a clean message, exit 0, PASS. Record:
   no message has carried one (0 of 6,959 first-project commits, 0 of 118 here): a running guard, not a repair.
3. `board.py` takes `--role` on its word. Record (girsa-verifier's role_mismatch.py over every transcript): 10,991
   Board writes under the session's own role, 66 under another - quoted text, probes on scratch Boards, and two sets
   of live writes: 10-20, a demo-operator session set girsa-operator's corner; 11-04 and 11-05, the
   `girsa-builder-mishmeret` sessions wrote as girsa-builder. Whether this item would have refused those two is not
   settled (a transcript's `agentName` may be `--name`, not `--agent`). It would NOT have refused 10-18 (aa79718f, the
   demo operator's session held main as girsa-operator under that `agentName`). None since 11-05. WHAT IT IS: a check
   on a mistaken `--role`, not a chosen one - the guard passes `env -u CLAUDE_CODE_AGENT` (girsa-verifier ran it: rc
   0), so a probe on a scratch Board writes as another role that way, and so could any write.
4. Two forms of one job (Lesson 60): agents.sh's `tell()` passes the alert's text to osascript as an argument,
   agents-morning.sh's `notify()` splices it into the AppleScript. NO REAL TEXT HAS BROKEN THE ALERT: my audit's case
   (an API error notice holding JSON quotes) was mine, not a record - girsa-verifier: 0 of the 255 notices Claude Code
   wrote itself on this machine hold a `"` or `\`; the night log's 24 alerts hold none. The change merges the copies.
5. `land.py commit ROLE code` on a branch runs no test unless `--tests` is given (land.py:203-211); here no one runs
   `land.py land`, so no landing gate runs either. Record: the first project's demo operator's 0b43841c and 1bbf7b95
   touch files no test names.
6. README "Every field is required" and config.py's "a field missing ... is an error - never a default" are wrong
   since A2 (nine OPTIONAL); config.py's `MISHMERET_<FIELD>_<KEY>` sentence too: measured,
   `MISHMERET_BUDGET_WARN_PERCENT=50` leaves `budget.warn_percent` at 80.
7. `board.py landed`, the old name of `finished`: no caller in this repository; in the first project, two that do not
   run on the new pin - design-study/step-mishmeret/shim_measure.py:90 (a by-hand measure of the move's step 2) and the
   `-mishmeret` worktree's `.claude/commands/land.md:46` (no session). Code reduction.

## The change

1. `board.answer(item_id, text, note="", change=False, via=None)` holds the page's rule, under `_append`'s lock: no
   item, a withdrawn one, or an answered one without `change`, raises `board.NotOpen` (a ValueError). The page's route
   calls it with the page's `change` and maps NotOpen to 409, as today; its own copy of the rule goes. The command gets
   `--change` and records `"via": "command"`; `items()` keeps `via` and `describe()` says "(relayed by command)", so
   the role that waits sees it. Drawing it on the page is girsa-ui-steward's look, not in this piece.
2. land.py writes the message file before the lane check and hands its path to the lane check's run alone, as
   `MISHMERET_COMMIT_MESSAGE` - a variable, not an argument: the first project's `check_lane.py` is argparse, and an
   argument it does not know would refuse its every commit at the pin bump. The file is removed on every exit.
   `.claude/lane_check.py`'s reading of it is GIRSA-OPERATOR'S OWN COMMIT (girsa-verifier: land.py runs the lane check
   from the working tree, so mine would judge the commit that brings it): I write and test the diff and hand it over,
   with its tests. With the variable unset it scans nothing more, so either commit may come first.
3. board.py's commands in three lists in code: `AS_ROLE` (write as `--role`: ask, status, plan, hold, release,
   finished, qa, qa-more, send, done), `READS` (wait, quiet, list, inbox, waiting-for, at-limit) and `NO_ROLE`
   (withdraw, defer, answer - no `--role`). `main()` refuses an `AS_ROLE` command whose `--role` is not
   `$CLAUDE_CODE_AGENT` when that is set. Unset (the night run, the reviewer's terminal, a test), nothing changes.
   tests/conftest.py clears the variable, which the suite otherwise inherits from the session running it.
4. One `alert TEXT TITLE` function in agents-lib.sh (the home both scripts source for what they share), passing both
   as osascript arguments; `tell()` and `notify()` call it, each keeping its own log line.
5. `land.py commit ROLE code` on a branch without `--tests` is refused, before anything is staged, with the form to
   use. `--tests none` (girsa-architect, the first project's design-study/MISHMERET-AUDIT-FIXES-ARCHITECT.md, f6f25c9c)
   runs no test and writes "No test was run (--tests none)." into the message. In the main tree (the operator's) the
   landing gate runs and `--tests` is not read: no line is written there.
6. The README's sentence points at `config.OPTIONAL`; config.py's header says what the loader does: an OPTIONAL field
   may be absent; `MISHMERET_<FIELD>` overrides a text or number field, `MISHMERET_NIGHT_<KEY>` a night key.
7. `landed` is no longer taken as a command; the function and the record's `"type": "landed"` keep the name
   (append-only).

## Files

- mishmeret/board.py (1, 3, 7), mishmeret/board_server.py (1), mishmeret/land.py (2, 5), mishmeret/agents-lib.sh,
  mishmeret/agents.sh, mishmeret/agents-morning.sh (4), mishmeret/config.py (6), README.md (6)
- tests/test_board.py (1, 3, 7), tests/test_guard.py (2, 5), tests/test_sessions.py (4), tests/conftest.py (3)
- handed to girsa-operator as a diff, not committed by me: .claude/lane_check.py and its test in
  tests/test_own_project.py (2)
- notes/PLAN-AUDIT-FIXES.md, notes/LOG.md, notes/STATE-mishmeret-builder.md

## Tests (each rule's test shown red with the rule taken out)

1. The command: an answered item refused without `--change`, taken with it (the earlier answer kept); a withdrawn
   one and a missing one refused; the answer says "relayed by command". The page's tests unchanged.
2. land.py hands the lane check the message, the reviewer's words line included; the file is removed after a commit,
   after a lane-check refusal, and after red `--tests`. In the diff: the lane check fails a message with the home
   folder, passes a clean one, and scans no message with the variable unset.
3. Over every command of `AS_ROLE`: refused under another role, taken under its own; and every subcommand is in one
   of the three lists, so a new command must be classed.
4. The notice test of the night run, and agents.sh's: the text reaches osascript as one argument.
5. A code commit on a branch with no `--tests` refused, nothing staged; `--tests none` committed, no pytest, the line
   in the message; in the main tree, `--tests none` writes no line.
6. none (prose).
7. `board.py landed` exits 2 (argparse); `finished` works.

## For the first project (its pin bump, girsa-builder's)

3 and 5 change what its roles may do. girsa-architect (f6f25c9c) and girsa-verifier: every Board write in its briefs,
skills and commands names its own role; a subagent's Bash has its parent's `$CLAUDE_CODE_AGENT` (measured by
girsa-verifier). At the pin bump: the demo operator's and the steward's briefs gain the `--tests` form and when
`none` is right; the operator's brief gains the relay's form, `board.py answer ID --answer X [--change]`. 2 protects it
only once its own `check_lane.py` reads `MISHMERET_COMMIT_MESSAGE`.

## Not in this piece

The page showing "relayed"; a stale hold's expiry; the first project's lane check reading the message; `withdraw` and
`defer` (girsa-verifier read them: no case).
