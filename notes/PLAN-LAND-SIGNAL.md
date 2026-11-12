# land.py ended by a signal releases the Board's hold and empties the index: the plan (mishmeret-builder, 2026-11-12)

Written 14:36 (`date`). This is M07's item 6, the third in the reviewer's order ("A" on the first project's Board
#201, 09:38), taken after items 4 and 1 were merged (main c773f5e). It is on branch `builder-land-signal` from
c773f5e. Its messages are recorded here, and in the log once `builder-lessons`, which holds the log and the state
file, is merged. Sent, live, at 0240039: the plan's HANDOFF to girsa-verifier, which is a new session since its
last answer; the message stands on its own. Also a NOTE to girsa-operator.

## The case

- `land.py` takes the Board's hold for a code commit in the main tree and for a code landing (`_held`). It releases
  the hold in a `finally`. A commit's `except BaseException` resets the index it staged, and a landing's frozen copy
  is removed in a `finally`. Python runs none of these when the process is ended by a signal it does not handle:
  SIGTERM's and SIGHUP's default action ends it at once.
- MEASURED, which signal ends a command here (Claude Code, this machine): when its time limit runs out, a Bash
  command is NOT ended - it is moved to the background and goes on. A stop (`TaskStop`, or the session's own stop)
  sends SIGTERM to the command's process group. A script that caught it was still running 1.4 s later, then was
  killed (SIGKILL, as it no longer ran: the grace is about 1.5 s). So M07's "a tool's time limit" was wrong in its
  cause. The case is a stop, of a command or of the session. A closed pane gives SIGHUP.
- MEASURED, on a placeholder project in scratch (its real `board.py`, `land._held` with a step whose child sleeps
  30 s, SIGTERM sent to the driver and to its child, as a group signal would): the driver ended by the signal
  (exit -15), and the HOLD WAS STILL TAKEN ("main is held by ex-builder since ...") - every landing after it is
  refused until someone runs `board.py release` by hand.

- THE CASE IS REAL, ONCE (girsa-verifier's LOW 1, from the transcripts). On 2026-11-09, `land.py commit girsa-operator
  code ...` in the main tree took the hold at 13:57:14. Claude Code moved it to the background so that a message
  could reach the session (a third way into the background, beside the time limit), and it was stopped at 13:59:15.
  The hold stayed until the next command's own trailing release, and that next `land.py commit` was refused: "the
  index already holds START_HERE.md". Of 129 land.py runs in the background and 240 TaskStops in the main clone's and
  Mishmeret's transcripts, this is the only stop of a land.py that had taken the hold or staged names.

## Review, 15:05: girsa-verifier at 0240039, NOT READY (one MEDIUM, three LOWs), all taken

- MEDIUM 1, A STOP IN THE AFTER-LANDING GATE STILL LEFT THE HOLD. `_frozen_gate` removed its copy in its own
  `finally`, inside the hold's step, so before `_held` released it. girsa-verifier's measures: the grace 1.47 s;
  `cp -c -R` of the first project's main clone (60,898 files) 8.43 s, its `rmtree` 2.74 s; `board.py` hold or release
  0.05 s. NOW: `land` creates the copy's folder for a code landing and removes it after `_held` returns. A stop then
  releases first, and SIGKILL may leave a partly removed copy in the temporary folder, which is harmless.
  MEASURED (a real `land.land` on the tests' fixture, its frozen gate waiting, its copy's removal 3 s, SIGTERM then
  SIGKILL 1.47 s later): with the handler and the old order, the Board's calls were hold, the frozen gate, the
  removal, and no release. With the new order: hold, the frozen gate, RELEASE, the removal.
- LOW 2: a closed pane's SIGHUP is reasoned, not measured. `signal.SIGHUP` is read with `getattr`, since Windows
  has none; Windows is not run.
- LOW 3: a second signal during the cleanup had raised again, and cut the release short. The handler now sets both
  signals to ignored before it raises.
- girsa-verifier: no signal handling in Mishmeret to reuse; the shim reaches `main()` in-process (`runpy`), so the
  handler covers the first project's `tools/land.py` too.

## The behaviour

- `land.py`'s `main` first installs one handler for SIGTERM and SIGHUP (`_exit_on_signals`). The handler raises
  `SystemExit(128 + signum)`, so the signal ends `land.py` as an exit does. Every `finally` and `except
  BaseException` runs: the hold is released, the index reset, the frozen copy removed. `subprocess.run` ends a child
  it waits on (the gate's pytest) when an exception reaches it. SIGINT already does this (KeyboardInterrupt).
- MEASURED with the handler, the same probe: exit 143 after 0.07 s, "main released" printed, the hold released (a
  second role could take it), and the child gone. 0.07 s is well inside the 1.5 s grace.
- Not covered: SIGKILL, which no process can catch. A hold left that way is still released by hand.

## Tests (BUILT 15:05: `test_land_py_stopped_releases_the_hold_and_leaves_nothing_staged`)

A driver in a subprocess builds the tests' placeholder fixture and calls `land.main`, so its own handler is
installed. The Board's calls are written to a file as they happen. The test does what a stop does: the signal to
each of the driver's processes, then SIGKILL 1.47 s later.
- A landing stopped in its frozen gate (the copy's removal 3 s; a second SIGTERM 0.2 s after the first, during a
  release made to take 0.5 s): the release comes before the removal.
- The same landing under SIGHUP alone: exit 129, released.
- A commit stopped in its lane check: exit 143, nothing staged.
- Red with each part taken out, in a scratch copy, `__pycache__` cleared: the handler out of `main` (exit -15, no
  release), SIGHUP out (exit -1), the second signal not ignored (no release), the exit's code, and the copy removed
  inside the hold (no release). Green with none. Two runs gave the same result; the test green three runs in a row.
  The suite: 141 passed.
- Not as planned: the `_held`-alone driver is gone. A test over `land.main` is what a stop meets, and the old
  driver had no slow cleanup and no SIGKILL, so it could not see MEDIUM 1.

## Files

- `mishmeret/land.py`, `tests/test_guard.py`, this plan. One code commit, `land.py commit mishmeret-builder code
  --tests "tests/test_guard.py"`, then the suite.

## Not in this piece

- A hold left by SIGKILL, or by a machine's crash: no stale-hold rule on the Board (a hold with no live process).
- `board.py`'s own long calls (`wait`, `quiet`) end by a signal with nothing to release: not changed.
- Not run on Linux: the signals' numbers there are the same for SIGTERM (15) and SIGHUP (1). The grace measured is
  Claude Code's on this machine.
