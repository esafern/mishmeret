---
name: mishmeret-sessions
description: Mishmeret's general procedure for the roles' sessions - starting them with agents.sh (and a role run by pi), the night and morning runs and the two finish commands, the keep-alive, and a test tmux server - for the operator of a project run with Mishmeret; the project's own skill, if it has one, holds its particulars.
---

Shipped with Mishmeret (`mishmeret/skills/`), linked into the project's `.claude/skills/` by `agents.sh` from the
commit the project pins. The modes and options are each script's own: read its header (`agents.sh`,
`agents-morning.sh`) - this skill lists none of them.

**Starting the roles:** `bash agents.sh` in the project's main clone, through the project's own copy (its shim names
the config and the pinned commit). Each role starts in a pane of the config's `tmux_session` - a tmux session, or with
the config's `terminal: wezterm` a workspace of the WezTerm window agents.sh is run in (outside one it stops) - from
the main clone, its agent file's effort given. A role whose last session still runs elsewhere is not started twice. A role whose
config entry names `runner: pi` starts under pi with Mishmeret's guard extension and no other (`pi_guard.ts`), fresh,
never resumed; with the extension missing it is not started, and its pane says why.

**Ending a session:** the project's two commands, never written in a script - the config's `night.finish_command`
ends with "The session is ready to clear." (the role is cleared and started again in its pane by
`finish_hook.py`), and `night.finish_exit_command` with "The session is ready to clear and exit." (nothing is started).
The night run types the second, the morning run the first.

**The keep-alive:** `keepalive_due.py` names each role whose prompt cache is about to go cold; the operator sends each
named role a keep-alive message, and the role answers with `board.py status --role <role> --still`.

**A test server:** tmux only as `env -u TMUX TMUX_TMPDIR=<its own folder> tmux ...` or `tmux -S <its own socket>
...`; WezTerm only with `WEZTERM_UNIX_SOCKET=<its own socket>` set, a private server stopped by its pid. agents.sh holds
both terminals' kills, so a test of it names both: `env -u TMUX TMUX_TMPDIR=<folder> WEZTERM_UNIX_SOCKET=<socket>
bash agents.sh`. The role guard refuses a kill that would reach the live server, the roles' session or WezTerm's live
panes, for every role.

**The rules:**
- A pane's words standing at its prompt are never typed over (`agents.sh --next` checks first).
- A session that stopped without finishing is resumed (`bash agents.sh --resume`), never started fresh over its work.
