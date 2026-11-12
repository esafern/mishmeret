# The operator's push, every form of a force or a delete: the plan (mishmeret-builder, 2026-11-12)

Written 11:05 (`date`). This is M07's item 4, given by the reviewer's "A" on the first project's Board #201 (09:38,
by way of girsa-operator). It is the first of the items given there, taken one plan at a time, each checked by
girsa-verifier before the next. It is on branch `builder-push-forms` from main 158993f. The log and the state file
record it once the lessons branch (`builder-lessons`) is merged, as M06 was kept off M05's branch. Until then
the messages are recorded here. Sent, live, at 4c65b64: the QUESTION to girsa-architect, the HANDOFF to
girsa-verifier, and a NOTE of the path to girsa-operator. 11:07: girsa-operator's ANSWER (above, under the
question), taken into the plan. Sent, live, at 1f349a4: a NOTE to girsa-operator of the revision, asking whether
a `!` git push was ever seen to pass the guard. Then girsa-operator's ANSWER (under "Not run"). Sent, live: a
NOTE that the `!` test can run now, in any non-operator pane. Before 11:13: girsa-verifier's review of 4c65b64, NOT
READY, two MEDIUMs and one LOW, all taken (under "The behaviour"). It holds its reading of the delete question
until girsa-architect answers. Sent, live, at f664982: the ANSWER to girsa-verifier, the three findings taken. Then girsa-verifier: READY TO
BUILD once girsa-architect answers, with two side effects read (under "The measure" and "Not in this piece").

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

REVISED 11:13 on girsa-verifier's review of 4c65b64 (NOT READY: two MEDIUMs, one LOW), all three taken:

- MEDIUM 1, A QUOTED WORD IS NOT READ: the push's words come from the masked text, where what stands inside quotes
  is spaces. So `origin "+main"`, `"-f"` and `"--force"` get through today. Now the push rule alone reads the
  ORIGINAL span (`command[m.start(3):m.end(3)]`, the same offsets: the mask keeps the length), split by `shlex`, so
  `+"main"` and `'+'main` are read too. It falls back to a plain split on a quote the span leaves open. The other
  verbs keep `rest` as it is.
- MEDIUM 2, A LONG OPTION BY ITS UNIQUE PREFIX: git takes a unique prefix of a long option as that option
  (gitcli(7)), so `--del`, `--pru`, `--mir`, `--al` and `--bra` get through. Now a `--` word, read up to any `=`, is
  refused when it is a prefix of a refused long option. `--` alone is not refused (the end of the options). `--a`,
  `--d`, `--p` and `--fo` are refused too: git either refuses them as ambiguous or takes them as a force.
- LOW 1: the short cluster is `copy_refusal`'s own reading of one (`set(o[1:]) & {...}`), with `-o`'s argument
  cut off. No new parser.

The push rule (`role_guard.py`, under `verb == "push"`) refuses a word, as the shell passes it to git, that is
any of these:

- a retired remote;
- a word starting with `+` (a forced refspec) or `:` (a deleted ref);
- a `--` word (up to any `=`) starting with `--force`, or a prefix of `--all`, `--branches` (git's newer name for
  `--all`), `--mirror`, `--delete`, `--prune`, `--force`, `--force-with-lease` or `--force-if-includes`;
- a cluster of short options (`-` and no second `-`) holding `f` or `d` before any `o`. Whatever follows an `o` is
  `-o`'s argument (`-ofix` is the push option "fix"), so it is not read as options.

The check is one function, `push_forces(word)`, beside one tuple, `PUSH_LONG`. The refusal says "never pushes
--all, --mirror, a force or a delete", followed every time by girsa-operator's sentence (11:07): "a delete on a
remote runs only as the reviewer's own command: `! git push origin --delete <branch>` in the operator's pane". The
module's docstring line says the same.

QUESTION to girsa-architect: should the operator be refused EVERY remote delete, a merged branch's too? The rule
as planned refuses them all. The other way would refuse a delete of main alone, and that needs the remote's default
branch, which the guard does not know. My recommendation: refuse every delete. girsa-operator's answer (11:07, also
sent to girsa-architect as the first project's Board #979): refuse every delete. Its one delete on record, of
origin/master on 2026-11-04 on the reviewer's word, was of a merged branch, and the guard cannot tell from the
command whether the reviewer gave that word. girsa-architect's answer is still awaited.

NOT VERIFIED: that a command the reviewer types with `!` in a pane runs without the PreToolUse hook. Claude Code
runs `!` commands itself rather than through the Bash tool, but I have not seen it on this machine. If the hook
does see them, the sentence above points to a command that is refused too.

## The measure (the prototype: the revised rule in a scratch copy of `mishmeret/`, one probe, 11:13)

- 34 bad forms. These are the first 14, plus `--branches` and `--all`; the quoted `origin "+main"`, `origin ':main'`,
  `"-f"`, `"--force"`, `origin +"main"`, `origin '+'main` and `"retired" b`; the prefixes `--mirr`, `--al`,
  `--bra`, `--del`, `--dele`, `--pru`, `--mir`, `--forc`, `--fo`; and `--force-with-lease=main` and `retired b`.
  ALL 34 REFUSED; main 158993f lets 27 of them through.
- 25 ordinary pushes, NONE REFUSED: `origin some-branch`, `-u`, `origin HEAD:refs/heads/b`, `-o ci.skip`, `-ofix`,
  `-uofix`, `--follow-tags`, `--fol` (a prefix of `--follow-tags` alone), `-v -n`, `origin b:b`, `--set-upstream`,
  girsa-operator's push by sha (`origin <sha>:refs/heads/main` and the same to a branch: the form its push procedure
  prescribes, 11:07), `--dry-run`, `--porcelain`, `--progress`, `--push-option=x`, `--atomic`, `--tags`,
  `--no-verify`, `--recurse-submodules=check`, `--repo=origin`, `--` before the remote, `--quiet` and `--verbose`.
- `tests/test_guard.py` in the prototype: 30 passed.
- A side effect girsa-verifier read on f664982: a comment after the push, `git push origin b # --force later`, is
  now read as words (the mask had spaced it), so that push is refused. KEPT, and pinned by a test as refused: an
  error on the safe side. NOT TAKEN: `shlex.split(..., comments=True)`. Measured, it ends a comment at a `#` inside
  a word, which bash does not (`origin a#b` gives `origin a`). So `git push origin x#y +main` would lose its `+main`.

## Tests

- `test_the_role_guard_keeps_push_and_main_tree_commits_to_the_operator`: its `bad` loop takes the probe's 34
  forms. A new loop runs the probe's 25 ordinary pushes, each let through. One refusal is checked for
  girsa-operator's sentence.
- Each part of the rule is shown red with that part taken out (done: see BUILT): the `+`, the `:`, each long name in `PUSH_LONG`,
  the prefix reading (exact names only), the `=` cut, the cluster's `f`, the cluster's `d`, the `o` cut (red on
  `-ofix`, refused), the original span (the masked words back), and `shlex` (a plain split: red on `+"main"`).

BUILT, 11:21. Run in a scratch copy of the build, one rule part taken out at a time: GREEN with nothing taken out,
and RED with each of the 16 parts taken out, each failing on the form that part is there for. The 16: the `+`,
the `:`, each of PUSH_LONG's seven, the prefix reading, the `=` cut, the cluster's `f`, its `d`, the `o` cut, the
original span and `shlex`. Two runs gave the same result.

- FOUND in the red run: `--force` as its own PUSH_LONG entry stayed green with it taken out. It is a prefix of
  `--force-with-lease`, so the prefix reading refuses it anyway: an inert entry (the lesson THE MUTATION THAT DID
  NOT FAIL), deleted, with a comment where it was. The plan's `startswith("--force")` was inert the same way once
  the `=` cut is in, and was deleted before the run.
- MY SLIP, in the red script: its first runs reported rows that ran the wrong code. Each mutation rewrote
  `role_guard.py` within the same second, often at the same size (`"--force", ` and `"--prune", ` are both 11
  characters), so Python reused the last mutation's `.pyc`. Three rows ran another row's code: "the :",
  "--delete", and "--force" (red for another row's reason in two runs, green in one). Seen when that row changed
  between runs. The script now clears `__pycache__` and
  runs with `-B`, and has a baseline row that must be green. Only the runs after that fix are counted above.
- girsa-architect's ANSWER (its MISHMERET-PUSH-FORMS-ARCHITECT.md, the first project's main 83f04750): refuse
  every delete, on two conditions, girsa-operator's asks and the abbreviated options, both already in f664982.
  girsa-verifier, its one verdict with that folded in: READY TO BUILD at f664982.
- The suite on the build: 139 passed.
- Sent, live, at 21cb9ba: the build's HANDOFF to girsa-verifier for its check, and a NOTE to girsa-operator.
- VERIFIED at 21cb9ba (girsa-verifier, nothing found; sent to girsa-operator for the merge as the first project's
  message #986). On a git-archive export: the suite 139 passed; its probe's 19 forms all refused, the comment case
  too. Four of my reds re-run against the whole test_guard.py, each red. Not verified by it: whether `!` passes
  the hook.

## Files

- `mishmeret/role_guard.py`, `tests/test_guard.py`, this plan. One code commit through `land.py commit
  mishmeret-builder code --tests "tests/test_guard.py"`, then the suite.

## Not run (until the reviewer runs it) - RUN, 2026-11-12, before 12:23

- RESULT (girsa-architect's NOTE, live): the reviewer ran `! git push --dry-run origin --delete
  no-such-branch-girsa-test 2>&1; echo "exit=$?"` in girsa-architect's pane, a role the guard refuses any push. Git
  ran and reached origin: "error: unable to delete 'no-such-branch-girsa-test': remote ref does not exist", exit=1.
  So a `!` command does not pass through the hook, and the refusal's "the reviewer's own command" way works. The
  NOT VERIFIED line under "The behaviour" is settled by this. Nothing changed on origin. The test, as planned:

- Whether `!` passes through the hook. girsa-operator (between 11:07 and 11:13) has no record of a `!` git push going through with
  the guard on, and treats the answer as unknown. Its test is harmless: the reviewer types `! git push --dry-run
  origin --delete no-such-branch-girsa-test` in a role's pane. If the guard's refusal prints, `!` runs through the
  hook, and the delete's sentence must name another way. If git answers itself ("remote ref does not exist", or a
  dry-run line), `!` goes around the hook and the sentence is true. With `--dry-run` and a branch that does not
  exist, nothing can be deleted either way. In a pane of any role but the operator, today's guard already refuses
  every push, so the test does not need this build: it can be run now. girsa-operator puts it to the reviewer.

## Not in this piece

- A push with no refspec, where the force comes from config (`remote.origin.push = +refs/heads/*:...`, or `git -c`
  setting one): the guard reads the command, not git's config. Not read today; not changed here.
- A refspec or an option in a variable (`git push origin $REF`): not read (girsa-verifier, on f664982).
- A force given through an alias (`git config alias.p "push -f"`): not read either. The docstring does not name
  aliases, but they fall under its "a guard on the ordinary forms, not a sandbox".
