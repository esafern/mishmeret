"""The config loader (mishmeret/config.py): exact fields, typed, overridden by MISHMERET_<FIELD>, and every field read
by some module. A placeholder project; no project's names."""
import ast
import glob
import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.join(os.path.dirname(HERE), "mishmeret")
sys.path.insert(0, PKG)
import config  # noqa: E402


def sample():
    return {
        "repository": "https://example.org/mishmeret.git", "mishmeret_commit": "0" * 40, "project": "Example",
        "roles": [
            {"name": "ex-operator", "short": "operator", "colour": "#111111", "page_light": "#222222",
             "page_dark": "#333333", "corner": True, "tmux": True},
            {"name": "ex-builder", "short": "builder", "colour": "#444444", "page_light": "#555555",
             "page_dark": "#666666", "corner": True, "tmux": True},
            {"name": "ex-helper", "short": "helper", "colour": "", "page_light": "", "page_dark": "",
             "corner": False, "tmux": False}],
        "page_order": ["builder", "operator"], "operator": "ex-operator", "board_dir": "~/board",
        "board_port": 9450, "tmux_session": "ex", "tmux_conf": "~/.tmux-ex.conf", "claude_projects": "~/.claude/projects",
        "agent_files": ".claude/agents/{role}.md", "python": "venv/bin/python", "launchd_prefix": "org.example", "state_dir": "scratch/state",
        "night": {"check_every": 1, "you_idle": 2, "role_idle": 3, "landed_quiet": 4, "poll": 5, "context_limit": 6,
                  "gap": 7},
        "sizes": {"warn_percent": 80, "files": {"RULES.md": [1000, "RULES-HISTORY.md"]}, "status_file": "STATUS.md",
                  "item_pattern": r"^(X[0-9]{2})\. ", "item_limit": 3000, "item_home": "a new item",
                  "state_files": "STATE-*.md", "state_limit": 600, "state_home": "the log"},
        "start_reads": {"briefs": "roles/ex-*.md", "logs": ["STATUS.md"]},
        "effort": {"ex-operator": ["high", "bookkeeping"]},
        "drafts": {"pattern": r"^draft_.*\.txt$", "check": "tools/check.py", "passed": "passed", "failed": "{path}"}}


@pytest.fixture
def write(tmp_path, monkeypatch):
    for k in list(os.environ):
        if k.startswith("MISHMERET_"):
            monkeypatch.delenv(k)
    config._LOADED.clear()

    def _write(cfg):
        (tmp_path / ".claude").mkdir(exist_ok=True)
        p = tmp_path / ".claude" / "mishmeret.json"
        p.write_text(json.dumps(cfg), encoding="utf-8")
        monkeypatch.setenv("MISHMERET_CONFIG", str(p))
        config._LOADED.clear()
        return p
    return _write


def test_the_sample_loads_and_its_root_is_the_config_files_project(write, tmp_path):
    write(sample())
    cfg = config.load()
    assert cfg["board_port"] == 9450 and cfg["night"]["gap"] == 7
    assert config.root() == str(tmp_path)
    assert config.role_names() == ["ex-operator", "ex-builder", "ex-helper"]
    assert config.role_names(tmux=True) == ["ex-operator", "ex-builder"]
    assert config.expand("venv/bin/python") == os.path.join(str(tmp_path), "venv/bin/python")


@pytest.mark.parametrize("change, said", [
    (lambda c: c.pop("board_port"), "missing board_port"),
    (lambda c: c.update(extra=1), "unknown extra"),
    (lambda c: c["night"].pop("gap"), "night: missing gap"),
    (lambda c: c["roles"][0].pop("tmux"), "roles[0]: missing tmux"),
    (lambda c: c.update(board_port="x"), "board_port must be int"),
    (lambda c: c.update(board_port=True), "board_port must be int"),
    (lambda c: c.update(operator="nobody"), "operator 'nobody' is not one of the roles"),
    (lambda c: c.update(page_order=["builder"]), "page_order must name each role with a corner once"),
    (lambda c: c["roles"][2].update(colour="#777777"), 'roles[2].colour must be "" (the role is not drawn)'),
    (lambda c: c["roles"][0].update(page_dark=""), "roles[0].page_dark must be a colour"),
    (lambda c: c["sizes"].pop("item_limit"), "sizes: missing item_limit"),
    (lambda c: c["drafts"].update(extra="x"), "drafts: unknown extra"),
    (lambda c: c["start_reads"].update(logs="STATUS.md"), "start_reads.logs must be list"),
    (lambda c: c["sizes"]["files"].update({"A.md": [100]}), "sizes.files: A.md must be [int, str]"),
    (lambda c: c["sizes"]["files"].update({"A.md": ["100", "home"]}), "sizes.files: A.md must be [int, str]"),
    (lambda c: c["effort"].update({"ex-builder": "high"}), "effort: ex-builder must be [str, str]"),
])
def test_a_field_missing_unknown_or_of_the_wrong_kind_is_refused_by_name(write, change, said):
    cfg = sample()
    change(cfg)
    write(cfg)
    with pytest.raises(config.ConfigError) as e:
        config.load()
    assert said in str(e.value)


def test_an_environment_variable_overrides_its_field_and_a_night_key(write, monkeypatch):
    write(sample())
    monkeypatch.setenv("MISHMERET_BOARD_DIR", "/elsewhere")
    monkeypatch.setenv("MISHMERET_BOARD_PORT", "9999")
    monkeypatch.setenv("MISHMERET_NIGHT_POLL", "50")
    cfg = config.load()
    assert (cfg["board_dir"], cfg["board_port"], cfg["night"]["poll"]) == ("/elsewhere", 9999, 50)


def test_the_shell_form_quotes_every_value(write):
    write(dict(sample(), project="Ex ample's"))
    out = subprocess.run([sys.executable, os.path.join(PKG, "config.py"), "--shell"], capture_output=True, text=True,
                         env=os.environ)
    assert out.returncode == 0, out.stderr
    got = subprocess.run(["bash", "-c", 'eval "$1"; printf "%s|%s|%s" "$MM_PROJECT" "$MM_ROLES" "$MM_NIGHT_GAP"',
                          "-", out.stdout], capture_output=True, text=True)
    assert got.stdout == "Ex ample's|ex-operator ex-builder|7"


def test_every_field_is_read_by_some_module_or_the_projects_shim():
    """Lesson 47 in Girsa (WIRED TO NOTHING): a field no module reads is refused here, not left in every config."""
    shim = {"repository", "mishmeret_commit"}
    files = [f for f in glob.glob(os.path.join(PKG, "*")) if os.path.isfile(f) and not f.endswith("config.py")]
    py = "".join(open(f, encoding="utf-8").read() for f in files if f.endswith(".py"))
    sh = "".join(open(f, encoding="utf-8").read() for f in files if f.endswith(".sh"))
    by_shell = {field: var for field, var, _how in config.SHELL}
    by_shell.update(roles="MM_ROLES", night="MM_NIGHT_")
    unread = [f for f in config.FIELDS if f not in shim and f'"{f}"' not in py and f"'{f}'" not in py
              and not (f in by_shell and by_shell[f] in sh)]
    assert unread == []
