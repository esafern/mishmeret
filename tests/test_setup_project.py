"""setup_project.py (notes/PLAN-PROJECT-SETUP.md): a project set up to take the guard alone, by one command - on a
placeholder main clone in tmp_path, never a real project; the pin a link to this tree, so the hook the project's files
run is this tree's guard."""
import json
import os
import shutil
import subprocess
import sys

from conftest import PKG

HOME = os.path.expanduser("~")
ID = ["-c", "user.name=placeholder", "-c", "user.email=placeholder@example.org"]


def checkout(tmp_path):
    """A Mishmeret checkout the setup runs from: this tree's setup_project.py, project_shim.py and config.py in a git
    repository of their own, its origin a placeholder, an older commit before them - (its setup_project.py, HEAD)."""
    t = tmp_path / "mishmeret-checkout"
    if not t.exists():
        (t / "mishmeret").mkdir(parents=True)
        for name in ("setup_project.py", "project_shim.py", "config.py"):
            shutil.copy(os.path.join(PKG, name), t / "mishmeret" / name)
        subprocess.run(["git", "init", "-q", str(t)], check=True)
        subprocess.run(["git", "-C", str(t), "remote", "add", "origin", "https://example.org/mishmeret.git"], check=True)
        subprocess.run(["git", "-C", str(t), *ID, "commit", "-q", "--allow-empty", "-m", "an older commit"], check=True)
        subprocess.run(["git", "-C", str(t), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(t), *ID, "commit", "-q", "-m", "a tree"], check=True)
    head = subprocess.run(["git", "-C", str(t), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    return str(t / "mishmeret" / "setup_project.py"), head


def clone(tmp_path):
    """A placeholder main clone on `main`, one commit."""
    root = tmp_path / "book"
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), *ID, "commit", "-q", "--allow-empty", "-m", "start"], check=True)
    return root


def setup(tmp_path, *args, pins=None):
    """setup_project.py run with `args`, MISHMERET_DIR a folder of `tmp_path` holding `pins` (commit: its tree)."""
    mm = tmp_path / "mm"
    (mm / ".pins").mkdir(parents=True, exist_ok=True)
    for sha, tree in (pins or {}).items():
        if not (mm / ".pins" / sha).exists():
            (mm / ".pins" / sha).symlink_to(tree)
    env = {k: v for k, v in os.environ.items() if not k.startswith("MISHMERET_")}
    env["MISHMERET_DIR"] = str(mm)
    return subprocess.run([sys.executable, checkout(tmp_path)[0], *map(str, args)], capture_output=True, text=True,
                          env=env, cwd=str(tmp_path), timeout=60)


def written(root):
    return sorted(os.path.relpath(os.path.join(d, f), root) for d, _, fs in os.walk(root) if ".git" not in d
                  for f in fs)


def test_setup_writes_what_the_guard_needs_and_never_a_projects_own_file(tmp_path):
    """The dry run writes nothing; --write writes the config, the shim's helper, the hooks' shims, the hook in
    settings.json and an agent file a role - every path under the home folder as `~/...` (girsa-verifier's MEDIUM 1 on
    the plan: the home folder holds its owner's name, and these files are committed), `guard.foreign` given expanded as
    an unquoted `~` reaches it; the config loads as this tree's config.py reads it; a second run writes nothing; a
    project's own file is kept and said, the shim's said to differ; settings.json keeps what it held."""
    root = clone(tmp_path)
    (root / ".claude").mkdir()
    (root / ".claude" / "settings.json").write_text(json.dumps({"model": "x", "hooks": {"Stop": [{"hooks": []}]}}))
    builder = os.path.join(HOME, "work", "placeholder-builder")
    args = [root, "--project", "Placeholder", "--operator", "ex-operator", "--role", f"ex-builder={builder}",
            "--role", "ex-pi=~/work/placeholder-pi:pi", "--foreign", os.path.join(HOME, "work", "placeholder-foreign"),
            "--protect", "refs/tags/stage"]
    out = setup(tmp_path, *args)
    assert out.returncode == 0 and "Nothing written" in out.stdout, out.stderr
    assert written(root) == [".claude/settings.json"], written(root)
    out = setup(tmp_path, *args, "--write")
    assert out.returncode == 0, out.stderr
    assert written(root) == [".claude/agents/ex-builder.md", ".claude/agents/ex-operator.md", ".claude/hooks/ref_hook.py",
                             ".claude/hooks/role_guard.py", ".claude/mishmeret_shim.py", ".claude/settings.json",
                             ".mishmeret/config.json"], written(root)      # no agent file for the pi role
    for rel in written(root):
        assert HOME not in (root / rel).read_text(encoding="utf-8"), rel
    cfg = json.loads((root / ".mishmeret" / "config.json").read_text())
    assert cfg["roles"] == [{"name": "ex-operator"}, {"name": "ex-builder", "worktrees": ["~/work/placeholder-builder"]},
                            {"name": "ex-pi", "worktrees": ["~/work/placeholder-pi"], "runner": "pi"}], cfg["roles"]
    assert cfg["guard"] == {"main": "main", "foreign": ["~/work/placeholder-foreign"],
                            "refs": {"refs/tags/stage": "ex-operator"}}, cfg["guard"]
    assert cfg["mishmeret_commit"] == checkout(tmp_path)[1] and cfg["repository"] == "https://example.org/mishmeret.git"
    env = {k: v for k, v in os.environ.items() if not k.startswith("MISHMERET_")}
    loaded = subprocess.run([sys.executable, "-c", "import config; c = config.load(); print(c['project'], c['operator'])"],
                            cwd=PKG, env=dict(env, MISHMERET_CONFIG=str(root / ".mishmeret" / "config.json")),
                            capture_output=True, text=True)
    assert loaded.stdout.strip() == "Placeholder ex-operator", loaded.stderr
    settings = json.loads((root / ".claude" / "settings.json").read_text())
    assert settings["model"] == "x" and settings["hooks"]["Stop"] == [{"hooks": []}]
    assert [h["hooks"][0]["command"] for h in settings["hooks"]["PreToolUse"]] == \
        ['python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/role_guard.py"']
    assert open(os.path.join(PKG, "project_shim.py")).read() == (root / ".claude" / "mishmeret_shim.py").read_text()
    assert "~/work/placeholder-builder && claude --agent ex-builder" in (root / ".claude/agents/ex-builder.md").read_text()
    # a second run writes nothing; a project's own file is kept and said
    before = {rel: (root / rel).read_text() for rel in written(root)}
    out = setup(tmp_path, *args, "--write")
    assert out.returncode == 0 and out.stdout.count("as it is") == 7 and "wrote" not in out.stdout, out.stdout
    (root / ".claude" / "mishmeret_shim.py").write_text("# the project's own\n")
    out = setup(tmp_path, *args, "--write")
    assert "KEPT       .claude/mishmeret_shim.py - the project's own, not replaced: it differs from " \
           "mishmeret/project_shim.py" in out.stdout, out.stdout
    assert (root / ".claude" / "mishmeret_shim.py").read_text() == "# the project's own\n"
    assert all((root / rel).read_text() == text for rel, text in before.items() if rel != ".claude/mishmeret_shim.py")


def test_setup_prints_gits_steps_in_order_each_a_command_and_refuses_what_it_cannot_write(tmp_path):
    """Git's steps printed, not run (girsa-architect's Q2), each a command of its own: the pin only when absent, the
    files' add and their commit, each worktree, the ref hook after both, each role's start - a pi role's line with the
    pin's pi_guard.ts. Refused: a config this tree's config.py would refuse (nothing written), a DIR that is no main
    clone's top folder, a --role without its worktree; a --commit other than the tree's own is said."""
    root = clone(tmp_path)
    tree = os.path.dirname(PKG)
    head = checkout(tmp_path)[1]
    pi_tree = tmp_path / "book-pi"
    args = [root, "--project", "P", "--operator", "ex-operator", "--role", f"ex-builder={tmp_path / 'book-builder'}",
            "--role", f"ex-pi={pi_tree}:pi", "--protect", "refs/tags/stage"]
    out = setup(tmp_path, *args, "--write")
    lines = [line.strip() for line in out.stdout.split("Then,", 1)[1].splitlines() if line.startswith("   ")]
    pin = tmp_path / "mm" / ".pins" / head
    assert lines[0] == f"git -C {tmp_path / 'mm'} worktree add --detach {pin} {head}", lines
    assert lines[1] == (f"git -C {root} add .mishmeret/config.json .claude/mishmeret_shim.py .claude/hooks/role_guard.py "
                        ".claude/hooks/ref_hook.py .claude/agents/ex-operator.md .claude/agents/ex-builder.md "
                        ".claude/settings.json"), lines                   # the add alone, the commit its own line
    assert lines[2] == f"git -C {root} commit -m \"Mishmeret's role guard, pinned at {head[:9]}\"", lines
    assert lines[3:5] == [f"git -C {root} worktree add {tmp_path / 'book-builder'} -b ex-builder",
                          f"git -C {root} worktree add {pi_tree} -b ex-pi"], lines
    assert lines[5] == f"cd {root} && python3 .claude/hooks/ref_hook.py --install", lines
    assert lines[6:] == [f"cd {root} && claude --agent ex-operator", f"cd {tmp_path / 'book-builder'} && claude --agent "
                         f"ex-builder", f"cd {pi_tree} && pi --no-extensions --name ex-pi --role ex-pi -e "
                         f"{pin}/mishmeret/pi_guard.ts"], lines
    # the pin there, its step gone; nothing written, no add and no commit
    out = setup(tmp_path, *args, "--write", pins={head: tree})
    steps = out.stdout.split("Then,", 1)[1]
    assert "worktree add --detach" not in steps and " add .mishmeret" not in steps and " commit -m" not in steps, steps
    # refused, nothing written
    other = clone(tmp_path / "x")
    out = setup(tmp_path, other, "--project", "P", "--operator", "ex-operator", "--protect", "tags/stage", "--write")
    assert out.returncode != 0 and "not written" in out.stderr and "refs/" in out.stderr and written(other) == [], \
        (out.stderr, written(other))
    (root / "sub").mkdir()
    out = setup(tmp_path, root / "sub", "--project", "P", "--operator", "ex-operator")
    assert out.returncode != 0 and "not a repository's main clone" in out.stderr, out.stderr
    out = setup(tmp_path, other, "--project", "P", "--operator", "ex-operator", "--role", "ex-builder")
    assert out.returncode != 0 and "--role takes ROLE=WORKTREE" in out.stderr, out.stderr
    out = setup(tmp_path, other, "--project", "P", "--operator", "ex-operator", "--commit", "HEAD~1")
    assert "is not the commit this runs from" in out.stdout, out.stdout


def test_the_written_project_is_guarded_as_claude_code_runs_its_hook(tmp_path):
    """End to end on the placeholder: the files written and committed, the builder's worktree made, the pin a link to
    this tree - then the project's own hook, run as Claude Code runs it (the event on stdin, CLAUDE_PROJECT_DIR the
    session's tree): the builder's push and its commit in the main clone refused, its commit in its worktree let
    through; the operator's commit in the main clone let through."""
    root = clone(tmp_path)
    work = tmp_path / "book-builder"
    head = checkout(tmp_path)[1]       # its pin: this tree, whose guard the written hook runs
    out = setup(tmp_path, root, "--project", "P", "--operator", "ex-operator", "--role", f"ex-builder={work}", "--write",
                pins={head: os.path.dirname(PKG)})
    assert out.returncode == 0, out.stderr
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(root), *ID, "commit", "-q", "-m", "the guard"], check=True)
    subprocess.run(["git", "-C", str(root), "worktree", "add", "-q", str(work), "-b", "ex-builder"], check=True)
    env = {k: v for k, v in os.environ.items() if not k.startswith(("MISHMERET_", "CLAUDE_"))}
    env["MISHMERET_DIR"] = str(tmp_path / "mm")

    def hook(tree, role, command):
        event = {"hook_event_name": "PreToolUse", "cwd": str(tree), "tool_name": "Bash",
                 "tool_input": {"command": command}, "agent_type": role}
        r = subprocess.run(["python3", str(tree / ".claude" / "hooks" / "role_guard.py")], input=json.dumps(event),
                           capture_output=True, text=True, env=dict(env, CLAUDE_PROJECT_DIR=str(tree)), timeout=60)
        assert r.returncode in (0, 2), r.stderr
        return r.stderr if r.returncode else None
    assert "pushing is the operator's (ex-operator)" in hook(work, "ex-builder", "git push origin ex-builder")
    assert "the operator's alone" in hook(work, "ex-builder", f"git -C {root} commit -m x")
    assert hook(work, "ex-builder", "git commit -m x") is None
    assert hook(root, "ex-operator", "git commit -m x") is None
