"""Each rule taken out, one at a time: for every [name, old, new] in MUTATIONS (a JSON list), FILE (a path inside TREE)
with `old` replaced by `new` - exactly once - on a fresh copy of TREE's `mishmeret/` and `tests/` folders (never the
tree itself, and no .git: a worktree's copy would share its index), then pytest run there with PYTEST_ARGS. A rule
whose test stays green, or an `old` not found exactly once, is printed and makes the exit 1.

    python3 -I mutate.py TREE FILE MUTATIONS SCRATCH -- PYTEST_ARGS...

Prints RED or GREEN per mutation, with the first assertion or error line of a red run."""
import json
import os
import shutil
import subprocess
import sys

DROP_ENV = ("MISHMERET_CONFIG", "MISHMERET_AS", "CLAUDE_PROJECT_DIR")


def main(tree, rel, mutations, scratch, pytest_args):
    src = open(os.path.join(tree, rel), encoding="utf-8").read()
    env = {k: v for k, v in os.environ.items() if k not in DROP_ENV}
    bad = 0
    for name, old, new in json.load(open(mutations, encoding="utf-8")):
        if src.count(old) != 1:
            print(f"NOT FOUND ONCE ({src.count(old)}): {name}")
            bad = 1
            continue
        work = os.path.join(scratch, "mutant")
        shutil.rmtree(work, ignore_errors=True)
        os.makedirs(work)
        for d in ("mishmeret", "tests"):
            shutil.copytree(os.path.join(tree, d), os.path.join(work, d))
        with open(os.path.join(work, rel), "w", encoding="utf-8") as fh:
            fh.write(src.replace(old, new))
        r = subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider", *pytest_args], cwd=work, env=env,
                           capture_output=True, text=True, stdin=subprocess.DEVNULL)
        first = next((ln.strip() for ln in r.stdout.splitlines() if ln.startswith("E ")), "")
        print(f"{'RED  ' if r.returncode else 'GREEN'} {name}  {first[:150]}")
        bad |= r.returncode == 0
    return bad


if __name__ == "__main__":
    if "--" not in sys.argv or sys.argv.index("--") != 5:
        sys.exit(__doc__)
    sys.exit(main(*sys.argv[1:5], sys.argv[6:]))
