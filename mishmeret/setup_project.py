#!/usr/bin/env python3
"""A project takes Mishmeret's guard alone (notes/PLAN-PROJECT-SETUP.md; the README's "The guard alone"). Writes into
the project's main clone what the guard needs - its config (`.mishmeret/config.json`), the shim's helper and the
hooks' shims (`.claude/`), the PreToolUse hook (`.claude/settings.json`), an agent file for each Claude Code role -
then prints the steps that are git's, each a command of its own, in their order, for the operator: the pin, the
commit, each role's worktree, the ref hook, each role's start.

    python3 <mishmeret>/mishmeret/setup_project.py DIR --project NAME --operator ROLE --role ROLE=WORKTREE[:pi] ...
            [--foreign PATH ...] [--protect REF_GLOB ...] [--commit SHA] [--write]

DIR is the project's main clone; a relative WORKTREE or PATH is taken from the folder this runs in. `:pi` runs the
role under pi, guarded by the pin's pi_guard.ts when started by its printed line (a bare `pi` runs no hook). Without
--write it says what it would write. A file of the project's is never replaced (settings.json gains the hook beside
what it holds, written back in json's own form), so a second run writes nothing new. Every path under the home folder
is written as `~/...`. The pin is the commit this file runs from, or --commit."""
import argparse
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import config  # noqa: E402  (this tree's: the config written is the one it loads)

HOOK = {"matcher": "Bash|Edit|Write|NotebookEdit",
        "hooks": [{"type": "command", "command": 'python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/role_guard.py"',
                   "timeout": 15}]}
HOOK_SHIM = '''#!/usr/bin/env python3
"""mishmeret/{module}.py, run from the commit the project's Mishmeret config pins (.claude/mishmeret_shim.py), with the
same arguments, or stood in for when imported. A missing checkout or pin is said, and the hook refuses: it fails
closed."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mishmeret_shim  # noqa: E402

mishmeret_shim.stand_in(__name__, ".claude/hooks/{module}.py", "{module}", "refuses")
'''
AGENT = """---
name: {role}
description: {project}'s {role} - it works in {place}, started there with `{start}`.
---

You are {project}'s {role}. You work in {place}, started there with `{start}`. Mishmeret's role guard refuses what
is not this role's, and says why.
"""
SHIM = ".claude/mishmeret_shim.py"


def tilde(path):
    """`path` with the home folder as `~`, as Mishmeret's configs write a path (girsa-verifier's MEDIUM 1 on the plan:
    the home folder holds its owner's name, and these files are committed)."""
    home = os.path.expanduser("~")
    return "~" + path[len(home):] if path == home or path.startswith(home + os.sep) else path


def full(path):
    """A path given on the command line, from the folder this runs in, `~` expanded."""
    return os.path.abspath(os.path.expanduser(path))


def git(where, *args):
    r = subprocess.run(["git", "-C", where, *args], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"git {' '.join(args)} in {where}: {r.stderr.strip()}")
    return r.stdout.strip()


def files(root, project, operator, roles, foreign, protect, commit):
    """{path from the root: its text} - what the guard needs, settings.json merged with the project's own."""
    cfg = {"repository": git(HERE, "remote", "get-url", "origin"), "mishmeret_commit": commit, "project": project,
           "roles": [{"name": operator}] + [{"name": r, "worktrees": [tilde(w)], **({"runner": "pi"} if pi else {})}
                                            for r, w, pi in roles],
           "operator": operator,
           "guard": {"main": git(root, "symbolic-ref", "--short", "HEAD"),
                     **({"foreign": [tilde(f) for f in foreign]} if foreign else {}),
                     **({"refs": {g: operator for g in protect}} if protect else {})}}
    with open(os.path.join(HERE, "project_shim.py"), encoding="utf-8") as fh:
        shim = fh.read()
    out = {".mishmeret/config.json": json.dumps(cfg, indent=2) + "\n", SHIM: shim,
           ".claude/hooks/role_guard.py": HOOK_SHIM.format(module="role_guard")}
    if protect:
        out[".claude/hooks/ref_hook.py"] = HOOK_SHIM.format(module="ref_hook")
    for role, place, tree in [(operator, "the main clone", root)] + [(r, f"{r}'s own worktree", w)
                                                                    for r, w, pi in roles if not pi]:
        out[f".claude/agents/{role}.md"] = AGENT.format(role=role, project=project, place=place,
                                                        start=f"cd {tilde(tree)} && claude --agent {role}")
    path = os.path.join(root, ".claude", "settings.json")
    settings = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    pre = settings.setdefault("hooks", {}).setdefault("PreToolUse", [])
    if not any("role_guard.py" in h.get("command", "") for e in pre for h in e.get("hooks", ())):
        pre.append(HOOK)
    out[".claude/settings.json"] = json.dumps(settings, indent=2) + "\n"
    return out


def refused(text):
    """config.py's refusal of the config `text`, or None: it is loaded as this tree reads it before it is written
    (girsa-architect's Q1), so a config the pin would refuse is never written."""
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, ".mishmeret"))
        p = os.path.join(d, ".mishmeret", "config.json")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)
        was = os.environ.get("MISHMERET_CONFIG")
        os.environ["MISHMERET_CONFIG"] = p
        try:
            config.load()
        except config.ConfigError as e:
            return str(e).replace(p, "the config it would write")
        finally:
            os.environ.pop("MISHMERET_CONFIG") if was is None else os.environ.update(MISHMERET_CONFIG=was)
    return None


def main(argv):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("dir")
    p.add_argument("--project", required=True)
    p.add_argument("--operator", required=True)
    p.add_argument("--role", action="append", default=[], metavar="ROLE=WORKTREE[:pi]")
    p.add_argument("--foreign", action="append", default=[], metavar="PATH")
    p.add_argument("--protect", action="append", default=[], metavar="REF_GLOB")
    p.add_argument("--commit")
    p.add_argument("--write", action="store_true")
    a = p.parse_args(argv[1:])
    root = full(a.dir)
    if git(root, "rev-parse", "--git-dir") != ".git":
        raise SystemExit(f"{root} is not a repository's main clone (its top folder, holding .git)")
    roles = []
    for given in a.role:
        role, _, tree = given.partition("=")
        pi = tree.endswith(":pi")
        tree = tree[:-3] if pi else tree
        if not role or not tree:
            raise SystemExit("--role takes ROLE=WORKTREE[:pi]: the role's worktree, the path it will be made at")
        roles.append((role, full(tree), pi))
    head = git(HERE, "rev-parse", "HEAD")
    commit = git(HERE, "rev-parse", "--verify", (a.commit or head) + "^{commit}")
    if commit != head:
        print(f"the pin {commit[:9]} is not the commit this runs from ({head[:9]}): its config.py may read these "
              "fields otherwise - the config is checked by this one")
    written = []
    for rel, text in files(root, a.project, a.operator, roles, [full(f) for f in a.foreign], a.protect,
                           commit).items():
        if rel == ".mishmeret/config.json":
            why = refused(text)
            if why:
                raise SystemExit(f"not written: {why}")
        path = os.path.join(root, rel)
        old = open(path, encoding="utf-8").read() if os.path.exists(path) else None
        if old == text:
            print(f"  as it is   {rel}")
            continue
        if old is not None and rel != ".claude/settings.json":
            said = "it differs from mishmeret/project_shim.py" if rel == SHIM else "compare it with what this would write"
            print(f"  KEPT       {rel} - the project's own, not replaced: {said}")
            continue
        written.append(rel)
        print(f"  {'wrote ' if a.write else 'writes'}     {rel}")
        if a.write:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
            if rel.endswith(".py"):
                os.chmod(path, 0o755)
    checkout = full(os.environ.get("MISHMERET_DIR") or "~/work/mishmeret")
    pin = os.path.join(checkout, ".pins", commit)
    steps = [] if os.path.isdir(os.path.join(pin, "mishmeret")) else [
        ("the pin", f"git -C {tilde(checkout)} worktree add --detach {tilde(pin)} {commit}")]
    if written:
        steps += [("the files", f"git -C {tilde(root)} add {' '.join(written)}"),
                  ("their commit", f"git -C {tilde(root)} commit -m \"Mishmeret's role guard, pinned at {commit[:9]}\"")]
    for r, w, _ in roles:
        if not os.path.exists(w):
            has = subprocess.run(["git", "-C", root, "show-ref", "--verify", "-q", f"refs/heads/{r}"]).returncode == 0
            steps.append((f"{r}'s worktree", f"git -C {tilde(root)} worktree add {tilde(w)} {r if has else '-b ' + r}"))
    if a.protect:
        steps.append(("the ref hook, after the pin and the commit",
                      f"cd {tilde(root)} && python3 .claude/hooks/ref_hook.py --install"))
    steps.append((f"{a.operator}'s start", f"cd {tilde(root)} && claude --agent {a.operator}"))
    for r, w, pi in roles:
        steps.append((f"{r}'s start", f"cd {tilde(w)} && " + (
            f"pi --no-extensions --name {r} --role {r} -e {tilde(pin)}/mishmeret/pi_guard.ts" if pi
            else f"claude --agent {r}")))
    print(("\nThen, in your own terminal or the operator's, in order:" if a.write else
           "\nNothing written (--write writes it). Then, in order:"))
    for i, (what, command) in enumerate(steps, 1):
        print(f"{i}. {what}:\n   {command}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
