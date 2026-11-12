# A subagent is not judged as the role its type names: the plan (mishmeret-builder, 2026-11-12)

Written 15:39 (`date`). This is M07's item 2, the fifth in the reviewer's order ("A" on the first project's Board
#201, 09:38). It is on branch `builder-subagent-role` from main c773f5e. Its messages are recorded here, and in the
log once `builder-lessons` is merged. The plan only, for now: one design question first. Sent, live, at 69f39dc:
the QUESTION to girsa-architect, and the HANDOFF to girsa-verifier with a harmless probe for a real subagent's input
(a subagent of the operator's type runs a dry-run delete of a branch that does not exist: the guard's refusal names
how it judged the role), whose running is the reviewer's to say.

## The case

- `role_guard.role_of` judges the hook input's `agent_type`. Claude Code's hooks reference (read today) says:
  "`agent_type` ... Present when the session uses `--agent` or the hook fires inside a subagent. For subagents, the
  subagent's type takes precedence over the session's `--agent` value". Also: "`agent_id`: unique identifier for
  the subagent or in-process teammate the hook fires in"; and a subagent's tool events "carry the `agent_id` and
  `agent_type`" fields that identify it.
- So a role that has the Agent tool can start a subagent whose type is the operator's agent file. Inside it, every
  hook says `agent_type: <the operator>`, and the guard gives it the operator's rights.
- MEASURED, the guard asked on the documented input (placeholder project, a scratch script): `{"agent_type":
  "ex-operator", "agent_id": "a1"}` is judged as the operator. `git push origin main` and `git commit -m x` in the main
  tree are LET THROUGH. A built-in type (`Explore`, with an `agent_id`) is judged as a role that does not exist, so it
  is refused what a non-operator is.
- NOT MEASURED: a real subagent's hook input. This role has no Agent tool, and no hook of mine may log the input. The
  case rests on the reference.
- The same in `land.py`, unmeasured: it takes the role from `$CLAUDE_CODE_AGENT`, and what that holds inside a
  subagent is not known.

## Answers and measures, 15:45

- girsa-verifier (its review, written before girsa-architect's answer): the case is real. A real general-purpose
  subagent of its role printed `agent=[girsa-verifier]` from its Bash, and was refused `land.py commit girsa-verifier`
  as "this session is general-purpose". Of 87 subagents in the transcripts, 43 were of a project type, none of the
  six roles' types: the hole is open, and has not been used. ITS MEDIUM 1: the hook's own `$CLAUDE_CODE_AGENT` is a
  source of the parent's role the guard can trust; it asked that the question be put again with that option.
- girsa-architect (73eb073f, before girsa-verifier's read): (c). A subagent is judged as a name no role has, one line
  in `role_of`, since the guard already refuses any non-role name a push, a commit and `land.py`. Its reason against
  the parent's role is policy: a subagent is not meant to have a role's rights (the first project's LANES.md). Its
  condition: a role's own session never carries an `agent_id`.
- MEASURED (Claude Code 2.1.322; a scratch project with its own PreToolUse logging hook; headless Haiku sessions
  allowed only the Agent tool and `true`):
  - A session started with `--agent probe-role`: its own hooks had `agent_type` probe-role, no `agent_id`, env
    probe-role. Its general-purpose subagent's hook had `agent_type` general-purpose, an `agent_id`, and env probe-role.
    So girsa-architect's condition holds, and the hook's env holds the parent's role.
  - A session started with no `--agent`, whose subagent was of type probe-role: that subagent's hook had `agent_type`
    probe-role, an `agent_id`, and env unset. So no rule may fall back to `agent_type` when an `agent_id` is present.
- Sent, live: girsa-verifier's option and both measures to girsa-architect (does (c) stand?); girsa-architect's
  answer and the measures to girsa-verifier. The build waits on girsa-architect's reply.

## Decided, 15:47, and built

- girsa-architect, revision 2 (e4d2def2): (c) stands. Its first reason against (b) is gone, since the hook's
  `$CLAUDE_CODE_AGENT` is a source it can trust; the LANES.md reason holds whatever the source. Under (b) a role's
  Haiku or Sonnet subagent could push or land as the role. (c)'s cost meets no task in the record: every subagent
  task the briefs name writes nothing. It asked that the reviewer decide, believing girsa-verifier differed. It did
  not: girsa-verifier's folded verdict already accepted (c) on the same ground, and girsa-architect corrected that
  (f50ba18d). girsa-verifier: READY TO BUILD with (c), triggered by `agent_id` first and never falling back to
  `agent_type`, with a test of the four measured inputs.
- THE REVIEWER, asked directly in this session: "No role (c)".
- BUILT: `role_of` returns "a subagent of type <X>" when the input has an `agent_id`, before any `agent_type`. The
  test (in `test_the_role_guard_keeps_push_and_main_tree_commits_to_the_operator`) covers the four measured inputs:
  a role's own session (its type is the role), a session with no role (NO_ROLE), and three subagent inputs
  (operator-typed, general-purpose, no type), each judged as no role. For each it checks a push, a commit in the
  main tree and in a worktree, and `land.py commit ex-operator`, each refused; the project-tree predicate is held
  true, as girsa-architect's probe did. Red with the line out (the operator-typed subagent judged as `ex-operator`).
  The suite: 140 passed. `land.py` is unchanged: the guard refuses a subagent every `land.py` call.
- VERIFIED at 5aa9a0a by girsa-verifier, nothing found in the code. On its clone: the suite 140 passed, the rule out
  red, and a fall-back to `agent_type` in the subagent branch red. Its sweep found `role_of` the only reader of
  `agent_type`/`agent_id` in Mishmeret and in the first project's `.claude/`, `tools/` and `pipeline/`;
  `edit_refusal` takes `role_of`'s role, so a subagent's edits are judged the same way. ITS LOW, LEFT FOR THE NEXT
  TOUCH of `role_guard.py` (words only, so the verified commit merges as checked): the module's header, "WHO: the
  hook input's `agent_type`", should say that a subagent is no role. Not run: a real subagent under the built guard,
  possible only once the first project's pin moves.

## The behaviour - QUESTION to girsa-architect

When the input has an `agent_id` (a subagent or in-process teammate), its `agent_type` is not a role. What is it
judged as?
- (a) NO_ROLE, the guard's own name for a session started without a role: refused the main tree and every push,
  like any role but the operator. One line in `role_of`. The cost: the operator's own subagents lose its rights
  too. A subagent in a worktree may also `git commit` outside `land.py`, since NO_ROLE is let commit in a worktree
  (made for one-off sessions).
- (b) the parent session's role. The input keeps the parent's `session_id`, but nothing the guard can trust maps it to
  a role: the Board's session record holds the session's NAME, which a session can rename, so it is not a safe source.
- (c) a role of its own for subagents: refused all that NO_ROLE is, and a commit anywhere outside `land.py`.

My recommendation: (c) if a worktree commit by a subagent matters to the project, else (a). Both are a few lines in
`role_of` and `refusal`. The one measure the build needs first: a role with the Agent tool logs one real subagent
hook input (its `agent_type`, `agent_id`, `session_id`) and `$CLAUDE_CODE_AGENT` in it. That is asked of the roles
that can.

## Tests (once answered)

- `role_of` on the documented input: an `agent_id` with the operator's type is not the operator; without an
  `agent_id`, the type is the role as today. The push and the main-tree commit refused in a subagent of any type.
  Each red with the rule out.

## Files

- `mishmeret/role_guard.py`, `tests/test_guard.py`, this plan; `land.py` if `$CLAUDE_CODE_AGENT` is the subagent's
  type there too.
