# Plan: a main-tree commit's failure path undid a landing

## The case

girsa-verifier's FINDING, 2026-11-13, in the first project (its main tree's reflog, read here too): 07:54:13 "merge
verifier: Fast-forward" to b3ea803c (`land.py land girsa-verifier notes`), and in the same second "reset: moving to
HEAD" back to 2537c00e. girsa-operator confirmed the trigger: its own `land.py commit` in the main tree was refused
(its state file over the cap), and the failure path's `git reset -q` (land.py:223 at the pin 8818221) ran as the merge
moved HEAD. Its effects: (1) the landing exited 2 under "git merge --ff-only refused:", though the merge had run; (2)
the main tree was left holding b3ea803c's files, unstaged and untracked, and the next landing was refused over them;
(3) girsa-operator's next commit carried girsa-verifier's status line - another role's work under its name. Neither
path takes a hold: a notes landing takes none, nor does a notes commit in the main tree.

REPRODUCED, two processes, scratch repositories:
- git alone (race_git.py): `git merge --ff-only` stepping main forward 300 times while another process loops
  `git reset -q`: 242 resets in the reflog, 1 MOVED HEAD BACK - a reset with no path resolves HEAD at its start and
  writes it at its end, so a merge between the two is undone. The same with `git reset -q -- <path>`: 0 reset entries
  in the reflog, 0 moves back - a path reset writes the index alone.
- land.py itself (race.py: `land.py land ex-verifier notes` against `land.py commit ex-operator notes` in the main
  tree, the operator's commit refused by its own lane check, its start swept in 0.7-2 ms steps): 0 rewinds in 700
  trials - the window is narrow - and two faults of the same race: 5 times the failure path's reset lost the index
  lock to the merge, leaving the operator's name STAGED; once the landing was refused on the index lock ("Another git
  process seems to be running").

## The change

1. The commit's failure path unstages only the names it staged, `git reset -q -- NAME...`: it writes the index and
   never HEAD, so no merge running beside it is undone. Its status is read: when it fails, the sentence says which
   names are still staged and the command that unstages them.
2. ONE LOCK ON THE MAIN TREE (`fcntl.flock` on `<the git common dir>/mishmeret-land.lock`, the kernel's: released on
   any exit, SIGKILL included): taken by a commit in the main tree around its git steps - staging and its compare;
   then the last check, `git commit` and the failure path - and by a landing around its `git merge --ff-only` and the
   check after it. Blocking: each holds it for git's own steps alone (the landing gate, minutes long, runs outside it),
   so a wait is a fraction of a second. The two can then not interleave, which (1) alone does not stop: the index-lock
   faults above. Not the Board's hold: it is kept by role name (girsa-operator's queued item), notes paths take none,
   and a stale one needs a hand to release.
3. The landing's check after the merge says what happened: the merge refused (its own words, as now), or "the merge
   ran and main no longer holds it - another command moved main back; the main tree may hold this branch's files,
   unstaged: tell the operator, whose tree it is".

## Files

- mishmeret/land.py, tests/test_guard.py
- notes/PLAN-LAND-RACE.md, notes/LOG.md, notes/STATE-mishmeret-builder.md

## Tests (each rule's test shown red with the rule taken out)

1. A refused main-tree commit's failure path is `git reset -q -- NAME...` (its names), and a name it could not unstage
   is said.
2. The lock: held by the test, a landing's merge waits until it is released, and a main-tree commit's git steps too;
   a worktree commit does not take it.
3. A merge that ran and was moved back is said as such (main moved back by the test after the merge).
Measures after the build: race.py again - 0 names left staged, 0 landings refused on the index lock; race_git.py's
path form as the reset's own.

## Not in this piece

The Board's hold by session (girsa-operator's queued item 3); git commands run by hand in the main tree beside
land.py (the guard sends commits and landings through land.py); the first project's main tree today - its clean-up is
girsa-operator's (#1250 there).
