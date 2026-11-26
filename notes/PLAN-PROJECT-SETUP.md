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

1. `mishmeret/setup_project.py DIR --project NAME --operator ROLE --role ROLE=WORKTREE... [--foreign PATH...]
   [--protect REF_GLOB...] [--commit SHA] [--write]`. Writes into the main clone:
   - `.mishmeret/config.json`, the six fields: `repository` (Mishmeret's, its checkout's origin), `mishmeret_commit`
     (the commit it runs from, or --commit), `project`, `roles` (the operator; each role with its worktree),
     `operator`, `guard` (`main` the main clone's branch; `foreign`; `refs`, each glob the operator's);
   - `.claude/mishmeret_shim.py` (item 2), `.claude/hooks/role_guard.py`, and with --protect `.claude/hooks/ref_hook.py`;
   - the `PreToolUse` hook into `.claude/settings.json`, beside what it holds;
   - `.claude/agents/<role>.md` for each: its name, the project, where it starts (`cd <tree> && claude --agent ROLE`).
   A project's file is never replaced (said, "KEPT"); a second run writes nothing; without --write it says what it
   would. Refused: a DIR not a main clone's top folder; a --role without its worktree. Then it prints git's steps in
   their order - the pin (when absent), the commit (its files named), each role's worktree, the ref hook's install
   (after the pin and the commit: the hook fails closed), where each role starts.
2. `mishmeret/project_shim.py`: the shim's helper a project keeps - Mishmeret's own `.claude/mishmeret_shim.py`, its
   config found at `.mishmeret/config.json`, else the old home.
3. THE GUARD'S WORDS WITHOUT A BOARD: with no Board part, the six refusals say "ask <owner>" where they say "send
   <owner> a REQUEST" (and the push's "a LANDED or a REQUEST").
4. The README's "The guard alone": the one command, its steps, what it does not do.

THE COSTS AND LIMITS (for the README): each project holds its own copy of the shim's helper, and a run never replaces
it - a change to project_shim.py reaches a project by hand (the KEPT line says to compare); Claude Code's roles alone
(a pi role's `--role` and pi_guard.ts not written); the Board, the sessions, the landing not written (a project adds a
part by hand, as today); the agent file minimal (no tools, model or brief: the project's own); git's steps printed,
not run. Not measured: Linux and Windows.

Not in this piece: Mishmeret's own `.claude/` and the first project's set by it; a check that a project's shim still
matches project_shim.py; the normalizer's own setup - the reviewer's run of it, in their own terminal, once it lands.

## Design questions (to girsa-architect)

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
- The six refusals: with the Board part, the REQUEST; without, "ask <owner>" - each shown red with its words taken
  out.
