#!/usr/bin/env python3
"""This project's lane check (its config's `land.lane_check`), run by `land.py commit` from the repository's top:

    python3 .claude/lane_check.py ROLE [--doc-only] [--because WORDS]

Fails (exit 1) on a staged path outside ROLE's lane in `.claude/lanes.txt` - reported, not failed, under `--because`,
the reviewer's words the commit message then carries; on a path not a `.md` under `--doc-only`; and, on every commit,
whatever its paths (this repository is PUBLIC), on an added line holding a personal address, a name or address from
the local roster, or this machine's home folder - counted by file, the text never shown. The roster is
`.claude/roster.local.json` in the MAIN clone, untracked ({"reviewers": {id: {"display", "email"}}}, a Girsa roster's
shape); without it the names go unchecked and the report says so. `--range` and `--plan` are refused (exit 2): no one
runs `land.py land` here; the operator merges."""
import fnmatch
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PERSONAL_ADDRESS = re.compile(r"[._%+-]*[A-Za-z0-9][A-Za-z0-9._%+-]*@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
NOT_PERSONAL = re.compile(r"(?i)@(?:example\.(?:com|org|net)|[a-z]+\.example)\b|noreply@anthropic\.com"
                          r"|^ID\+login@users\.noreply\.github\.com$")


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def lane(role, path, rows):
    return (any(r == role and k == "may" and fnmatch.fnmatch(path, p) for r, k, p in rows)
            and not any(r == role and k == "not" and fnmatch.fnmatch(path, p) for r, k, p in rows))


def forbidden():
    """(pattern, why names are unchecked or None): the roster's names and addresses, and the home folder."""
    main = os.path.dirname(git("rev-parse", "--path-format=absolute", "--git-common-dir").strip())
    pats, why = [re.escape(os.path.expanduser("~"))], None
    try:
        with open(os.path.join(main, ".claude", "roster.local.json"), encoding="utf-8") as fh:
            people = json.load(fh)["reviewers"].values()
    except (OSError, ValueError, KeyError, AttributeError):
        people, why = (), "no readable .claude/roster.local.json in the main clone: no name was checked"
    for p in people:
        pats += [r"[ ._]?".join(map(re.escape, (p.get("display") or "").split()))] if p.get("display") else []
        pats += [re.escape(p["email"])] if p.get("email") else []
    return re.compile("(?i)" + "|".join(pats)), why


def main(argv):
    if not argv or argv[0].startswith("-") or any(a in ("--range", "--plan") for a in argv):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    role, doc_only = argv[0], "--doc-only" in argv
    because = argv[argv.index("--because") + 1] if "--because" in argv else None
    with open(os.path.join(HERE, "lanes.txt"), encoding="utf-8") as fh:
        rows = [tuple(line.split()) for line in fh if line.strip() and not line.startswith("#")]
    names = sorted(set(git("diff", "--cached", "--name-only", "--no-renames").split("\n")) - {""})
    out, failed = [f"lane check, {role}: {len(names)} path{'s' * (len(names) != 1)} staged"], False
    for p in names:
        if not lane(role, p, rows):
            said = f", ON THE REVIEWER'S WORD ({because})" if because else ""
            out.append(f"  OUTSIDE THE LANE{said}: {p}")
            failed |= not because
        if doc_only and not p.endswith(".md"):
            out.append(f"  NOT A DOCUMENT (--doc-only): {p}")
            failed = True
    pattern, why = forbidden()
    added, path = {}, None
    for line in git("diff", "--cached", "-U0", "--no-color", "--no-renames").splitlines():
        if line.startswith("+++ "):
            path = line[6:]
        elif line.startswith("+") and path:
            if [a for a in PERSONAL_ADDRESS.findall(line) if not NOT_PERSONAL.search(a)] or pattern.search(line):
                added[path] = added.get(path, 0) + 1
    for p, n in sorted(added.items()):
        out.append(f"  {p}: {n} added line{' carries' if n == 1 else 's carry'} a personal address, a roster name or "
                   "this machine's home folder (the text is not shown here)")
        failed = True
    out += [f"  {why}"] if why else []
    print("\n".join(out + ["FAIL" if failed else "PASS"]))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
