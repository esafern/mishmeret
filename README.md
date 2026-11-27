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
  certificates - the project's list) as a calendar feed, `/expiring.ics`, with reminders 7 days and 1 day ahead. The
  server reads the project's config once, at its start: after a config change, restart it.
- **Sessions and the night run** (`agents.sh`, `agents-morning.sh`, `finish_hook.py`): start the roles in tmux or
  WezTerm, keep them warm, and clear the ones that have finished - by day each is started again in its pane, by night
  none is.
- **Reports**: tokens per role, start-up reading sizes, each role's effort setting, and a check of every draft the
  moment it is written.
- **The lessons** (`LESSONS.md`): the rules every session of a project run with Mishmeret works by, cited by name. A
  project's roles read the file at the commit the project pins, beside the project's own lessons.

I built Mishmeret to develop Girsa (girsa.net), which turns scanned 19th-century Hebrew books into corrected digital
editions: 140,000+ lines of code and tests, and 19 release candidates since July 2026, written by Claude Code sessions
(since October, these roles) and reviewed by me. Mishmeret names no project of its own; a project supplies its roles
and rules in one config file (below).

Standard library only. The sessions (`agents.sh`, `agents-morning.sh`) are macOS-only: tmux or WezTerm (below),
launchd, osascript and iTerm2. The Board, the hooks, the status line and the reports are portable.

## How a project uses it

A project keeps Mishmeret as a sibling checkout (`~/work/mishmeret`, or `MISHMERET_DIR`) and its own configuration in
`.mishmeret/config.json` - or in its old home, `.claude/mishmeret.json`, read when the new one is absent (Girsa's and
Mishmeret's own, until both pins pass the move). The config's folder's parent is the project's root, so a config kept
outside the project's tree guards another folder and leaves the project unguarded. Each file of the process in the
project is a shim: a few lines that run the same-named module
of `mishmeret/` with the same arguments, from the ONE commit the config names (`mishmeret_commit`), checked out as its
own worktree:

    git -C ~/work/mishmeret worktree add --detach ~/work/mishmeret/.pins/<sha> <sha>

The code every hook runs and the config it reads then change together, in one commit of the project. A pin is never
edited: a change is a new commit and a new pin. The shim's helper is the project's (in Girsa,
`.claude/mishmeret_shim.py`).

## The config

`mishmeret/config.py` is its one reader. Every field is required but those `OPTIONAL` there names (each absent is
taken as off), and no other is accepted. What a project may leave out whole is a part (`config.PARTS`), each all its
fields or none: the Board (its folder, port, page order and budget), the sessions (the tmux session and settings, the
transcripts, the agent files, the launchd prefix, the state folder, the night run's knobs), `sizes`, `start_reads`,
`effort`, and the landing (`land`). A module that reads a field of a part the project left out stops with that part's
sentence, naming itself. A role's drawing keys are required with the Board or the sessions.
`FIELDS` lists them with the module that reads each: the project's name, its roles (name, short name, tmux colour, the Board page's two
colours, whether it has a corner and a tmux pane), the page's order, the operator, the Board's folder and port, the
terminal (`terminal`: tmux, absent, or wezterm - below), the tmux session and settings file, each runner's transcripts
folder (`transcripts`, `{"claude": "~/.claude/projects",
"pi": "~/.pi/agent/sessions"}`; its old name `claude_projects`, Claude Code's folder alone, read as its `claude` until
both configs move), the agent files, the project's Python, the launchd
prefix, the state folder and the night run's knobs (with the project's two commands that end a session, below);
and the reports' tables - the start-up documents' limits and where
a whole block of each goes (`sizes`), the briefs and the logs never named at start (`start_reads`), the recommended
effort per role (`effort`), and which files are drafts, their check and its two sentences (`drafts`); and the guard's
and the landing's - the list of the project's homes (its corpus roots) with a fallback, the other trees whose main
tree is the operator's (the Mishmeret checkout: nothing is written into its `.pins/`, by any role), the repositories
no role changes in any tree, their main clone or any worktree (another project's), the remotes never
pushed to, the checks whose own status must decide a commit, the pre-commit hook's path, the refs only their owner
moves (`guard.refs`, `{"refs/<ref glob>": "<role>"}`), and main's branch by name (`guard.main`); each role's worktrees
(`roles[].worktrees`); the role whose code
landing names its plan, the verifier a round goes back to, the project's lane check (a script run with ROLE,
`--doc-only`, `--range`, `--because`, `--plan`, read by its exit status), the live rulings file, what a review server
loads, and the gate's lists (`land`).
`MISHMERET_<FIELD>` overrides a field, `MISHMERET_NIGHT_<KEY>` one of the night run's; `MISHMERET_TRANSCRIPTS` names
the transcripts folder itself, and `MISHMERET_NIGHT_DRY_RUN=1` makes the night run say what it would type. A command
(never a hook) may run another tree with `MISHMERET_TREE`. A project's shim sets `MISHMERET_AS` to the path it runs
`board.py` by, for the commands the Board prints. The start scripts (`agents.sh`, `agents-morning.sh`) run only with
a project named - through the project's own, whose shim sets `MISHMERET_CONFIG` and marks it as the shim's, or with
`MISHMERET_CONFIG` set by hand; with neither, they stop and say so.

The session's role, for `land.py`, `board.py`, the Stop hook, the effort report and the ref hook, is `MISHMERET_ROLE`,
else Claude Code's `CLAUDE_CODE_AGENT`; the two set and differing are no role. The guard refuses a command that sets
either. The Bash guard's own role is the hook input's alone (Claude Code's from `--agent`, pi's extension's from
`--role`): an environment is inherited by a nested `claude -p`, which is no role.

## The guard alone

A project may take the guard and nothing else (notes/PLAN-GUARD-ONLY.md). Its config holds six fields - `repository`,
`mishmeret_commit`, `project`, `roles` (each a name, and a role's `worktrees`), `operator`, `guard` (`foreign`,
`refs`, `main` as it needs) - and no part. It needs the shim and its `.claude/hooks/role_guard.py`, the `PreToolUse`
hook in `.claude/settings.json`, and an agent file for each role, so that a session starts as its role (or pi's
`--role` with `pi_guard.ts`); for its protected refs, the ref hook's install. With no landing part, `git commit` and a
landing `git merge` run as git makes them - there is no `land.py`; every other rule stands: the main clone the
operator's, pushing the operator's and never a delete, the foreign repositories no role's, the stash, the checks'
status, the live tmux server.

Measured on a copy of a one-agent project's record (380 commands, every one run in its main clone): as its builder,
beside an operator, 34 refused - 10 pushes, 18 writes in the main clone, 5 into another project it vendors a file into,
and a stash - so the builder works in its own worktree and the operator lands and pushes; as its operator, 7. A session
started with no role is refused what the builder is: 34.

ONE COMMAND WRITES IT (notes/PLAN-PROJECT-SETUP.md), run once from a Mishmeret checkout by the reviewer or the
operator, in their own terminal:

    python3 ~/work/mishmeret/mishmeret/setup_project.py <the main clone> --project NAME --operator ROLE \
        --role ROLE=WORKTREE[:pi] ... [--foreign PATH ...] [--protect REF_GLOB ...] [--commit SHA] [--write]

It writes the six-field config (checked by its own tree's config.py first), the shim's helper (`project_shim.py`'s
text), the hooks' shims, the `PreToolUse` hook beside what `.claude/settings.json` holds, and an agent file for each
Claude Code role; without `--write` it says what it would. Every path under the home folder is written `~/...`. It
never replaces a project's file - a second run writes nothing, and one that differs is kept and said - and runs no
git: it prints git's steps, each a command, in order - the pin (when absent), the files' add, their commit, each
worktree, the ref hook's install (after the pin and the commit: the hook fails closed), each role's start. A pi role
(`:pi`) has no agent file; its start line runs pi with the pin's `pi_guard.ts`. Its costs: each project keeps its own
copy of the shim's helper, which a later run does not replace; a pi role is guarded only when started by its line - a
bare `pi` runs no hook; settings.json is written back in json's own form (its spacing, and any non-ASCII as `\uXXXX`);
a relative path is taken from the folder the command runs in; the agent file names no tools, model or brief. With no
Board part, a refusal sends a role to ask its owner, never to send a Board REQUEST.

## A ref is judged by the repository

A branch or a tag belongs to the shared repository, which the main clone and every worktree read, so the guard judges a
git command that moves one by the ref it moves, wherever in that repository it runs (not in a copy, which has its own
refs). Main's branch - the one `guard.main` names, and the one checked out in the main clone - is the operator's. A ref
`guard.refs` names is its owner's alone, the operator too refused it; an object replacement (`refs/replace/`) is the
operator's. The branch checked out in a role's worktree (`roles[].worktrees`) is that
role's and the operator's, and so is the worktree: another role may not move or delete that branch, remove or move that
worktree, or run a git write in it. The forms the guard cannot read for the ref they move (`update-ref --stdin`, `rebase
--update-refs`, `filter-branch`, `fast-import`, `replay`, xargs) and the shared repository's own writes (`replace`,
`reflog delete/expire`, `gc --prune`, `prune`) are the operator's alone - and so they reach a `guard.refs` ref of
another owner too. `git maintenance register` and `git init --separate-git-dir` in a guarded tree are refused to every
role. A branch checked out nowhere (a role's branch while its worktree holds another) is no one's. A subagent is no
role, so a role's own subagent is refused a git write in its parent's worktree too.

## The ref hook

The guard reads a command's words; a script, or a form it cannot read, moves a ref it never sees. Git's own
`reference-transaction` hook sees every ref update of the repository, whatever makes it, and `ref_hook.py` judges it by
the guard's own rule: main's branch may move forward (a landing) for any role, and back, be deleted or made a link only
by the operator; a `guard.refs` ref and a replacement are their owner's alone. A role's branch stays the guard's. The
role is the session's (`MISHMERET_ROLE`, else `CLAUDE_CODE_AGENT`); with none - a session with no role, or the reviewer's own terminal - a
protected move is refused and the refusal names the owner's pane. A copy of the main clone has its own refs, and is
left alone. Main's branch is named in the config (`guard.main`) so that a detached or mid-rebase main clone does not
leave it no one's; where it is set, `land.py` refuses a landing while the main clone holds another branch, so a wrong
name is met at the next landing.

Installed by the operator, once per clone, in the main clone, through the project's shim:
`python3 .claude/hooks/ref_hook.py --install`. It writes `.git/hooks/reference-transaction`, which the worktrees share,
naming the shim, the Python and the Mishmeret checkout by path and taking PATH and HOME as they were at the install -
the command's own environment (another config, another Python, git's exec path, a field's override) does not reach it.
It replaces its own older hook and refuses another's, and refuses when `core.hooksPath` is set. The order matters: the
pin bump that brings the hook lands first, then the install; before the pin ever moves back to a commit without it,
the hook is removed - else every commit in every tree is refused, the pin's own revert too. A hook installed before the
role's two names (notes/PLAN-GUARD-ONLY.md) passes `CLAUDE_CODE_AGENT` alone and still works; the install run again at
the bump that brings them writes the text that passes both. The hook fails closed: a
missing shim, a missing pin or its own fault refuses every transaction naming a ref under `refs/`. The reviewer's way
out is their own terminal's `git -c core.hooksPath=/dev/null ...`.

What would switch it off is the guard's to refuse, in a guarded repository, to every role, the operator too:
`core.hooksPath`, `include.` and `includeIf.` set by `-c` or `--config-env` on git's line, and a `GIT_CONFIG...=`,
`HOME=` or `XDG_CONFIG_HOME=` (another config file) where it reaches git - but for a read, `clone` and `init`.

Its costs, measured (notes/PLAN-REF-HOOK.md): a forward move of main that skips `land.py` is let through (the main tree's
rule refuses its words), and leaves the main clone holding the reverse diff staged; a tag made on origin outside the
shared repository fails a non-owner's plain `git fetch` (git would make it there) - `--no-tags` fetches the rest; an
operator's subagent carries the operator's variable, so has the operator's rights here; a script that detaches the
main clone leaves main's branch the one `guard.main` names, and `land.py` refuses every landing till the main clone
holds it again; a script that runs git with
its hooks off, or a shell write into the main clone's `.git/`, is read by neither. Git spends about 0.1 s a commit on a
hook, most of it starting `/bin/sh` for each state of each transaction. Measured with git 2.56.1 on macOS; git before
2.28 runs no such hook, and Linux, Windows and the reftable format are unmeasured.

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

## The terminal: tmux or WezTerm

Every step the session scripts take in a terminal - make a pane, type into it, read it back, find a role's pane, close
the session - is a function of `term.sh`, in tmux's form and in WezTerm's (notes/PLAN-TERMINAL-ADAPTER.md); the
scripts name no terminal themselves. The config's OPTIONAL `terminal` chooses: `"tmux"` (absent) or `"wezterm"`. The
sessions part keeps tmux's names for both - `tmux_session`, `tmux_conf`, a role's `tmux` - and `tmux_conf` is read by
nothing under WezTerm; their renaming waits for the next change of a required key.

Under WezTerm a session is a workspace of the window `bash agents.sh` runs in - run outside a WezTerm window, it stops
and says so; no script starts one. A pane's role and colour are lines of `<state_dir>/panes-<session>.tsv`, begun
afresh with the session (pane ids repeat across servers) and removed when it is killed. Its costs: no label on each
pane's border (the tab's title names the session); no tiled layout (the splits as made); a line wrapped exactly at a
space stays two lines in a capture (WezTerm pads a line with spaces, so only a full one is read as wrapped); a pane
closed by hand leaves its tags in the file, read against the panes listed.

The guard keeps WezTerm's live panes as it keeps tmux's server: `wezterm cli kill-pane` is refused for every role,
the operator too, unless the command sets `WEZTERM_UNIX_SOCKET` to a socket of its own; pkill, killall or taskkill
naming wezterm is refused outright (a private server is stopped by its pid). It reads a script with the `.sh` files
it sources, a library's function where what runs names it - so a test run of `agents.sh`, whose `term.sh` holds both
kills, names a private server for each: `env -u TMUX TMUX_TMPDIR=<folder> WEZTERM_UNIX_SOCKET=<socket> bash agents.sh`.

Measured on macOS (WezTerm 20240203, a private headless server; tmux on its own): the same 22 checks on each. Not
measured: WezTerm's window (attaching, a start from inside one), Claude Code's own screen typed into by WezTerm, Linux,
and Windows - the case WezTerm is here for, where the scripts would run under Git Bash and a pane is a ConPTY (a pane's
command and a process's pane read its tty): the reviewer's own run on the Windows machine, before the case is called
done.

## Skills shipped to every project

`mishmeret/skills/` holds four Claude Code skills, Mishmeret's general procedures, pinned with the code they describe:
`mishmeret-status-report`, `mishmeret-landing`, `mishmeret-sessions` and `mishmeret-push-and-pin`. At each start
`agents.sh` links each into the project's `.claude/skills/` from the tree it runs from, so a pin bump moves them at the
next start. It replaces or removes only a link - a link to a skill the tree no longer ships is removed - and never a
file or folder of the project's own. The links hold this machine's path and are not committed: the project's
`.gitignore` lists `.claude/skills/mishmeret-*`, below any line that un-ignores the folder. A role run by pi gets them
by `--skill`, and the project's own skills one by one. A project's own skill holds its particulars and points to the
shipped one for the rest. Windows is unmeasured (its `ln -s` may copy, and an edit to a copy is lost at the next start).

## A role run by pi

A role whose config entry names `"runner": "pi"` runs under pi (the coding agent `@earendil-works/pi-coding-agent`) instead of Claude Code. pi has
no `--agent` and runs no Claude Code hook, so `agents.sh` starts it as `pi --no-extensions --name ROLE --role ROLE -e
<the pinned tree>/mishmeret/pi_guard.ts`, with the agent file's effort as `--thinking`, the agent file appended to the
system prompt, and its `initialPrompt` as the first message. The extension puts every bash, edit and write call to the
project's own `.claude/hooks/role_guard.py`, as Claude Code does, and blocks it unless the guard lets it run; `read`
runs, and any other tool is blocked. It sets `MISHMERET_ROLE` and `CLAUDE_CODE_AGENT` to the role in each bash call,
for `land.py` and `board.py`. `agents.sh` starts nothing for a pi role whose extension file is missing.

What a pi role lacks: the reports and night-run steps that read Claude Code's transcripts (the token report, the
status line, the keep-alive, the night run's context check, `agents.sh --resume`, which starts a pi role fresh); the
finish hook (a pi role is cleared and started again by hand); and SendMessage between sessions (it is reached through
the Board's `send` and `inbox`). A pin older than the commit that brought `runner` refuses a config naming it. Measured
on macOS only (pi 1.6.0); Linux and Windows are not.

## Tests

    python3 -m pytest tests/

They run against a placeholder project, with stub `tmux`, `wezterm`, `claude`, `osascript` and `launchctl` first on
PATH, so no test reaches a real tmux server or WezTerm, or starts a session (`tests/conftest.py`). The pi tests run pi itself with a scripted
provider (`tests/pi/`, no model), and are skipped where `pi` is not on PATH.

MIT licence (`LICENSE`).
