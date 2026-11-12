#!/usr/bin/env python3
"""
tools/land.py

Every commit and every landing, one procedure (Board #85 A, step 2; design-study/STEP-LANDING-SCRIPT-PLAN.md, its
section 10 the review's list; girsa-architect's answers in STEP-LANDING-SCRIPT-ARCHITECT.md). The rules it follows were
written in five places and done by hand, or by three scripts each with its own file list (Lesson 60); here they are
steps, each a git or tool call whose return code is read, and the Board's hold released on every exit - a stop's
SIGTERM, or SIGHUP, included (M07 item 6; notes/PLAN-LAND-SIGNAL.md).

  ./venv/bin/python tools/land.py commit ROLE notes|code -F MESSAGE NAME... [--tests "PYTEST ARGS"] [--because "WORDS"]
  ./venv/bin/python tools/land.py land ROLE notes|code [--plan PLAN] [--accept FILE::NAME...] [--because WORDS]
  ./venv/bin/python tools/land.py check-conflict FILE... [--accept NAME...]
  ./venv/bin/python tools/land.py gate [--set landing|rebuild|after-apply] [--tree DIR]

`commit`: the index empty first; the NAMEs staged and compared; the lane check (`--doc-only` for notes); on a branch,
the tests `--tests` names; in the main tree (girsa-operator's alone) the landing gate under the Board's hold; the
message's times checked by the role guard's own function; HEAD unmoved; `git commit -F`.
`land` (in a worktree): a code landing of girsa-builder names its plan (`--plan`, committed); the hold (code); the
rebase as its own step - stopped, the rule printed; every commit the rebase replayed checked against the three versions
git merged it from, however the rebase was continued; the base on main's tip; the range's lane check, with the plan
(`check_lane.py --plan`: its `## The case`); the landing gate (code); `git merge --ff-only` in the main clone; then the
gate again on a frozen copy of the main clone with the live rulings file (code); the hold released.
`check-conflict`: at a stopped rebase, each resolved file compared statement by statement with the three versions git
is merging, before it is continued. `gate`: the one home of the gate's file lists.

Standard library only, git and the repository's tools by subprocess, nothing from pipeline/ imported: a landing tool
must not depend on the code it lands. Exit 0 done, 1 a red gate, 2 refused.
"""
import argparse
import ast
import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile

import config

HERE = os.path.dirname(os.path.abspath(__file__))
# THE PROJECT'S OWN (its .claude/mishmeret.json, `land`): the operator, the role whose code landing names its plan, the
# verifier a code round goes back to, the lane check run at each commit and landing (the project's path to it), the
# live rulings file copied into the frozen gate, and what a running review server loads (`server_loads`: its entry,
# the folders whose modules it may import - the first first - and the page's folder)
_CFG = config.load()
_LAND = _CFG["land"]
OPERATOR = _CFG["operator"]
BUILDER = _LAND["planned"]
VERIFIER = _LAND["verifier"]
LANE_CHECK = _LAND["lane_check"]
LEDGER = _LAND.get("ledger")        # absent (config.OPTIONAL): no live file is copied into the frozen gate
SERVER = _LAND.get("server")        # absent: a repository with no review server - nothing it loads, nothing to restart
SERVER_CODE_FOLDERS = tuple(SERVER["folders"]) if SERVER else ()

# THE GATE'S LISTS, their one home (in Girsa: START_HERE, LANES.md, two scripts and a test header each wrote the five
# out; no test pinned them) - the project's `land.gate_sets`, each set's environment (`gate_env`), and the test files no
# gate runs, each with why (`hand_run`; a new test file is in a set or there, or the project's test fails)
GATE_SETS = _LAND["gate_sets"]
GATE_ENV = _LAND["gate_env"]
HAND_RUN = _LAND["hand_run"]


class Refused(Exception):
    """A step that must not go on: its sentence, exit 2."""


class Red(Exception):
    """A gate that failed: exit 1."""


def git(cwd, *args):
    return subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True)


def said(cwd, *args):
    """git's answer, stripped; refused where git fails."""
    run = git(cwd, *args)
    if run.returncode != 0:
        raise Refused(f"git {' '.join(args)}: {(run.stderr or run.stdout).strip()}")
    return run.stdout.strip()


# THE TOOLS IT CALLS, one function each - the tests replace these, so what the script does with their answers is what
# they test
def lane_check(repo, role, doc_only=False, rng=None, because=None, plan=None):
    cmd = [sys.executable, os.path.join(repo, LANE_CHECK), role]
    cmd += ["--doc-only"] * doc_only + (["--range", rng] if rng else []) + (["--because", because] if because else [])
    cmd += ["--plan", plan] if plan else []
    run = subprocess.run(cmd, cwd=repo, capture_output=True, text=True)
    return run.returncode, (run.stdout + run.stderr).strip()


def unworded(top, role, rng, because):
    """THE REVIEWER'S WORDS AT A LANDING COVER ONLY THE COMMITS MADE UNDER THEM (the Mishmeret move's step 2, Board #114
    A: `commit --because` passed, and `land` had no way to say the same of the range): the commits of `rng` that go
    outside ROLE's lane on their own lane check and do not carry `The reviewer's words: BECAUSE`, which `commit
    --because` writes - so the words at the landing never reach a commit that was not made under them. The line is
    compared whole (girsa-verifier's LOW 2 on 0e730ccf: as a substring, words that began another commit's covered it)."""
    bare = []
    for c in said(top, "rev-list", "--reverse", rng).split():
        if f"The reviewer's words: {because}" in said(top, "log", "-1", "--format=%B", c).splitlines():
            continue
        if lane_check(top, role, rng=f"{c}^..{c}")[0]:
            bare.append(c[:8])
    return bare


def board(repo, *args):
    run = subprocess.run([sys.executable, os.path.join(HERE, "board.py"), *args], cwd=repo,      # this package's Board
                         capture_output=True, text=True)
    return run.returncode, (run.stdout + run.stderr).strip()


def run_gate(tree, name):
    """The gate set `name` in the folder `tree`: pytest's exit status, its last line printed."""
    env = dict(os.environ, **GATE_ENV.get(name, {}))
    log = tempfile.NamedTemporaryFile("w+", encoding="utf-8", suffix=".log", delete=False)
    with log:
        run = subprocess.run([sys.executable, "-m", "pytest", *GATE_SETS[name], "-q", "-p", "no:cacheprovider"],
                             cwd=tree, env=env, stdout=log, stderr=subprocess.STDOUT)
    with open(log.name, encoding="utf-8", errors="replace") as fh:
        lines = fh.read().strip().splitlines()
    print(f"  gate ({name}) in {tree}: exit {run.returncode}: {lines[-1] if lines else 'no output'}")
    if run.returncode:
        print("".join(f"    {line}\n" for line in lines if line.startswith("FAILED"))[:4000], end="")
        print(f"  the whole log: {log.name}")
    else:
        os.unlink(log.name)
    return run.returncode


def time_refusal(text, now=None):
    """The role guard's own check of a written time (`future_time_refusal`), on a message the guard never sees - a
    file the script commits (girsa-architect's Q7). `now` is the clock's, or a test's fixed one. The guard is this
    package's own (until the move, the main tree's copy, loaded by path)."""
    import role_guard
    return role_guard.future_time_refusal(text, now)


class Where:
    """Which tree the command runs in, read from git: its top, its git folder, the main clone and its branch."""

    def __init__(self, cwd):
        self.top = os.path.realpath(said(cwd, "rev-parse", "--show-toplevel"))
        self.git_dir = os.path.realpath(said(cwd, "rev-parse", "--absolute-git-dir"))
        common = said(cwd, "rev-parse", "--git-common-dir")
        common = os.path.realpath(common if os.path.isabs(common) else os.path.join(self.top, common))
        self.main_tree = os.path.dirname(common)
        self.in_main = self.top == self.main_tree
        self.main_branch = said(self.main_tree, "symbolic-ref", "--short", "HEAD")


def session_refusal(role, where, verb):
    """Why ROLE may not run this, or None (girsa-verifier's MEDIUM 1: the guard never sees the git this script runs, so
    the role is the session's own, never an argument's alone). `$CLAUDE_CODE_AGENT` is the agent a role session was
    started as; the role guard refuses a command that sets it (girsa-operator's, Board #86)."""
    agent = os.environ.get("CLAUDE_CODE_AGENT")
    if not agent:
        return "this is no role's session ($CLAUDE_CODE_AGENT is not set): land.py commits and lands for a role"
    if agent != role:
        return f"this session is {agent}, not {role}: a role commits and lands as itself"
    if where.in_main and (verb != "commit" or role != OPERATOR):
        return (f"the main tree is {OPERATOR}'s alone, and it only commits there"
                if verb == "commit" else "land runs in a role's worktree, never in the main tree")
    return None


def _staged(cwd):
    return sorted(filter(None, said(cwd, "diff", "--cached", "--name-only", "--no-renames").split("\n")))


def commit(role, kind, message, names, tests=None, because=None, cwd="."):
    where = Where(cwd)
    refusal = session_refusal(role, where, "commit")
    if refusal:
        raise Refused(refusal)
    if _staged(where.top):
        raise Refused(f"the index already holds {', '.join(_staged(where.top))} - stage nothing by hand: name the "
                      f"files here, and nothing of another's is swept in")
    head = said(where.top, "rev-parse", "HEAD")
    with open(message, encoding="utf-8") as fh:
        text = fh.read().strip()
    if because:
        text = f"{text}\n\nThe reviewer's words: {because}"
    refusal = time_refusal(text)
    if refusal:
        raise Refused(refusal)
    added = git(where.top, "add", "--", *names)
    try:
        if added.returncode != 0:
            raise Refused(f"git add: {added.stderr.strip()}")
        staged = _staged(where.top)
        if staged != sorted(set(names)):
            raise Refused(f"staged {staged}, named {sorted(set(names))} - a name that is ignored, unchanged or "
                          f"misspelt stages nothing")
        rc, output = lane_check(where.top, role, doc_only=kind == "notes", because=because)
        print(output)
        if rc:
            raise Refused("the lane check refused")
        if kind == "code" and where.in_main:
            _held(where.main_tree, role, "a code commit in the main tree", lambda: _gated(where.top))
        elif kind == "code" and tests:
            run = subprocess.run([sys.executable, "-m", "pytest", *shlex.split(tests), "-q", "-p", "no:cacheprovider"],
                                 cwd=where.top)
            if run.returncode == 5:                 # pytest's "no tests collected" (found by the plan's rehearsal)
                raise Refused(f"--tests {tests!r} collected no test: name the tests the change touches")
            if run.returncode:
                raise Red(f"the tests named exited {run.returncode}")
        if said(where.top, "rev-parse", "HEAD") != head or _staged(where.top) != staged:
            raise Refused("HEAD or the staged names moved while the checks ran")
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", suffix=".txt", delete=False) as fh:
            fh.write(text + "\n")
        try:
            done = git(where.top, "commit", "-q", "-F", fh.name)
        finally:
            os.unlink(fh.name)
        if done.returncode != 0:
            raise Refused(f"git commit: {(done.stderr or done.stdout).strip()}")
    except BaseException:
        git(where.top, "reset", "-q")                     # the index was empty before: nothing of another's unstaged
        raise
    print(f"  committed {said(where.top, 'log', '--oneline', '-1')}")


def _gated(tree, name="landing"):
    if run_gate(tree, name):
        raise Red(f"the {name} gate is red in {tree}")


def _held(main_tree, role, why, step):
    """`step` run under the Board's hold for ROLE, released on every exit."""
    rc, output = board(main_tree, "hold", "--role", role, "--why", why)
    print(f"  {output}")
    if rc:
        raise Refused("the Board refused the hold")
    try:
        return step()
    finally:
        rc, output = board(main_tree, "release", "--role", role)
        print(f"  {output}")


STAMP = "land-rebase.json"


# GIRSA-BUILDER'S CODE LANDING NAMES ITS PLAN (Board Q&A #62, gate 1, the reviewer's "go" of 2026-10-27, through
# girsa-operator: C11 was built and landed for stop marks no one could make, and no tool read its case). The range's
# lane check runs with it, so check_lane.py --plan reads its `## The case` at each such landing. The builder's alone
# (Board #99, the reviewer's "99 B"): the other roles' code landings, and any notes landing, need none - a plan they name
# is checked the same way; girsa-operator's same-day fixes are commits in the main tree, never a landing.
def named_plan(where, cwd, plan):
    """PLAN as a path in the worktree, committed at HEAD - refused when there is none."""
    if not plan:
        raise Refused(f"a code landing of {BUILDER} names its plan: --plan PLAN, the plan whose `## The case` this "
                      f"work serves (Board Q&A #62, gate 1; #99 B); a round on {VERIFIER}'s findings names its "
                      "piece's plan")
    rel = os.path.relpath(os.path.realpath(os.path.join(cwd, plan)), where.top)
    if git(where.top, "cat-file", "-e", f"HEAD:{rel}").returncode != 0:      # outside the tree too
        raise Refused(f"no plan at {plan} in the branch's HEAD: a plan is committed before its landing")
    return rel


def land(role, kind, cwd=".", accept=(), plan=None, because=None):
    where = Where(cwd)
    refusal = session_refusal(role, where, "land")
    if refusal:
        raise Refused(refusal)
    if (kind == "code" and role == BUILDER) or plan:
        plan = named_plan(where, cwd, plan)
    if _rebasing(where):                # before the branch is read: mid-rebase, HEAD names no branch (the rehearsal)
        raise Refused("a rebase is still in progress: check the conflicts (land.py check-conflict), `git rebase "
                      "--continue`, then land again")
    branch = said(where.top, "symbolic-ref", "--short", "HEAD")
    if branch == where.main_branch:
        raise Refused(f"{branch} is the main branch: land a branch of your own")
    if said(where.top, "status", "--porcelain", "--untracked-files=no"):
        raise Refused("the worktree has uncommitted changes: commit them (land.py commit) or set them aside in a patch")
    if kind == "code":
        subject = said(where.top, "log", "-1", "--format=%s")[:120]
        named = f" (plan {plan})" if plan else ""            # the plan where every role reads it (girsa-verifier's LOW 1)
        copy = tempfile.mkdtemp(prefix=f"{_CFG['project'].lower()}-land-")      # for the frozen gate
        try:
            return _held(where.main_tree, role, f"{branch}{named}: {subject}",
                         lambda: _landing(role, kind, where, branch, accept, plan, because, copy))
        finally:    # after the release: a stop's grace before SIGKILL is ~1.5 s, a big clone's removal longer
            shutil.rmtree(copy, ignore_errors=True)
    return _landing(role, kind, where, branch, accept, plan, because)


def _landing(role, kind, where, branch, accept=(), plan=None, because=None, copy=None):
    tip = said(where.main_tree, "rev-parse", where.main_branch)
    # EVERY REPLAY CHECKED, HOWEVER IT WAS CONTINUED (girsa-verifier's MEDIUM 1 on the build: a stamp of the stop's files
    # failed open - a finished rebase onto a main that moved since looked like one taken back, and a second stop met by
    # a bare `git rebase --continue` was stamped by nothing). The stamp names the branch before its rebase and what it
    # was rebased onto; while HEAD holds that, every commit the rebase replayed is checked against the three versions
    # git merged it from (`replay_faults`), before a further rebase. A rebase that finishes in this call stopped nowhere,
    # so nothing in it was resolved by hand (its check after it was inert: a mutation removing it stayed green).
    stamp = _stamp(where)
    if stamp is not None and stamp.get("clean"):
        # A CLEAN STAMP (the last call's rebase finished, nothing resolved by hand) is dropped while the branch still
        # sits on what it was rebased onto - an amend since is no replay - and checked from there when a rebase run by
        # hand has moved it since (girsa-verifier's LOW 2 on step 3: a dropped stamp left such a rebase unchecked)
        onto = said(where.top, "merge-base", "HEAD", where.main_branch)
        stamp = None if onto == stamp["onto"] else dict(stamp, onto=onto)
    for file, names in _accepted(accept).items():
        if stamp is not None:
            stamp["accept"].setdefault(file, []).extend(names)
    if stamp is not None:
        _refuse_faults(where, stamp)
    stamp = {"before": said(where.top, "rev-parse", "HEAD"), "onto": tip,
             "accept": (stamp or {}).get("accept") or _accepted(accept)}
    _write_stamp(where, stamp)
    rebased = git(where.top, "rebase", where.main_branch)
    if rebased.returncode != 0:
        conflicted = sorted(filter(None, said(where.top, "diff", "--name-only", "--diff-filter=U").split("\n")))
        if not conflicted:
            raise Refused(f"the rebase stopped: {(rebased.stderr or rebased.stdout).strip()}")
        raise Refused("the rebase stopped on a conflict in " + ", ".join(conflicted) + ". Resolve each file, check it "
                      "(`land.py check-conflict " + " ".join(shlex.quote(f) for f in conflicted) + "`; a "
                      "conflict resolved by keeping both sides is checked function by function), `git add` them, "
                      "`git rebase --continue`, and land again - the landing checks every replayed commit itself. A "
                      f"code round goes back to {VERIFIER}.")
    if said(where.top, "merge-base", "HEAD", where.main_branch) != tip:
        raise Refused(f"the branch is not on {where.main_branch}'s tip after the rebase")
    # finished here, it stopped nowhere, and an earlier stop's replays were checked above: the stamp is marked clean
    # now, so a commit amended after a later refusal (the words, the lane, the gate) is not taken for one reworded at a
    # stop (the Mishmeret move's step 3: an unworded commit amended with the words was refused so), while a rebase run
    # by hand before the next call is still checked (above)
    _write_stamp(where, {"before": said(where.top, "rev-parse", "HEAD"), "onto": tip, "accept": {}, "clean": True})
    if because:
        bare = unworded(where.top, role, f"{tip}..HEAD", because)
        if bare:
            raise Refused(f"--because {because!r} covers only the commits made under it (`commit --because` writes the "
                          f"reviewer's words into each); outside the lane without them: {', '.join(bare)}")
    rc, output = lane_check(where.top, role, doc_only=kind == "notes", rng=f"{tip}..HEAD", because=because,
                            plan=plan)
    print(output)
    if rc:
        raise Refused("the lane check refused the range")
    head = said(where.top, "rev-parse", "HEAD")
    if kind == "code":
        _gated(where.top)
    if said(where.top, "rev-parse", "HEAD") != head or said(where.main_tree, "rev-parse", where.main_branch) != tip:
        raise Refused(f"HEAD or {where.main_branch} moved while the gate ran: land again")
    merged = git(where.main_tree, "merge", "--ff-only", branch)
    if merged.returncode != 0 or git(where.main_tree, "merge-base", "--is-ancestor", head,
                                     where.main_branch).returncode != 0:
        raise Refused(f"git merge --ff-only refused: {(merged.stderr or merged.stdout).strip()}")
    os.unlink(os.path.join(where.git_dir, STAMP))       # landed: nothing of this branch's rebases is left to check
    print(f"  LANDED {tip[:8]}..{head[:8]} on {where.main_branch}:")
    print("".join(f"    {line}\n" for line in said(where.top, "log", "--oneline", f"{tip}..{head}").split("\n")), end="")
    changed = set(filter(None, said(where.top, "diff", "--name-only", tip, head).split("\n")))
    loads = server_loads(where.top)
    restart = sorted(p for p in changed if p in loads or (SERVER and p.startswith(SERVER["page"])))
    print(f"  the servers load: {'restart - ' + ', '.join(restart) if restart else 'none of it changed'}")
    if kind == "code":
        _frozen_gate(where, copy)
    return head


def _accepted(accept):
    """{file: [statement names]} from `--accept FILE::NAME` (a statement compared by hand) or `--accept FILE` (a file
    that is not Python, compared by hand: "*"); `--accept dropped:COMMIT` (a commit the rebase left out on purpose,
    named by its original's id) is kept under that key."""
    out = {}
    for item in accept:
        file, _sep, name = item.partition("::")
        out.setdefault(file, []).append(name or "*")
    return out


def _stamp(where):
    """The stamp of this branch's last rebase while HEAD still holds what it was rebased onto, else None - a branch taken
    back before its rebase has nothing replayed to check, and its old stamp is dropped."""
    path = os.path.join(where.git_dir, STAMP)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        stamp = json.load(fh)
    if git(where.top, "merge-base", "--is-ancestor", stamp["onto"], "HEAD").returncode != 0:
        os.unlink(path)
        return None
    return stamp


def _write_stamp(where, stamp):
    with open(os.path.join(where.git_dir, STAMP), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(stamp, fh, indent=1)


def _refuse_faults(where, stamp):
    faults = replay_faults(where.top, stamp["before"], stamp["onto"], stamp.get("accept") or {})
    if faults:
        raise Refused("a replayed commit holds a resolution its three versions do not give:\n" + "\n".join(
            f"    {commit[:8]} {file}: {key}: {why}" for commit, file, key, why in faults) + "\nFix it - take the "
            f"branch back (`git reset --hard {stamp['before'][:8]}`) and land again - or, for what was compared by "
            "hand, land with `--accept FILE::NAME` (a file that is not Python: `--accept FILE`; a commit left out on "
            "purpose: `--accept dropped:COMMIT`, its id as named above).")


def replay_faults(top, before, onto, accept=None):
    """[(commit, file, statement, why)]: for every commit the rebase of `before` onto `onto` replayed (onto..HEAD, each
    matched to its original by author, date and subject), the files git could not merge cleanly - asked again of git
    (`merge-tree` with the original's parent as base, the replay's parent as ours, the original as theirs) - and, in
    each, what the replay holds against the three-way rule (`merged_statement_faults`)."""
    accept = accept or {}
    key = lambda c: said(top, "log", "-1", "--format=%aI%x00%ae%x00%s", c)
    fork = said(top, "merge-base", before, onto)
    originals = {key(c): c for c in said(top, "rev-list", f"{fork}..{before}").split()}
    show = lambda rev, name: (lambda run: run.stdout if run.returncode == 0 else None)(git(top, "show", f"{rev}:{name}"))
    faults = []
    replays = said(top, "rev-list", "--reverse", f"{onto}..HEAD").split()
    matched = {key(r) for r in replays}
    # A COMMIT THE REBASE LEFT OUT (found writing the test of (a)): a stop resolved to what main holds leaves the
    # replay empty, and git drops it - right where its change is already in the branch, a lost change where it is not
    head_tree = said(top, "rev-parse", "HEAD^{tree}")
    # A DROPPED COMMIT IS NAMED BY ONE ORIGINAL'S ID, 7 characters at least (girsa-verifier's LOW on the LOWs round:
    # `dropped:1` took every left-out original whose id starts with 1)
    dropped = set()
    for d in (k[len("dropped:"):] for k in accept if k.startswith("dropped:")):
        named = [c for c in originals.values() if c.startswith(d)]
        if len(d) >= 7 and len(named) == 1:
            dropped.add(named[0])
        else:
            faults.append((d or "(no id)", "(the accept)", f"dropped:{d}", f"names {len(named)} of the branch's "
                           "commits - give one commit's id as named above, 7 characters at least"))
    left_out = [c for k, c in originals.items() if k not in matched and c not in dropped]   # not dropped on purpose
    for original in left_out:
        kept = git(top, "merge-tree", "--write-tree", "--merge-base", f"{original}^", "HEAD", original)
        if kept.returncode != 0 or kept.stdout.split("\n")[0].strip() != head_tree:
            faults.append((original, "(the commit)", "left out by the rebase", "the branch does not hold its change"))
    # A REPLAY REWORDED AT ITS STOP (girsa-verifier's LOW 1 on the round, its case B): a new message matches no
    # original, so the replay would pass for new work and its original for one whose change the branch holds - while an
    # original is left out, a replay that matches none cannot be checked, and is refused
    unmatched = [r for r in replays if key(r) not in originals]
    if left_out and unmatched:
        faults += [(r, "(the commit)", "matches no original while one was left out",
                    "a commit reworded at its stop cannot be checked: take the branch back and land again, keeping "
                    "each message") for r in unmatched]
    for replay in replays:
        original = originals.get(key(replay))
        if original is None or original == replay:
            continue                    # a commit made after the rebase, or one the rebase did not move
        merged = git(top, "merge-tree", "--write-tree", "--name-only", "--merge-base", f"{original}^", f"{replay}^",
                     original)
        if merged.returncode not in (0, 1):
            raise Refused(f"git merge-tree: {(merged.stderr or merged.stdout).strip()}")
        if merged.returncode == 0:
            continue
        files = []
        for line in merged.stdout.split("\n")[1:]:
            if not line:
                break
            files.append(line)
        for file in files:
            allowed = accept.get(file, [])
            if not file.endswith(".py"):
                if "*" not in allowed:
                    faults.append((replay, file, "(the file)", "not Python: compared by hand, then --accept " + file))
                continue
            for k, why in merged_statement_faults(show(f"{original}^", file), show(f"{replay}^", file),
                                                  show(original, file), show(replay, file), allowed):
                faults.append((replay, file, k, why))
    return faults


def _frozen_gate(where, copy):
    """The gate in main after a code landing, on a frozen copy of the main clone with the live rulings file
    (girsa-architect's Q4; girsa-verifier's landing_rerun.sh's learnt rules 8 and 12): nothing written into the main
    tree, no Save raced. Red: the merge stands, and the fix is the lander's. `copy`: an empty folder, removed by
    `land` after the hold is released (girsa-verifier's MEDIUM 1 on PLAN-LAND-SIGNAL.md)."""
    tree = os.path.join(copy, "main")
    if sys.platform == "darwin":
        subprocess.run(["cp", "-c", "-R", where.main_tree, tree], check=True)        # APFS: a clone, instant
    else:
        shutil.copytree(where.main_tree, tree, symlinks=True)                        # untried on Linux (0II)
    # the copy carries the main clone's INDEX, so a reset to HEAD, not `checkout -- .`; then the live rulings in
    said(tree, "reset", "-q", "--hard", "HEAD")
    live = LEDGER and os.path.join(where.main_tree, LEDGER)
    if live and os.path.exists(live):
        shutil.copyfile(live, os.path.join(tree, LEDGER))
        with open(live, "rb") as a, open(os.path.join(tree, LEDGER), "rb") as b:
            if a.read() != b.read():
                raise Refused(f"the live ledger ({LEDGER}) changed while it was copied: gate main again")
    if run_gate(tree, "landing"):
        raise Red("LANDED, and the gate on main is red - the fix is yours")


def _rebasing(where):
    return any(os.path.isdir(os.path.join(where.git_dir, d)) for d in ("rebase-merge", "rebase-apply"))


# CHECK-CONFLICT: three-way, per top-level statement (girsa-verifier's MEDIUM 2). The base is the replayed commit's
# parent (REBASE_HEAD^), "ours" HEAD, "theirs" REBASE_HEAD - the three versions git itself merged.
def statements(source):
    """{key: ast dump} of a module's top-level statements: a function or class by its name, an assignment by its targets,
    any other statement by its own text; a repeat keyed with its count."""
    out = {}
    for node in ast.parse(source).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            key = node.name
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            key = "= " + ", ".join(ast.unparse(t) for t in targets)
        else:
            key = ast.unparse(node)[:200]
        n, base = 1, key
        while key in out:
            n += 1
            key = f"{base} ({n})"
        out[key] = ast.dump(node)
    return out


def merged_statement_faults(base, ours, theirs, resolved, accept=()):
    """[(key, why)]: each statement the resolved file does not hold as the three-way rule says."""
    b, o, t, r = (statements(s) if s is not None else {} for s in (base, ours, theirs, resolved))
    faults = []
    for key in sorted(set(b) | set(o) | set(t) | set(r)):
        bk, ok, tk, rk = b.get(key), o.get(key), t.get(key), r.get(key)
        if ok == tk:
            want = ok
        elif ok == bk:
            want = tk
        elif tk == bk:
            want = ok
        else:
            if key not in accept:
                faults.append((key, "changed on both sides (or deleted against changed): compare it by hand, then "
                                    "--accept it"))
            continue
        if rk != want:
            faults.append((key, "absent, where the merge keeps it" if rk is None else
                          "present, where one side deleted it and the other left it" if want is None else
                          "differs from the side that changed it"))
    return faults


def check_conflict(files, accept=(), cwd="."):
    """At a stopped rebase, each resolved file against the three versions git is merging (REBASE_HEAD^, HEAD,
    REBASE_HEAD) - said before `git rebase --continue`, so a wrong resolution is fixed at its stop; what `--accept`
    names (a statement, or a file that is not Python) is kept in the stamp for the landing, which checks every replayed
    commit again itself (`replay_faults`)."""
    where = Where(cwd)
    if not os.path.exists(os.path.join(where.git_dir, "REBASE_HEAD")):
        raise Refused("no rebase is stopped here (no REBASE_HEAD)")
    show = lambda rev, name: (lambda run: run.stdout if run.returncode == 0 else None)(
        git(where.top, "show", f"{rev}:{name}"))
    stamp_path = os.path.join(where.git_dir, STAMP)
    stamp = None
    if os.path.exists(stamp_path):
        with open(stamp_path, encoding="utf-8") as fh:
            stamp = json.load(fh)
    red = False
    for name in files:
        with open(os.path.join(where.top, name), encoding="utf-8") as fh:
            resolved = fh.read()
        if not name.endswith(".py"):
            faults = [] if name in accept else [("(the file)", f"not Python - compare it by hand, then --accept {name}")]
            accepted = ["*"] if name in accept else []
        else:
            faults = merged_statement_faults(show("REBASE_HEAD^", name), show("HEAD", name), show("REBASE_HEAD", name),
                                             resolved, accept)
            accepted = [a for a in accept if a != name]
        for key, why in faults:
            print(f"  {name}: {key}: {why}")
        red = red or bool(faults)
        if not faults:
            print(f"  {name}: green")
        if stamp is not None and accepted:
            stamp.setdefault("accept", {}).setdefault(name, []).extend(accepted)
    if stamp is not None:
        _write_stamp(where, stamp)
    if red:
        raise Red("a resolved file is not what the three versions say")


def server_loads(repo):
    """{repository path}: what a running review server loads - review_server.py, the modules it imports, directly or
    through another, and the files it loads by path (`spec_from_file_location`: tools/export_corpus.py since 4194d974).
    START_HERE's restart rule is held to this by a test; a landing that changes one says "restart" (girsa-verifier's
    LOW 1 on this plan: one computation, not a second list).
    AN IMPORT IS LOOKED FOR IN EVERY CODE FOLDER, not pipeline/ alone: the server and the exporter put citations/ on
    sys.path for the notes' references, and its module went unseen until 959e1e23's landing said "none of it changed"
    (2026-10-27). A name in two folders counts both - a restart too many costs less than one missed."""
    if not SERVER or not os.path.isfile(os.path.join(repo, SERVER["entry"])):
        return set()                                    # a repository with no review server
    local = {}
    for folder in SERVER_CODE_FOLDERS:
        if os.path.isdir(os.path.join(repo, folder)):
            for f in sorted(os.listdir(os.path.join(repo, folder))):
                if f.endswith(".py"):
                    local.setdefault(f[:-3], []).append(f"{folder}/{f}")
    loads, frontier = {SERVER["entry"]}, [SERVER["entry"]]
    while frontier:
        path = frontier.pop()
        with open(os.path.join(repo, path), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        for node in ast.walk(tree):
            found = []
            if isinstance(node, ast.Call) and getattr(node.func, "attr", getattr(node.func, "id", None)) \
                    == "spec_from_file_location":
                parts = [c.value for a in node.args[1:] for c in ast.walk(a)
                         if isinstance(c, ast.Constant) and isinstance(c.value, str)]
                if not (parts and parts[-1].endswith(".py")):
                    raise ValueError(f"a load by path in {path} that cannot be read: {ast.unparse(node)}")
                found = ["/".join(parts)]
            elif isinstance(node, ast.Import):
                found = [f for a in node.names for f in local.get(a.name.split(".")[0], ())]
            elif isinstance(node, ast.ImportFrom) and node.module:
                found = local.get(node.module.split(".")[0], [])
            for f in found:
                if f not in loads:
                    loads.add(f)
                    frontier.append(f)
    return loads


def _exit_on_signals():
    """SIGTERM (a stop: Claude Code's, to the command's group, SIGKILL ~1.5 s after) and SIGHUP end land.py as an exit
    does, so every `finally` and `except BaseException` runs - the hold released, the index reset. Their default ends
    the process at once: a stopped `land.py commit` had left the hold and its staged names (M07 item 6)."""
    signals = [s for s in (signal.SIGTERM, getattr(signal, "SIGHUP", None)) if s]     # no SIGHUP on Windows

    def ended(signum, frame):
        for s in signals:               # a second signal must not cut the cleanup short (girsa-verifier's LOW 3)
            signal.signal(s, signal.SIG_IGN)
        raise SystemExit(128 + signum)
    for s in signals:
        signal.signal(s, ended)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="verb", required=True)
    c = sub.add_parser("commit")
    c.add_argument("role")
    c.add_argument("kind", choices=("notes", "code"))
    c.add_argument("-F", dest="message", required=True, help="the commit message's file")
    c.add_argument("names", nargs="+")
    c.add_argument("--tests", help="on a branch, the tests the change touches (pytest's arguments)")
    c.add_argument("--because", help="the reviewer's words giving this work to ROLE outside its lane")
    lnd = sub.add_parser("land")
    lnd.add_argument("role")
    lnd.add_argument("kind", choices=("notes", "code"))
    lnd.add_argument("--plan", help=f"the plan this landing serves, committed - {BUILDER}'s code needs one "
                                    "(Board Q&A #62, #99 B)")
    lnd.add_argument("--accept", action="append", default=[], metavar="FILE::NAME",
                     help="a replayed statement compared by hand (a file that is not Python: FILE)")
    lnd.add_argument("--because", help="the reviewer's words the range's commits outside ROLE's lane were made under")
    k = sub.add_parser("check-conflict")
    k.add_argument("files", nargs="+")
    k.add_argument("--accept", action="append", default=[], help="a statement or a file compared by hand")
    g = sub.add_parser("gate")
    g.add_argument("--set", dest="name", choices=sorted(GATE_SETS), default="landing")
    g.add_argument("--tree", default=".")
    args = ap.parse_args(argv)
    _exit_on_signals()
    try:
        if args.verb == "commit":
            commit(args.role, args.kind, args.message, args.names, args.tests, args.because)
        elif args.verb == "land":
            land(args.role, args.kind, accept=args.accept, plan=args.plan, because=args.because)
        elif args.verb == "check-conflict":
            check_conflict(args.files, args.accept)
        else:
            return 1 if run_gate(os.path.realpath(args.tree), args.name) else 0
    except Refused as e:
        print(f"REFUSED: {e}")
        return 2
    except Red as e:
        print(f"RED: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
