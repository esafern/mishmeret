---
name: mishmeret-landing
description: Mishmeret's general procedure for committing and landing work through land.py - commit, land, check-conflict, the gate, the Board's hold, the lane check and --because - for any role of a project run with Mishmeret; the project's own skill, if it has one, holds its particulars (its paths, its gate's files, its roles).
---

Shipped with Mishmeret (`mishmeret/skills/`), linked into the project's `.claude/skills/` by `agents.sh` from the
commit the project pins: it describes that commit's `land.py`. Its options are the script's own: run
`<the project's Python> .claude/land.py --help`, and a subcommand's after it - this skill lists none of them.

**Why one script:** every commit and every landing runs the same steps, each read by its return code: the lane check,
the tests or the gate, the Board's hold released on every exit. The role guard lets a role run `land.py` only as itself,
and refuses a `git commit` in the project's repository, and a landing `git merge` in its main tree, done any other way.

**The steps:**
1. COMMIT, in your worktree: `land.py commit ROLE notes|code -F MESSAGE NAME...`. Name every file; the index must be
   empty first. `notes` is for documents only (the lane check's `--doc-only`); `code` runs the tests the change
   touches (`--tests`), or `none` where no test can, said in the message. In the main tree (the config's `operator`
   alone) a code commit runs the landing gate under the hold.
2. OUTSIDE YOUR LANE: only on the reviewer's words, given with `--because "<their words>"`, which the commit message
   then carries. The lane check reports the paths, and refuses them without it.
3. LAND, from your worktree, your branch checked out: `land.py land ROLE notes|code`. The role named in the config's
   `land.planned` names its plan with `--plan`. The script takes the hold, rebases as a step of its own, checks the
   range's lanes, runs the gate, merges with `--ff-only`, then runs the gate again on a frozen copy of the main tree,
   and releases the hold.
4. A STOPPED REBASE: resolve, then `land.py check-conflict FILE...` before `git add` and `git rebase --continue`, each a
   command of its own; then land again.
5. THE GATE ALONE: `land.py gate`, a set from the config's `land.gate_sets`, `--tree` for a copy.

**The rules:**
- A check's own exit status decides the next step: land.py's output to a file, its status read with `echo "rc=$?"`,
  then the file read - never through a pipe.
- A red after a landing is the lander's: read the red against what the main tree holds uncommitted before it is yours.
- Holding main is a flag on the Board (`board.py hold`, `board.py release`), never a message; a hold another role
  holds is waited for.
- A landing goes to the config's `land.verifier` first; its findings are fixed in one round.
