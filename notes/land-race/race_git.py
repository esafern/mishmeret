"""The land.py race (notes/PLAN-LAND-RACE.md) at git's own level: `git merge --ff-only` stepping main forward STEPS
times while a thread loops a reset (each git call its own process) - `git reset -q`, then `git reset -q -- <path>` - on
a scratch repository.
Counts the reset entries in the reflog that moved HEAD back.

    python3 notes/land-race/race_git.py SCRATCH STEPS

Measured 2026-11-13 (300 steps): `git reset -q` - 242 resets in the reflog, 1 moved HEAD back (it resolves HEAD at its
start and writes it at its end, undoing a merge made between); `git reset -q -- o.md` - no reset entry, none back (a
path reset writes the index alone)."""
import os
import shutil
import subprocess
import sys
import threading

scratch, steps = sys.argv[1], int(sys.argv[2])
env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
env.update(GIT_AUTHOR_NAME="placeholder", GIT_AUTHOR_EMAIL="placeholder@example.org",
           GIT_COMMITTER_NAME="placeholder", GIT_COMMITTER_EMAIL="placeholder@example.org")
for form in (["reset", "-q"], ["reset", "-q", "--", "o.md"]):
    root = os.path.join(scratch, "race-git")
    shutil.rmtree(root, ignore_errors=True)
    os.makedirs(root)

    def g(*a):
        return subprocess.run(["git", "-C", root, *a], env=env, capture_output=True, text=True)
    for name, text in (("o.md", "o\n"), ("v.md", "0\n")):
        with open(os.path.join(root, name), "w", encoding="utf-8") as fh:
            fh.write(text)
    g("init", "-q", "-b", "main")
    g("add", ".")
    g("commit", "-q", "-m", "0")
    g("checkout", "-q", "-b", "feature")
    for k in range(1, steps + 1):
        with open(os.path.join(root, "v.md"), "w", encoding="utf-8") as fh:
            fh.write(f"{k}\n")
        g("commit", "-q", "-am", str(k))
    commits = g("rev-list", "--reverse", "main..feature").stdout.split()
    g("checkout", "-q", "main")
    done = threading.Event()

    def resets():
        while not done.is_set():
            g(*form)
    t = threading.Thread(target=resets)
    t.start()
    for c in commits:
        g("merge", "-q", "--ff-only", c)
    done.set()
    t.join()
    log = g("reflog", "--format=%H %gs", "HEAD").stdout.splitlines()
    back = sum(1 for k, e in enumerate(log[:-1])
               if e.split(" ", 1)[1].startswith("reset:") and log[k + 1].split()[0] != e.split()[0])
    logged = sum(1 for e in log if e.split(" ", 1)[1].startswith("reset:"))
    print(f"git {' '.join(form)}: {steps} merges; {logged} resets in the reflog, {back} of them moved HEAD back")
