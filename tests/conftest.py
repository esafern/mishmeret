"""Every test runs against a placeholder project (its config written here) and with stub `tmux`, `claude`, `osascript`
and `launchctl` first on PATH - so no test reaches the real tmux server, starts Claude Code, shows an alert or loads a
launchd job (in Girsa, 2026-11-01: a test whose clone variable the moved code no longer read reached the roles' live
tmux session). A test that needs a stub to say something puts its own in front."""
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.join(os.path.dirname(HERE), "mishmeret")
sys.path.insert(0, PKG)

COLOURS = {"operator": ("#ca8a04", "#9a7f2e", "#bfa66e"), "builder": ("#0891b2", "#3d8590", "#73aab2"),
           "verifier": ("#16a34a", "#4f8048", "#8fb487"), "ui-steward": ("#c46686", "#a75a80", "#c793ab"),
           "architect": ("#6a9bcc", "#4a6fa0", "#86a2c9")}


def project_config(root, **over):
    """The placeholder project's config: Girsa's role shapes under the prefix "ex-", its Board in `root`/board."""
    roles = [{"name": "ex-" + s, "short": s, "colour": c, "page_light": lt, "page_dark": dk, "corner": True,
              "tmux": True} for s, (c, lt, dk) in COLOURS.items()]
    roles.append({"name": "ex-demo-operator", "short": "demo-operator", "colour": "", "page_light": "",
                  "page_dark": "", "corner": False, "tmux": False})
    cfg = {"repository": "https://example.org/mishmeret.git", "mishmeret_commit": "0" * 40, "project": "Example",
           "roles": roles, "page_order": ["ui-steward", "architect", "operator", "verifier", "builder"],
           "operator": "ex-operator", "board_dir": os.path.join(str(root), "board"), "board_port": 8450,
           "tmux_session": "ex", "tmux_conf": os.path.join(str(root), "tmux.conf"),
           "claude_projects": os.path.join(str(root), "projects"), "agent_files": ".claude/agents/{role}.md",
           "python": sys.executable, "launchd_prefix": "org.example", "state_dir": "scratch/state",
           "night": {"check_every": 1800, "you_idle": 900, "role_idle": 900, "landed_quiet": 120, "poll": 60,
                     "context_limit": 200000, "gap": 5}}
    cfg.update(over)
    return cfg


def write_project(root, **over):
    """A project at `root`: its .claude/mishmeret.json. Returns the config's path."""
    os.makedirs(os.path.join(str(root), ".claude"), exist_ok=True)
    p = os.path.join(str(root), ".claude", "mishmeret.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(project_config(root, **over), fh)
    return p


REPO = tempfile.mkdtemp(prefix="mishmeret-project-")
os.environ["MISHMERET_CONFIG"] = write_project(REPO)
for k in [k for k in os.environ if k.startswith("MISHMERET_") and k != "MISHMERET_CONFIG"]:
    del os.environ[k]

STUBS = os.path.join(REPO, "stub-bin")
os.makedirs(STUBS)
for name in ("tmux", "claude", "osascript", "launchctl"):
    with open(os.path.join(STUBS, name), "w", encoding="utf-8") as fh:
        fh.write("#!/bin/sh\nexit 0\n" if name != "claude" else "#!/bin/sh\necho '[]'\n")
    os.chmod(os.path.join(STUBS, name), 0o755)
os.environ["PATH"] = STUBS + os.pathsep + os.environ["PATH"]
