# Plan: a ref judged by the repository, not the folder

## The case

The first project's Board #304, girsa-architect's item, found while answering the classification plan: the guard
judges a git command by the folder it runs in, but a branch or a tag belongs to the shared repository, which the main
clone and every worktree share. So from its own worktree a role can move main's branch (`git update-ref
refs/heads/<main> HEAD~1`) or the `known-good` tag (`git tag -f known-good HEAD~1`), which the public demo builds from
and "verified through" is read against. The reviewer answered A, 2026-11-23 20:32: "A. A next piece, after the
classification lands. Each protected ref is refused to every role but its owner, wherever the command runs: main's
branch, `known-good` and the release tags are the operator's, and `demo-good` the demo operator's. Another role's
branch and worktree are that role's. mishmeret-builder's list goes in the same piece" - that list: `git branch -D/-f`
of another role's branch, `git worktree remove --force` of another role's worktree, `git replace`, `git reflog delete`
and `gc --prune=now`, `git maintenance register`; and, from the state file, `branch -m` and `init --separate-git-dir`.
(The answer stood on the record a day before I read it: no watcher was running on an item another role had posted.)

THE HOLE, on main's guard (9b979d3; the guard-measure skill's probe.py, placeholder paths, as a builder in its
worktree unless named): 42 cases, 2 of them owners' own (the operator's `tag -f known-good`, the demo operator's
`tag -f demo-good`); of the other 40, 38 let through. Refused already: only `git push . HEAD:main` (push is the
operator's) and `git -C <main> update-ref ...` (the main tree's folder rule). Let through, among them: update-ref of
main's branch (`-d` and `--stdin` too); `tag -f`, `-d` and a new `known-good`, `alpha-rc21`; the operator's `tag -f
demo-good` and the demo operator's `tag -f known-good`; `branch -f/-D/-m/-M/-C` naming main's branch; `fetch .
HEAD:main`, `fetch -f origin 'refs/tags/*:refs/tags/*'`, `fetch --tags -f`; a verifier's `branch -D/-f` of the builder's
branch and `worktree remove --force`/`move` of the builder's worktree; `replace`, `reflog delete/expire`, `gc
--prune=now`, `prune --expire=now`; `maintenance register/start`; `init --separate-git-dir`; `checkout
--ignore-other-worktrees -B main`, `switch --ignore-other-worktrees -C main`; `rebase --update-refs`, `filter-branch --
--all`, `fast-import`, `symbolic-ref refs/heads/main ...`, `replay --ref-action=update`.

WHAT GIT ITSELF REFUSES (git 2.56.1, a scratch repository: main checked out in the main clone, a branch in a worktree,
each case on a fresh copy): `branch -f`/`-D` of a branch checked out in any worktree; `checkout -B main` and `branch -M
<x> main` from a worktree; `fetch . <x>:main` (`+` too); `push . <x>:main`; `worktree remove` of the main working tree.
It lets through, and the ref moves: `update-ref refs/heads/main`; `tag -f known-good`; `branch -m` of a branch checked
out elsewhere (it renames that worktree's branch); `checkout --ignore-other-worktrees -B main`; `symbolic-ref
refs/heads/main refs/heads/<x>` (main becomes a link to another branch); `fetch -f <remote> --tags` (moves a local tag
to the remote's; without `-f` git refuses to clobber it); `worktree add -f <path> main`, and a commit there moves main;
`worktree remove` of another worktree, from anywhere. `update-ref main <x>` (a short name) writes no branch.

ON THE RECORD (the first project's 1,061 Claude Code transcripts, 165,915 distinct role-command-cwd triples, each
command's role from its transcript's agentSetting; Mishmeret's 11 transcripts, 1,808 command-cwd pairs, hold none of
these forms but its builder's own `branch -d`/`-m` and two `replay -h`). Each git call found by the guard's own GIT
matcher:
- Protected tags moved (`tag -f/-d` naming `known-good`, `demo-good` or `alpha-rc*`): girsa-operator 510, the demo
  operator 5 (each `demo-good`, its own), no role 5 (release tags before the roles, 2026-09), girsa-builder 1 and
  girsa-verifier 1 (each in a scratch clone or copy). Created by a role other than
  the operator: the demo operator's `demo-good`, and two placeholder tags in a verifier's and a builder's copies.
- update-ref: 31. With no role, before the roles, 22: main's branch once, and 21 of a commit-tree loop on a branch
  named by a variable. The operator's 5: 2 of #306's rewrite (`refs/heads/$b`, a loop over the branches, on the
  reviewer's A) and 3 of one of its own branches. girsa-architect's 3, each `refs/heads/main` of a scratch repository;
  girsa-ui-steward's 1, its own branch.
- branch -d/-D: 38, each of the role's own branch (girsa-builder 17, girsa-ui-steward 9, girsa-operator 4, girsa-verifier
  2, the demo operator 1, no role 3 - one, `-C <the ui-steward's worktree> branch -D <a branch>`, whose owner the record
  does not say). branch -f: 14, each the role's own or a scratch repository's (2 naming main's branch as the start point).
  branch -m: 3, girsa-builder's own. branch -c/-C: 10.
- worktree remove: 30 - girsa-operator 18 (copies, scratch trees, `~/work/mishmeret-operator`), girsa-builder 3 (its
  own second worktree and two scratch worktrees it made), girsa-verifier 2 (in its copies), no role 2. worktree prune: 1.
- symbolic-ref written: 2, girsa-operator's, in another repository. init --separate-git-dir: 1, girsa-verifier's, in a
  scratch probe outside every guarded tree.
- None (A SENTENCE OF ABSENCE: each searched as a word of the git call): update-ref --stdin; fetch into main's branch or
  into refs/tags; fetch --tags --force; push to `.`; checkout/switch --ignore-other-worktrees; worktree add -f; rebase
  --update-refs; filter-branch; fast-import; replay (but `-h`); replace; reflog delete/expire; gc (any); prune;
  maintenance (any).
So no role but an owner has moved a protected ref in the shared repository, and no role another role's branch or
worktree. The case is the reviewer's A: one `tag -f` points the demo and the "verified" mark at an unchecked commit,
and nothing refuses it.

THE MEASURE, a prototype on a scratch copy of `mishmeret/` (the change below, as recommended in the design questions):
- The probe, with git's answers faked on the placeholder paths (main checked out in `/work/book`, the builder's branch
  in its worktree, the three tags in `guard.refs`): of the 40, 39 refused and `worktree prune` let through (it drops
  only the entries of worktrees whose folders are gone), the owners' 2 let through; 6 forms more, each refused
  (`worktree add -f <path> main`, update-ref of `refs/heads/$b`, a verifier's forced tag fetch and its `-C <the
  builder's worktree> branch -m`, `tag -f "alpha-rc$N"`, a worktree removed by a variable); and 29 siblings, each let
  through as intended - a builder's own `tag -f
  my-test`, `branch -D/-m/-f` and update-ref of its own branch, `checkout -B` of a new one, `fetch origin [main]`, a
  scratch worktree removed, `replay --ref-action=print`, `gc`, `prune -n`, `replace -l`, `reflog show`, `maintenance
  run`, and `init --separate-git-dir` and `tag -f known-good` in a scratch folder let through; the operator's `tag -a
  alpha-rc22`, `tag -f known-good`, update-ref of main's branch from a worktree, and its removal of a role's worktree
  let through; the demo operator's `tag -f -a demo-good` let through; a ref named by a variable refused.
- RULE 45 BY ROLE (each command judged as the role that ran it, the old guard against the prototype, under the first
  project's config with `guard.refs` and `roles[].worktrees` added; scratch versions of decide.py and extract.py, item 6
  below). The first project, 165,915 judged: newly refused 4, newly let through 0, faults 0. The 4 are each a release
  tag made by a session with no role, before the roles (`git tag -a alpha-rc9`, `alpha-rc10`, and `alpha-rc14` twice,
  once `-f`): the refusal intended, since a release tag is now the operator's and a session with no role is told to
  start as it. Mishmeret, 1,840 judged (its config, the builder's worktree named): no change.
  The prototype's first run had 9; 5 were false refusals, fixed in the prototype: 3 of girsa-architect's, a `$(git -C
  <its worktree> branch --show-current)` inside a quoted string, whose words ran past the substitution's `)` and were
  read as a branch made; and 2 with no role, a fetch into `refs/remotes/origin/audit/<name>-$L`, refused because a
  variable stood in the name. Now git's words end at the substitution they are in, and a variable the command does not
  set is read as `*`: refused only where it may cover a protected ref (`git tag -f "alpha-rc$N"` refused, `git tag -f
  "rc-$N"` let through), and a worktree named by one is refused to every role but the operator.
  The build's run adds the skill's two fixed roles, a non-operator and the operator, over both records.

## The change

1. THE OWNERS. Main's branch - the branch checked out in a guarded repository's main clone, read from git (`git
   worktree list --porcelain`, its first entry) - is the operator's, with no config. The config gains two OPTIONAL
   fields: `guard.refs`, `{"<ref glob>": "<role>"}` (the first project: `refs/tags/known-good` and
   `refs/tags/alpha-rc*` the operator's, `refs/tags/demo-good` the demo operator's), and `roles[].worktrees`, each
   role's worktree paths; the branch checked out in one is that role's, and so is the worktree. Each owner must be a
   role of the config, or it is refused at load.
2. THE REF A COMMAND MOVES, read from its words (a short name as git reads it there):
   - update-ref `<ref>` and `-d <ref>` (`HEAD`: the branch checked out where it runs); tag create, `-f` and `-d` (none
     for a listing form); branch `-f`, `-d/-D`, `-m/-M`, `-c/-C` (both names; one name: the checked-out branch too)
     and create; checkout/switch `-B/-C/-b/-c`, and the branch a `--ignore-other-worktrees` checks out a second time;
     worktree add `-b/-B`, and the branch `-f` checks out a second time; symbolic-ref `refs/...` written or deleted;
     fetch's refspec destinations, and `refs/tags/*` for a forced `--tags`; push's destinations to `.` or a path.
   - worktree remove and move: the worktree named.
   Each, where the command runs in a guarded repository (the main clone or any worktree, the places `_git_trees`
   reads; not a copy), is refused to every role but its owner. The operator may also move a role's branch and remove
   or move a role's worktree (design question 2); a `guard.refs` ref stays its owner's alone.
3. WHAT THE GUARD CANNOT READ, refused in a guarded repository to every role but the operator (design question 3):
   `update-ref --stdin`, `rebase --update-refs`, `filter-branch`, `fast-import`, `replay` but `--ref-action=print`, and
   a worktree named by a variable the command does not set. A ref so named is read with `*` for the variable, and
   judged as a glob: refused where it may cover a protected ref.
4. MISHMERET-BUILDER'S LIST: in a guarded repository, to every role but the operator - `replace` but its listing,
   `reflog delete/expire/drop`, `gc --prune...`, `prune` but `-n`; for every role, wherever it runs - `maintenance
   register/unregister/start/stop` (they write the global config, as `config --global`, the reviewer's own command);
   for every role in a guarded tree - `init --separate-git-dir`.
5. ONE PLACE IN THE GUARD: a function `refusal` calls on each git call after the config rule, before the pin rule, so
   no new rule joins rules.py's RULES.
6. THE SKILL'S MEASURE BY ROLE: extract.py writes each command's role (its transcript's agentSetting; a subagent's from
   its parent session; pi's none), and decide.py takes `each` for ROLE, judging every command as the role that ran it.
   Its self-check gains the rows.

Not in this piece: a protected branch already checked out a second time before this rule (by `worktree add -f` or
`--ignore-other-worktrees`, none on the record) - a commit there moves it, and those commands are judged by folder; a
branch checked out nowhere (a role's parked branch) is no one's; writes into another role's worktree's files.

## Design questions (to girsa-architect)

1. THE OWNERS IN THE CONFIG: `guard.refs` by glob, and each role's worktrees, the branch checked out there its own. Or
   a role's branches by name globs (`builder-*`), which would also cover a parked branch? My recommendation: the
   worktrees. The record's branch names follow no one prefix per role (its own deletions include `land-*` and `keep-*`
   names and others with no role's prefix), so a glob would refuse a role its own branch or miss one; git already refuses `branch -f/-D` of a
   checked-out branch; a parked branch stays unprotected, a named cost.
2. THE OPERATOR AND A ROLE'S BRANCH AND WORKTREE: #304 says each is "that role's". The record: the operator removed 18
   worktrees (copies, scratch, a finished one) and moved roles' branches once, #306's rewrite on the reviewer's A; the
   cleanup of #307 is under way. My recommendation: the operator may move a role's branch and remove or move a role's
   worktree (its cleanup, on the reviewer's word), and no other role may; a `guard.refs` ref stays its owner's alone,
   so the operator is refused `demo-good`.
3. THE FORMS THE GUARD CANNOT READ, and the repository-wide writes: refused in a guarded repository to every role but
   the operator, or to every role, the operator too (the reviewer's own command, as `config --global`)? My
   recommendation: all but the operator - none of them is on the record, and the operator's #306 rewrite was of this
   kind.

## Files

- mishmeret/role_guard.py (the owners, the refs a command moves, the refusal)
- mishmeret/config.py (`guard.refs`, `roles[].worktrees`, OPTIONAL; owners checked)
- .claude/skills/guard-measure/extract.py, decide.py, self-check.json, SKILL.md (the measure by role)
- tests/test_guard.py, tests/test_config.py, tests/test_guard_measure.py
- README.md (the config's two fields; what the guard refuses)
- notes/PLAN-PROTECTED-REFS.md, notes/LOG.md, notes/STATE-mishmeret-builder.md

## Tests (each rule red with it taken out: mutate.py)

- On placeholder paths, git's two answers faked (the checked-out branches; the branch where a command runs): each of
  the probe's 45 refused forms refused as its role, each of the 29 siblings let through, and the owners' own forms let
  through - the
  operator's tags and main's branch, the demo operator's `demo-good`, a role's own branch and worktree, the operator's
  move of a role's branch and worktree.
- A real scratch repository (git, no fake): main's branch read from its main clone, a worktree's branch read as its
  role's, from a worktree and from the main clone.
- The config: each field absent taken as none; an owner that is no role refused at load.
- The measure by role: extract.py's role from agentSetting and from a subagent's parent; decide.py's `each`.

## For the first project

At its pin bump to this commit, main's branch is the operator's with no config change. Its config then gains
`guard.refs` (`known-good`, `alpha-rc*`, `demo-good`) and `roles[].worktrees` - an older pin refuses a config naming
them, so they land with the bump, as `runner` did.
