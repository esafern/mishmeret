---
name: guard-measure
description: Change Mishmeret's role guard and measure the change - the hole probed on placeholder paths first, its case counted on the record, each rule's test shown red with the rule taken out, and rule 45, the old guard against the new on every command any session ran - with the scripts beside this file; mishmeret-builder's procedure, read when a piece touches role_guard.py.
---

The reviewer, 2026-11-23, on mishmeret-builder's list of skills: "go ahead with the guard measure skill". The known
gaps' two pieces (notes/PLAN-KNOWN-GAPS.md, notes/PLAN-KNOWN-GAPS-SEVEN.md; the log's M14 and M15) measured the guard
this way. The first piece's scripts lived in a scratch folder that was cleared, and were written again for the
second. These are those scripts, made general, kept here.

**Why each step:** the guard decides what every role of every pinning project may run. A rule that refuses too much
stops real work; one that refuses too little is the hole it was meant to close. The tests show what the builder
thought of; the record shows what sessions actually type.

**The steps:**
1. THE HOLE, BEFORE ANY CHANGE: write each form as a case, `[role, cwd, command]`, in a JSON list. Run them on main's
   guard: `python3 probe.py <a copy of main> CASES`. `probe.py` judges on placeholder paths: the main tree
   `/work/book`, a worktree `/work/book-builder`, the guarded repository both. Each form named in the plan is let
   through or refused as written, and each sibling form is swept (SWEEP THE SIBLINGS).
2. THE CASE ON THE RECORD: `python3 -I extract.py <scratch>/cmds-<project>.jsonl <transcript folder>...`, one file per
   project (its config decides). The folders are Claude Code's `~/.claude/projects/<the project's folder>` and pi's
   `~/.pi/agent/sessions/<folder>`. Then a count of the form, written for it. The count goes in the plan's case: how
   many commands, how many of the form, and each one read when there are few (ASK WHY BEFORE DESIGNING FOR A GAP).
   None on the record is a case for the reviewer, not a reason to build.
3. THE BUILD AND ITS TESTS: each form of the plan as a refused case, each let-through form as a fine one, in
   tests/test_guard.py, on placeholder paths.
4. EACH RULE RED WITH IT TAKEN OUT: one `[name, old, new]` per rule in a JSON list, `old` the rule's own text, then
   `python3 -I mutate.py <the worktree> mishmeret/role_guard.py MUTATIONS <scratch> -- tests/test_guard.py -k "<the
   new tests>" -q -x`. Every line must read RED. A GREEN is answered before the piece goes on: either the tests cannot
   see the rule, or the rule does nothing (THE MUTATION THAT DID NOT FAIL). Add the case that pins it, or delete the
   rule.
5. RULE 45, OLD AGAINST NEW ON THE WHOLE RECORD:
   - The old side: `git -C ~/work/mishmeret archive <main> mishmeret | tar -x -C <scratch>/old`.
   - The new side: `cp -c -R mishmeret <scratch>/new/` from the worktree. Never the worktree itself, and never a copy
     of the worktree whole: the guard refuses that, since a copy's .git would share the worktree's index.
   - For each project, for a non-operator role and for the operator, one process per side:
     `python3 -I decide.py <scratch>/old/mishmeret <its config> <its cmds> <role> <scratch>/r45-old-<side>.jsonl`, and
     the same for new. They are independent: run them in the background, together.
   - `python3 -I compare.py <its cmds> <old> <new>`.
   - Read every changed decision. A newly refused command must be the plan's named cost or a refusal the plan
     intends. A newly let-through one must be a false refusal fixed. Anything else is a finding, and a fault is a
     defect.
   - The counts and each change, in placeholder words, go in the plan's head: "THE BUILD'S RUN OF RULE 45".
6. THE HANDOFF to the verifier names the scripts and the decision files, so it can reproduce the run on its own copy.

**The rules:**
- Every count is copied from the scripts' output on screen, never typed from memory (SAY WHICH ONE YOU CHECKED); a
  count of zero names what it searched (A SENTENCE OF ABSENCE IS A CLAIM).
- The transcripts are private and this repository is public. The extracts, decision files and comparisons stay in
  the session's scratch folder. Into the repository go only counts, roles, and placeholder forms of a command:
  `<main>`, `<a corpus root>`, `<URL>`.
- A check's own exit status decides the next step: each script's output goes to a file, its status is read with
  `echo "rc=$?"`, then the file is read.
- A long run works on a snapshot, never on the tree being edited (DO NOT MUTATE A TREE YOU ARE EDITING). `decide.py`
  memoizes git's answers within one run only.
- pi and other runners: `extract.py` reads pi's sessions too, and a pi role's commands are judged like any other.
