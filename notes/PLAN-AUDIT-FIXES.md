# Plan: the seven fixes of my audit of 2026-11-12

## The case

The reviewer, 2026-11-12, in my pane, on my whole-repository audit: "fix 1 through 7". Each finding, what it costs
today, and its measure on a prototype (run before this plan was written; scratch files only):

1. `board.py answer` (the relay of an answer the reviewer gave in a pane) skips the page's rule: on a scratch Board
   item #1 answered A took `answer 1 --answer B` with no word (`list`: "answered: B - no"), and withdrawn #2 took an
   answer event. The record cannot tell a relayed answer from the page's.
2. The lane check, this PUBLIC repository's only scan for personal details, never reads the commit message. Measured
   in a scratch repository: today's lane check with a message holding this machine's home folder, exit 0, PASS; a
   prototype reading the message from `MISHMERET_COMMIT_MESSAGE`, exit 1, FAIL ("(the commit message): 1 added line
   carries ..."); with a clean message, exit 0, PASS. All 107 commits' messages are clean today (`git log`, 0 lines).
3. `board.py` takes `--role` on its word: from this builder session, on a scratch Board, `hold --role
   mishmeret-operator` and then `release --role mishmeret-operator` both went through. land.py checks the role
   against `$CLAUDE_CODE_AGENT`; board.py does not.
4. The night run's alert builds its AppleScript from the text: measured, a Claude Code API error notice (`API Error:
   529 {"type":"error",...}`) in it is a syntax error, osascript exit 1 (its output goes to /dev/null, so nothing is
   shown); agents.sh's own form (`on run a`, the text as an argument) gives the text back whole, exit 0.
5. `land.py commit ROLE code` on a branch runs no test unless `--tests` is given (land.py:203-211); here no one runs
   `land.py land`, so no landing gate runs either.
6. README "Every field is required" and config.py's "a field missing ... is an error - never a default" are wrong
   since A2 (nine OPTIONAL); config.py's `MISHMERET_<FIELD>_<KEY>` sentence too: measured,
   `MISHMERET_BUDGET_WARN_PERCENT=50` leaves `budget.warn_percent` at 80.
7. `board.py landed`, the old name of `finished`: no caller in this repository's code, scripts or tests, nor in the
   first project's tracked files (git grep: only its test asserting the name is NOT used).

## The change

1. `board.answer(item_id, text, note="", change=False, via=None)` holds the page's rule, under `_append`'s lock (the
   check and the write in one step): no item, a withdrawn one, or an answered one without `change`, raises
   `board.NotOpen` (a ValueError). The page's route calls it with the page's `change` and maps NotOpen to 409, as
   today; its own copy of the rule goes. The command gets `--change`, and records `"via": "command"`; `items()` keeps
   `via` in the answer and `describe()` says "(relayed by command)" - so the role that waits sees it. Drawing it on the
   page is girsa-ui-steward's look, not in this piece.
2. land.py writes the message file before the lane check and hands its path to the lane check's run alone, as
   `MISHMERET_COMMIT_MESSAGE` - an environment variable, not an argument: the first project's `check_lane.py` is
   argparse, so an argument it does not know would refuse its every commit at its pin bump, while a variable it does
   not read changes nothing. The file is removed on every exit. `.claude/lane_check.py` scans the message's lines with
   the pattern it scans added lines with, counted as "(the commit message)", the text never shown.
3. A Board command that writes as a role (ask, status, plan and its end, hold, release, finished, qa, qa-more, send,
   done) refuses a `--role` other than `$CLAUDE_CODE_AGENT` when that is set - the variable land.py reads, which the
   guard refuses a command to set. Unset (the night run, the reviewer's own terminal, a test), nothing changes. Reads
   (list, inbox, waiting-for, wait) are not checked. tests/conftest.py clears the variable, which the suite otherwise
   inherits from the session running it.
4. agents-morning.sh's `notify` uses agents.sh's form.
5. `land.py commit ROLE code` on a branch without `--tests` is refused, before anything is staged, with the form to
   use. In the main tree (the operator's) the landing gate runs, as today.
6. The README's sentence names the optional fields by pointing at `config.OPTIONAL`; config.py's header says what the
   loader does: an OPTIONAL field may be absent, and `MISHMERET_<FIELD>` overrides a text or number field,
   `MISHMERET_NIGHT_<KEY>` a night key.
7. `landed` is no longer taken as a command; the function and the record's `"type": "landed"` keep the name
   (append-only).

## Files

- mishmeret/board.py (1, 3, 7), mishmeret/board_server.py (1), mishmeret/land.py (2, 5),
  mishmeret/agents-morning.sh (4), mishmeret/config.py (6), README.md (6)
- .claude/lane_check.py (2): `.claude/` is outside my lane (`.claude/lanes.txt`); committed with `--because "fix 1
  through 7"`, the reviewer's words, unless girsa-verifier's review says it is the operator's own commit (as
  8818221's config edit was)
- tests/test_board.py (1, 3, 7), tests/test_guard.py (2, 5), tests/test_own_project.py (2), tests/test_sessions.py
  (4), tests/conftest.py (3)
- notes/PLAN-AUDIT-FIXES.md, notes/LOG.md, notes/STATE-mishmeret-builder.md

## Tests (each rule's test shown red with the rule taken out)

1. The command: an answered item refused without `--change`, taken with it (the earlier answer kept); a withdrawn
   one and a missing one refused; the answer says "relayed by command". The page's existing test unchanged.
2. land.py hands the lane check the message, the reviewer's words line included, and removes the file; the lane
   check fails a message with the home folder and passes a clean one.
3. With `CLAUDE_CODE_AGENT` set: another role's hold, release, status and send refused, the own role's taken; unset,
   taken.
4. The night run's notice test: a notice text with a `"` reaches osascript whole, as one argument.
5. A code commit on a branch with no `--tests` is refused and stages nothing; a notes commit needs none.
6. none (prose).
7. `board.py landed` exits 2 (argparse); `finished` works.

## For the first project (its pin bump, girsa-builder's)

3 and 5 change what its roles may do: every role there posts as itself (its role files, git grep), and its builder's
brief already asks for `--tests`; a verifier's, steward's or demo-operator's code commit on a branch now names tests.
2 protects it only once its own `check_lane.py` reads `MISHMERET_COMMIT_MESSAGE`.

## Not in this piece

The page showing "relayed"; a stale hold's expiry; the first project's lane check reading the message.
