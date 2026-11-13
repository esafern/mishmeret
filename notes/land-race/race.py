"""The land.py race (notes/PLAN-LAND-RACE.md), through land.py itself: a notes landing (`land.py land ex-verifier
notes`, the merge into the main tree) against a notes commit in the main tree (`land.py commit ex-operator notes`,
refused by its own lane check, as the first project's operator's commit was on 2026-11-13), each its own process, on a
scratch repository and the placeholder project (tests/conftest.py). The commit starts RACE_STEP x trial seconds after
the landing (default 0.002), so the trials sweep the window. Each process's role is set here, as the suite sets it.

    python3 notes/land-race/race.py TREE SCRATCH TRIALS     # TREE: the Mishmeret tree whose mishmeret/land.py runs

Counts: a reset that moved main back; a landing reported done whose commit is not on main; a name left STAGED in the
main tree; a landing refused on git's index lock; anything else left in the main tree (the operator's own refused
file aside). Measured 2026-11-13 on main d35d110's land.py: 0, 0, 5, 1, 0 in 500 trials (RACE_STEP 0.0007)."""
import os
import shutil
import subprocess
import sys
import time

tree, scratch, trials = sys.argv[1], sys.argv[2], int(sys.argv[3])
sys.path.insert(0, os.path.join(tree, "tests"))
from conftest import write_project  # noqa: E402  (the placeholder project's config)

root = os.path.join(scratch, "race")
shutil.rmtree(root, ignore_errors=True)
main, wt = os.path.join(root, "main"), os.path.join(root, "wt")
os.makedirs(os.path.join(main, "tools"))
os.makedirs(os.path.join(main, "notes"))
cfg = write_project(main)
env0 = {k: v for k, v in os.environ.items() if not k.startswith(("MISHMERET_", "CLAUDE_"))}
env0.update(MISHMERET_CONFIG=cfg, GIT_AUTHOR_NAME="placeholder", GIT_AUTHOR_EMAIL="placeholder@example.org",
            GIT_COMMITTER_NAME="placeholder", GIT_COMMITTER_EMAIL="placeholder@example.org")


def git(cwd, *a):
    return subprocess.run(["git", "-C", cwd, *a], env=env0, capture_output=True, text=True)


with open(os.path.join(main, "tools", "lanes.py"), "w", encoding="utf-8") as fh:   # the operator's commit refused
    fh.write("import sys\nif sys.argv[1] == 'ex-operator':\n    print('FAIL: a placeholder cap')\n    sys.exit(1)\n"
             "print('PASS')\n")
for f in ("v.md", "o.md"):
    with open(os.path.join(main, "notes", f), "w", encoding="utf-8") as fh:
        fh.write("start\n")
with open(os.path.join(main, ".gitignore"), "w", encoding="utf-8") as fh:
    fh.write(".claude/\n")
git(main, "init", "-q", "-b", "main")
git(main, "add", ".")
git(main, "commit", "-q", "-m", "start")
git(main, "worktree", "add", "-q", "-b", "feature", wt)
land = os.path.join(tree, "mishmeret", "land.py")
msg = os.path.join(root, "msg.txt")
with open(msg, "w", encoding="utf-8") as fh:
    fh.write("placeholder\n")
stamp = os.path.join(main, ".git", "worktrees", "wt", "land-rebase.json")
step = float(os.environ.get("RACE_STEP", "0.002"))
rewound = lost = staged = lock_refused = other = 0
for i in range(trials):
    tip = git(main, "rev-parse", "main").stdout.strip()
    git(wt, "reset", "-q", "--hard", tip)
    if os.path.exists(stamp):              # a refused trial's rebase stamp would refuse every landing after it
        os.unlink(stamp)
    with open(os.path.join(wt, "notes", "v.md"), "w", encoding="utf-8") as fh:
        fh.write(f"verifier {i}\n")
    git(wt, "commit", "-q", "-am", f"verifier {i}")
    with open(os.path.join(main, "notes", "o.md"), "w", encoding="utf-8") as fh:
        fh.write(f"operator {i}\n")
    before = len(git(main, "reflog", "main").stdout.splitlines())
    a = subprocess.Popen([sys.executable, land, "land", "ex-verifier", "notes"], cwd=wt,
                         env=dict(env0, CLAUDE_CODE_AGENT="ex-verifier"), stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True)
    time.sleep(step * i)
    b = subprocess.Popen([sys.executable, land, "commit", "ex-operator", "notes", "-F", msg, "notes/o.md"], cwd=main,
                         env=dict(env0, CLAUDE_CODE_AGENT="ex-operator"), stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True)
    out_a = a.communicate()[0]
    b.communicate()
    new = len(git(main, "reflog", "main").stdout.splitlines()) - before
    log = git(main, "reflog", "--format=%H %gs", "HEAD").stdout.splitlines()[:new + 1]
    if any(e.split(" ", 1)[1].startswith("reset:") and log[k + 1].split()[0] != e.split()[0]
           for k, e in enumerate(log[:-1])):
        rewound += 1
        print(f"trial {i}: a reset moved main back: {[e.split(' ', 1)[1][:40] for e in log]}")
    head = git(main, "rev-parse", "HEAD").stdout.strip()
    if a.returncode == 0 and git(main, "merge-base", "--is-ancestor", git(wt, "rev-parse", "HEAD").stdout.strip(),
                                 head).returncode != 0:
        lost += 1
    if a.returncode and ("index.lock" in out_a or "Another git process" in out_a):
        lock_refused += 1
        print(f"trial {i}: the landing refused on the index lock")
    status = [line for line in git(main, "status", "--porcelain").stdout.splitlines() if line != " M notes/o.md"]
    if any(line[0] not in " ?" for line in status):
        staged += 1
        print(f"trial {i}: left staged: {status}")
    elif status:
        other += 1
        print(f"trial {i}: left in the main tree: {status}")
    if status:
        git(main, "reset", "-q", "--hard", head)
        git(main, "clean", "-qfd", "notes")
    if b.returncode:                        # the operator's file, committed by hand, so the next trial starts clean
        git(main, "commit", "-q", "-am", f"operator {i} by hand")
print(f"{trials} trials: {rewound} moved back by a reset, {lost} landings done but not on main, {staged} with a name "
      f"left staged, {lock_refused} landings refused on the index lock, {other} with something else left")
