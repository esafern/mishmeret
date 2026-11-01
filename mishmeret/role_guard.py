#!/usr/bin/env python3
"""The role guard: a PreToolUse hook on Bash, Edit, Write and NotebookEdit for every session in this repository
(`.claude/settings.json`) - the file tools since 2026-10-09 (FILE_TOOLS below).

The reviewer, 2026-10-01: "i want each role to have tools explicitly set so we can prevent certain activities", then
"yes go on your tool and role recomm." A role's tool list can take Bash away but cannot stop one command inside it,
so this stops what the roles plan gives to the operator alone (`.claude/agents/LANES.md`; START_HERE "Working in
parallel"):
  * `git push` - pushing is the operator's, on the reviewer's word; and the operator never pushes `--all`,
    `--mirror` or `--force`, nor to `old-origin` (the retired repository);
  * CHANGING THE MAIN TREE through git - it is the operator's alone; every other role works in its own worktree and
    lands with `git merge --ff-only`, the one change it may make there (girsa-verifier's probe, 2026-10-01: commit,
    update-ref, merge --no-ff, cherry-pick, revert and reset --hard had all passed the first version).
  * STOPPING THE LIVE TMUX SERVER - for every role, the operator too (below, TMUX_KILL).
  * LANDING AS ANOTHER ROLE through `tools/land.py`, which runs git where this hook cannot see it (below, LAND); and
    a `git commit` or a landing `git merge` in this repository run any other way (below, THROUGH_LAND).

WHAT IT READS: the command, and the text of a shell script it runs (`bash x.sh`, `sh x.sh`, `./x.sh`, its path from
a variable the same command sets) - commits here are made by script. Only git in COMMAND POSITION counts (a line's
start, or after ; & | ( ` or $(), and never what stands inside quotes or a heredoc's body: `grep "git push"` and a
commit message saying "never git push --all" are words, not commands (the builder's and the verifier's probes). It
is a guard on the ordinary forms, not a sandbox: `bash -c "..."`'s argument and git behind env, time, command, exec,
nice, sudo or xargs, or by a path, are read; git hidden in a variable, another interpreter or a deeper script is not. Anything it cannot judge runs.

WHO: the hook input's `agent_type` - the agent a session was started as (`claude --agent girsa-builder`). A session
started without one is guarded like any role other than the operator (the reviewer, 2026-10-04, "do a and b to prevent
future misuse": an external session told to work on a branch checked it out in the main clone, blocking every landing
and putting its page under the running servers) - the main clone and the corpus roots are the operator's alone; a one-off
session works in a worktree, where nothing is refused. Hooks in an agent file's own frontmatter
do not run for a session started as that agent (probed 2026-10-01, Claude Code 2.1.286: an inline --agents hook and
a settings hook ran, an agent file's did not) - hence the settings file.

usage:  python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/role_guard.py" [ROLE]   (ROLE overrides agent_type, for a probe)
Exit 2 refuses the command and says why; exit 0 lets it run. Needs only Python's standard library.
"""
import json
import os
import re
import subprocess
import sys

import config

# THE PROJECT'S OWN (its .claude/mishmeret.json, read by config.py): the operator, the roles' tmux session, the role
# whose code landing names a plan, and the `guard` table - the corpus roots' list and its fallback, the other trees
# whose main tree is the operator's, the remotes never pushed to, the checks whose status decides a commit
_CFG = config.load()
OPERATOR = _CFG["operator"]
PLANNED = _CFG["land"]["planned"]
GUARD = _CFG["guard"]
BOUNDARY = r"(?:^|[;&|(`]|\$\()\s*"
# what may stand before git and still run it (girsa-verifier's probe of 78b8088): assignments, and the prefixes env,
# time, command, exec, nice, sudo and xargs with their options; and git by a path (/usr/bin/git)
PREFIX = (r"(?:(?:[A-Za-z_]\w*=\S*|env(?:\s+-\S+)*|time|command|exec|nice(?:\s+-n\s*\S+|\s+-\d+)?"
          r"|sudo(?:\s+-[A-Za-z]+(?:\s+[\w.-]+)?)*|xargs(?:\s+-\S+(?:\s+\S+)?)*)\s+)*")
GIT = re.compile(BOUNDARY + PREFIX + r"(?:\S*/)?git"
                 r"((?:\s+-C\s+\S+|\s+-c\s+\S+)*)\s+([a-z][\w-]*)([^;&|\n]*)", re.M)
SHELL_C = re.compile(r"(?<![\w-])(?:bash|sh|zsh|dash|ksh)\s+(?:-\w+\s+)*-c\s+(\"(?:[^\"\\]|\\.)*\"|'[^']*')"
                     r"|(?<![\w-])(?:bash|sh|zsh|dash|ksh)(?:\s+-\w+)*\s*<<<\s*(\"(?:[^\"\\]|\\.)*\"|'[^']*')")
# a heredoc that a shell reads as its script (girsa-verifier, 2026-10-11): `bash <<'EOF'`, `sh -s <<EOF`, `. /dev/stdin
# <<EOF`, or `cat <<EOF | bash` - its body is commands, not words
STDIN_SHELL = re.compile(r"^\s*(?:[A-Za-z_]\w*=\S*\s+|env(?:\s+-\S+)*\s+|exec\s+|command\s+)*"
                         r"(?:(?:\S*/)?(?:bash|sh|zsh|dash|ksh)(?:\s+-\w+)*|(?:source|\.)\s+/dev/stdin)\s*$")
PIPED_TO_SHELL = re.compile(r"\|\s*(?:\S*/)?(?:bash|sh|zsh|dash|ksh)(?:\s+-\w+)*\s*(?:$|[;&|)])")


def shell_arg(m):
    """The command text of a SHELL_C match: `bash -c '...'`'s argument, or `bash <<< '...'`'s string."""
    return _unquote(m.group(1) or m.group(2))


def shell_c(command, masked):
    """The SHELL_C matches standing in command text: not in a heredoc body, a quote or a comment the mask blanked (a
    probe's own heredoc quoting `bash -c '...'` is words - 2026-10-13, the check-status guard refused the operator's
    probe of it)."""
    return [m for m in SHELL_C.finditer(command) if masked[m.start()] == command[m.start()]]
CD = re.compile(BOUNDARY + r"cd\s+(\S+)", re.M)
SCRIPT = re.compile(BOUNDARY + r"(?:(?:bash|sh|zsh)\s+(?:-\w+\s+)*)?(\S+\.sh)(?![\w.])", re.M)
ASSIGN = re.compile(r"(?<![\w$])([A-Za-z_]\w*)=(\"[^\"]*\"|'[^']*'|[^\s;&|]+)")
HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_]\w*)\1")
# what a role other than the operator may not run against the main tree, and the forms of them that change nothing
# tools/land.py (the landing script, Board #85 A step 2) runs git add, commit and merge as Python subprocesses, which
# this hook never sees, and takes the role as its second word (`land.py commit ROLE ...`, `land.py land ROLE ...`).
# The reviewer, 2026-10-26, Board #86 A (girsa-verifier's MEDIUM 1 on the script's plan): refused - a land.py commit or
# land naming a role other than the session's own; a command that sets CLAUDE_CODE_AGENT, the variable land.py reads
# for the session's role; and land.py commit in the main tree for any session but the operator's.
LAND = re.compile(r"(?<![\w./-])(?:\S*/)?land\.py(?![\w.])\s+([a-z][\w-]*)([^;&|\n]*)")
LAND_AS_ROLE = ("commit", "land")
SETS_AGENT = re.compile(r"(?<![\w$])CLAUDE_CODE_AGENT=")
# THE SCRIPT IS THE ONLY WAY IN (the reviewer, 2026-10-26: "add the extra guard"; the landing plan's section 6): in this
# repository - its main clone or a linked worktree, not a copy and not a corpus root - `git commit` is refused for every
# role, and `git merge` in the main tree (a landing) too, but `git merge --abort`: land.py commit and land.py land do
# both, with the lane check, the gate and the hold. A session with no role keeps its commits in a worktree (it cannot
# name a role to land.py).
THROUGH_LAND = {"commit": "`tools/land.py commit ROLE notes|code -F MESSAGE NAME...`",
                "merge": f"`tools/land.py land ROLE notes|code` ({PLANNED}'s code: `--plan PLAN`), from your worktree"}
# ...and the other git commands that make a commit on main, which CHANGES_MAIN already refuses every other role there:
# refused to the operator too in this repository's main tree (girsa-verifier's LOW on 23be3451; the reviewer, Board #87
# A), but each one's --abort.
OPERATOR_THROUGH_LAND = {"revert", "cherry-pick", "am", "rebase", "commit-tree", "update-ref"}
CHANGES_MAIN = {"commit", "update-ref", "cherry-pick", "revert", "rebase", "am", "reset", "stash", "checkout",
                "switch", "restore", "clean", "rm", "mv", "add", "apply", "pull", "merge"}
LEAVES_IT = {"merge": ("--ff-only",), "stash": ("list", "show"), "apply": ("--check", "--stat", "--numstat")}


def mask(text):
    """`text` with what stands inside quotes and every heredoc body turned to spaces, its length kept - so a span
    found in the mask reads the same span of the original. One pass, the quotes and the heredocs together: a heredoc
    opened outside quotes masks its body from the next line to the line that is its tag alone. Until 2026-10-11 the
    tag was looked for in the text already masked, where a quoted tag (`<<'EOF'`, the form every role writes) had
    become spaces - so such a body was read as commands (found by the tmux check's first probe). A comment - `#` at a
    word's start, outside quotes - is masked to its line's end: an apostrophe in a script's comment ("the role's")
    had opened a quote that hid or showed the lines after it, by the count of apostrophes above them; a `#` after an
    escaped character (`a\\ #b`) is not a word's start. A heredoc that a shell reads as its script (STDIN_SHELL,
    PIPED_TO_SHELL) is NOT masked: its body is commands (girsa-verifier's MEDIUM on bba1587e)."""
    out, quote, i, n, pending, escaped = list(text), None, 0, len(text), [], -1
    while i < n:
        c = text[i]
        if quote:
            if c == quote:
                quote = None
            elif c != "\n":
                out[i] = " "
        elif c == "#" and (i == 0 or (text[i - 1] in " \t\n;&|()" and i - 1 != escaped)):
            while i < n and text[i] != "\n":
                out[i] = " "
                i += 1
            continue
        elif c in "'\"":
            quote = c
        elif c == "\\" and i + 1 < n:
            out[i + 1] = " "
            escaped = i + 1
            i += 1
        elif c == "<" and text.startswith("<<", i) and not text.startswith("<<<", i):
            m = HEREDOC.match(text, i)
            if m:
                done = "".join(out[:i])
                start = max(done.rfind(ch) for ch in ";&|(\n") + 1
                eol = text.find("\n", m.end())
                if not (STDIN_SHELL.match(done[start:]) or PIPED_TO_SHELL.search(text[m.end():n if eol < 0 else eol])):
                    pending.append(m.group(2))
                i = m.end()
                continue
        elif c == "\n" and pending:         # the bodies of the heredocs opened on this line, in order
            j = i + 1
            for tag in pending:
                end = re.compile(r"^\s*%s\s*$" % re.escape(tag), re.M).search(text, j)
                stop = end.start() if end else n
                for k in range(j, stop):
                    if text[k] != "\n":
                        out[k] = " "
                j = end.end() if end else n
            pending, i = [], j
            continue
        i += 1
    return "".join(out)


def _unquote(s):
    return s[1:-1] if len(s) > 1 and s[0] == s[-1] and s[0] in "\"'" else s


def _expand(path, text):
    """`path` with ~ and the shell variables the same command sets before it (`S=...; bash $S/x.sh`), then the
    environment's."""
    for name, value in ASSIGN.findall(text):
        path = path.replace("${%s}" % name, _unquote(value)).replace("$" + name, _unquote(value))
    return os.path.expanduser(os.path.expandvars(path))


# The trees only the operator changes through git: THIS repository's main clone - the project's root, from its config
# (config.root()) - and each book's corpus root, read from the one list of homes (Girsa's pipeline/book_homes.json)
# (a new book's root is one line there; the reviewer's go, 2026-10-23, on girsa-builder's REQUEST). Not a linked
# worktree of either, and not a copy (`cp -c -R`, every rehearsal), which carries its own .git. The reviewer,
# 2026-10-02: "guard - (a)" - girsa-verifier's finding: the first version took any tree whose git dir is its common dir
# for the main tree, which is every repository that is not a linked worktree, so a role could not reset its own
# rehearsal copy with git.
HOOK_REPO = config.root()
# When the list cannot be read, the root it held before it was the source - the guard never opens wider for a
# broken file.
FALLBACK_CORPUS_ROOTS = tuple(GUARD["fallback_roots"])
# THE OTHER TREES WHOSE MAIN TREE IS THE OPERATOR'S (design-study/STEP-MISHMERET-MOVE-PLAN.md in Girsa, step 4): the
# Mishmeret checkout - its worktrees anyone's, its pins (`<tree>/.pins/<sha>`) no one's (`pin_of`)
TREES = tuple(GUARD["trees"])


def corpus_roots(path=None):
    """Every home's root in the project's list of homes (`guard.homes`, Girsa's pipeline/book_homes.json; this
    repository's own among them, which HOOK_REPO also names).
    FALLBACK_CORPUS_ROOTS is added beside the well-formed roots when any home has no root, and is all there is when
    the file is missing, unreadable or not the list's shape - a broken entry never drops a good one (girsa-verifier's
    LOW on 71175b1d)."""
    try:
        with open(path or config.expand(GUARD["homes"]), encoding="utf-8") as fh:
            homes = json.load(fh)["homes"]
        roots = tuple(h["root"] for h in homes if isinstance(h, dict) and isinstance(h.get("root"), str) and h["root"])
        whole = len(roots) == len(homes)
    except (OSError, ValueError, KeyError, TypeError):
        return FALLBACK_CORPUS_ROOTS
    return roots if roots and whole else roots + tuple(r for r in FALLBACK_CORPUS_ROOTS if r not in roots)


CORPUS_ROOTS = corpus_roots()


def _git_dirs(path):
    """(git dir, common dir) of the repository `path` is in, both resolved; None when it is not in one."""
    try:
        out = subprocess.run(["git", "-C", path, "rev-parse", "--path-format=absolute", "--git-dir",
                              "--git-common-dir"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    lines = out.stdout.splitlines()
    if out.returncode != 0 or len(lines) != 2:
        return None
    return tuple(os.path.realpath(line) for line in lines)


def guarded_git_dirs():
    """The git dirs of the trees in the comment above: this repository's, and each corpus root's and TREES' that
    exists."""
    found = (_git_dirs(root) for root in (HOOK_REPO,) + tuple(os.path.expanduser(r) for r in CORPUS_ROOTS + TREES))
    return {dirs[1] for dirs in found if dirs}


def pin_of(path):
    """The pin `path` is in - `<tree>/.pins/<sha>` of one of TREES - or None. By path alone, no git (the shim finds a
    pin the same way): a pin is the code every hook runs, so nothing is written into one, by any role."""
    real = os.path.realpath(os.path.expanduser(path))
    for tree in TREES:
        pins = os.path.join(os.path.realpath(os.path.expanduser(tree)), ".pins") + os.sep
        if real.startswith(pins) and real[len(pins):]:
            return pins + real[len(pins):].split(os.sep)[0]
    return None


def pin_refusal(pin):
    return (f"refused by the role guard: {pin} is a pinned Mishmeret tree - every hook runs its code, so no role, the "
            "operator too, changes it: a change is a new Mishmeret commit, its own pin made from it, and the "
            "project's `mishmeret_commit` set to that sha")


def is_main_tree(path, guarded=None):
    """True when `path` is inside a guarded tree's own working tree (not a linked worktree of it, not a copy), False
    in any other repository, None when not in one. `guarded`: the git dirs to guard (default `guarded_git_dirs()`)."""
    dirs = _git_dirs(path)
    if dirs is None:
        return None
    git_dir, common = dirs
    return git_dir == common and common in (guarded_git_dirs() if guarded is None else guarded)


def is_project_tree(path):
    """True when `path` is in THIS repository - its main clone or a linked worktree of it - and not in a copy (its own
    .git) or a corpus root, where git commits are made by hand."""
    dirs, own = _git_dirs(path), _git_dirs(HOOK_REPO)
    return bool(dirs and own and dirs[1] == own[1])


def _read(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return None


def _dir_before(text, masked, at, base):
    """The directory the last `cd` before position `at` went to, or `base`."""
    cds = list(CD.finditer(masked[:at]))
    if not cds:
        return base
    a, b = cds[-1].span(1)
    return os.path.join(base, _expand(_unquote(text[a:b]), text[:at]))


def _git_where(command, masked, m, cwd):
    """The directory a GIT match runs in: its `-C`, else the last `cd` before it, else `cwd`."""
    opts = command[m.span(1)[0]:m.span(1)[1]]
    c = re.search(r"-C\s+(\S+)", opts)
    return (os.path.join(cwd, _expand(_unquote(c.group(1)), command[:m.start()])) if c
            else _dir_before(command, masked, m.start(), cwd))


def refusal(role, command, cwd, main_tree=is_main_tree, read=_read, depth=0, project_tree=is_project_tree):
    """None to let `command` run as `role` from `cwd`, or the reason to refuse it."""
    masked = mask(command)
    if depth == 0:                          # one level into a script the command runs
        for m in SCRIPT.finditer(masked):
            a, b = m.span(1)
            path = _expand(_unquote(command[a:b]), command[:a])
            here = _dir_before(command, masked, a, cwd)
            body = _moved(read(os.path.join(here, path)), read)
            if body:
                why = refusal(role, body, here, main_tree, read, depth + 1, project_tree)
                if why:
                    return f"{why} (in the script {path})"
    for m in shell_c(command, masked):          # `bash -c "..."`: the quoted argument is a command, read as one
        why = refusal(role, shell_arg(m), _dir_before(command, masked, m.start(), cwd), main_tree, read,
                      depth, project_tree)
        if why:
            return why
    no_role = (f" (this session was started without a role: for the main clone start it as {OPERATOR}; a one-off "
               "session works in a worktree, where nothing is refused)") if role == NO_ROLE else ""
    for m in GIT.finditer(masked):
        verb, rest = m.group(2), m.group(3).split()
        if verb in CHANGES_MAIN and not ((verb == "stash" and rest[:1] and rest[0] in LEAVES_IT["stash"])
                                         or (verb == "apply" and any(w in rest for w in LEAVES_IT["apply"]))):
            pin = pin_of(_git_where(command, masked, m, cwd))       # a pin: refused to every role, merge --ff-only too
            if pin:
                return pin_refusal(pin)
        if verb in THROUGH_LAND and "--abort" not in rest:
            where = _git_where(command, masked, m, cwd)
            in_main = main_tree(where)
            if (verb == "commit" or in_main) and not (role == NO_ROLE and not in_main) and project_tree(where):
                return (f"refused by the role guard: `git {verb}` in this repository goes through {THROUGH_LAND[verb]} "
                        "(skill `landing`; the reviewer, 2026-10-26)" + no_role)
        if role == OPERATOR and verb in OPERATOR_THROUGH_LAND and "--abort" not in rest:
            where = _git_where(command, masked, m, cwd)
            if main_tree(where) and project_tree(where):
                return (f"refused by the role guard: `git {verb}` in the main tree makes a commit no gate saw - make the "
                        "change in a worktree and land it with `tools/land.py land`, or commit its result with "
                        "`tools/land.py commit` (Board #87 A)")
        if verb == "push":
            if role != OPERATOR:
                return (f"refused by the role guard: pushing is the operator's ({OPERATOR}), on the reviewer's "
                        "word - send it a LANDED or a REQUEST instead" + no_role)
            retired = GUARD["retired_remotes"]
            bad = [w for w in rest if w in ("--all", "--mirror", "-f", *retired) or w.startswith("--force")]
            if bad:
                return ("refused by the role guard: the operator never pushes --all, --mirror or --force"
                        + (f", nor to {' or '.join(retired)}" if retired else "")
                        + f" (found {' '.join(bad)}) - push the branch to origin by name")
        elif (verb == "stash" and not (rest[:1] and rest[0] in LEAVES_IT["stash"])
              and project_tree(_git_where(command, masked, m, cwd))):
            return ("refused by the role guard: `git stash` in this repository - its stash list is shared by the main "
                    "clone and every worktree, so a pop can take another role's work (LANES.md; 2026-10-20: one role "
                    "popped another's) - set the work aside as a patch: `git diff > <file>.patch`" + no_role)
        elif verb in CHANGES_MAIN and role != OPERATOR:
            leaves = LEAVES_IT.get(verb, ())
            if (rest[:1] and rest[0] in leaves) if verb == "stash" else any(w in rest for w in leaves):
                continue
            if main_tree(_git_where(command, masked, m, cwd)):
                return (f"refused by the role guard: `git {verb}` would change the main tree or a book's corpus "
                        "root, which are the operator's alone - work in your worktree or a copy and land with `git "
                        "merge --ff-only`, or send the operator a HANDOFF" + no_role)
    if SETS_AGENT.search(masked):
        return ("refused by the role guard: a command may not set CLAUDE_CODE_AGENT - Claude Code sets it to the "
                "session's role, and tools/land.py lands as that role (Board #86 A)" + no_role)
    for m in LAND.finditer(masked):
        verb = m.group(1)
        if verb not in LAND_AS_ROLE:
            continue
        words = command[m.start(2):m.end(2)].split()
        named = _expand(_unquote(words[0]), command[:m.start()]) if words else ""
        if named != role:
            return (f"refused by the role guard: `land.py {verb}` names the role {named or '(none)'}, and this session "
                    f"is {role} - a role commits and lands only as itself (Board #86 A)" + no_role)
        if verb == "commit" and role != OPERATOR and main_tree(_dir_before(command, masked, m.start(), cwd)):
            return ("refused by the role guard: `land.py commit` in the main tree is the operator's alone - commit in "
                    "your worktree and land with `land.py land` (Board #86 A)" + no_role)
    return None


NO_ROLE = "a session with no role"

# A REHEARSAL COPY IS OF THE MAIN CLONE, NEVER OF A WORKTREE (LANES.md; 2026-10-02: a worktree's .git is a file pointing
# into the main repository, so a copy of it shares that worktree's index and HEAD - girsa-verifier's `git checkout <rev>
# -- tests/` in such a copy staged into its worktree; the reviewer's sweep for missing gates, 2026-10-27). Refused for
# every role: a recursive `cp` whose source is a linked worktree's top folder (a `.git` that is a file).
CP = re.compile(BOUNDARY + PREFIX + r"(?:\S*/)?cp(?=\s)([^;&|\n]*)", re.M)


def _home_as_tilde(path):
    home = os.path.expanduser("~")
    return "~" + path[len(home):] if path == home or path.startswith(home + os.sep) else path


def copy_refusal(command, cwd, is_worktree=lambda p: os.path.isfile(os.path.join(p, ".git"))):
    """None, or the reason to refuse a recursive copy of a linked worktree."""
    masked = mask(command)
    for m in CP.finditer(masked):
        words = command[m.start(1):m.end(1)].split()
        opts = [w for w in words if w.startswith("-")]
        paths = [w for w in words if not w.startswith("-")]
        if not any(o == "--recursive" or (not o.startswith("--") and set(o[1:]) & {"R", "r"}) for o in opts):
            continue
        here = _dir_before(command, masked, m.start(), cwd)
        for src in paths[:-1]:
            path = os.path.join(here, _expand(_unquote(src), command[:m.start(1)]))    # an assignment may lead it
            if is_worktree(path.rstrip("/") or "/"):
                return (f"refused by the role guard: `cp` of {src}, a linked worktree - its .git is a file pointing "
                        "into the main repository, so git in the copy changes that worktree (LANES.md, 2026-10-02); "
                        f"a rehearsal copies the main clone: `cp -c -R {_home_as_tilde(HOOK_REPO)} <copy>`")
    return None

# THE LIVE TMUX SERVER IS NO ROLE'S TO STOP (the reviewer, 2026-10-11, the Board #14: "A - Add the guard"). Every role
# runs in a pane of the "girsa" tmux server, so $TMUX is set in its shell, and tmux follows $TMUX ahead of TMUX_TMPDIR:
# on 2026-10-11 at 17:51 the operator's test of agents.sh ran `TMUX_TMPDIR=<its folder> tmux kill-server`, meant for a
# throwaway server, and stopped the live one with all five roles in it, none landed. Refused for every role: tmux
# kill-server, and kill-session or kill-window on the "girsa" session (or with no target, which is the pane's own
# session; or a target this guard cannot read, as "$SESSION") - unless the command reaches a server of its own: a socket
# named with -S or -L (not -L default), or $TMUX cleared (`env -u TMUX`, `TMUX=`, an earlier `unset TMUX`) AND
# TMUX_TMPDIR set for it (as a prefix, or an earlier `export`). One level into a script the command runs, which inherits
# that command's environment (`env -u TMUX TMUX_TMPDIR=<folder> bash agents.sh` may test agents.sh --restart).
# The forms tmux itself takes count (girsa-verifier's LOW on bba1587e): the aliases killw and killp, a unique prefix
# (kill-serv, kill-sess), kill-pane (one role's pane); a target is read as another session only when it names one outright
# (not %N, @N, $N or ":1", which point into the server the command reaches). `pkill` / `killall` naming tmux is refused
# outright. Not covered: tmux behind a variable or another interpreter, or `kill <pid>` of the server.
TMUX_PREFIX = (r"(?:(?:[A-Za-z_]\w*=\S*|env(?:\s+-u\s*\w+|\s+-\S+)*|time|command|exec|nice(?:\s+-n\s*\S+|\s+-\d+)?"
               r"|sudo(?:\s+-[A-Za-z]+(?:\s+[\w.-]+)?)*|xargs(?:\s+-\S+(?:\s+\S+)?)*)\s+)*")
TMUX_KILL = re.compile(BOUNDARY + "(" + TMUX_PREFIX + r")(?:\S*/)?tmux((?:\s+-(?:[2CDlNuvV]+|[cfLST]\s*\S+))*)\s+"
                       r"(kill[\w-]*)(?![\w-])([^;&|\n]*)", re.M)
KILL_VERBS = ("kill-server", "kill-session", "kill-window", "kill-pane")
KILL_ALIASES = {"killw": "kill-window", "killp": "kill-pane"}
PKILL = re.compile(BOUNDARY + TMUX_PREFIX + r"(?:\S*/)?(?:pkill|killall)(?![\w-])([^;&|\n]*)", re.M)


def _kill_verb(word):
    """The tmux kill command `word` names (an alias, or a unique prefix - an ambiguous one read as kill-server), or
    None."""
    if word in KILL_ALIASES:
        return KILL_ALIASES[word]
    hits = [v for v in KILL_VERBS if v.startswith(word)] if word.startswith("kill-") and len(word) > 5 else []
    return hits[0] if len(hits) == 1 else ("kill-server" if hits else None)
TMUX_SCRIPT = re.compile(BOUNDARY + "(" + TMUX_PREFIX + r")(?:(?:bash|sh|zsh)((?:\s+-\w+)*)\s+)?(\S+\.sh)(?![\w.])", re.M)
ROLES_SESSION = _CFG["tmux_session"]


def _own_tmux_env(prefix, before):
    """True when a command with this `prefix` (its assignments and env), after the text `before` it, runs tmux with
    $TMUX cleared AND TMUX_TMPDIR set - so it reaches a server in that folder, never the roles' one."""
    cleared = (re.search(r"(?<![\w-])env\s+(?:-\S+\s+)*-u\s*TMUX(?!\w)", prefix)
               or re.search(r"(?<![\w$])TMUX=(?:\s|$|\"\"|'')", prefix)
               or re.search(r"(?<![\w-])unset\s+(?:-v\s+)?TMUX(?!\w)", before))
    tmpdir = (re.search(r"(?<![\w$])TMUX_TMPDIR=\S", prefix)
              or re.search(r"(?<![\w-])export\s+TMUX_TMPDIR=\S", before))
    return bool(cleared and tmpdir)


# the project's shell shim, by its form (`HELPER.py --sh NAME`), not by the helper's name - a project's own file
SHELL_SHIM = re.compile(r'\.py"?\s+--sh\s+([\w.-]+\.sh)\b')
HERE = os.path.dirname(os.path.abspath(__file__))


def _moved(body, read):
    """A SCRIPT MOVED TO MISHMERET IS READ WHERE IT RUNS (design-study/STEP-MISHMERET-MOVE-PLAN.md in Girsa, step 2): a
    project's shell shim (`.claude/mishmeret_shim.py --sh NAME`) runs Mishmeret's NAME from the pinned tree - the tree
    this guard runs from - so the guard reads that; read as the shim, `agents.sh --restart`'s kill-session would be
    hidden. A script not found here leaves the shim itself."""
    m = SHELL_SHIM.search(body or "")
    if not m:
        return body
    return read(os.path.join(HERE, m.group(1))) or body


def tmux_refusal(command, cwd, read=_read, own_env=False, depth=0):
    """None to let `command` run, or the reason to refuse it: it would stop the live tmux server or the roles' session
    (the comment above). `own_env`: the command runs in an environment already set to a server of its own."""
    masked = mask(command)
    for m in TMUX_KILL.finditer(masked):
        prefix, opts = command[m.start(1):m.end(1)], command[m.start(2):m.end(2)]
        before, verb, rest = masked[:m.start()], _kill_verb(m.group(3)), command[m.start(4):m.end(4)]
        if not verb:
            continue
        sock = re.search(r"-([LS])\s*(\S+)", opts)
        if sock and not (sock.group(1) == "L" and _unquote(sock.group(2)) == "default"):
            continue
        if own_env or _own_tmux_env(prefix, before):
            continue
        if verb != "kill-server":
            target = re.search(r"-t\s*(\S+)", rest)
            session = (_unquote(target.group(1)) if target else "").lstrip("=").split(":")[0]
            if re.fullmatch(r"[A-Za-z][\w.-]*", session) and session != ROLES_SESSION:
                continue                    # another session on the live server, named outright: not the roles'
        return (f"refused by the role guard: `tmux {verb}` here would reach the LIVE tmux server - the one every "
                f"role's session runs in (2026-10-11 17:51: a test's kill-server stopped every role, none landed). "
                "A test server is reached only as `env -u TMUX TMUX_TMPDIR=<its own folder> tmux ...` or `tmux -S "
                f"<its own socket> ...`; the live server and the {ROLES_SESSION} session are the reviewer's to stop")
    for m in PKILL.finditer(masked):
        if re.search(r"(?<![\w-])tmux(?![\w-])", command[m.start(1):m.end(1)]):
            return ("refused by the role guard: pkill / killall of tmux would stop the LIVE tmux server with every "
                    "role's session in it - stop a test server by its own socket (`tmux -S <socket> kill-server`)")
    if depth == 0:                          # one level into a script the command runs, with that command's environment
        for m in TMUX_SCRIPT.finditer(masked):
            if re.search(r"-\w*n", m.group(2) or ""):  # `bash -n x.sh` reads it for its syntax, runs nothing
                continue
            a, b = m.span(3)
            path = _expand(_unquote(command[a:b]), command[:a])
            here = _dir_before(command, masked, a, cwd)
            body = _moved(read(os.path.join(here, path)), read)
            if body:
                why = tmux_refusal(body, here, read,
                                   own_env or _own_tmux_env(command[m.start(1):m.end(1)], masked[:m.start()]), 1)
                if why:
                    return f"{why} (in the script {path})"
    for m in shell_c(command, masked):
        why = tmux_refusal(shell_arg(m), _dir_before(command, masked, m.start(), cwd), read, own_env, depth)
        if why:
            return why
    return None

# THE FILE TOOLS TOO (the reviewer, 2026-10-09: "A" - girsa-verifier's finding: this hook ran on Bash only, so a role's
# Edit, Write and NotebookEdit changed the main tree's files unguarded; at 14:13 its Edit reached the main clone's copy of
# its own brief, which it reverted within a minute). The same trees are guarded - this repository's main clone and the
# named corpus roots, never a linked worktree or a copy - and only the operator writes there; a file that does not exist
# yet is judged by the nearest folder that does.
FILE_TOOLS = {"Edit": "file_path", "Write": "file_path", "NotebookEdit": "notebook_path"}


# A CHECK'S OWN EXIT STATUS DECIDES THE STEP AFTER IT (the reviewer, 2026-10-13: "this issue keeps biting us"). START_HERE
# has said "A check's own exit status decides a commit, never a pipe's" since 2026-10-06, and it was broken by the
# operator (e57d558, 2026-10-05: `echo "exit $?"`; 621d4699, 2026-10-12: `check_lane.py --doc-only | tail -1` committed
# over a FAIL) and by another role on 2026-10-13 (a FAIL piped through tail went on to `git merge`; git refused only
# because main had moved). Refused for every role, the operator too: a command in which a check (CHECKS) is followed
# by a commit, merge, push or tag (GATED_STEPS) that its failure cannot stop - the check piped into another command
# without `set -o pipefail` (the pipe's status is the last command's), followed by `;` or a newline without `set -e`
# before it, `check && echo ...;` (a failure in an && list does not stop even under set -e), or `check || true`. Read in
# the command and one level into a script it runs. Its status counts when the command uses it: `if ! check; then`,
# `check || { ...; exit 1; }`, `check && git commit`, or `set -e` before a check alone on its line.
CHECKS = tuple(GUARD["checks"])
GATED_STEPS = {"commit", "merge", "push", "tag", "update-ref", "cherry-pick", "am"}
STEP_SPLIT = re.compile(r"(\|\||&&|\|&?|;|(?<![<>&])&(?![>&])|\n)")
LEAD_WORDS = {"if", "!", "then", "else", "elif", "do", "while", "until", "{", "(", "time", "command", "exec"}


def _words(stmt):
    """The statement's words with what stands before its program taken off: keywords, assignments, env and its
    options, `timeout N`; and the keywords so taken, as a set."""
    words, lead = stmt.replace("(", " ( ").replace("{", " { ").split(), set()
    while words:
        w = words[0]
        if w in LEAD_WORDS or w == "env":
            lead.add(w)
            words = words[1:]
        elif "env" in lead and w in ("-u", "--unset"):
            words = words[2:]
        elif re.match(r"[A-Za-z_]\w*=", w) or ("env" in lead and w.startswith("-")):
            words = words[1:]
        elif w == "timeout" and len(words) > 1:
            words = words[2:]
        else:
            break
    return words, lead


def _check_in(stmt):
    """The check a statement runs (one of CHECKS), or None."""
    words, _ = _words(stmt)
    if not words:
        return None
    prog = os.path.basename(words[0])
    if prog in CHECKS:
        return prog
    # a python by a variable (`$PY -m pytest`, `"$PY" ...`) is read as a python (girsa-verifier's LOW on 8ac9341b)
    # (quoted, `"$PY"` reaches here masked as `"   "`: its two quote marks are words of their own)
    if re.match(r"python(\d[\d.]*)?$", prog) or words[0][:1] in "\"'" or words[0].startswith("$"):
        rest = [w for w in words[1:] if w not in ("-I", "-u", "-B", "-q", '"', "'")]
        if rest[:2] == ["-m", "pytest"]:
            return "pytest"
        if rest and os.path.basename(rest[0]) in CHECKS:
            return os.path.basename(rest[0])
    return None


def _gated_step_in(stmt):
    """`git <verb>` when the statement is one of GATED_STEPS, else None."""
    words, _ = _words(stmt)
    if not words or os.path.basename(words[0]) != "git":
        return None
    i = 1
    while i < len(words) and words[i] in ("-C", "-c"):
        i += 2
    return f"git {words[i]}" if i < len(words) and words[i] in GATED_STEPS else None


def _pipelines(command, masked):
    """(pipes, raws): the command's pipelines - each its statements (as masked) joined by `|`, with the operator after
    its last one - and each pipeline's first statement as written."""
    stmts, at = [], 0                       # (the statement as masked, the operator after it, its own text)
    for m in STEP_SPLIT.finditer(masked):
        stmts.append((masked[at:m.start()].strip(), m.group(1), command[at:m.start()]))
        at = m.end()
    stmts.append((masked[at:].strip(), "\n", command[at:]))
    stmts = [x for x in stmts if x[0] or x[1] in ("|", "|&")]
    pipes, raws, cur = [], [], []
    for s, op, raw in stmts:
        if not cur:
            raws.append(raw)
        cur.append(s)
        if op not in ("|", "|&"):
            pipes.append((cur, op.strip() or ";"))
            cur = []
    if cur:
        pipes.append((cur, ";"))
    return pipes, raws


def check_status_refusal(command, cwd, read=_read, depth=0):
    """None to let `command` run, or the reason to refuse it: a check in it whose failure cannot stop a commit, merge,
    push or tag after it (the comment above)."""
    masked = mask(command)
    if depth == 0:
        for m in SCRIPT.finditer(masked):
            a, b = m.span(1)
            path = _expand(_unquote(command[a:b]), command[:a])
            here = _dir_before(command, masked, a, cwd)
            body = _moved(read(os.path.join(here, path)), read)
            if body:
                why = check_status_refusal(body, here, read, depth + 1)
                if why:
                    return f"{why} (in the script {path})"
    for m in shell_c(command, masked):
        why = check_status_refusal(shell_arg(m), _dir_before(command, masked, m.start(), cwd), read, depth)
        if why:
            return why
    pipes, raws = _pipelines(command, masked)
    errexit = pipefail = False
    for i, (pipe, op) in enumerate(pipes):
        first_words, lead = _words(pipe[0])
        if first_words[:1] == ["set"]:
            flags = " ".join(first_words[1:])
            if re.search(r"(?:^|\s)\+[a-z]*e|\+o\s+errexit", flags):
                errexit = False
            elif re.search(r"(?:^|\s)-[a-z]*e|-o\s+errexit", flags):
                errexit = True
            pipefail = pipefail or "pipefail" in flags
        found = [(n, c) for n, c in enumerate(_check_in(s) for s in pipe) if c]
        if not found:
            continue
        n, check = found[0]
        later = next((st for p, _ in pipes[i + 1:] for st in (_gated_step_in(x) for x in p) if st), None)
        if not later:
            continue
        # its status read at once in the next statement - `rc=$?`, `[ "${PIPESTATUS[0]}" = 0 ] || ...` - is used
        # (`$?` only where the check is not hidden in a pipe: after `check | tail` it is tail's)
        hidden = n < len(pipe) - 1 and not pipefail
        nxt_raw = raws[i + 1] if i + 1 < len(raws) else ""
        if op in (";", "\n", "&") and ("PIPESTATUS" in nxt_raw or ("$?" in nxt_raw and not hidden)):
            continue
        if hidden:
            how = f"it is piped into `{(_words(pipe[-1])[0] or ['?'])[0]}`, so the pipe's status is that command's"
        else:
            how = None
            if lead & {"if", "!", "while", "until"}:
                continue
            if op == "||":
                nxt = pipes[i + 1][0][0] if i + 1 < len(pipes) else ""
                nw, nlead = _words(nxt)
                if not nlead & {"{", "("} and nw[:1] and nw[0] in ("true", ":", "echo", "printf"):
                    how = f"`|| {nw[0]}` lets its failure through"
                else:
                    continue
            elif op == "&&":
                chain, j = [], i
                while j < len(pipes) and pipes[j][1] == "&&":
                    chain.extend(pipes[j + 1][0] if j + 1 < len(pipes) else [])
                    j += 1
                if any(_gated_step_in(x) for x in chain):
                    continue
                how = "a failure in an `&&` list does not stop the command, even under `set -e`"
            elif errexit:
                continue
            else:
                how = "it is followed by `;` or a new line with no `set -e` before it"
        return (f"refused by the role guard: `{check}` cannot stop `{later}` later in this command - {how}. A check's "
                "own exit status decides the step after it (START_HERE; the reviewer, 2026-10-13: \"this issue keeps "
                "biting us\"): put `set -e` first and the check alone on its line, or `if ! <check>; then ...; exit 1; "
                "fi`; send its output to a file and read the file, never through a pipe")
    return None


# A CHECK PIPED INTO ANOTHER COMMAND READS AS A PASS (Board #66 A, 2026-10-20; the reviewer: "i keep seeing agents
# messing up by picking up tail's exit status. how do we fix that properly for all?"). check_status_refusal stops such a
# pipe only before a commit, merge, push or tag; a session that READ the status went on to report a failure as a pass
# (the operator, that morning: `bash commit_step12.sh | tail -6` showed exit 0 over a red gate). Refused for every role:
# a check (CHECKS) or a shell script (`bash x.sh`, `./x.sh`) anywhere but last in a pipeline, unless `set -o pipefail`
# came first or the next statement reads `${PIPESTATUS[...]}`. Read in the command, `bash -c`, and one level into a
# script it runs. Any other pipe (`git log | head`) is untouched.
def _script_in(stmt):
    """The shell script a statement runs (`bash x.sh`, `sh -e x.sh`, `./x.sh`), or None."""
    words, _ = _words(stmt)
    if not words:
        return None
    if os.path.basename(words[0]) in ("bash", "sh", "zsh"):
        return next((w for w in words[1:] if w.endswith(".sh")), None)
    return words[0] if words[0].endswith(".sh") else None


def piped_check_refusal(command, cwd, read=_read, depth=0):
    """None to let `command` run, or the reason to refuse it: a check or a script whose status a pipe hides."""
    masked = mask(command)
    if depth == 0:
        for m in SCRIPT.finditer(masked):
            a, b = m.span(1)
            path = _expand(_unquote(command[a:b]), command[:a])
            here = _dir_before(command, masked, a, cwd)
            body = _moved(read(os.path.join(here, path)), read)
            if body:
                why = piped_check_refusal(body, here, read, depth + 1)
                if why:
                    return f"{why} (in the script {path})"
    runs = lambda text: next((c for p, _ in _pipelines(text, mask(text))[0] for c in map(_check_in, p) if c), None)
    for m in shell_c(command, masked):
        why = piped_check_refusal(shell_arg(m), _dir_before(command, masked, m.start(), cwd), read, depth)
        if why:
            return why
        # `bash -c "<check>" | tail`: the argument runs the check, and the pipe hides the shell's status
        after = masked[m.end():].lstrip()
        if after.startswith("|") and not after.startswith("||") and runs(shell_arg(m)):
            return _piped_why(f"bash -c running {runs(shell_arg(m))}", (after[1:].lstrip("&").split() or ["?"])[0])
    pipes, raws = _pipelines(command, masked)
    pipefail = False
    for i, (pipe, op) in enumerate(pipes):
        first_words, _ = _words(pipe[0])
        if first_words[:1] == ["set"] and "pipefail" in " ".join(first_words[1:]):
            pipefail = not re.search(r"\+o\s+pipefail", " ".join(first_words[1:]))
        if pipefail or len(pipe) < 2:
            continue
        hidden = next((c for c in (_check_in(s) or _script_in(s) for s in pipe[:-1]) if c), None)
        if not hidden and pipe[0].lstrip().startswith(("}", ")")):
            # a group piped whole (`{ pytest x; } | tail`): the checks inside it, back to where it opened
            j = i
            while j > 0 and not (_words(pipes[j][0][0])[1] & {"{", "("}):
                j -= 1
            hidden = next((c for p, _ in pipes[j:i] for c in map(_check_in, p) if c), None)
        if not hidden or (i + 1 < len(raws) and "PIPESTATUS" in raws[i + 1]):
            continue
        return _piped_why(hidden, (_words(pipe[-1])[0] or ["?"])[0])
    return None


def _piped_why(hidden, last):
    return (f"refused by the role guard: `{hidden}` is piped into `{last}`, so the exit status you see is `{last}`'s "
            "and a failure reads as a pass (Board #66 A). Write its output to a file and read the check's own status: "
            "`<check> > log 2>&1; echo \"rc=$?\"; tail log` - or put `set -o pipefail` first, or read "
            "`${PIPESTATUS[0]}` in the next statement")


# A TIME TYPED AHEAD OF THE CLOCK (the reviewer, 2026-10-13, Q&A #8 "go 1 and 2": "we're wasting time on this class of
# mistake. i don't part [particularly] care about time accuracy to the second, just the order of events"). Every slip
# on record was a time later than the clock - an estimate of when the work would end - or a minute left as "x". Only a
# time written after TODAY's date is judged, and every time of a range after it ("2026-10-13 14:43-15:01"); a planned
# time is written without the date. A time with an offset ("...T12:26:16+00:00") is compared as that instant.
_CLOCK = r"(\d{1,2}):(\d{2}|\d?[xX]{1,2})(?::\d{2}(?:\.\d+)?(Z|[+-]\d{2}:?\d{2})?)?"   # an offset only after seconds
_RANGE = re.compile(r"\s*(?:-|to|until)\s*" + _CLOCK)
_X_MINUTE = re.compile(r"(?<![\w:])\d{1,2}:(?:\d[xX]|[xX]{2})(?!\w)")


def future_time_refusal(text, now=None):
    """None, or the reason to refuse `text`: it holds today's date followed by a time later than `now` (a minute's
    grace), or by a minute with an x in it."""
    from datetime import datetime, timedelta
    now = now or datetime.now().astimezone()
    # A MINUTE LEFT AS X, WITH OR WITHOUT A DATE (Board #51 A, 2026-10-18: an architect's Board corner wrote one with
    # no date, the dated check let it through, and the correction cost turns) - "19:1x", "14:xx"; never a slice's "1:x"
    if (x := _X_MINUTE.search(text or "")):
        return (f"refused by the role guard: {x.group(0)!r} leaves a minute as x - read `date` or the record, "
                "and write the minute it says, or no time at all (WRITING.md)")
    stamp = re.compile(re.escape(now.strftime("%Y-%m-%d")) + r"(?:,\s*|\s+|T)" + _CLOCK)
    for m in stamp.finditer(text or ""):
        times, at = [m.groups()], m.end()
        while (r := _RANGE.match(text, at)):
            times.append(r.groups())
            at = r.end()
        for hh, mm, tz in times:
            written = text[m.start():at].strip()
            if not mm.isdigit():
                return (f"refused by the role guard: {written!r} leaves a minute as x - read `date` or the record, "
                        "and write the minute it says, or no time at all (WRITING.md)")
            try:
                t = now.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
            except ValueError:
                continue
            if tz:
                off = 0 if tz == "Z" else (1 if tz[0] == "+" else -1) * (int(tz[1:3]) * 60 + int(tz[-2:]))
                t = t.replace(tzinfo=None) - timedelta(minutes=off) + now.utcoffset()
                t = t.replace(tzinfo=now.tzinfo)
            if t > now + timedelta(minutes=1):
                return (f"refused by the role guard: {written!r} is later than the clock ({now:%H:%M}) - a time is "
                        "read from `date` or a record, never typed ahead; tell events in order and by their record "
                        "(a commit, a ruling, a Board item), and write a plan's time without the date (WRITING.md)")
    return None


# what the time check reads: the text a file tool writes into a document, a Board post, a commit message, and a
# command that writes a document (girsa-verifier's LOW on 19170cc1: `cat >>`, `sed -i` and a script's .write() were
# not read - the way most notebook and review text is written)
TIME_CHECKED_FILES = (".md", ".txt")
TIME_CHECKED_COMMAND = re.compile(r"board\.py|git\s+(?:-C\s+\S+\s+)?(?:commit|tag)\b")
NAMES_A_DOCUMENT = re.compile(r"\.(?:md|txt)\b")
WRITES = re.compile(r">|\btee\b|\bsed\s+(?:-\w+\s+)*-i|\.write\(|write_text\(")
_TEXT_FILE_ARG = re.compile(r"--(?:answer|body)-file[=\s]+(\"[^\"]+\"|'[^']+'|\S+)|(?:^|\s)-F\s+(\"[^\"]+\"|'[^']+'|[^\s-]\S*)")


def time_refusal(tool, tool_input, cwd, read=_read):
    """The time check for one tool call (every role, the operator too)."""
    if tool in ("Edit", "Write"):
        path = tool_input.get("file_path") or ""
        if not path.endswith(TIME_CHECKED_FILES):
            return None
        # ONLY THE LINES THE CALL ADDS (Board #51 A): a notebook rewritten whole, or an edit around an old line, carries
        # lines written before a check judged them (an x minute in the history) - not this call's to answer for
        new = tool_input.get("new_string") if tool == "Edit" else tool_input.get("content")
        old = tool_input.get("old_string") if tool == "Edit" else read(path)
        kept = set((old or "").splitlines())
        return future_time_refusal("\n".join(line for line in (new or "").splitlines() if line not in kept))
    if tool == "Bash":
        command = tool_input.get("command") or ""
        if not (TIME_CHECKED_COMMAND.search(command)
                or (NAMES_A_DOCUMENT.search(command) and WRITES.search(command))):
            return None
        why = future_time_refusal(command)
        for m in _TEXT_FILE_ARG.finditer(command):
            name = _expand((m.group(1) or m.group(2)).strip("\"'"), command)
            why = why or future_time_refusal(read(name if os.path.isabs(name) else os.path.join(cwd, name)) or "")
        return why
    return None


def edit_refusal(role, path, main_tree=is_main_tree):
    """None to let a file tool write `path` as `role`, or the reason to refuse it."""
    if role == OPERATOR or not path:
        return None
    here = os.path.dirname(os.path.abspath(os.path.expanduser(path)))
    while here and not os.path.isdir(here):
        parent = os.path.dirname(here)
        if parent == here:
            return None
        here = parent
    if main_tree(here):
        no_role = (" (this session was started without a role: a one-off session works in a worktree)"
                   if role == NO_ROLE else "")
        return ("refused by the role guard: this file is in the main tree or a book's corpus root, which only the "
                f"operator ({OPERATOR}) changes - edit your worktree's copy and land with `git merge --ff-only`, or "
                "send the operator a HANDOFF" + no_role)
    return None


def role_of(event, argv):
    """The role the guard judges: ROLE on the command line (a probe), else the session's agent_type, else NO_ROLE -
    which is refused what every role but the operator is refused (the reviewer, 2026-10-04)."""
    if len(argv) > 1:
        return argv[1]
    return event.get("agent_type") or NO_ROLE


def main(argv):
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 0
    # THE GUARD FAILS CLOSED ON ITS OWN FAULT (girsa-architect's Mishmeret audit, item 118, 1): an exception inside a
    # rule left Python with exit 1, which Claude Code reads as a non-blocking error, so the command ran - a push whose
    # tool_input was a string went through. Now the fault is printed and the command refused.
    try:
        return check(event, argv)
    except Exception as e:
        print(f"refused by the role guard: the guard itself failed ({type(e).__name__}: {e}) - nothing was checked, so "
              f"nothing runs; tell {OPERATOR}, which owns the hooks", file=sys.stderr)
        return 2


def check(event, argv):
    tool = event.get("tool_name")
    why = time_refusal(tool, event.get("tool_input") or {}, event.get("cwd") or os.getcwd())
    if why:
        print(why, file=sys.stderr)
        return 2
    if tool in FILE_TOOLS:
        path = (event.get("tool_input") or {}).get(FILE_TOOLS[tool]) or ""
        pin = pin_of(path) if path else None
        why = pin_refusal(pin) if pin else edit_refusal(role_of(event, argv), path)
        if why:
            print(why, file=sys.stderr)
            return 2
        return 0
    if tool != "Bash":
        return 0
    role = role_of(event, argv)
    command = (event.get("tool_input") or {}).get("command") or ""
    cwd = event.get("cwd") or os.getcwd()
    why = (refusal(role, command, cwd) or tmux_refusal(command, cwd) or copy_refusal(command, cwd)
           or check_status_refusal(command, cwd)
           or piped_check_refusal(command, cwd))
    if why:
        print(why, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
