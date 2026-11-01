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
                     "context_limit": 200000, "gap": 5},
           "sizes": {"warn_percent": 80, "files": {"RULES.md": [1000, "RULES-HISTORY.md"],
                                                   "docs/LANES.md": [2000, "docs/LANES-PLAN.md"]},
                     "status_file": "STATUS.md", "item_pattern": r"^(X[0-9]{2})\. ", "item_limit": 3000,
                     "item_home": "a new item", "state_files": "docs/STATE-ex-*.md", "state_limit": 600,
                     "state_home": "the role's log"},
           "start_reads": {"briefs": ".claude/roles/ex-*.md", "logs": ["STATUS.md", "STATUS-HISTORY.md"]},
           "effort": {"ex-operator": ["high", "bookkeeping"], "ex-builder": ["high", "the heaviest user"],
                      "ex-auditor": ["xhigh", "a one-off audit"]},
           "drafts": {"pattern": r"^draft_.*\.txt$", "check": "tools/check.py", "passed": "A draft: its rules are ex's.",
                      "failed": "the check failed on {path} - fix the draft:"},
           "guard": {"homes": "homes.json", "fallback_roots": [os.path.join(str(root), "fallback-book")],
                     "trees": [os.path.join(str(root), "checkout")], "retired_remotes": ["retired"],
                     "checks": ["check_lane.py", "pytest", "check_words.py", "check_draft.py"], "precommit": ".claude/hooks/time_check.py"},
           "land": {"planned": "ex-builder", "verifier": "ex-verifier", "lane_check": "tools/lanes.py",
                    "ledger": "rulings.jsonl", "server": {"entry": "app/server.py", "folders": ["app", "lib", "tools"],
                                                          "page": "page/"},
                    "gate_sets": {"landing": ["tests/test_a.py", "tests/test_b.py"], "quick": ["tests/test_a.py"]},
                    "gate_env": {"quick": {"EX_QUICK": "1"}}, "hand_run": {"tests/test_slow.py": "by hand"}}}
    cfg.update(over)
    return cfg


# the placeholder project's draft check (its `drafts.check`): a draft holding "BAD" fails, with a line naming it
DRAFT_CHECK = 'import sys\ntext = open(sys.argv[1], encoding="utf-8").read()\nif "BAD" in text:\n' \
              '    print("BAD found in the draft")\n    sys.exit(1)\n'


def write_project(root, **over):
    """A project at `root`: its .claude/mishmeret.json. Returns the config's path."""
    os.makedirs(os.path.join(str(root), ".claude"), exist_ok=True)
    p = os.path.join(str(root), ".claude", "mishmeret.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(project_config(root, **over), fh)
    return p


REPO = tempfile.mkdtemp(prefix="mishmeret-project-")
os.environ["MISHMERET_CONFIG"] = write_project(REPO)
os.makedirs(os.path.join(REPO, "tools"))
with open(os.path.join(REPO, "tools", "check.py"), "w", encoding="utf-8") as fh:
    fh.write(DRAFT_CHECK)
for k in [k for k in os.environ if k.startswith("MISHMERET_") and k != "MISHMERET_CONFIG"]:
    del os.environ[k]

STUBS = os.path.join(REPO, "stub-bin")
os.makedirs(STUBS)
for name in ("tmux", "claude", "osascript", "launchctl"):
    with open(os.path.join(STUBS, name), "w", encoding="utf-8") as fh:
        fh.write("#!/bin/sh\nexit 0\n" if name != "claude" else "#!/bin/sh\necho '[]'\n")
    os.chmod(os.path.join(STUBS, name), 0o755)
os.environ["PATH"] = STUBS + os.pathsep + os.environ["PATH"]
