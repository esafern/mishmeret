"""Git's reference-transaction hook (notes/PLAN-REF-HOOK.md), measured as the plan measured it: a scratch project made as
a pinning project is - its main clone with the real shim and a config, the tree under test as its pin, a bare origin,
the builder's, the verifier's and the demo operator's worktrees, `guard.refs` giving `known-good` and `alpha-rc*` to the
operator and `demo-good` to the demo operator, `guard.main` naming main - the hook installed by the shim; each command
run as its role, set in-process (the suite's way: the guard refuses a command line that sets the variable)."""
import os
import shutil
import subprocess
import sys

import pytest

from conftest import HERE, PKG, project_config

SHA = "1" * 40
ROOT_DIR = os.path.dirname(HERE)


def _git(cwd, *a, env=None):
    return subprocess.run(["git", "-C", cwd, *a], check=True, capture_output=True, text=True, env=env).stdout.strip()


@pytest.fixture(scope="module")
def live(tmp_path_factory):
    import json
    L = str(tmp_path_factory.mktemp("ref-hook"))
    os.makedirs(os.path.join(L, "mm", ".pins", SHA))
    os.symlink(PKG, os.path.join(L, "mm", ".pins", SHA, "mishmeret"))
    B = os.path.join(L, "book")
    os.makedirs(os.path.join(B, ".claude", "hooks"))
    os.makedirs(os.path.join(B, "tests"))
    cfg = project_config(L, mishmeret_commit=SHA, python=sys.executable)
    for r in cfg["roles"]:
        r["worktrees"] = {"ex-builder": [os.path.join(L, "book-builder")],
                          "ex-verifier": [os.path.join(L, "book-verifier")],
                          "ex-demo-operator": [os.path.join(L, "book-demo")]}.get(r["name"], [])
    cfg["guard"] = {"fallback_roots": [os.path.join(L, "no-book")], "trees": [os.path.join(L, "mm")],
                    "retired_remotes": [], "checks": ["pytest"], "main": "main",
                    "refs": {"refs/tags/known-good": "ex-operator", "refs/tags/alpha-rc*": "ex-operator",
                             "refs/tags/demo-good": "ex-demo-operator"}}
    cfg["land"] = {"planned": "ex-builder", "verifier": "ex-verifier", "lane_check": ".claude/lane_check.py",
                   "gate_sets": {"landing": ["tests/"]}, "gate_env": {}, "hand_run": {}}
    del cfg["drafts"]
    with open(os.path.join(B, ".claude", "mishmeret.json"), "w", encoding="utf-8") as fh:
        json.dump(cfg, fh)
    for name in ("mishmeret_shim.py", "land.py"):
        shutil.copy(os.path.join(ROOT_DIR, ".claude", name), os.path.join(B, ".claude", name))
    files = {".claude/hooks/ref_hook.py": 'import os\nimport sys\n\nsys.path.insert(0, os.path.join(os.path.dirname('
                                          'os.path.abspath(__file__)), ".."))\nimport mishmeret_shim  # noqa: E402\n\n'
                                          'mishmeret_shim.stand_in(__name__, ".claude/hooks/ref_hook.py", "ref_hook", '
                                          '"refuses")\n',
             ".claude/lane_check.py": "import sys\nsys.exit(0)\n", "tests/test_ok.py": "def test_ok():\n    pass\n",
             "plan.md": "# A placeholder plan\n\n## The case\n\nplaceholder\n", "a.txt": "a\n"}
    for name, text in files.items():
        with open(os.path.join(B, name), "w", encoding="utf-8") as fh:
            fh.write(text)
    env = {k: v for k, v in os.environ.items() if not k.startswith(("MISHMERET_", "CLAUDE_", "GIT_"))}
    env.update(MISHMERET_DIR=os.path.join(L, "mm"), GIT_AUTHOR_NAME="placeholder",
               GIT_AUTHOR_EMAIL="placeholder@example.org", GIT_COMMITTER_NAME="placeholder",
               GIT_COMMITTER_EMAIL="placeholder@example.org")
    _git(L, "init", "-q", "--bare", "origin.git")
    _git(L, "init", "-q", "-b", "main", "book")
    _git(B, "add", ".", env=env)
    _git(B, "commit", "-q", "-m", "c1", env=env)
    for tag in (["known-good"], ["-a", "-m", "rc1", "alpha-rc1"], ["demo-good"]):
        _git(B, "tag", *tag, env=env)
    _git(B, "remote", "add", "origin", os.path.join(L, "origin.git"))
    _git(B, "push", "-q", "origin", "main", "--tags", env=env)
    for wt, br in (("book-builder", "builder-x"), ("book-verifier", "verifier-x"), ("book-demo", "demo-x")):
        _git(B, "worktree", "add", "-q", "-b", br, os.path.join(L, wt), env=env)
    run = subprocess.run([sys.executable, os.path.join(B, ".claude", "hooks", "ref_hook.py"), "--install"], cwd=B,
                         capture_output=True, text=True, env=env)
    assert run.returncode == 0, run.stderr
    env.update(L=L, B=B, W=os.path.join(L, "book-builder"), V=os.path.join(L, "book-verifier"),
               D=os.path.join(L, "book-demo"), PY=sys.executable)
    return env


def _refs(env):
    return {r: subprocess.run(["git", "-C", env["B"], "rev-parse", "-q", "--verify", r], capture_output=True,
                              text=True, env=env).stdout.strip() or None
            for r in ("main", "known-good", "alpha-rc1", "demo-good", "builder-x")}


def _run(env, role, where, cmd, more=None):
    """(git's exit status, the refs before, after, the output) of `cmd` run as `role` (None: no role) in `where`."""
    run_env = dict(env, **(more or {}), **({"CLAUDE_CODE_AGENT": role} if role else {}))
    before = _refs(env)
    p = subprocess.run(["bash", "-c", cmd], cwd=env[where] if where in env else where, capture_output=True,
                       text=True, env=run_env)
    return p.returncode, before, _refs(env), p.stdout + p.stderr


OWN = [   # the roles' own work: each let through
    ("ex-builder", "W", "echo b1 > b.txt && git add b.txt && git commit -q -m b1"),
    ("ex-builder", "W", "echo b2 >> b.txt && $PY $B/.claude/land.py commit ex-builder code -F <(echo 'placeholder: b2')"
                        " b.txt --tests tests/"),
    ("ex-builder", "W", "git commit -q --amend -m 'b2 amended' && git fetch -q origin"),
    ("ex-builder", "W", "git switch -q -c builder-tmp && git switch -q builder-x && git branch -q -D builder-tmp"),
    ("ex-builder", "W", "git worktree add -q -b builder-y $L/book-builder2 && git worktree remove $L/book-builder2 && "
                        "git branch -q -D builder-y"),
    ("ex-builder", "W", "git tag my-test && git tag -f my-test HEAD~1 && git tag -d my-test"),
    ("ex-operator", "B", "echo m1 > m.txt && $PY $B/.claude/land.py commit ex-operator notes -F <(echo 'placeholder: "
                         "m1') m.txt"),
    ("ex-builder", "W", "git rebase -q main && for i in 1 2 3; do echo $i >> r.txt; git add r.txt; git commit -q -m r$i;"
                        " done && GIT_SEQUENCE_EDITOR=true git rebase -q -i --force-rebase --exec true main"),
    ("ex-builder", "W", "$PY $B/.claude/land.py land ex-builder code --plan plan.md"),
    ("ex-verifier", "V", "git merge -q --ff-only main && echo v1 > v.txt && git add v.txt && git commit -q -m v1"),
    ("ex-builder", "W", "git gc -q && git pack-refs --all"),
    ("ex-operator", "B", "git push -q origin main && git tag -a -m rc2 alpha-rc2 && git push -q origin alpha-rc2"),
    ("ex-operator", "B", "git tag -f known-good main && git tag -a -m rc3 alpha-rc3 && git pack-refs --all && "
                         "git tag -d alpha-rc3"),
    ("ex-demo-operator", "D", "git tag -f demo-good main"),
    ("ex-operator", "B", "git reset -q --hard HEAD~1 && git merge -q --ff-only builder-x"),
    ("ex-operator", "B", "git replace HEAD $(git rev-list --max-parents=0 HEAD) && git replace -d $(git rev-parse HEAD)"),
    ("ex-verifier", "L", "rm -rf $L/vcopy && cp -R $B $L/vcopy && git -C $L/vcopy reset -q --hard HEAD~1 && "
                         "git -C $L/vcopy tag -f known-good HEAD~1 && git -C $L/vcopy tag -d demo-good"),
    ("ex-builder", "W", "echo f >> b.txt && git commit -q -am f && git update-ref refs/heads/main builder-x"),
    ("ex-operator", "/", "git --git-dir=$B/.git tag -f known-good main"),     # the repository is GIT_DIR's
    # the hook's scope (girsa-architect's Q2): a role's checked-out branch is the Bash guard's, so a script moving it
    # is let through here
    ("ex-verifier", "V", "$PY -c \"import subprocess; subprocess.run(['git', 'update-ref', 'refs/heads/demo-x', "
                         "'main'], check=True)\""),
]
OTHERS = [   # a protected ref moved by another, by a form the Bash guard cannot read, or by the command's environment
    ("ex-builder", "W", "git -C $B reset -q --hard HEAD~1"),
    ("ex-builder", "W", "git update-ref refs/heads/main $OLD"),
    ("ex-builder", "W", "git update-ref refs/heads/main $OLD $CUR"),
    ("ex-builder", "W", "printf 'update refs/heads/main %s\\n' $OLD | git update-ref --stdin"),
    ("ex-builder", "W", "$PY -c \"import subprocess; subprocess.run(['git','update-ref','refs/heads/main','$OLD'], "
                        "check=True)\""),
    ("ex-builder", "W", "git update-ref -d refs/heads/main"),
    ("ex-builder", "W", "git symbolic-ref refs/heads/main refs/heads/builder-x"),
    ("ex-builder", "W", "git branch -m main main-old"),
    ("ex-builder", "/", "git --git-dir=$B/.git update-ref refs/heads/main $OLD"),
    ("ex-builder", "W", "git tag -f known-good $ROOT"),
    ("ex-builder", "W", "git tag -d known-good"),
    ("ex-builder", "W", "git pack-refs --all && git tag -d known-good"),
    ("ex-builder", "W", "git pack-refs --all --no-prune && git update-ref -d refs/tags/known-good "
                        "$(git rev-parse known-good)"),
    ("ex-builder", "W", "git tag alpha-rc9"),
    ("ex-builder", "W", "git fetch . +$ROOT:refs/tags/known-good"),
    ("ex-operator", "B", "git tag -f demo-good $ROOT"),
    ("ex-demo-operator", "D", "git tag -f known-good $ROOT"),
    (None, "W", "git update-ref refs/heads/main $OLD"),
    (None, "W", "git tag -f demo-good $ROOT"),
    ("ex-builder", "W", "PATH=$L/fake:$PATH git update-ref refs/heads/main $OLD"),
    ("ex-builder", "W", "PYTHONPATH=$L/fake git update-ref refs/heads/main $OLD"),
    ("ex-builder", "W", "MISHMERET_OPERATOR=ex-builder git update-ref refs/heads/main $OLD"),
    ("ex-builder", "W", "MISHMERET_CONFIG=/nonexistent/c.json git update-ref refs/heads/main $OLD"),
    ("ex-builder", "W", "MISHMERET_DIR=$L/fake git update-ref refs/heads/main $OLD"),
    # girsa-architect's answer, Q3: git's exec path, set by the command, first on the hook's PATH
    ("ex-builder", "W", "GIT_EXEC_PATH=$L/fakegit git update-ref refs/heads/main $OLD"),
    ("ex-builder", "W", "git --exec-path=$L/fakegit update-ref refs/heads/main $OLD"),
    ("ex-builder", "W", "GIT_EXEC_PATH=$L/fakegit git tag -f known-good $ROOT"),
    ("ex-builder", "W", "GIT_EXEC_PATH=$L/fake2 git update-ref refs/heads/main $OLD"),
    ("ex-builder", "W", "GIT_DIR=$L/fakeB git update-ref refs/heads/main $OLD"),
    # girsa-verifier's review of the plan: MEDIUM 1, main with the main clone detached and mid-rebase; LOW 1, a
    # replacement
    ("ex-builder", "W", "git -C $B checkout -q --detach && git update-ref refs/heads/main $OLD; rc=$?; "
                        "git -C $B checkout -q main; exit $rc"),
    ("ex-builder", "W", "GIT_SEQUENCE_EDITOR=true git -C $B rebase -q -i --exec false HEAD~1 >/dev/null 2>&1; "
                        "git update-ref refs/heads/main $OLD; rc=$?; git -C $B rebase --abort; exit $rc"),
    ("ex-builder", "W", "git replace $CUR $ROOT"),
]
ESCAPES = [   # git's hooks switched off or moved: past the hook, so the Bash guard refuses each (test_guard.py)
    "git -c core.hooksPath=/dev/null update-ref refs/heads/main $OLD",
    "GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.hooksPath GIT_CONFIG_VALUE_0=/dev/null git update-ref refs/heads/main $OLD",
    "HOME=$L/h git update-ref refs/heads/main $OLD",
    "git -c include.path=$L/h/.gitconfig update-ref refs/heads/main $OLD",
]


def _stand_ins(L):
    """The command's own stand-ins: a python3 and a git that exit 0, a sitecustomize that exits, a cat that reads
    nothing beside the real git, a git dir outside the repository naming it, a global config that moves the hooks."""
    for d in ("fake", "fakegit", "fake2", "fakeB", "h"):
        os.makedirs(os.path.join(L, d), exist_ok=True)
    for p in ("fake/python3", "fakegit/git", "fake2/cat"):
        with open(os.path.join(L, p), "w", encoding="utf-8") as fh:
            fh.write("#!/bin/sh\nexit 0\n")
        os.chmod(os.path.join(L, p), 0o755)
    with open(os.path.join(L, "fake", "sitecustomize.py"), "w", encoding="utf-8") as fh:
        fh.write("import os\nos._exit(0)\n")
    exec_path = subprocess.run(["git", "--exec-path"], capture_output=True, text=True).stdout.strip()
    os.symlink(os.path.join(exec_path, "git"), os.path.join(L, "fake2", "git"))
    with open(os.path.join(L, "fakeB", "HEAD"), "w", encoding="utf-8") as fh:
        fh.write("ref: refs/heads/nobody\n")
    with open(os.path.join(L, "fakeB", "commondir"), "w", encoding="utf-8") as fh:
        fh.write(os.path.join(L, "book", ".git") + "\n")
    with open(os.path.join(L, "h", ".gitconfig"), "w", encoding="utf-8") as fh:
        fh.write("[core]\n\thooksPath = /dev/null\n")


def test_the_ref_hook_lets_each_roles_work_through_and_refuses_each_protected_move(live):
    """The live measure's cases: the roles' own work let through, a landing and packing among it; main moved back,
    deleted or linked, `guard.refs` tags moved, made or deleted, a replacement made - by another role, a script, a form
    the Bash guard cannot read, the command's environment, a detached or mid-rebase main clone - each refused with the
    ref unmoved; with no role the refusal names the owner's pane; the hooks moved, past the hook (the Bash guard's)."""
    env = live
    _stand_ins(env["L"])
    faults = []
    for role, where, cmd in OWN:
        rc, before, after, out = _run(env, role, where, cmd)
        if rc:
            faults.append(f"refused, want let through: {role} {cmd}\n  {out.strip()[-300:]}")
    old, cur = _git(env["B"], "rev-parse", "main~1"), _git(env["B"], "rev-parse", "main")
    root = _git(env["B"], "rev-list", "--max-parents=0", "main")
    more = {"OLD": old, "CUR": cur, "ROOT": root}
    for role, where, cmd in OTHERS:
        rc, before, after, out = _run(env, role, where, cmd, more)
        if not rc or before != after or "refused by the ref hook" not in out and "branch -f" not in cmd:
            faults.append(f"let through or moved, want refused: {role} {cmd} rc={rc}\n  {out.strip()[-300:]}")
        if role is None and "run it in ex-" not in out:
            faults.append(f"no role, and the owner's pane not named: {cmd}\n  {out.strip()[-300:]}")
    for cmd in ESCAPES:
        rc, before, after, out = _run(env, "ex-builder", "W", cmd, more)
        moved = after["main"] == old
        _git(env["B"], "-c", "core.hooksPath=/dev/null", "update-ref", "refs/heads/main", cur)
        if rc or not moved:
            faults.append(f"the hooks moved, and the hook ran: {cmd} rc={rc}")
    assert not faults, "\n".join(faults)


def test_a_tag_made_on_origin_elsewhere_fails_a_non_owners_plain_fetch(live):
    """The plan's observed cost: git's tag auto-follow would make the operator's tag, so a builder's plain fetch is
    refused whole; `--no-tags` fetches the rest; the operator's fetch brings the tag."""
    env, L = live, live["L"]
    _git(L, "clone", "-q", "-b", "main", os.path.join(L, "origin.git"), os.path.join(L, "other"))
    _git(os.path.join(L, "other"), "commit", "-q", "--allow-empty", "-m", "elsewhere", env=env)
    _git(os.path.join(L, "other"), "tag", "alpha-rc7")
    _git(os.path.join(L, "other"), "push", "-q", "origin", "HEAD:main", "alpha-rc7", env=env)
    tip = _git(env["B"], "rev-parse", "origin/main")
    rc, *_ = _run(env, "ex-builder", "W", "git fetch -q origin")
    assert rc and not _git(env["B"], "tag", "-l", "alpha-rc7") and _git(env["B"], "rev-parse", "origin/main") == tip
    rc, *_ = _run(env, "ex-builder", "W", "git fetch -q --no-tags origin")
    assert not rc and _git(env["B"], "rev-parse", "origin/main") != tip
    rc, *_ = _run(env, "ex-operator", "B", "git fetch -q origin")
    assert not rc and _git(env["B"], "tag", "-l", "alpha-rc7") == "alpha-rc7"


def test_the_install_replaces_its_own_hook_and_refuses_anothers(live, tmp_path):
    """girsa-architect's answer, Q4: the hook's text holds the paths it was installed with; the install knows its own by
    its marker line and replaces it - another checkout's path here - and refuses a hook that is not its own; refused
    with core.hooksPath set."""
    env, B = live, live["B"]
    hook = os.path.join(B, ".git", "hooks", "reference-transaction")
    mine = open(hook, encoding="utf-8").read()
    shim = os.path.join(B, ".claude", "hooks", "ref_hook.py")
    inst = lambda py, cwd=B, more=None: subprocess.run([py, shim, "--install"], cwd=cwd, capture_output=True,
                                                       text=True, env=dict(env, **(more or {})))
    other = str(tmp_path / "mm-again")
    os.symlink(env["MISHMERET_DIR"], other)
    again = inst(sys.executable, more={"MISHMERET_DIR": other})
    assert again.returncode == 0 and other in open(hook, encoding="utf-8").read(), again.stderr
    with open(hook, "w", encoding="utf-8") as fh:
        fh.write("#!/bin/sh\nexit 0\n")
    theirs = inst(sys.executable)
    assert theirs.returncode == 1 and "is not this hook" in theirs.stderr
    assert open(hook, encoding="utf-8").read() == "#!/bin/sh\nexit 0\n"
    with open(hook, "w", encoding="utf-8") as fh:
        fh.write(mine)
    _git(B, "config", "core.hooksPath", str(tmp_path))
    moved = inst(sys.executable)
    _git(B, "config", "--unset", "core.hooksPath")
    assert moved.returncode == 1 and "core.hooksPath is set" in moved.stderr
    assert open(hook, encoding="utf-8").read() == mine
    first_line = mine.splitlines()[3]
    assert first_line.startswith("PATH=") and "export PATH HOME" in first_line     # before the hook's first command


def test_the_hooks_python_runs_isolated_from_the_users_own_site(live, tmp_path):
    """The hook's Python with -I: a `usercustomize` in the user's site - under HOME, which the hook keeps as installed
    and a role can write - runs at every start without it. A Python that reads a user site (the venv's base) installs
    the hook with a scratch HOME; a usercustomize that exits 0 is planted there, shown to run without -I (the control),
    and a builder's rewind of main is still refused."""
    env, B = live, live["B"]
    base = getattr(sys, "_base_executable", "")          # a venv's own base interpreter
    home = tmp_path / "home"
    home.mkdir()
    plain = {"HOME": str(home), "PATH": os.environ["PATH"]}
    if not os.path.isfile(base):
        pytest.skip("no base interpreter to read a user site")
    site = subprocess.run([base, "-c", "import site; print(site.ENABLE_USER_SITE, site.getusersitepackages())"],
                          capture_output=True, text=True, env=plain).stdout.split()
    if site[:1] != ["True"]:
        pytest.skip("no Python here reads a user site")
    hook = os.path.join(B, ".git", "hooks", "reference-transaction")
    mine = open(hook, encoding="utf-8").read()
    shim = os.path.join(B, ".claude", "hooks", "ref_hook.py")
    try:
        # installed first: planted before, the usercustomize would end the install itself, silently (the mutation run)
        inst = subprocess.run([base, shim, "--install"], cwd=B, capture_output=True, text=True, env=dict(env, **plain))
        text = open(hook, encoding="utf-8").read()
        assert inst.returncode == 0 and text != mine and f"HOME={home};" in text, (inst.stdout, inst.stderr)
        os.makedirs(site[1])
        with open(os.path.join(site[1], "usercustomize.py"), "w", encoding="utf-8") as fh:
            fh.write("import os\nos._exit(0)\n")
        control = subprocess.run([base, "-c", "print('ran')"], capture_output=True, text=True, env=plain)
        assert control.returncode == 0 and control.stdout == "", "the planted usercustomize does not run: no control"
        old = _git(B, "rev-parse", "main")
        rc, *_ = _run(env, "ex-operator", "B", "git commit -q --allow-empty -m 'placeholder: forward'")
        assert rc == 0
        rc, before, after, out = _run(env, "ex-builder", "W", f"git update-ref refs/heads/main {old}")
        assert rc and before == after and "refused by the ref hook" in out, out
    finally:
        with open(hook, "w", encoding="utf-8") as fh:
            fh.write(mine)


def test_the_hooks_shell_judges_at_prepared_alone_and_refuses_with_its_shim_missing(live):
    """The hook's own text, run as git runs it: a rewind of main by a builder is refused at `prepared`, and let pass at
    the states that cannot refuse (`committed`: git ignores the exit there - no Python is started for it); with the shim
    it names missing, every transaction naming a ref under refs/ is refused (fail closed, girsa-architect's Q4)."""
    env, B = live, live["B"]
    hook = os.path.join(B, ".git", "hooks", "reference-transaction")
    line = f"{_git(B, 'rev-parse', 'main')} {'1' * 40} refs/heads/main\n"      # to no descendant of main's
    run = lambda state: subprocess.run([hook, state], input=line, cwd=env["W"], capture_output=True, text=True,
                                       env=dict(env, CLAUDE_CODE_AGENT="ex-builder"))
    prepared, committed = run("prepared"), run("committed")
    assert prepared.returncode == 1 and "refused by the ref hook" in prepared.stderr, prepared.stderr
    assert committed.returncode == 0 and committed.stderr == "", committed.stderr
    shim = os.path.join(B, ".claude", "hooks", "ref_hook.py")
    os.rename(shim, shim + ".away")
    try:
        gone = run("prepared")
    finally:
        os.rename(shim + ".away", shim)
    assert gone.returncode == 1 and "is missing, so nothing is checked" in gone.stderr, gone.stderr


def test_the_hook_takes_the_role_by_mishmeret_role_and_two_names_that_differ_as_no_role(live):
    """notes/PLAN-GUARD-ONLY.md, item 5: the hook's text passes MISHMERET_ROLE beside CLAUDE_CODE_AGENT, and the hook
    reads them by config.session_role - a protected tag moved by its owner named only so is let through, by a builder so
    named refused, and with the two names differing refused as no role's, naming both."""
    env, B = live, live["B"]
    with open(os.path.join(B, ".git", "hooks", "reference-transaction"), encoding="utf-8") as fh:
        assert 'MISHMERET_ROLE="${MISHMERET_ROLE-}" CLAUDE_CODE_AGENT="${CLAUDE_CODE_AGENT-}"' in fh.read()
    root = _git(B, "rev-list", "--max-parents=0", "main")
    back = _git(B, "rev-parse", "known-good")
    to = root if back != root else _git(B, "rev-parse", "main")
    tag = f"git tag -f known-good {to}"
    rc, before, after, out = _run(env, None, "W", tag, {"MISHMERET_ROLE": "ex-builder"})
    assert rc and before == after and "refused by the ref hook" in out, out
    rc, before, after, out = _run(env, None, "W", tag, {"MISHMERET_ROLE": "ex-operator", "CLAUDE_CODE_AGENT": "ex-builder"})
    assert rc and before == after and "MISHMERET_ROLE (ex-operator) and CLAUDE_CODE_AGENT (ex-builder) differ" in out, out
    rc, before, after, out = _run(env, None, "B", tag, {"MISHMERET_ROLE": "ex-operator"})
    assert rc == 0 and after["known-good"] == to, out
    _run(env, None, "B", f"git tag -f known-good {back}", {"MISHMERET_ROLE": "ex-operator"})


def test_a_repository_git_cannot_name_is_refused(tmp_path):
    """girsa-architect's answer, Q3: the hook fails closed - a repository it cannot resolve (a stand-in git named none)
    refuses the transaction."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("ref_hook", os.path.join(PKG, "ref_hook.py"))
    rh = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rh)
    why = rh.refusal("ex-operator", [("0" * 40, "1" * 40, "refs/heads/main")], str(tmp_path))
    assert why and "could not name the repository" in why
