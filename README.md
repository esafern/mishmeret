# Mishmeret

משמרת - a watch, a shift of duty. The process that runs a team of Claude Code sessions, each in a standing role, on
one project: the Board where the roles put their questions to a person and the person answers, the roles' tmux
session, the night run that lands and clears them, the session hooks and the status line, and the reports a role or
the project's gate runs - the start-up documents' sizes, what each role reads at start, each role's effort, and the
check of a draft the moment a session writes it. Extracted from Girsa, a digitization project, where it was built; it
names no project of its own.

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

`mishmeret/config.py` is its one reader. Every field is required and no other is accepted; `FIELDS` there lists them
with the module that reads each: the project's name, its roles (name, short name, tmux colour, the Board page's two
colours, whether it has a corner and a tmux pane), the page's order, the operator, the Board's folder and port, the
tmux session and settings file, Claude Code's transcripts folder, the agent files, the project's Python, the launchd
prefix, the state folder and the night run's knobs; and the reports' tables - the start-up documents' limits and where
a whole block of each goes (`sizes`), the briefs and the logs never named at start (`start_reads`), the recommended
effort per role (`effort`), and which files are drafts, their check and its two sentences (`drafts`); and the guard's
and the landing's - the list of the project's homes (its corpus roots) with a fallback, the other trees whose main
tree is the operator's (the Mishmeret checkout: nothing is written into its `.pins/`, by any role), the remotes never
pushed to, the checks whose own status must decide a commit, the pre-commit hook's path (`guard`); the role whose code
landing names its plan, the verifier a round goes back to, the project's lane check (a script run with ROLE,
`--doc-only`, `--range`, `--because`, `--plan`, read by its exit status), the live rulings file, what a review server
loads, and the gate's lists (`land`).
`MISHMERET_<FIELD>` overrides a field, `MISHMERET_NIGHT_<KEY>` one of the night run's; `MISHMERET_TRANSCRIPTS` names
the transcripts folder itself, and `MISHMERET_NIGHT_DRY_RUN=1` makes the night run say what it would type. A command
(never a hook) may run another tree with `MISHMERET_TREE`. A project's shim sets `MISHMERET_AS` to the path it runs
`board.py` by, for the commands the Board prints.

## What the project's sessions must say

The night run clears a role whose last message ends with the line `The session is ready to clear.` - the project's
own `/land` command prints it.

## Tests

    python3 -m pytest tests/

They run against a placeholder project, with stub `tmux`, `claude`, `osascript` and `launchctl` first on PATH, so no
test reaches a real tmux server or starts a session (`tests/conftest.py`).

MIT licence (`LICENSE`).
