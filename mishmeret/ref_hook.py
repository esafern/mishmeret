#!/usr/bin/env python3
"""git's reference-transaction hook: main's branch, the `guard.refs` refs and git's object replacements judged by what
git is about to write, whatever writes it (notes/PLAN-REF-HOOK.md; the first project's Board #304 A, girsa-architect's
follow-up at its 350e01e37). The role guard reads a command's words; a script, or a form it cannot read, moves a ref it
never sees - this sees every ref update of the repository, from its main clone or any worktree.

    python3 .claude/hooks/ref_hook.py --install   # in the main clone, by the project's shim: writes the repository's
                                                  # hook (once per clone; the worktrees share it), naming that shim
    python3 .claude/hooks/ref_hook.py prepared    # git's own run, the transaction's lines on its input

Who may move which ref is the guard's one rule (role_guard._owner and may_move): a `guard.refs` ref and a replacement
their owner's alone; main's branch (`guard.main`, and the one the main clone has checked out) the operator's, but a
fast-forward - a landing - any role's. The role is the session's (config.session_role: MISHMERET_ROLE, else
CLAUDE_CODE_AGENT); with none, a session with no role.
Exit 1 refuses the transaction and says why; the hook's own fault refuses it too."""
import os
import shlex
import subprocess
import sys

import config
import role_guard as rg                     # this package's own guard, never a project's shim

# THE COMMAND'S ENVIRONMENT IS NOT THE HOOK'S: git runs a hook with whatever the command set, so the hook takes only what
# it needs - its Python by path and isolated (-I: no PYTHON... variable, no python3 earlier on PATH), the shim's own
# config (a MISHMERET_CONFIG or a field's override, MISHMERET_OPERATOR=..., would choose who may), the checkout as
# installed, and PATH and HOME as installed, set before the hook's first command (girsa-architect's answer, Q3: git
# puts the command's own exec path first on a hook's PATH - `GIT_EXEC_PATH=<x>` or `--exec-path=<x>` gave the hook a
# `git` that said yes, and main moved back); from the command, only where git runs it (GIT_DIR) and the role
MARKER = "'s ref hook (notes/PLAN-REF-HOOK.md in Mishmeret)"
HOOK = """#!/bin/sh
# {project}""" + MARKER + """: who may move main's branch and the guard.refs refs.
# Judged when the refs are locked, and only for a ref under refs/ - HEAD and git's own pseudo-refs are no one's.
PATH={path}; HOME={home}; export PATH HOME
[ "$1" = prepared ] || exit 0
s={shim}
[ -f "$s" ] || {{ echo "refused by the ref hook: $s is missing, so nothing is checked - the operator installs it again" >&2; exit 1; }}
lines=$(cat)
case "$lines" in *" refs/"*) ;; *) exit 0 ;; esac
printf '%s\\n' "$lines" | env -i PATH="$PATH" HOME="$HOME" GIT_DIR="${{GIT_DIR-}}" \\
    MISHMERET_ROLE="${{MISHMERET_ROLE-}}" CLAUDE_CODE_AGENT="${{CLAUDE_CODE_AGENT-}}"{checkout} {python} -I "$s" prepared
"""


def _git(where, *args):
    return subprocess.run(["git", "-C", where, *args], capture_output=True, text=True)


def _packed(common, ref):
    """The value git's packed refs will hold for `ref` once this transaction is done: its next packed-refs (the lock a
    deletion writes, while one is being written), else the file - or None. PACKING IS NO DELETION (measured, git
    2.56.1): `pack-refs`, and so `gc`, writes each ref into packed-refs, then deletes its loose file in a transaction of
    its own, `<value> 0000... <ref>` - the ref keeps its value. A real deletion of a packed ref writes the lock without
    it before the hook is asked."""
    for name in ("packed-refs.lock", "packed-refs"):
        try:
            with open(os.path.join(common, name), encoding="utf-8") as fh:
                return next((line.split(" ", 1)[0] for line in fh if line.rstrip("\n").endswith(" " + ref)
                             and not line.startswith(("#", "^"))), None)
        except OSError:
            continue
    return None


def refusal(role, lines, where):
    """Why git may not write `lines` ([(old, new, ref)]) in the repository at `where` as `role`, or None. Only in a
    guarded repository - a copy has its own refs. The ref's value is read here, not the line's: `update-ref <ref>
    <older>` with no old value hands the hook zeros (girsa-architect's measure). A line of HEAD or a pseudo-ref has no
    owner; a transaction of those alone never reaches here (the hook's shell)."""
    if not lines:
        return None
    own = rg._git_dirs(where)
    if not own:                             # fails closed (girsa-architect's Q3: a stand-in git named no repository)
        return f"refused by the ref hook: git could not name the repository at {where}, so nothing is checked"
    if own[1] not in rg.guarded_git_dirs():
        return None
    listing = rg._checked_out(where)
    if listing is None:
        return None if role == rg.OPERATOR else ("refused by the ref hook: git could not list this repository's "
                                                 "worktrees, to say whose main's branch is - try again")
    for old, new, ref in lines:
        o = rg._owner(ref, listing[:1])      # main's branch, guard.refs, replacements; a role's branch the Bash guard's
        if not o:
            continue
        cur = _git(where, "rev-parse", "-q", "--verify", ref).stdout.strip() or None
        if cur == new or (set(new) == {"0"} and cur and _packed(own[1], ref) == cur):
            continue                        # it moves nothing: the same value, or a loose ref's file after packing
        # git says forward only of a commit that descends from the ref's own: not of zeros (a deletion), nor of
        # `ref:<target>` (a symbolic ref), which it cannot name
        forward = cur is not None and _git(where, "merge-base", "--is-ancestor", cur, new).returncode == 0
        if rg.may_move(role, *o, forward=forward):
            continue
        owner, kind = o
        what = {"main": "main's branch: it moves only forward but for the operator's",
                "refs": f"a ref `guard.refs` gives to {owner} alone",
                "replace": f"an object replacement, as `git replace` makes - {owner}'s alone"}[kind]
        # outside every session there is no REQUEST to send (girsa-architect's Q1): the owner's pane, or the reviewer's
        way = (f"run it in {owner}'s pane, as `! git ...`" if role == rg.NO_ROLE else rg.ask(owner))    # the guard's
        return (f"refused by the ref hook: {role} may not move {ref} ({(cur or 'none')[:12]} to {new[:16]}) - {what}; "
                + way)
    return None


def install(root=None):
    """Write the repository's reference-transaction hook, naming the shim this was run by in the main clone."""
    root = root or config.root()
    shim = os.environ.get("MISHMERET_AS")
    dirs = rg._git_dirs(root)
    if not shim or not dirs:
        raise SystemExit("run it by the project's shim, in its main clone: python3 .claude/hooks/ref_hook.py --install")
    if dirs[0] != dirs[1]:
        raise SystemExit(f"{root} is a linked worktree: the hook is the repository's - install it from the main clone")
    moved = _git(root, "config", "--get", "core.hooksPath").stdout.strip()
    if moved:
        raise SystemExit(f"core.hooksPath is set ({moved}): git would not run a hook in {dirs[1]}/hooks - not installed")
    checkout = os.environ.get("MISHMERET_DIR")      # the shim's own default (~/work/mishmeret) when unset
    q = shlex.quote
    text = HOOK.format(project=rg._CFG["project"], shim=q(os.path.join(root, shim)), python=q(sys.executable),
                       path=q(os.environ.get("PATH", "")), home=q(os.path.expanduser("~")),
                       checkout=f" MISHMERET_DIR={q(os.path.abspath(os.path.expanduser(checkout)))}" if checkout else "")
    path = os.path.join(dirs[1], "hooks", "reference-transaction")
    # ITS OWN HOOK IS REPLACED, another refused (girsa-architect's Q4: the text holds the paths it was installed with,
    # so a new Python or checkout, or a new Mishmeret commit's text, had left a hook the install would not replace)
    if os.path.exists(path) and MARKER not in open(path, encoding="utf-8").read():
        raise SystemExit(f"{path} exists and is not this hook - not replaced")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    os.chmod(path, 0o755)
    return path


def main(argv):
    if argv[1:] == ["--install"]:
        print(f"installed {install()}")
        return 0
    if argv[1:] != ["prepared"]:
        return 0
    # the repository git runs the hook for: its GIT_DIR (a worktree's, or one named by --git-dir from anywhere), else
    # the folder; git's own variables go before the guard asks git about other repositories
    where = os.path.abspath(os.environ.get("GIT_DIR") or ".")
    for k in [k for k in os.environ if k.startswith("GIT_")]:
        del os.environ[k]
    lines = [tuple(line.split(" ", 2)) for line in sys.stdin.read().splitlines() if line.count(" ") >= 2]
    try:
        why = refusal(config.session_role() or rg.NO_ROLE, lines, where)
    except Exception as e:
        why = f"refused by the ref hook: the hook itself failed ({type(e).__name__}: {e}) - nothing was checked"
    if why:
        print(why, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
