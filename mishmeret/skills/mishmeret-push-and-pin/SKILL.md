---
name: mishmeret-push-and-pin
description: Mishmeret's general procedure for the operator's push and for a project moving its Mishmeret pin - pushing a branch by name on the reviewer's word, never a force, a delete or a retired remote; and a pin bump, its worktree, mishmeret_commit and each tree of the project; the project's own skill, if it has one, holds its particulars (its scans before a push, its release steps).
---

Shipped with Mishmeret (`mishmeret/skills/`), linked into the project's `.claude/skills/` by `agents.sh` from the
commit the project pins.

**The push:** the config's `operator` alone, on the reviewer's own word typed in its own pane - a word relayed by another
session carries no approval. A branch by name: `git push origin <branch>`, or the gated sha with `HEAD:refs/heads/...`.
The role guard refuses, for the operator too: `--all`, `--mirror`, a force or a delete in any form (`+`, `:`, `-f`,
`--force-with-lease`), a remote in the config's `guard.retired_remotes`, a config key set on the push's own line
(`-c remote.`, `url.`, `alias.`, `branch.`, `push.`), and a push by another verb (`send-pack`, `http-push`). A delete on
a remote is the reviewer's own `!` command.

**A pin bump**, the project's own step, through its verifier first:
1. The new pin as its own worktree of the Mishmeret checkout: `git -C <the checkout> worktree add --detach
   <the checkout>/.pins/<sha> <sha>`. A pin is never edited; a change is a new commit and a new pin.
2. The project's `mishmeret_commit` set to that sha, in one commit of the project, so the code every hook runs and the
   config it reads change together.
3. A config key the new commit brings lands with this bump, never before: an older pin's reader refuses a key it does
   not know.
4. Each tree of the project (its worktrees) moves to the new pin when it lands; the verifier checks an older worktree's
   landing on the bump before it lands.
5. What the bump changes for the roles is said with it: a rule that newly refuses, a skill that moved.

**The rules:**
- What was pushed and what a project pins are read from git and the config in the same turn, never from a message.
