"""Mishmeret's own project files (`.claude/`, notes/PLAN-OWN-CLAUDE.md): its config loads through the library's reader,
and its lane check (`.claude/lane_check.py`) on a placeholder repository. An address or home folder a test needs is
built at run time, so no line here carries one for the check to find."""
import json
import os
import shutil
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "mishmeret"))
import config  # noqa: E402


def test_the_projects_own_config_loads(monkeypatch):
    monkeypatch.setenv("MISHMERET_CONFIG", os.path.join(ROOT, ".claude", "mishmeret.json"))
    config._LOADED.clear()
    try:
        cfg = config.load()
    finally:
        config._LOADED.clear()
    assert cfg["operator"] == "mishmeret-operator" and cfg["land"]["lane_check"] == ".claude/lane_check.py"
    assert os.path.isfile(os.path.join(ROOT, cfg["land"]["lane_check"]))


@pytest.fixture
def staged(tmp_path):
    """A placeholder repository with this project's lane check and table; returns (stage(path, text), check(*args))."""
    os.makedirs(tmp_path / ".claude")
    for f in ("lane_check.py", "lanes.txt"):
        shutil.copy(os.path.join(ROOT, ".claude", f), tmp_path / ".claude" / f)
    git = lambda *a: subprocess.run(["git", "-C", str(tmp_path), *a], check=True, capture_output=True)
    git("init", "-q", "-b", "main")

    def stage(path, text="x\n"):
        os.makedirs(os.path.dirname(tmp_path / path), exist_ok=True)
        (tmp_path / path).write_text(text, encoding="utf-8")
        git("add", "--", path)

    def check(*args):
        run = subprocess.run([sys.executable, ".claude/lane_check.py", *args], cwd=tmp_path, capture_output=True,
                             text=True)
        return run.returncode, run.stdout + run.stderr
    return stage, check, tmp_path


def test_the_lane_check_keeps_claude_from_the_builder_and_takes_the_reviewers_words(staged):
    stage, check, _ = staged
    stage("mishmeret/x.py")
    stage("notes/a.md")
    assert check("mishmeret-builder")[0] == 0
    assert check("mishmeret-builder", "--doc-only")[0] == 1, "x.py is not a document"
    assert check("nobody")[0] == 1, "a role with no row may commit nothing"
    stage(".claude/settings.json")
    rc, out = check("mishmeret-builder")
    assert rc == 1 and "OUTSIDE THE LANE: .claude/settings.json" in out
    rc, out = check("mishmeret-builder", "--because", "A - yes")
    assert rc == 0 and "ON THE REVIEWER'S WORD (A - yes): .claude/settings.json" in out
    for refused in (("--range", "a..b"), ("--plan", "p.md"), ()):
        assert check(*(("mishmeret-builder",) if refused else ()) + refused)[0] == 2, refused


def test_every_commit_is_scanned_for_an_address_a_roster_name_and_the_home_folder(staged):
    stage, check, root = staged
    stage("notes/ok.md", "write to someone" + "@" + "example.org\n")
    rc, out = check("mishmeret-builder")
    assert rc == 0 and "no name was checked" in out, out
    for i, line in enumerate(("mail pp" + "@" + "mail.co\n", "kept in " + os.path.expanduser("~") + "/x\n")):
        stage(f"notes/bad{i}.md", line)
        rc, out = check("mishmeret-builder")
        assert rc == 1 and f"notes/bad{i}.md: 1 added line carries" in out and line.strip() not in out, out
        subprocess.run(["git", "-C", str(root), "rm", "-q", "--cached", f"notes/bad{i}.md"], check=True)
    (root / ".claude" / "roster.local.json").write_text(json.dumps(
        {"reviewers": {"r1": {"display": "Placeholder Person", "email": "pp" + "@" + "mail.co"}}}), encoding="utf-8")
    stage("notes/named.md", "as placeholder.person said\n")
    rc, out = check("mishmeret-builder")
    assert rc == 1 and "notes/named.md: 1 added line" in out and "no name was checked" not in out, out
