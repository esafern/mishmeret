#!/usr/bin/env python3
"""The time check at every commit: git's pre-commit hook refuses a commit whose ADDED lines in a .md or .txt file carry
today's date followed by a time later than the clock, a later range end, or a minute left as x.

The reviewer, 2026-10-13, Board #33: "A". The role guard (role_guard.py, future_time_refusal) checks text when a role
writes it - the file tools, a Board post, a command naming the document - but girsa-verifier's probe found what it
cannot see: a script that writes (`bash write_note.sh`), a path built at run time, a scratch file moved onto the
document in a second command, a commit made inside a script. Every commit passes here, however it is made. Its limit:
only a time still ahead of the clock when the commit runs.

    python3 .claude/hooks/time_precommit.py            # the hook's own run: checks the staged changes
    python3 .claude/hooks/time_precommit.py --install  # writes the repository's pre-commit hook (once per clone;
                                                       # the worktrees share it)
Exit 1 refuses the commit and says why. Needs only Python's standard library."""
import importlib.util
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HOOK = """#!/bin/sh
# Girsa's time check (.claude/hooks/time_precommit.py; Board #33). A tree whose branch predates it has no script: let
# the commit run.
s="$(git rev-parse --show-toplevel)/.claude/hooks/time_precommit.py"
[ -f "$s" ] || exit 0
exec python3 "$s"
"""


def added_lines(cwd=None):
    """[(path, line)] for every line the staged changes add to a .md or .txt file."""
    diff = subprocess.run(["git", "diff", "--cached", "-U0", "--no-color", "--diff-filter=AMR", "--", "*.md", "*.txt"],
                          cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    out, path = [], None
    for line in diff.splitlines():
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else line[4:]
        elif line.startswith("+") and path:
            out.append((path, line[1:]))
    return out


def refusal(lines, now=None):
    spec = importlib.util.spec_from_file_location("role_guard", os.path.join(HERE, "role_guard.py"))
    rg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rg)
    for path, line in lines:
        why = rg.future_time_refusal(line, now)
        if why:
            return f"{path}: {why.replace('refused by the role guard', 'commit refused by the time check')}"
    return None


def install(cwd=None):
    common = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=cwd, capture_output=True, text=True,
                            check=True).stdout.strip()
    hooks = os.path.join(cwd or os.getcwd(), common, "hooks") if not os.path.isabs(common) else os.path.join(common, "hooks")
    os.makedirs(hooks, exist_ok=True)
    path = os.path.join(hooks, "pre-commit")
    if os.path.exists(path) and open(path, encoding="utf-8").read() != HOOK:
        raise SystemExit(f"{path} exists and is not this hook - not replaced")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(HOOK)
    os.chmod(path, 0o755)
    return path


def main(argv):
    if "--install" in argv:
        print(f"installed {install()}")
        return 0
    why = refusal(added_lines())
    if why:
        print(why, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
