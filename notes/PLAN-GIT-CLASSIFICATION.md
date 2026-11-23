# Plan: git's command list as a classification

## The case

The first project's Board #302, girsa-architect's question, answered A by the reviewer at 18:49 on 2026-11-23: "close
the eight in the piece you are building". In its record, A reads: git's main list becomes a classification - each name
in a verb set that changes a branch, the index or the tree, refused where `reset --hard` is, or in a named set that
changes none - and a test fails on a name in neither; the eight are placed in the first.

The eight, found while measuring the known gaps' seven (notes/PLAN-KNOWN-GAPS-SEVEN.md, "Found, for the reviewer"),
are `history`, `replay`, `symbolic-ref`, `read-tree`, `update-index`, `checkout-index`, `sparse-checkout` and
`filter-branch`. They are in no verb set of the guard's, so any role may run them in the main tree. Item 6a
(e5a4d40) wrote git's own list down, `GIT_VERBS`, 181 names from `git --list-cmds=main` on git 2.56.1, tested as a
superset of what git lists.

GIRSA-ARCHITECT'S ANSWER on the two departures (the first project's design-study/MISHMERET-GIT-CLASSIFICATION-ARCHITECT.md
at 046d111f): both agreed. Four sets, since only CHANGES_MAIN decides a refusal and the others are labels; its caution
taken: WRITES ELSEWHERE holds the writers of the shared repository (refs, tags, objects, config), not a harmless set.
The 27 are within #302 A, send-pack and http-push within the push rule, for-each-repo within item 6a: none goes back to
the reviewer. Its finding beyond #302, the reviewer's Board #304 for a later piece: the guard judges a ref by the
folder a command runs in, but the ref is the repository's - from a worktree `update-ref refs/heads/<main's branch>`,
and from anywhere `tag -f known-good`, pass both the guard and git. With it, this plan's found writers below. Nothing
of #304 is built here.

GIRSA-VERIFIER'S REVIEW (the first project's design-study/step5-verification/mishmeret-git-classification-plan-
2026-11-23/REVIEW.md; its message #3072): READY on two conditions, both built with a test each.
- MEDIUM 1: three "read forms" wrote the main tree's files, run in a throwaway repository on git 2.56.1:
  - `GIT_INDEX_FILE=<tmp> git read-tree --reset -u HEAD~1`;
  - `git read-tree --reset -u --index-output=<tmp> HEAD~1` (read-tree's -u updates the work tree whatever index it
    writes);
  - `git checkout-index -a -f --prefix=./` (the prefix is put before each path as a string).
  Now read-tree's exemptions hold only without -u, and checkout-index's prefix is a read form only when it is
  absolute and outside the tree.
- LOW 1: GIT_INDEX_FILE naming the tree's own index (`.git/index`, `$GIT_DIR/index`) had counted as temporary; now it
  does not.
- NOTE 2: `submodule foreach` runs a command the guard cannot read, the reason for-each-repo is refused; it is now
  refused for every role with it (no guarded tree has a .gitmodules today).
- NOTE 3: rule 45 run on the build with all 53 in CHANGES_MAIN (below).
- NOTE 1, for #304's piece: `git branch -m <new>` with one name renames the checked-out branch; `git init
  --separate-git-dir=<path>` in an existing repository moves its .git.

THE BUILD'S RUN OF RULE 45 (the build against main's guard, e5a4d40's, on the record as extracted above): girsa-builder
3 newly refused, girsa-operator 0, mishmeret-builder 0, mishmeret-operator 0; 0 newly let through, 0 faults. The 3 are
the prototype's second run's, each read there: 2 `update-index --cacheinfo` into the main clone's index, 1
`symbolic-ref` write in a corpus root.

THE RECORD before the measure (girsa-verifier's count, that project's #3010, over 1,055 transcripts):
- `read-tree` and `update-index`, with `replay` and `history`, ran 72 times, most on copies or against a temporary
  index of their own.
- Two sessions (2026-10-08 and 2026-10-11) built a commit by hand in the main clone this way.
- `update-index --chmod=-x` ran 3 times in Mishmeret.
- `symbolic-ref` ran 27 times, nearly all reads; it wrote once in a guarded folder (2026-11-10).

THE MEASURE, a prototype on a scratch copy of `mishmeret/` (the guard-measure skill's scripts):
- PROBED (probe.py, placeholder paths), as a builder in the main tree:
  - each of the eight is refused: `history drop`, `replay --advance`, `symbolic-ref HEAD <ref>` and `-d`,
    `read-tree HEAD`, `update-index --assume-unchanged`, `checkout-index -a -f`, `sparse-checkout set`,
    `filter-branch`;
  - their read forms are let through: `history ... --dry-run`, `replay --ref-action=print`, `symbolic-ref --short
    HEAD`, `read-tree` with GIT_INDEX_FILE or `--index-output=`, `update-index --refresh`, `update-index` with
    GIT_INDEX_FILE, `checkout-index --prefix=`, `sparse-checkout list`;
  - in a worktree and for the operator, `history drop` is let through, as `reset --hard` is. The suite's guard tests:
    40 passed.
- RULE 45 (extract.py over the record again: the first project's 1,049 transcripts with its pi sessions, 162,951
  command-and-cwd pairs; Mishmeret's 9, 1,449). The guard on main (e5a4d40's) against the prototype, as girsa-builder,
  girsa-operator, mishmeret-builder and mishmeret-operator:
  - FIRST RUN: 7, 0, 3 and 1 newly refused, 0 let through, 0 faults. Every one read; 8 were false refusals of the
    prototype, in three kinds:
    - `git history -h` and `git replay -h` (my own, reading their help);
    - `git -C <foreign> symbolic-ref refs/remotes/origin/HEAD 2>&1`, a read whose redirection was counted as a second
      word;
    - four `read-tree`/`update-index` runs on a temporary index set by `export GIT_INDEX_FILE=<scratch>` earlier in the
      command and `unset` after it.
    Fixed in the prototype: `-h`/`--help` is a read; a redirection is no word; a temporary index exported earlier in
    the command and not unset since counts as one on git's line.
  - SECOND RUN: girsa-builder 3 newly refused, the others 0; 0 let through; 0 faults. Each of the 3 is a write the
    rule means to refuse a builder:
    - 2: `git update-index --cacheinfo 100644,<blob>,<file>` in the main clone, with no temporary index - it stages
      into the main tree's own index;
    - 1: `cd <a corpus root> && git symbolic-ref HEAD refs/heads/main`, the 2026-11-10 write.
    As girsa-operator, none changes: the operator's main-tree rights are as before.
  - With the 27 FOUND writers below also in the first set (a third run of the first): the same counts. They cost
    nothing on the record.

## The change (mishmeret/role_guard.py)

1. THE EIGHT INTO CHANGES_MAIN, with their read forms in one function, `_leaves_it(verb, rest, lead, before)`, which
   replaces the two hand-written LEAVES_IT tests in `refusal`. A form leaves the tree when it is:
   - `-h` or `--help` (any verb);
   - for history, `--dry-run`; for replay, `--ref-action=print`;
   - for symbolic-ref, one name and no `-d`/`--delete`;
   - for read-tree, `-n`/`--dry-run` or `--index-output=`; for read-tree and update-index, a temporary index
     (GIT_INDEX_FILE on git's line, or exported earlier in the command and not unset since);
   - for update-index, `--refresh` or `--really-refresh` alone (the stat cache, as `git status` refreshes it);
   - for checkout-index, `--prefix=` or `--temp`; for sparse-checkout, `list` or `check-rules`;
   - as before: `merge --ff-only`, `stash list|show`, and `apply --check|--stat|--numstat`.
   Redirections are not words of git's. A pin and a foreign tree stay refused to every role, `merge --ff-only` too,
   as now.
2. THE CLASSIFICATION: every name of GIT_VERBS in exactly one named set, and a test that fails on a name in none or in
   two, and on a name `git --list-cmds=main` gives that GIT_VERBS lacks (as now). Four sets, not the answer's two -
   see DEPARTURE 1:
   - CHANGES_MAIN (53): the guard's 18; the eight; and 27 FOUND, each of which writes the branch, the index or the
     files of the tree it runs in:
     - `stage` (add's other name);
     - `bisect` (its start, good, bad and reset check out commits; log, visualize, view and help are reads);
     - `merge-file` (`-p`/`--stdout` a read), `merge-index`, `merge-one-file`, `merge-octopus`, `merge-ours`,
       `merge-recursive`, `merge-recursive-ours`, `merge-recursive-theirs`, `merge-resolve`, `merge-subtree` (merge's
       strategies), `mergetool`, `checkout--worker` (checkout's), `rerere` (replays resolutions into files);
     - `submodule` and `submodule--helper` (status and summary are reads; foreach is refused for every role, as
       for-each-repo is), `subtree`;
     - `fast-import`, `p4`, `cvsimport`, `archimport`, `quiltimport`, `cvsexportcommit`, `cvsserver`,
       `receive-pack` (import or receive commits onto the branches here);
     - `refs` (`migrate` rewrites ref storage; list and verify are reads).
   - OWN RULES (6): `push` (the operator's); `config` and `remote` (item 6b); and FOUND, for every role:
     - `send-pack` and `http-push`: a push without `git push`, which the push rule's force and delete reading never
       sees. Refused for every role: the operator pushes with `git push`.
     - `for-each-repo`: it runs a git command in each repository a config key lists, a verb this guard cannot read.
       Refused as an alias is (item 6a).
     0 of either on the record.
   - WRITES ELSEWHERE (65): objects, other refs, other folders, credentials, mail and servers - no checked-out branch,
     index or tree. For example branch, tag, fetch, worktree, gc, prune, repack, notes, replace, reflog, clone, init,
     maintenance, bundle, archive, format-patch, credential-*, send-email, imap-send, daemon, hook. Let through as
     today.
   - READS (57): change nothing. For example log, show, diff, status, grep, rev-parse, ls-files, cat-file, blame,
     describe, fsck, version, help.
   Counted from the prototype's four sets over git's 181 names (53 + 6 + 65 + 57): every name placed, none twice.
3. The message for the eight is CHANGES_MAIN's own ("would change the main tree ..."); for the two pushes and
   for-each-repo, their own words.

DEPARTURE 1, for the review: the answer names two sets, one that changes and one that changes none. 65 names write
something, but not the checked-out branch, index or tree. Called "changes none" they would be a false label (A SENTENCE
OF ABSENCE IS A CLAIM), so they are a set of their own, WRITES ELSEWHERE, and READS holds only names that change nothing.
The guard's decision is the answer's: only CHANGES_MAIN is refused where `reset --hard` is.

DEPARTURE 2, for the review: the 27 found and the 3 own-rule names were not among #302's eight. The answer's rule
places the 27: each changes the branch, index or tree it runs in, and none is on the record. The 3 own-rule names
extend the push rule and item 6a by the same reasoning (a push or a git verb this guard cannot see), 0 on the record.

Not in this piece - FOUND FOR THE REVIEWER, in WRITES ELSEWHERE and let through today, each able to undo another
role's work without touching the main tree:
- `git branch -D/-f` of another role's branch;
- `git worktree remove --force` of another role's worktree;
- `git replace`, which changes what every tree reads as history;
- `git reflog delete/expire` and `git gc --prune=now`;
- `git maintenance register`, which writes the global config (a sibling of item 6b's `--global` rule).
Not counted on the record yet. A question for the reviewer after this piece, not built here.

## Files

- mishmeret/role_guard.py, tests/test_guard.py
- notes/PLAN-GIT-CLASSIFICATION.md, notes/LOG.md, notes/STATE-mishmeret-builder.md

## Tests (each rule red with it taken out: mutate.py)

- Each of the eight refused in the main tree as a builder; let through in a worktree and for the operator.
- Each read form above let through in the main tree; each first-run false refusal's form (help, a redirection, an
  exported temporary index) let through; the same command with the index unset before git refused.
- The classification: every name in exactly one set; a name added to GIT_VERBS but placed nowhere fails; the list
  test as now.
- send-pack, http-push and for-each-repo refused for every role, the operator too.
- Rule 45 again on the build, as above.

## For the first project

Nothing in its config. At its next pin bump its builder's 3 measured writes would be refused: the 2 `update-index
--cacheinfo` into the main clone's index, and a symbolic-ref write in a corpus root. Each is the operator's.
