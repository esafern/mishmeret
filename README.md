# Mishmeret

משמרת - a watch, a shift of duty.

Mishmeret runs a software project with a team of Claude Code sessions, each in a standing role with its own git
worktree. It is the process around the agents, not the agents themselves: what each role may do, how its work lands,
and how one person stays in charge of every decision that is theirs.

- **The role guard** (`role_guard.py`): a Claude Code hook that refuses any command or file edit outside the session's
  role, such as a write to the main tree or a push to a protected remote.
- **Landing** (`land.py`): one procedure for every commit and merge, running the project's checks, with a round back
  to the verifier role.
- **The Board** (`board.py`, `board_server.py`): a local web page where the roles put their questions and decisions to
  the person in charge, and wait for the answer. It also serves what expires (`expiring.py`: tokens, logins,
  certificates - the project's list) as a calendar feed, `/expiring.ics`, with reminders 7 days and 1 day ahead.
- **Sessions and the night run** (`agents.sh`, `agents-morning.sh`, `finish_hook.py`): start the roles in tmux, keep
  them warm, and clear the ones that have finished - by day each is started again in its pane, by night none is.
- **Reports**: tokens per role, start-up reading sizes, each role's effort setting, and a check of every draft the
  moment it is written.
- **The lessons** (`LESSONS.md`): the rules every session of a project run with Mishmeret works by, cited by name. A
  project's roles read the file at the commit the project pins, beside the project's own lessons.

I built Mishmeret to develop Girsa (girsa.net), which turns scanned 19th-century Hebrew books into corrected digital
editions: 140,000+ lines of code and tests, and 19 release candidates since July 2026, written by Claude Code sessions
(since October, these roles) and reviewed by me. Mishmeret names no project of its own; a project supplies its roles
and rules in one config file (below).

Standard library only. The sessions (`agents.sh`, `agents-morning.sh`) are macOS-only: tmux, launchd, osascript and
iTerm2. The Board, the hooks, the status line and the reports are portable.

## How a project uses it

A project keeps Mishmeret as a sibling checkout (`~/work/mishmeret`, or `MISHMERET_DIR`) and its own configuration in
`.claude/mishmeret.json`. Each file of the process in the project is a shim: a few lines that run the same-named module
of `mishmeret/` with the same arguments, from the ONE commit the config names (`mishmeret_commit`), checked out as its
own worktree:

    git -C ~/work/mishmeret worktree add --detach ~/work/mishmeret/.pins/<sha> <sha>

The code every hook runs and the config it reads then change together, in one commit of the project. A pin is never
edited: a change is a new commit and a new pin. The shim's helper is the project's (in Girsa,
`.claude/mishmeret_shim.py`).

## The config

`mishmeret/config.py` is its one reader. Every field is required but those `OPTIONAL` there names (each absent is
taken as off), and no other is accepted; `FIELDS` lists them with the module that reads each: the project's name, its roles (name, short name, tmux colour, the Board page's two
colours, whether it has a corner and a tmux pane), the page's order, the operator, the Board's folder and port, the
tmux session and settings file, Claude Code's transcripts folder, the agent files, the project's Python, the launchd
prefix, the state folder and the night run's knobs (with the project's two commands that end a session, below);
and the reports' tables - the start-up documents' limits and where
a whole block of each goes (`sizes`), the briefs and the logs never named at start (`start_reads`), the recommended
effort per role (`effort`), and which files are drafts, their check and its two sentences (`drafts`); and the guard's
and the landing's - the list of the project's homes (its corpus roots) with a fallback, the other trees whose main
tree is the operator's (the Mishmeret checkout: nothing is written into its `.pins/`, by any role), the repositories
no role changes in any tree, their main clone or any worktree (another project's), the remotes never
pushed to, the checks whose own status must decide a commit, the pre-commit hook's path (`guard`); the role whose code
landing names its plan, the verifier a round goes back to, the project's lane check (a script run with ROLE,
`--doc-only`, `--range`, `--because`, `--plan`, read by its exit status), the live rulings file, what a review server
loads, and the gate's lists (`land`).
`MISHMERET_<FIELD>` overrides a field, `MISHMERET_NIGHT_<KEY>` one of the night run's; `MISHMERET_TRANSCRIPTS` names
the transcripts folder itself, and `MISHMERET_NIGHT_DRY_RUN=1` makes the night run say what it would type. A command
(never a hook) may run another tree with `MISHMERET_TREE`. A project's shim sets `MISHMERET_AS` to the path it runs
`board.py` by, for the commands the Board prints. The start scripts (`agents.sh`, `agents-morning.sh`) run only with
a project named - through the project's own, whose shim sets `MISHMERET_CONFIG` and marks it as the shim's, or with
`MISHMERET_CONFIG` set by hand; with neither, they stop and say so.

## What the project's sessions must say

A session finishes; a change lands. The project has two commands of its own that end a session, named in its config
and never in a script, each ending its report with a sentence on a line of its own once every step is done - and with
what is left instead, when one is not:

- `night.finish_command` (in Girsa, `/finish`) ends with `The session is ready to clear.` The session is then cleared,
  exited and started again in its pane. The morning run (`bash agents-morning.sh`) types it.
- `night.finish_exit_command` (`/finish-and-exit`) ends with `The session is ready to clear and exit.` The session is
  cleared and exited, and nothing is started. The night run types it.

By day the project's Stop hook does the rest: its `.claude/settings.json` names `finish_hook.py` on `Stop`, which
starts `agents.sh --next` for a role's pane that said either sentence. That script types nothing over words standing
in the pane's prompt, and does not start a role twice in ten minutes; what it did is in `<state_dir>/next.log`.
While a night run is going it stands down and the run closes the session itself: at night nothing is started again,
and `bash agents.sh` starts each closed role in its pane when you are back.

## Tests

    python3 -m pytest tests/

They run against a placeholder project, with stub `tmux`, `claude`, `osascript` and `launchctl` first on PATH, so no
test reaches a real tmux server or starts a session (`tests/conftest.py`).

MIT licence (`LICENSE`).
