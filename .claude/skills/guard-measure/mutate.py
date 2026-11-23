"""Each rule taken out, one at a time: for every [name, old, new] in MUTATIONS (a JSON list; a fourth element names the
row's own file, else FILE), the file (a path inside TREE) with `old` replaced by `new` - exactly once - on a fresh copy
of TREE's `mishmeret/`, `tests/` and `.claude/skills/` (never the tree itself, and no .git: a worktree's copy would
share its index), then pytest run there with PYTEST_ARGS.

First the same run unmutated, which must pass: a selection that collects nothing, or a red suite, stops it there
(girsa-verifier's LOW 2 on 59f84a2: an exit 5 or 2 had read as RED). Then each mutation is RED only on pytest's exit 1
- its tests ran and one failed; any other exit is printed with its code. A GREEN, another exit, or an `old` not found
exactly once makes the exit 1.

    python3 -I mutate.py TREE FILE MUTATIONS SCRATCH -- PYTEST_ARGS...

Prints the baseline's result, then RED, GREEN or EXIT <code> per mutation, with the first assertion or error line."""
import json
import os
import shutil
import subprocess
import sys

DROP_ENV = ("MISHMERET_CONFIG", "MISHMERET_AS", "CLAUDE_PROJECT_DIR")
COPIED = ("mishmeret", "tests", os.path.join(".claude", "skills"))


def run(tree, scratch, pytest_args, rel=None, old=None, new=None):
    """pytest's exit and its first `E ` line, on a fresh copy of `tree` with `rel`'s `old` replaced by `new`."""
    work = os.path.join(scratch, "mutant")
    shutil.rmtree(work, ignore_errors=True)
    for d in COPIED:
        if os.path.isdir(os.path.join(tree, d)):
            shutil.copytree(os.path.join(tree, d), os.path.join(work, d))
    if rel:
        path = os.path.join(work, rel)
        src = open(path, encoding="utf-8").read()
        open(path, "w", encoding="utf-8").write(src.replace(old, new))
    env = {k: v for k, v in os.environ.items() if k not in DROP_ENV}
    r = subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider", *pytest_args], cwd=work, env=env,
                       capture_output=True, text=True, stdin=subprocess.DEVNULL)
    return r.returncode, next((ln.strip() for ln in r.stdout.splitlines() if ln.startswith("E ")), "")


def main(tree, rel, mutations, scratch, pytest_args):
    rc, first = run(tree, scratch, pytest_args)
    if rc != 0:
        print(f"BASELINE EXIT {rc}: the unmutated run must pass before a mutation means anything  {first[:150]}")
        return 1
    print("BASELINE passed")
    bad = 0
    for row in json.load(open(mutations, encoding="utf-8")):
        name, old, new, path = (row + [rel])[:4]
        count = open(os.path.join(tree, path), encoding="utf-8").read().count(old)
        if count != 1:
            print(f"NOT FOUND ONCE ({count}): {name}")
            bad = 1
            continue
        rc, first = run(tree, scratch, pytest_args, path, old, new)
        verdict = "RED  " if rc == 1 else "GREEN" if rc == 0 else f"EXIT {rc}"
        print(f"{verdict} {name}  {first[:150]}")
        bad |= rc != 1
    return bad


if __name__ == "__main__":
    if "--" not in sys.argv or sys.argv.index("--") != 5:
        sys.exit(__doc__)
    sys.exit(main(*sys.argv[1:5], sys.argv[6:]))
