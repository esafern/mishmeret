# Plan: the known gaps' seven

## The case

The first project's Board #223 (girsa-verifier's question, "build the seven items no session has ever hit, or leave
them until one happens?"), answered B, "Build all fifteen", on 2026-11-13 at 16:05 (read in its Board's record). The
seven are items 3, 4, 5, 6, 9, 10 and 15 of notes/PLAN-KNOWN-GAPS.md, which the first eight landed under (main f2126a1).
Item 6 is taken in girsa-architect's form B (the first project's design-study/MISHMERET-ALIAS-CONFIG-ARCHITECT.md,
d721b739); girsa-verifier's LOW 3 on that plan with it (git's own verb list, not the guard's).

Each item was measured again on main d9fda25 with probe scripts on the guard's own functions and placeholder paths
(the main tree `/work/book`, a worktree `/work/book-builder`, role ex-builder unless named). Each form below is let
through there unless it says refused. Three NEW FINDINGS were made while measuring; they are items 17 and 18 and the
siblings named under items 4, 5 and 6.

THE RECORD, for the new findings and for item 6's cost: every Bash command in the transcripts, 1,044 of the first
project's (161,803 distinct command-and-cwd pairs) and 9 of Mishmeret's (1,298), read by d9fda25's own mask:
- 113,908 git runs. 5 have a verb that is not in git's list: `git filter-repo --version` 4 times (an add-on on this
  machine's PATH), and `git $o status` once (a probe looping over git's options).
- A quoted or escaped verb (item 17): 0. A `popd` or a bare `pushd`: 0. A `-c` or `--config-env` key on a push: 0.
- `git config --global`, `--system` or `-f`: 4, each a read (`--get-regexp`).
- `git remote` writes: 3. Two ran in scratch repositories the same command had made. The third is girsa-operator's
  `git remote set-url origin <its URL>` in a corpus root, on 2026-11-22: item 6's rule refuses it (design question 1).
- A case arm holding git, a cd or a check: 25, nearly all `case "$PWD" in /private/tmp/*) git reset ...`, a session's
  own guard on a scratch copy. Rule 45 reads each one the build changes.

Not in this piece, and why:
- FOUND, FOR THE REVIEWER: git 2.56.1 has commands that write a branch or a tree and are in no verb set of the guard's
  (`CHANGES_MAIN`): `git history drop|fixup|reword|split` (rewrites commits, `--update-refs`), `git replay --advance`,
  `symbolic-ref`, `read-tree`, `update-index`, `checkout-index`, `sparse-checkout`, `filter-branch`. A role may run
  them in the main tree. Not one of the fifteen, so not built here.
- `cd ~-` and `cd $OLDPWD`; a `cd -` or `popd` with no cd before it on its line (where the shell was before the
  command is not in the hook's input: the place is kept).
- girsa-verifier's LOW on 075f49a (PREFIX and TMUX_PREFIX two copies), and the piped-check rule inside a substitution
  after another word: the state file's Open, untouched.

## The change

### The guard (mishmeret/role_guard.py)

3. TWO -C. `git -C /work -C book reset --hard` from a worktree is let through, and `git -C /work/book -C ../book-builder
   reset --hard`, which runs in the worktree, is refused. `_git_trees` reads the first -C only; git takes each from
   where the one before left. Fix: every -C, in order.
4. `cd -`, A BARE `cd`, AND (sibling, new) `popd` AND A BARE `pushd`.
   - `cd /work/book; cd /work/book-builder; cd -; git reset --hard` is let through, and the other way round is refused
     (`-` read as a folder named "-").
   - A bare `cd` is not read: `cd; git reset --hard` is judged where the command started.
   - `pushd /work/book-builder; popd; git reset --hard` from the main tree is let through, and the other way round is
     refused (`popd` not read).
   Fix in `_places_before`: each place kept with the one before it and pushd's stack. `cd -` goes to the place before,
   a bare `cd` to $HOME, `popd` to the stack's top, and a bare `pushd` swaps the two.
5. A CASE ARM. `case x in x) git push origin main;; esac` is let through, and so are `case x in (x) ...` and an arm
   after `;;`. So is a cd there, and (sibling, new) a check: `case x in a) python3 -m pytest tests | tail -3;; esac`
   passes the piped-check rule, and a check then a commit in an arm passes the check-status rule. Fix:
   - After `in`, `;;`, `;&` or `;;&`, a pattern (its words, `|` between them) and its `)` are command position for
     every rule built on BOUNDARY: git, a script, cp, the tmux kill and pkill.
   - A cd in an arm may not run, so it is read as one after a keyword (KEYWORD_CD).
   - `_words`, the check rules' reader, takes a statement's leading `case WORD in` and a pattern ending in `)` off, as
     it takes off a keyword.
6. AN ALIAS, AND A FORCE FROM GIT'S CONFIG - girsa-architect's B:
   a. GIT'S OWN VERB LIST, WRITTEN DOWN: `git --list-cmds=main` on git 2.56.1, 181 names. A verb not in it is refused for
      every role, in every tree: an alias or an add-on runs what the guard cannot see (`git -c alias.p='push --force'
      p origin main`, the operator's, is refused as `p`). A test checks that every name this machine's
      `git --list-cmds=main` gives is in the list, so a newer git's command is noticed. The cost on the record: 5 of
      113,908 git runs (above). The 28 add-ons on this machine's PATH are not taken in.
   b. THE WRITE CLOSED: in a tree whose common git dir is guarded (`guarded_git_dirs`: the project's main clone, a pin,
      a corpus root, TREES), and in a foreign repository's, for every role, the operator too:
      - `git config` in any form but a read;
      - `git remote add`, `set-url`, `rename`, `remove`/`rm` and `set-branches`.
      A read is `--get`, `--get-all`, `--get-regexp`, `--get-urlmatch`, `--get-color`, `--get-colorbool`, `-l`/`--list`,
      `get`, `list`, or a key alone. Siblings (new): a `--global` or `--system` write is refused from any tree, since
      git reads that file in every repository; a `-f`/`--file` write is judged by the folder of the file it names.
      The refusal names the way out: the reviewer's own `!` command, as for a remote delete.
   c. ON THE OPERATOR'S PUSH: a `-c` or `--config-env` with a `remote.`, `url.`, `alias.` or `branch.` key, or a
      `GIT_CONFIG...=` assignment before git, is refused. A text rule, no subprocess. (`branch.<name>.pushRemote` and
      `remote.pushDefault` choose a bare push's remote: girsa-architect's point 2.)
   No `git config` subprocess is added.
17. A QUOTED OR ESCAPED VERB (new, found measuring item 6, the class of item 1). `git "push" origin main`,
    `git 'reset' --hard` (from the main tree) and `git \push origin main` are let through for every role: GIT's verb is
    `[a-z][\w-]*` in the masked text, where a quoted verb is its quotes around spaces. Fix: the verb is one WORD, not
    starting with `-`, read in the original as the shell reads it (`_word`). With 6a a capitalised verb (`git Push`,
    which git looks up as an alias) is refused as unknown.

### The rest (built before the review, kept whole in notes/known-gaps/held-9-10-15.diff, applied here)

9. An added line that begins "++ " is a file's header no more: in `.claude/lane_check.py` and
   `mishmeret/time_precommit.py`, a `+++ ` line is a header only between `diff --git` and the first `@@`.
10. `agents.sh`'s `effort_of` gives `--effort X` only when the agent file names X.
15. On a red gate, each file the frozen gate's compare read is read again in the main tree; one that moved is named
    first: "X changed in the main tree during the gate: gate main again before the red is yours". A green is left
    alone.
18. A TEST FIX (new, found running the suite): Chromium 1255, installed with Playwright 1.65.2 on 2026-11-22, writes a
    computed `outline` as `1px solid <colour>`; the test expected `<colour> solid 1px`. The open-messages pill test read
    the shorthand and went red at both window sizes; the page is unchanged. The test reads `outlineStyle` and
    `outlineWidth` (green; red with the page's outline made 2px).

## Design questions (to girsa-architect)

1. Item 6b refuses girsa-operator's `git remote set-url origin <URL>` in a corpus root (2026-11-22, the one write on
   the record in a guarded tree). Your B says every role, the operator included, the way out being the reviewer's own
   `!` command. My recommendation: keep that. A set-url is what sends a push to `origin` somewhere else, and the
   retired-remote rule reads only the name.
2. Item 6a refuses `git filter-repo` (4 on the record, each `--version`). It is an add-on, and it rewrites a
   repository's whole history. My recommendation: refused, as any add-on.

## Files

- mishmeret/role_guard.py, tests/test_guard.py (items 3-6, 17)
- .claude/lane_check.py, mishmeret/time_precommit.py, tests/test_own_project.py, tests/test_guard.py (item 9)
- mishmeret/agents.sh, tests/test_sessions.py (item 10)
- mishmeret/land.py, tests/test_guard.py (item 15)
- tests/test_board.py (item 18)
- notes/PLAN-KNOWN-GAPS-SEVEN.md, notes/LOG.md, notes/STATE-mishmeret-builder.md

## Tests (each rule's test shown red with the rule taken out)

- Items 3, 4, 5, 17: each form above refused, and each other-way form let through, as the plan's probes measured.
  Every rule built on BOUNDARY after a case arm: git, a script, cp, the tmux kill.
- Item 5's checks: a piped check and a check before a commit, in an arm, refused.
- Item 6: the list test against `git --list-cmds=main`; an alias on the line refused; each config and remote write
  form refused in a guarded tree and let through in a scratch repository; each read form let through; `--global` and
  a `-f` into a guarded config refused from a scratch folder; each `-c`, `--config-env` and `GIT_CONFIG` form on the
  operator's push refused, and `-c user.name=x` let through.
- Items 9, 10, 15, 18: the held diff's tests, and the pill test.
- RULE 45, as for the first eight: d9fda25's guard and the built one on every command of the record at its cwd, the
  first project's under its config as girsa-builder and girsa-operator, Mishmeret's as mishmeret-builder and
  mishmeret-operator; every changed decision listed and read.

## For the first project

Nothing in its config. Each change reaches it at its next pin bump. After it, girsa-operator's `git remote set-url` in
a corpus root runs as the reviewer's own `!` command (design question 1).
