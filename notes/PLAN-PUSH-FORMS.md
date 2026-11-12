# The operator's push, every form of a force or a delete: the plan (mishmeret-builder, 2026-11-12)

Written 11:05 (`date`). This is M07's item 4, given by the reviewer's "A" on the first project's Board #201 (09:38,
by way of girsa-operator). It is the first of the items given there, taken one plan at a time, each checked by
girsa-verifier before the next. It is on branch `builder-push-forms` from main 158993f. The log and the state file
record it once the lessons branch (`builder-lessons`) is merged, as M06 was kept off M05's branch.

## The case

- `role_guard.py` refuses the operator's push of `--all`, `--mirror`, `-f`, any word starting with `--force`, and a
  retired remote. It reads the push's words one by one, and only those exact forms count. A force or a delete
  written in any other form goes through.
- Measured, the operator's role asked through `refusal` on text, with the tests' placeholder project (scratch
  script, nothing in the repository run). LET THROUGH: `git push origin +main`, `origin +HEAD:main`, `-uf`, `-fu`,
  `-df`, `-ud`, `origin :main`, `--delete`, `-d`, `--prune`. Refused: `-f`, `--force-with-lease`,
  `--force-if-includes`, `--mirror`. A `+` before a refspec forces that ref, as `--force` would. `-uf` is `-u -f`.
  `:main`, `-d` and `--delete` delete the remote's branch, and `--prune` deletes every remote branch with no local
  one.

## The behaviour

The push rule (`role_guard.py`, the `bad` list under `verb == "push"`) refuses a word that is any of these:

- one of `--all`, `--branches` (git's newer name for `--all`), `--mirror`, `--delete`, `--prune`, or a retired
  remote;
- a word starting with `--force`, with `+` (a forced refspec), or with `:` (a deleted ref);
- a cluster of short options (`-` and no second `-`) holding `f` or `d` before any `o`. Whatever follows an `o` is
  `-o`'s argument (`-ofix` is the push option "fix"), so it is not read as options.

The refusal's words become "never pushes --all, --mirror, a force or a delete". The module's docstring line says
the same.

QUESTION to girsa-architect: should the operator be refused EVERY remote delete, a merged branch's too? The rule
as planned refuses them all. A branch is then deleted on the remote by the reviewer, or through a host's page. The
other way would refuse a delete of main alone, and that needs the remote's default branch, which the guard does
not know. My recommendation: refuse every delete.

## The measure (the prototype: the rule above in a scratch copy of `mishmeret/`, the same probe)

- All 14 bad forms refused: the 10 above, plus `-f`, `--force-with-lease`, `--force-if-includes` and `--mirror`.
- Still let through, 8 ordinary pushes: `origin some-branch`, `-u origin some-branch`, `origin
  HEAD:refs/heads/b`, `-o ci.skip`, `--follow-tags`, `-v -n`, `origin b:b`, `--set-upstream`. Also let through:
  `-ofix` and `-uofix` (an `f` inside `-o`'s argument). `--branches` is refused.

## Tests

- `test_the_role_guard_keeps_push_and_main_tree_commits_to_the_operator`: its `bad` loop gains the ten forms and
  `--branches`. A new loop over the ordinary pushes, each let through, includes `-ofix`.
- Each part of the rule is shown red with that part taken out: the `+`, the `:`, `--delete`, `--prune`,
  `--branches`, the cluster's `f`, the cluster's `d`, and the `o` cut (that last one red on `-ofix`, refused).

## Files

- `mishmeret/role_guard.py`, `tests/test_guard.py`, this plan. One code commit through `land.py commit
  mishmeret-builder code --tests "tests/test_guard.py"`, then the suite.

## Not in this piece

- A push with no refspec, where the force comes from config (`remote.origin.push = +refs/heads/*:...`, or `git -c`
  setting one): the guard reads the command, not git's config. Not read today; not changed here.
- A force given through an alias (`git config alias.p "push -f"`): not read either. The docstring does not name
  aliases, but they fall under its "a guard on the ordinary forms, not a sandbox".
