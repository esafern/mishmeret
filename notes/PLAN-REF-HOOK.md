# Plan: git's reference-transaction hook - main's branch and `guard.refs` guarded by the ref, whatever writes it

## The case

The role guard reads a command's words, so a ref moved by what it cannot read moves unguarded: a script (`python3 -c
"...subprocess.run(['git','update-ref','refs/heads/main',...])"`), a form it reads only as "the operator's" (the
first project's MEDIUM 2 and LOW 1 on notes/PLAN-PROTECTED-REFS.md: 20 forms in 6 verbs found in one afternoon, none
on the record). girsa-architect's follow-up (the first project's design-study/MISHMERET-PROTECTED-REFS-ARCHITECT.md,
"Follow-up, 2026-11-24", at 350e01e37), on girsa-verifier's NOTE 3: git's `reference-transaction` hook sees every ref
update whatever makes it, so the open list of writers becomes the closed list of ways to switch the hook off (Lesson
57, GUARD DATA BY PATH, NOT BY WRITER) - a piece of its own, planned next. Its four measured points, each built here:
the hook reads the ref's own value (`update-ref <ref> <older>` hands it zeros); main needs no landing mark - a
deletion, or a move to a commit that does not descend from the current one, is refused to all but the operator; one
function of who may move which ref, called by the Bash guard and by the hook; and the escapes the Bash guard closes.
Its scope: main's branch and `guard.refs`. Its measure: a live run, with the hook installed, of every ref update the
roles make, none refused - not rule 45's replay of Bash text.

GIRSA-ARCHITECT'S ANSWER (the first project's design-study/MISHMERET-REF-HOOK-ARCHITECT.md at 0c778416f, written
before any review of this plan; it ran the prototype in a scratch project of its own, by live_setup.py):
- Q1, refuse - the reviewer's rule of 2026-10-04 carried to git, not a Board question. Measured: the reviewer's
  terminal history holds no git line that rewinds main or moves a `guard.refs` ref, and no scheduled job runs git; a
  plain fetch is refused only for a `guard.refs` tag on origin missing locally (origin's 22 all exist locally). With no
  role the refusal names the owner's pane and `! git ...`, not a REQUEST. MEASURED, for this plan's "unmeasured": a
  subagent's shell carries its parent's role variable (three of girsa-verifier's subagents printed it), so in the hook
  an operator's subagent has the operator's rights - a measured cost for the README.
- Q2, as set; a role's branch when the record shows a case, not next by default.
- Q3, agreed, the operator too - and an escape the list missed, closed in the hook: git puts the command's own exec
  path first on a hook's PATH, so `GIT_EXEC_PATH=<a folder>` or `--exec-path=<a folder>` gave the hook a `git` that
  said yes (main moved back, `known-good` moved; a stand-in `cat` too). The hook takes PATH and HOME as installed,
  from its text's first line, and refuses a repository it cannot name. The six rows into the tests.
- Q4, fail closed, agreed - and the install replaces its own hook (known by its marker line), refusing only another's:
  a second install with another Python had been refused. The README names the reviewer's way out when every commit
  is refused: `git -c core.hooksPath=/dev/null ...` in their own terminal.
BUILT INTO THE PROTOTYPE AND MEASURED AGAIN (live5.txt): the live measure's 59 cases and the five new rows refused
(the exec path by variable and option, a tag through it, a stand-in `cat`, and a git dir outside the repository whose
commondir names it - refused before too), 64 of 64 as expected; the install refused over another's hook, replaced
its own with another Python, and put back; with no role the refusal names the owner's pane.

ON THE RECORD (the guard-measure skill's extract.py, 2026-11-25: the first project's 1,105 transcripts with its pi
sessions, 170,908 command-cwd-role triples; Mishmeret's 11, 1,815), each form searched as text in the command:
- `core.hooksPath`: 21 commands - reads (`git config --get core.hooksPath`) but girsa-verifier's 2 (`-c
  core.hooksPath=/dev/null`, in a scratch copy) and girsa-architect's 2 probes (scratch repositories) and its count
  script's text. Mishmeret's: 0.
- A `GIT_CONFIG...=` assignment: 1, the architect's probe. `--config-env`: 2 in the first project (girsa-verifier's
  probe of git's options, `git --config-env x=HOME status`, a read; a sentence) and 4 in Mishmeret's (test text, a
  docstring, commit messages).
- `HOME=` or `XDG_CONFIG_HOME=` before git: 1, girsa-operator's `export HOME=<scratch>; git clone ...` of a cloud
  simulation.
- The role variable unset (`env -u`, `unset`, `env -i`): 68 in the first project (girsa-operator 32, no role 23,
  girsa-verifier 11, girsa-architect 1, girsa-ui-steward 1), 3 in Mishmeret's; with git after it in the command: 3 -
  the architect's probe, and 2 of no role where a server is started with `env -i` and a later `git diff`, in a scratch
  folder, runs outside it.
- A shell write into a `.git/` folder's refs, packed-refs, hooks or config: 2 in the first project (the architect's
  probes, each in a scratch repository) and 2 matches in Mishmeret's (a docstring, a commit message).
So no role has switched git's hooks off, or moved them, in a guarded repository. The case is the architect's: the
Bash guard's reading has no end; the hook's has one.

THE HOLE, on main's guard (e8cfcb0; probe.py, placeholder paths, as a builder in its worktree unless named), 38 cases:
refused already - `git config core.hooksPath` (and `--worktree`, `--global`, `include.path`): the config rule; `-C
<main> ... merge` (the main tree's rule); `CLAUDE_CODE_AGENT=<the operator> git ...`. Let through: `-c
core.hooksPath=...` in every spelling (`-c`, `-ckey`, quoted, any case), `--config-env core.hooksPath=V` (both forms),
`GIT_CONFIG_COUNT/KEY/VALUE` (before git, after env, after an `export`), `GIT_CONFIG_PARAMETERS`, `GIT_CONFIG_GLOBAL`,
`GIT_CONFIG_SYSTEM`, `HOME=`, `XDG_CONFIG_HOME=`, `-c include.path=` - and the operator's own; a shell write into
`<main>/.git/` (the hook, a loose ref, packed-refs, the config: the guard reads no shell write by path, as `echo x >
<main>/README.md`); the role variable unset before git; a Python script running git.

WHAT GIT DOES WITH THE HOOK (git 2.56.1, scratch repositories; a hook that logs each call): four states, `preparing`,
`prepared`, `committed`, `aborted`, each a run of the hook; only the first two can refuse. A commit hands `HEAD` while
preparing and the branch, resolved, when prepared; git's own pseudo-refs (`AUTO_MERGE`, `REBASE_HEAD`,
`CHERRY_PICK_HEAD`, `ORIG_HEAD`, a detached `HEAD`) each a transaction - about five for every commit a rebase
replays. In a worktree git sets `GIT_DIR` to the worktree's git dir; in the main clone none. A symbolic ref's new value
is `ref:<target>`. PACKING IS NO DELETION: `pack-refs` (so `gc`) writes each ref into packed-refs, then deletes each
loose file in a transaction of its own, `<value> 0000... <ref>` - at `prepared`, packed-refs already holds the ref at
that value. A real deletion of a packed ref (`tag -d`, `update-ref -d`) prepares a second transaction, packed-refs',
whose lock - the next packed-refs, without the ref - is written before the hook is asked. The prototype's first live
run refused a builder's `git gc` on that line: told apart so, below.

THE MEASURE, a prototype on a scratch copy of `mishmeret/` (the change below), installed in a scratch project made as
a pinning project is - its main clone with the real shim and config, the prototype as its pin, a bare origin, the
builder's, the verifier's and the demo operator's worktrees, `guard.refs` giving `known-good` and `alpha-rc*` to the
operator and `demo-good` to the demo operator. Each command run as its role, by a test (the suite's way to set a
placeholder role; the guard refuses a command line that sets the variable, and refused my first run's script so):
59 cases, 59 as expected.
- LET THROUGH, 25: a builder's commit, `land.py commit`, `--amend`, fetch, a branch made and deleted, a worktree
  added and removed, its own tag made, moved and deleted, `reset --hard` in its worktree, `rebase main`, 30 commits
  and an interactive rebase replaying them, `land.py land` (its rebase, main fast-forwarded in the main clone, the
  gate on a frozen copy holding the hook), a forward `update-ref` of main (not the hook's to catch: below); the
  operator's `land.py commit` in the main clone, push, an annotated release tag made and pushed, `tag -f known-good`,
  main moved back and forward again, `pull --ff-only`, a packed release tag deleted; the demo operator's `tag -f
  demo-good`; the verifier's merge, commit and cherry-pick in its worktree, and in a copy of the main clone main moved
  back and both tags moved (a copy has its own refs); a builder's `gc` and `pack-refs --all`.
- REFUSED, 27, the ref unmoved: main moved back by a builder - `reset --hard` in the main clone, `update-ref` with and
  without the old value, `--stdin`, from a Python script, `-d`, `symbolic-ref` onto its branch, `branch -m`, by
  `--git-dir` from `/tmp`, from inside `.git`, and `branch -f` (git's own refusal); `known-good` moved, deleted as it
  stood and after `pack-refs --all`, deleted by `update-ref -d` after `pack-refs --no-prune` (loose and packed), fetched
  over and pushed over from a copy (receive-pack); a release tag made by a builder; `demo-good` moved by the
  operator; `known-good` by the demo operator; main and `demo-good` by a session with no role; and five through the
  command's environment - `PATH=<a folder with a python3 that exits 0>:$PATH`, `PYTHONPATH=<a sitecustomize that
  exits 0>`, `MISHMERET_OPERATOR=<the builder>`, `MISHMERET_CONFIG=<another>`, `MISHMERET_DIR=<another checkout>`.
- PAST THE HOOK, 7, each moving main back - the escapes: `-c core.hooksPath=/dev/null`, `GIT_CONFIG_COUNT/KEY/VALUE`,
  `GIT_CONFIG_PARAMETERS`, `HOME=<a folder whose .gitconfig sets it>`, `GIT_CONFIG_GLOBAL=<that file>`, `-c
  include.path=<that file>`; and a shell write into `<main>/.git/refs/heads/`. The prototype's guard refuses the first
  six by their words. Its probe, the 38 cases above and 9 siblings, 47: 19 decisions changed, each to refused - the
  15 forms let through now, `HOME=<x>;` and `X=1 HOME=<x>;` as statements before git, an `export` naming
  `GIT_CONFIG_GLOBAL` among others, and the operator's `GIT_CONFIG_...` before `tag -f demo-good`; let through as
  before - the same forms in a scratch folder, another `-c` key, a config read, `git status` and `git log` with the
  hooks moved (a read), `HOME=<x> bash -c ...` and `GIT_CONFIG_GLOBAL=<x> python3 ...` before a later git, `clone`.
- A COST, OBSERVED: a release tag made on origin outside the shared repository (here a second clone's push; a
  release made on the hosting site would be one) fails a builder's plain `git fetch origin` whole - git's tag
  auto-follow would create the operator's tag, so the transaction is refused and `origin/main` stays where it was.
  `git fetch --no-tags origin` fetches the rest; the operator's fetch brings the tag.
- ITS COST IN TIME (macOS, the scratch project): 30 commits 3.7-4.0 s against 0.5-0.6 s with the hooks off; a rebase
  replaying 30 commits 2.6-2.8 s against 0.1 s. A hook that only exits 0 gives 1.5-2.5 s and 2.3 s: most of it is git
  starting `/bin/sh` for each state of each transaction, whatever the hook holds; the check adds about 0.05-0.08 s a
  commit.
RULE 45 (main e8cfcb0's guard against the prototype, the skill's decide.py and compare.py; by role, as girsa-builder
and as girsa-operator on the first project's 170,908, its config as it stands at its pin e7c1c6d; by role, as
mishmeret-builder and as mishmeret-operator on Mishmeret's 1,815, its config): the first project's three runs each
newly refused 1, newly let through 0, faults 0; Mishmeret's each 0, 0, 0. The 1 is girsa-operator's cloud simulation,
`export HOME=<scratch>; git clone ... ~/work/mishmeret && git -C ~/work/mishmeret worktree add ...`: there `~` meant
the scratch HOME, and the guard reads it with its own, as the Mishmeret checkout of `guard.trees` - a named cost. The
prototype's first run had 2: that one, and girsa-verifier's `HOME=<x> /bin/bash -c '...'; ... git show ...`, a HOME
that prefixed another command, before a read - the rule narrowed to where a variable reaches git, and a read let
through (the change, item 4).
The scripts, the decision files and the reports: this session's scratchpad, hook/ (live_setup.py, test_live.py,
live4.txt and, after the architect's answer, live5.txt; escapes2.json, probe2-old.out, probe2-new.out, r45-*-old.jsonl and r45-*-new2.jsonl, cmp2-*.txt).

## The change

1. ONE RULE, TWO CALLERS. `role_guard.may_move(role, owner, kind, forward=False)`: a `guard.refs` ref its owner's
   alone; a role's branch its own and the operator's (#310 A); main's branch the operator's, but a fast-forward any
   role's - and only the hook can tell one. `_ref_refusal` calls it where it now tests the role inline (so the Bash
   guard is unchanged: it passes no `forward`); the hook calls `_owner` and it on each line.
2. THE HOOK, `mishmeret/ref_hook.py`, run by git at `prepared` through the project's shim (`.claude/hooks/ref_hook.py`,
   kind `refuses`). For each line naming a ref under `refs/`, in a guarded repository (a copy has its own refs): its
   owner by `_owner` with main's entry of the worktree list (main's branch and `guard.refs`); the ref's value read by
   git, not the line's; nothing moved when the value is the same, or when a deletion leaves it in the packed refs (the
   lock being written, else the file); `forward` when the new value is a commit that descends from the current one.
   The repository is git's `GIT_DIR`, else the folder, and git's own variables are cleared before the guard asks git
   about other repositories; a repository git cannot name is refused (Q3). The role is CLAUDE_CODE_AGENT; with none,
   a session with no role, refused and told the owner's pane (Q1). Exit 1 refuses the transaction, with the reason;
   the hook's own fault refuses it too.
3. THE HOOK'S TEXT, written by `ref_hook.py --install`, run by the project's shim in the main clone (`MISHMERET_AS` names
   it): AS INSTALLED, NOT AS THE COMMAND SET IT - its first line sets PATH and HOME as the install had them (Q3: the
   command's exec path came first on a hook's PATH); `prepared` alone, and a transaction naming no ref under `refs/`
   let through in the shell, before any Python (`HEAD` and git's pseudo-refs are no one's); then `env -i` with
   `PATH`, `HOME`, `GIT_DIR`, the role variable and the checkout's `MISHMERET_DIR` if the install had one, the
   installing Python by its path with `-I`, the shim by its path, each quoted for the shell. A missing shim refuses.
   The install refuses a linked worktree, a set `core.hooksPath` (git would not run the hook), and a hook that is not
   its own; its own, by the marker line, it replaces (Q4).
4. THE ESCAPES IN THE BASH GUARD, in a guarded repository, for every role, the operator too (design question 3): on
   git's line `-c` or `--config-env` with `core.hooksPath`, `include.` or `includeIf.` (the push rule's own reading,
   `_push_config`, given the keys); and a `GIT_CONFIG...=`, `HOME=` or `XDG_CONFIG_HOME=` (another config file, which
   can set them) where it reaches git - on git's own prefix, in an `export` before it, or as an assignment that is a
   statement of its own (`HOME` is exported already) - not one that prefixes another command. Not for a verb of the
   classification's READS, nor `clone` and `init`: none runs a ref transaction of the repository.
5. THE CONFIG: each `guard.refs` glob is a ref's full name, `refs/...` (the hook's shell reads only those).

Not in this piece, each a named cost: a forward move of main that skips land.py (the main tree's rule stays the Bash
guard's); a role's branch (design question 2); a script that runs git with its hooks off (unread, as any script); a
shell write into the main clone's `.git/` (the older gap: no shell write is read by path); a `~` after an `export
HOME=` in the same command, read with the guard's HOME (rule 45's 1); a release tag made on origin elsewhere, which
fails a non-owner's plain fetch (measured above); an operator's subagent, which carries the operator's variable and
so has the operator's rights in the hook while the Bash guard judges it as no role (measured by girsa-architect); the
reviewer's own terminal, refused a protected move like a session with no role (Q1). Unmeasured: git before 2.28 (no
such hook), the reftable backend (no packed-refs), Linux and Windows (`env -i`, `/bin/sh`).

## Design questions (to girsa-architect; answered at 0c778416f, the plan's head)

1. NO ROLE VARIABLE: the hook judges a session with no role - refused a protected move, as land.py refuses one and the
   Bash guard judges one - so unsetting the variable is no escape (the architect's third), and the Bash guard needs no
   rule for it. Its cost: the reviewer's own terminal, outside every session, is refused moving main back or a
   `guard.refs` ref, and runs it as `! git ...` in the owner's pane, or with `-c core.hooksPath=/dev/null` in that
   terminal, which no guard reads. Or: let it through, and the Bash guard refuses the variable unset before git in a
   guarded repository (the record: 0 such but the probe). My recommendation: refuse; and is it the reviewer's?
2. THE SCOPE: main's branch and `guard.refs`, as the architect set it; a role's checked-out branch stays the Bash
   guard's. The hook reads the worktree list anyway, so a role's branch is `listing` for `listing[:1]` - but every
   commit is an update of one, and a false refusal there stops the most work. My recommendation: as set, and a
   role's branch a piece of its own, with its own live run.
3. THE ESCAPES, the operator too: with the hooks off any ref moves, `demo-good` too (#310 A: the demo operator's
   alone), so the operator is refused them as every role is; the reviewer's `! git ...` stays. My recommendation: so.
4. INSTALL AND FAULT: the operator installs the hook once per clone, at the pin bump that brings it, in the
   repository's main clone (each corpus root and the Mishmeret checkout by the project whose repository it is). A
   missing shim, a missing pin or the hook's fault refuses every transaction naming a ref under `refs/` - every commit
   - as the Bash guard's shim refuses every tool call on a missing pin. My recommendation: fail closed, so.

## Files

- mishmeret/ref_hook.py (new: the hook, its install)
- mishmeret/role_guard.py (`may_move`; the escapes; `_push_config` given its keys)
- mishmeret/config.py (`guard.refs` globs under `refs/`)
- tests/test_ref_hook.py (new), tests/test_guard.py, tests/test_config.py
- README.md (the hook, its install, what it refuses and its costs; the config's `guard.refs` line)
- notes/PLAN-REF-HOOK.md, notes/LOG.md, notes/STATE-mishmeret-builder.md

## Tests (each rule red with it taken out: mutate.py)

- The hook on a scratch project made as above (git, the real shim, a pin linked to the tree under test): the live
  measure's cases, each as its role - the roles' own work let through, a landing among it; each protected move
  refused, its ref unmoved; each variable of the command's environment refused, the exec path's six rows among them
  (girsa-architect's Q3); a copy let through; with no role, the owner's pane named.
- The install: its text; refused from a worktree, with `core.hooksPath` set, over another's hook; its own replaced
  with another Python (Q4).
- The Bash guard: each of the probe's 15 forms refused, the operator's too; the siblings let through (a scratch folder,
  another key, a read, `clone`).
- The config: a `guard.refs` glob not under `refs/` refused at load.

## For the first project

At its pin bump to this piece's commit: its `.claude/hooks/ref_hook.py` (a shim, as its others), then girsa-operator
runs `python3 .claude/hooks/ref_hook.py --install` in the main clone - the first project's own step, as the time
check's `--install` was. Its config is unchanged (`guard.refs` is already `refs/...`). For Mishmeret's own repository,
mishmeret-operator does the same after Mishmeret's own pin moves.
