# land.py ended by a signal releases the Board's hold and empties the index: the plan (mishmeret-builder, 2026-11-12)

Written 14:36 (`date`). This is M07's item 6, the third in the reviewer's order ("A" on the first project's Board
#201, 09:38), taken after items 4 and 1 were merged (main c773f5e). It is on branch `builder-land-signal` from
c773f5e. Its messages are recorded here, and in the log once `builder-lessons`, which holds the log and the state
file, is merged.

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

## The behaviour

- `land.py`'s `main` first installs one handler for SIGTERM and SIGHUP (`_exit_on_signals`). The handler raises
  `SystemExit(128 + signum)`, so the signal ends `land.py` as an exit does. Every `finally` and `except
  BaseException` runs: the hold is released, the index reset, the frozen copy removed. `subprocess.run` ends a child
  it waits on (the gate's pytest) when an exception reaches it. SIGINT already does this (KeyboardInterrupt).
- MEASURED with the handler, the same probe: exit 143 after 0.07 s, "main released" printed, the hold released (a
  second role could take it), and the child gone. 0.07 s is well inside the 1.5 s grace.
- Not covered: SIGKILL, which no process can catch. A hold left that way is still released by hand.

## Tests (`tests/test_guard.py`, each in a subprocess with real signals, against the placeholder project)

- The hold: a driver takes the hold through `land._held` with a step whose child sleeps. The test signals both with
  SIGTERM once the hold is taken. Asserted: exit 143, the Board's hold released (another role takes it), the child
  gone. The same with SIGHUP.
- The index: a driver runs `land.commit` in a placeholder worktree, its lane check made slow. The test sends SIGTERM
  while it waits. Asserted: nothing left staged.
- Each red with `_exit_on_signals` taken out of `main` (the hold still taken; the names still staged), and the
  SIGHUP one red with SIGHUP out of it.

## Files

- `mishmeret/land.py`, `tests/test_guard.py`, this plan. One code commit, `land.py commit mishmeret-builder code
  --tests "tests/test_guard.py"`, then the suite.

## Not in this piece

- A hold left by SIGKILL, or by a machine's crash: no stale-hold rule on the Board (a hold with no live process).
- `board.py`'s own long calls (`wait`, `quiet`) end by a signal with nothing to release: not changed.
- Not run on Linux: the signals' numbers there are the same for SIGTERM (15) and SIGHUP (1). The grace measured is
  Claude Code's on this machine.
