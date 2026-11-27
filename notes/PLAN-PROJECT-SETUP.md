# Plan: a project's setup - the guard alone, written by one command

## The case

The reviewer, 2026-11-27, in mishmeret-builder's pane: "what can we do to get a role in place to use mishmeret for
the normalizer project. is that work planned" - answered: not planned; the guard alone (notes/PLAN-GUARD-ONLY.md)
built what a project needs and put "setting the normalizer up" outside its piece, the reviewer's or its session's
step; a recipe by hand, or a Mishmeret piece that ships the setup. Then: "a mishmeret piece. plan it".

Today a project takes the guard alone by copying three of Mishmeret's own `.claude/` files by hand - the shim's
helper (94 lines, which names the config's old home, `.claude/mishmeret.json`), the hook's shim, the settings' hook -
and writing its config and an agent file per role. Mishmeret ships none of them, and the path has never run end to
end: the guard alone was measured by judging a copy's record against a config (decide.py), never by a session started
in a project set up so (A PATH TURNED ON IS RUN FOR THE FIRST TIME).

THE PROJECT, read 2026-11-27 (the citation normalizer, `~/work/sefaria-citation-normalizer`): its main clone on
`main`, its own work uncommitted there (data files); a branch `next-work`; two tags (`dataset-v1`, `v0.1.0`); no
`.claude/settings.json`, no agent file, no git hook. Its record (the guard-measure skill's extract.py, 2026-11-27): 2
transcripts with its pi sessions, 510 distinct commands, every one in its main clone, none with a role (380 on
2026-11-25). Its roles, the reviewer's (PLAN-GUARD-ONLY's head): `norm-builder` in a worktree of its own, and an
operator (`norm-operator`, a placeholder: the reviewer's `!` or a second session); `~/work/rav-shvat-blog` foreign;
`beta-rc*`, `stage` and `prod` the operator's tags.

THE REVIEWER'S ANSWERS (2026-11-27, to mishmeret-builder's three questions in its pane, after girsa-operator's "the
reviewer, in my pane: ... you will make that happen tonight"): the normalizer set up TONIGHT by the measured
prototype, pinned at 57b87b2, this piece landing after ("Prototype tonight"); `refs/tags/v*` not protected ("No, leave
v* open"); the design questions to girsa-architect ("Wait for girsa-architect"). DONE BY GIRSA-OPERATOR the same night,
as the prototype printed: the pin at 57b87b2; the 7 files, committed by name in the normalizer's main as 165f8dc (the
reviewer's own uncommitted files left out); norm-builder's worktree `~/work/sefaria-citation-normalizer-builder` on the
branch `norm-builder`; the ref hook installed (it runs its Python by path, Homebrew's 3.15: a move of it fails every
ref update closed till the install is run again). Its probes as measured. Not pushed: the normalizer's repository is
public, and 165f8dc names `~/work/rav-shvat-blog` (its name already in two pushed messages) - the reviewer's word.

GIRSA-ARCHITECT'S ANSWER (the first project's 332c2fdb1, design-study/MISHMERET-PROJECT-SETUP-ARCHITECT.md, written
before any review of this plan): Q1-Q4 agreed, with additions; the terminal adapter's pkill departure agreed.
- THE GAP: THE NORMALIZER'S RUNNER IS PI. Its shell calls by runner: Claude Code's one transcript 104 (2026-08-05 to
  09-03), pi's one session 412 (11-23 to 11-25) - so the session the reviewer runs there is unguarded by a Claude Code
  hook. In this piece: a role's runner on the command line, `"runner": "pi"` in its config entry (config.py's
  OPTIONAL `roles.runner`), no agent file for it, and its start line among the printed steps - agents.sh's own,
  `cd <tree> && pi --no-extensions --name ROLE --role ROLE -e <the pin>/mishmeret/pi_guard.ts`. MEASURED THE SAME NIGHT
  (scratchpad st/pirun.py): pi 1.6.1 in a fresh copy's worktree, started so with the pin's pi_guard.ts, on the suite's
  scripted provider (no model) - the push, a commit and a write in the main clone, the tag `stage` refused; status
  and a write in its worktree let through; its bash's CLAUDE_CODE_AGENT and MISHMERET_ROLE the role; nothing left the
  copy. The line given to the reviewer and girsa-operator that night: the normalizer needs no new file for it.
- Q1, a module: and the config it is about to write passed through `config.load` first, so a config its own tree
  refuses is never written; and said when `--commit` names a commit other than the tree it runs from.
- Q2, printed: each step a command of its own (the commit's `add` and `commit` two lines).
- Q3, project_shim.py: and the KEPT line compares the bytes - "same as" or "differs from" project_shim.py. Mishmeret's
  own copy made a byte copy, with a test, at the move to the names: not this piece.
- Q4, by the Board part: one constant beside LANDING (`BOARD = "board_dir" in _CFG`), read by the role guard's five
  sentences and by ref_hook.py's through `rg`; and the words say what a role is told when no session plays the
  operator (here "the reviewer's `!` or a second session"), as ref_hook.py:98's no-role sentence does.

GIRSA-VERIFIER'S REVIEW (session 1a7205, the first project's Board #3517; its REVIEW.md in its worktree,
design-study/step5-verification/mishmeret-project-setup-plan-2026-11-27/): READY on MEDIUM 1 - the prototype wrote the
home folder (its owner's name) into the files it has committed: the worktrees and the agent files' start lines whole,
`guard.foreign` from an unquoted `~/...`, and no test that no written file holds it (the normalizer's 165f8dc holds
none). LOW 1 (two copies of the shim's helper in Mishmeret) for the move to the names. NOTE 1: settings.json written
back in json.dumps's form - the README's costs. NOTE 2: a relative --role from the shell's folder - the usage.

THE BUILD (24bee91, on main f31c0c7 - the branch rebased; the reviewer: "a mishmeret piece. plan it"): items 1-4.
- MEDIUM 1 TAKEN: every path under the home folder written `~/...` (`tilde`), `guard.foreign` too, given expanded or
  not; a test that no written file holds the home folder. NOTEs 1 and 2 in the README and the usage.
- girsa-architect's additions: the config through `config.load` before it is written (a refused one: "not written");
  a --commit other than the tree's said; each step a command (the add, the commit); the KEPT shim "differs from
  mishmeret/project_shim.py"; `BOARD` and `ask()` in role_guard.py, read by its five refusals and ref_hook.py's.
- THE PI ROLE: `ROLE=WORKTREE:pi` - its runner in the config, no agent file, its start line with the pin's pi_guard.ts.
- TESTS (tests/test_setup_project.py, 3): the setup run from a Mishmeret checkout of its own (a git tree with an
  origin: mutate.py's copy has no .git) on a placeholder main clone - what it writes, `~` throughout, the config loaded,
  settings.json merged, a second run nothing, a project's file kept and said; git's steps in order, each a command,
  the pin's only when absent, a pi role's line; a refused config not written, a DIR no main clone, a --role without its
  path; end to end through the written hook. test_guard.py: no Board, "ask" and no REQUEST - the guard's and the ref
  hook's - and with the Board, the REQUEST. 19 decisions red with each taken out (one GREEN at first: the add line
  read by its start alone - now whole). The suite 209.
- MEASURED: the build run on a fresh APFS copy of the normalizer reset to its commit before 165f8dc, `norm-builder` a
  pi role - its steps followed, each exit 0; no home path in any written file; 25 hook cases as expected; a live pi
  session started by the printed line on the suite's scripted provider - the push, a main-clone commit and write, the
  tag `stage` refused, its worktree's write let through. Run first on the copy as it was (165f8dc in it): the shims and
  settings "as it is", the config and an agent file KEPT, the existing branch's worktree without `-b`.
- FOUND: an APFS copy of a main clone holds its worktrees' records, pointing at the real worktrees - in it, `git
  worktree remove` or a forced add could reach the real one. Not run; the copy's own record removed by its path.
- RULE 45 by role, main f31c0c7 against the build (the words alone changed): 0, 0, 0 on both records, every role.

## The measure (a prototype: setup_project.py and project_shim.py - this session's scratchpad, st/)

On an APFS copy of the normalizer, its origin set to a local bare repository (no push could leave it), with a private
Mishmeret checkout holding main 57b87b2 as the pin (`MISHMERET_DIR`), as the reviewer would run it:
`setup_project.py <copy> --project sefaria-citation-normalizer --operator norm-operator --role norm-builder=<worktree>
--foreign ~/work/rav-shvat-blog --protect 'refs/tags/beta-rc*' --protect refs/tags/stage --protect refs/tags/prod`.
- The dry run wrote nothing and named 7 files; `--write` wrote them; a second `--write` wrote nothing ("as it is", 7).
  The project's own uncommitted files untouched.
- The steps it printed, followed in order: the commit (its 7 files named), the builder's worktree (`git worktree add
  <worktree> -b norm-builder`), the ref hook's install - each exit 0. (The pin's step was not printed: it was there.)
- THE HOOK AS CLAUDE CODE RUNS IT (the event on stdin, CLAUDE_PROJECT_DIR the session's tree), 25 cases, 0 not as
  expected. norm-builder in its worktree: status, a commit, an unprotected tag, an edit let through; a push, a commit
  and a `reset --hard` in the main clone, a stash, a write into rav-shvat-blog, the tags `stage` and `beta-rc*`, an
  edit in the main clone refused; its `merge --ff-only` into the main clone let through. norm-operator in the main
  clone: a commit, a push, the tag `stage`, an edit let through; a force push, a delete, rav-shvat-blog, a stash
  refused. No role, and an operator's subagent: a push and a commit refused.
- THE REF HOOK, live (git's own run): from a session that is no role of the project, `git tag stage` and `git tag
  beta-rc4` refused; `git tag v0.2.0` and a commit on the builder's branch let through. The owner's own move not run
  live - the guard refuses a command that sets the role variable; tests/test_ref_hook.py holds it.
- A SESSION STARTED AS THE ROLE: `claude -p --agent norm-builder --model haiku` in the copy's worktree, asked to push
  and to read the log: the push refused by the hook, the log read; the bare origin holds no `norm-builder` branch.
- ITS RECORD UNDER THE WRITTEN CONFIG (decide.py, the pin's guard, the record's paths moved to the copy): of 510, as
  norm-builder 83 refused, as norm-operator 10 (5 into rav-shvat-blog, 4 stashes, 1 push with a force or a delete),
  with no role 83; faults 0. The builder's 83 are its main-clone work by their first refusal (`git add` 40, `git
  commit` 20, a switch, a pull, a push...): that work moves to its worktree. On 2026-11-25, 34 of 380.
- FOUND: the push's refusal says "send it a LANDED or a REQUEST" - the Board's words, and this project has no Board;
  the live session gave them back as its advice. Six refusals name a REQUEST so - the role guard's five (the push, a
  foreign repository, a protected ref, a worktree's removal, another role's worktree) and the ref hook's.

## The change

1. `mishmeret/setup_project.py DIR --project NAME --operator ROLE --role ROLE=WORKTREE[:pi]... [--foreign PATH...]
   [--protect REF_GLOB...] [--commit SHA] [--write]`. Writes into the main clone:
   - `.mishmeret/config.json`, the six fields: `repository` (Mishmeret's, its checkout's origin), `mishmeret_commit`
     (the commit it runs from, or --commit - said when it differs), `project`, `roles` (the operator; each role with
     its worktree, `~` for the home folder, and `"runner": "pi"` for a pi role), `operator`, `guard` (`main` the main
     clone's branch; `foreign`; `refs`, each glob the operator's) - passed through `config.load` before it is written;
   - `.claude/mishmeret_shim.py` (item 2), `.claude/hooks/role_guard.py`, with --protect `.claude/hooks/ref_hook.py`;
   - the `PreToolUse` hook into `.claude/settings.json`, beside what it holds;
   - `.claude/agents/<role>.md` for each Claude Code role: its name, the project, where it starts (`cd <tree> &&
     claude --agent ROLE`); none for a pi role.
   A project's file is never replaced ("KEPT", saying whether the shim is the same as project_shim.py or differs); a
   second run writes nothing; without --write it says what it would. Refused: a DIR not a main clone's top folder; a
   --role without its worktree. Then it prints git's steps in their order, each a command of its own - the pin (when
   absent), the files' `add` and the `commit`, each role's worktree, the ref hook's install (after the pin and the
   commit: the hook fails closed), where each role starts: a pi role's line `cd <tree> && pi --no-extensions --name
   ROLE --role ROLE -e <the pin>/mishmeret/pi_guard.ts`.
2. `mishmeret/project_shim.py`: the shim's helper a project keeps - Mishmeret's own `.claude/mishmeret_shim.py`, its
   config found at `.mishmeret/config.json`, else the old home.
3. THE GUARD'S WORDS WITHOUT A BOARD: one constant beside LANDING, `BOARD = "board_dir" in _CFG`; with no Board part,
   the six refusals (the role guard's five, ref_hook.py's through `rg`) say "ask <owner> - its session, or the
   reviewer where none plays it" where they say "send <owner> a REQUEST" (and the push's "a LANDED or a REQUEST").
4. The README's "The guard alone": the one command, its steps, what it does not do.

THE COSTS AND LIMITS (for the README): each project holds its own copy of the shim's helper, and a run never replaces
it - a change to project_shim.py reaches a project by hand (the KEPT line says whether it differs); a pi role is
guarded only when started by its printed line (a bare `pi` runs no hook); the Board, the sessions, the landing not
written (a project adds a part by hand, as today); the agent file minimal (no tools, model or brief: the project's
own); git's steps printed, not run. Not measured: Linux and Windows.

Not in this piece: Mishmeret's own `.claude/` and the first project's set by it (Mishmeret's own shim a byte copy of
project_shim.py at the move to the names, girsa-architect's Q3); the normalizer's setup - done the night the plan was
written, by the prototype (the head); its config's runner for norm-builder (`"runner": "pi"`) written at its pin
bump to this piece, by its operator.

## Design questions (to girsa-architect - answered at 332c2fdb1, each agreed: the head)

1. WHERE IT LIVES: a module of `mishmeret/`, pinned and tested with the rest, run once from a checkout - not a
   shipped skill (a skill is read by a session already in a project; this makes the project). My recommendation: so.
2. GIT'S STEPS PRINTED, NOT RUN: each is a write in the project's main clone or Mishmeret's checkout (the operator's
   or the reviewer's), and the ref hook's order matters (installed before the pin, every commit is refused). My
   recommendation: print them.
3. THE SHIM'S HELPER'S SOURCE: a new `mishmeret/project_shim.py` (pinned, this lane's), not Mishmeret's own
   `.claude/mishmeret_shim.py` (the operator's, and its config's old home). My recommendation: the new file; the two
   projects' copies stay theirs.
4. THE BOARD'S WORDS: chosen by the Board part's presence (`"board_dir" in` the config) - the REQUEST is a Board
   message, so its presence is the thing itself. My recommendation: so.

## Files

- mishmeret/setup_project.py, mishmeret/project_shim.py (new); mishmeret/role_guard.py and mishmeret/ref_hook.py (the
  six refusals' words)
- tests/test_setup_project.py (new), tests/test_guard.py, tests/test_ref_hook.py
- README.md
- notes/PLAN-PROJECT-SETUP.md, notes/LOG.md, notes/STATE-mishmeret-builder.md

## Tests

- On a placeholder main clone (tmp_path, `git init`, an origin): the dry run writes nothing; --write writes the 7 (6
  without --protect), each read back - the config loaded by config.py, its six fields; settings.json gains the hook
  beside a project's own keys and hooks, and not twice; a project's own file kept and said; a second run writes
  nothing; a DIR that is a worktree, and a --role without its path, refused; the steps in order - the pin's only when
  absent, the ref hook's after the commit.
- End to end on the placeholder: the written files committed, the pin a link to this tree (MISHMERET_DIR), the hook
  run as Claude Code runs it - a builder's push and its commit in the main clone refused, its commit in its worktree
  let through; no live Board, tmux or remote reached.
- A pi role (`ROLE=WORKTREE:pi`): its config entry's runner, no agent file, its start line printed with the pin's path;
  and, where pi is on PATH, pi started by that line in the written project on the suite's scripted provider - its push
  refused, its worktree's write let through (skipped elsewhere, as tests/test_pi_role.py is).
- A config the tree's own config.py refuses is not written; a --commit other than the tree's is said.
- The six refusals: with the Board part, the REQUEST; without, "ask <owner>" - each shown red with its words taken
  out.
