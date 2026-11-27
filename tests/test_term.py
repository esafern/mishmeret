"""term.sh (notes/PLAN-TERMINAL-ADAPTER.md): every terminal step of the session scripts, in tmux's form or WezTerm's,
the config's `terminal` choosing. Behind stubs that record each call - no test reaches a live tmux server or WezTerm
(conftest.py) - each call as the probe ran it on a private server (the plan's head); the real servers are the plan's
measure."""
import json
import os
import re
import subprocess
import sys

from conftest import PKG, write_project

# Each stub records a call as its words apart, so a word split or two joined is seen (girsa-verifier's LOW 2 on the
# build: "$*" joined them with spaces, and `send-keys -t "$1" $2 Enter` passed here, failing 7 of 22 checks on a real
# server). WezTerm's: spawn and split-pane make the next pane (its id), list answers the panes made, in the workspace
# each was spawned in (a split's, its first pane's), as `wezterm cli list --format json` does
WEZ = """#!{py}
import json, os, sys
d = os.environ["STUB_DIR"]
with open(os.path.join(d, "calls"), "a", encoding="utf-8", newline="") as fh:
    fh.write("\\x1f".join(["wezterm"] + sys.argv[1:]) + "\\n")
panes = os.path.join(d, "panes.json")
made = json.load(open(panes)) if os.path.exists(panes) else []
verb = sys.argv[3] if len(sys.argv) > 3 else ""
if verb in ("spawn", "split-pane"):
    ws = sys.argv[sys.argv.index("--workspace") + 1] if "--workspace" in sys.argv else (made[0]["workspace"] if made else "")
    made.append({{"pane_id": len(made), "workspace": ws, "size": {{"cols": 10}}, "tty_name": "/dev/ttys-none"}})
    json.dump(made, open(panes, "w"))
    print(len(made) - 1)
elif verb == "list":
    print(json.dumps(made))
elif verb == "get-text":
    print("0123456789\\nabc\\npad       \\nend")       # a full line, wrapped; a line padded to the width, not
"""
TMUX = """#!/bin/sh
{ printf 'tmux'; for a in "$@"; do printf '\\037%s' "$a"; done; printf '\\n'; } >> "$STUB_DIR/calls"
case "$1" in new-session|split-window) echo %7 ;; has-session) exit 1 ;; esac
exit 0
"""


def stubs(tmp_path, panes=None):
    """The two stubs first on PATH, their record in `tmp_path`; `panes` the WezTerm panes already there."""
    d = tmp_path / "bin"
    d.mkdir(exist_ok=True)
    for name, text in (("wezterm", WEZ.format(py=sys.executable)), ("tmux", TMUX)):
        (d / name).write_text(text, encoding="utf-8")
        (d / name).chmod(0o755)
    if panes is not None:
        (tmp_path / "panes.json").write_text(json.dumps(panes), encoding="utf-8")
    return dict(os.environ, PATH=f"{d}{os.pathsep}{os.environ['PATH']}", STUB_DIR=str(tmp_path), TERM="dumb")


def calls(tmp_path):
    """Each stub call, as its words."""
    p = tmp_path / "calls"
    if not p.exists():
        return []
    with open(p, encoding="utf-8", newline="") as fh:       # a typed line's own \r kept, not read as a line's end
        return [line.split("\x1f") for line in fh.read().split("\n")[:-1]]


def C(words, *more):
    """A call's words: `words` split at its spaces, then each of `more` as one word."""
    return words.split() + list(more)


def term(tmp_path, terminal, script, panes=None, **env):
    """`script` run by bash with term.sh sourced, under `terminal`; (its result, each stub call)."""
    e = dict(stubs(tmp_path, panes), MM_TERMINAL=terminal, SESSION="ex", MM_STATE_DIR=str(tmp_path / "state"), **env)
    out = subprocess.run(["bash", "-c", f'. "{PKG}/term.sh"; {script}'], env=e, capture_output=True, text=True,
                         stdin=subprocess.DEVNULL, timeout=30)
    return out, calls(tmp_path)


def test_each_terminal_step_makes_its_terminals_own_call(tmp_path):
    """Each function of term.sh, under each terminal: tmux's call as the scripts made it before (the adapter a refactor
    there), and WezTerm's as the probe ran it - a session its workspace, a pane's tags a line of the session's file."""
    ex = [{"pane_id": 3, "workspace": "ex", "size": {"cols": 10}, "tty_name": "/dev/ttys-none"},
          {"pane_id": 4, "workspace": "other", "size": {"cols": 10}, "tty_name": "/dev/ttys-none"}]
    W = "wezterm cli --no-auto-start "
    LIST = C(W + "list --format json")
    cases = [  # script, tmux's calls, WezTerm's calls
        ("term_has ex", [C("tmux has-session -t ex")], [LIST]),
        ("term_panes ex", [C("tmux list-panes -s -t ex -F #{pane_id}")], [LIST]),
        ("term_split 3 across /d", [C("tmux split-window -h -t 3 -c /d -P -F #{pane_id}")],
         [C(W + "split-pane --pane-id 3 --right --cwd /d")]),
        ("term_split 3 down /d", [C("tmux split-window -v -t 3 -c /d -P -F #{pane_id}")],
         [C(W + "split-pane --pane-id 3 --bottom --cwd /d")]),
        ("term_send 3 'echo hi'", [C("tmux send-keys -t 3", "echo hi", "Enter")],
         [C(W + "send-text --pane-id 3 --no-paste", "echo hi\r")]),
        ("term_capture 3 -e", [C("tmux capture-pane -e -p -t 3")], [C(W + "get-text --pane-id 3 --escapes")]),
        ("term_capture 3 200", [C("tmux capture-pane -p -J -S -200 -t 3")],
         [LIST, C(W + "get-text --pane-id 3 --start-line -200")]),
        ("term_cmd 3", [C("tmux display-message -p -t 3 #{pane_current_command}")], [LIST]),
        ("term_tag 3 role 'ex builder'", [C("tmux set-option -p -t 3 @role", "ex builder")], []),
        ("term_tag_of 3 role", [C("tmux show-options -pv -t 3 @role")], []),
        ("term_list ex", [C("tmux list-panes -s -t ex -F", "#{pane_id} #{@role} #{pane_current_command}")], [LIST] * 2),
        ("term_label ex", [C("tmux set-option -w -t ex pane-border-status top"),
                           C("tmux set-option -w -t ex pane-border-format", " #[fg=#{@colour},bold]#{@role}#[default] ")],
         [LIST, C(W + "set-tab-title --pane-id 3 ex")]),
        ("term_layout ex", [C("tmux select-layout -t ex tiled")], []),
        ("term_focus 3", [C("tmux select-pane -t 3")], [C(W + "activate-pane --pane-id 3")]),
        ("term_attach ex", [C("tmux attach-session -t ex")], []),
        ("term_kill ex", [C("tmux kill-session -t ex")], [LIST, C(W + "kill-pane --pane-id 3")]),
    ]
    for script, by_tmux, by_wez in cases:
        for terminal, want in (("tmux", by_tmux), ("wezterm", by_wez)):
            (tmp_path / "calls").unlink(missing_ok=True)
            out, made = term(tmp_path, terminal, script, panes=ex)
            assert made == want, (terminal, script, made, out.stderr)
    # the conf: tmux's loaded when there; WezTerm reads its own
    conf = tmp_path / "t.conf"
    conf.write_text("", encoding="utf-8")
    for terminal, want in (("tmux", [C(f"tmux source-file {conf}")]), ("wezterm", [])):
        (tmp_path / "calls").unlink(missing_ok=True)
        assert term(tmp_path, terminal, f"term_conf {conf}")[1] == want, terminal
    # the new session: tmux's detached session; WezTerm's a window in the server the command runs in, never outside one
    out, made = term(tmp_path, "tmux", "term_new ex /d")
    assert out.stdout.strip() == "%7" and made[-1][:6] == C("tmux new-session -d -s ex -x") and \
        made[-1][-5:] == C("-c /d -P -F #{pane_id}"), made
    (tmp_path / "calls").unlink()
    out, made = term(tmp_path, "wezterm", "term_new ex /d", panes=[], WEZTERM_UNIX_SOCKET=str(tmp_path / "sock"))
    assert out.returncode == 0 and made == [C(W + "spawn --new-window --workspace ex --cwd /d")], (made, out.stderr)
    (tmp_path / "calls").unlink()
    out, made = term(tmp_path, "wezterm", "term_new ex /d", WEZTERM_UNIX_SOCKET="")
    assert out.returncode == 1 and "run this from a WezTerm window" in out.stderr and made == [], out.stderr


def test_wezterms_tags_are_its_sessions_file_begun_afresh_and_its_capture_joins_a_wrapped_line(tmp_path):
    """WezTerm keeps no option of a pane's own (the probe), so a pane's tags are lines of <state_dir>/panes-<session>.tsv,
    the latest of a key the one read; the file begun afresh by term_new and gone with the session (girsa-architect's
    Q2: pane ids repeat across servers - a file a server left behind gave a new pane a role not its own). And a
    capture's line as wide as its pane is joined to the next, as tmux's -J does (the measure: two 19-column panes)."""
    ex = [{"pane_id": 1, "workspace": "ex", "size": {"cols": 10}, "tty_name": "/dev/ttys-none"}]
    tags = tmp_path / "state" / "panes-ex.tsv"
    tags.parent.mkdir()                                     # term_new makes it, as its session's first step
    out, _ = term(tmp_path, "wezterm", "term_tag 1 role ex-builder; term_tag 1 role ex-verifier; term_tag 1 colour '#16a34a';"
                  " echo \"$(term_tag_of 1 role) $(term_tag_of 1 colour) [$(term_tag_of 2 role)]\"", panes=ex,
                  WEZTERM_UNIX_SOCKET="x")
    assert out.stdout.strip() == "ex-verifier #16a34a []", out.stderr
    # a file left behind, its pane ids the next session's: only the new session's tags read
    out, _ = term(tmp_path, "wezterm", "term_new ex /d >/dev/null; term_tag 0 role ex-operator; echo \"[$(term_tag_of 1 role)]\"",
                  panes=[], WEZTERM_UNIX_SOCKET="x")
    assert out.stdout.strip() == "[]" and tags.read_text(encoding="utf-8") == "0\trole\tex-operator\n", out.stderr
    term(tmp_path, "wezterm", "term_kill ex", panes=ex)
    assert not tags.exists()
    out, _ = term(tmp_path, "wezterm", "term_capture 1 200", panes=ex)
    assert out.stdout.split("\n")[:3] == ["0123456789abc", "pad       ", "end"], out.stdout


def test_agents_sh_starts_the_roles_in_a_wezterm_window_as_it_does_in_tmux(tmp_path):
    """agents.sh under the config's `terminal: wezterm`: one window spawned in the roles' workspace, its panes split
    across and down in the page's order, each tagged with its role and colour, each role's start typed into its own
    pane, the tab titled, the operator's pane focused - and no tmux call at all. Run outside a WezTerm window it stops,
    nothing spawned (girsa-architect's Q4)."""
    root = tmp_path / "p"
    cfg = write_project(root, terminal="wezterm")
    env = dict(stubs(tmp_path, panes=[]), MISHMERET_CONFIG=cfg, WEZTERM_UNIX_SOCKET=str(tmp_path / "sock"))
    out = subprocess.run(["bash", os.path.join(PKG, "agents.sh")], env=env, capture_output=True, text=True,
                         stdin=subprocess.DEVNULL, timeout=60)
    made = calls(tmp_path)
    assert out.returncode == 0 and not [c for c in made if c[0] == "tmux"], (out.stderr, made)
    W = "wezterm cli --no-auto-start "
    assert made[1] == C(W + f"spawn --new-window --workspace ex --cwd {root}"), made
    splits = [c for c in made if "split-pane" in c]
    assert splits == [C(W + f"split-pane --pane-id {i} {s} --cwd {root}")
                      for i, s in enumerate(("--right", "--bottom", "--right", "--bottom"))], splits
    order = ["ex-ui-steward", "ex-architect", "ex-operator", "ex-verifier", "ex-builder"]       # the page's order
    rows = [line.split("\t") for line in (tmp_path / "p" / "scratch" / "state" / "panes-ex.tsv").read_text().splitlines()]
    assert sorted(r for r in rows if r[1] == "role") == sorted([str(i), "role", n] for i, n in enumerate(order)), rows
    assert len([r for r in rows if r[1] == "colour" and r[2].startswith("#")]) == 5, rows
    typed = [c for c in made if "send-text" in c]           # each its pane, and its start whole, one word
    for i, name in enumerate(order):
        assert [t for t in typed if t[:7] == C(W + f"send-text --pane-id {i} --no-paste") and len(t) == 8
                and f" claude --agent {name} " in t[7] and t[7].endswith("\r")], (name, typed)
    assert C(W + "set-tab-title --pane-id 0 ex") in made and made[-1] == C(W + "activate-pane --pane-id 2"), made
    # outside a WezTerm window: said, and nothing spawned
    (tmp_path / "calls").unlink()
    (tmp_path / "panes.json").write_text("[]", encoding="utf-8")
    out = subprocess.run(["bash", os.path.join(PKG, "agents.sh")], env=dict(env, WEZTERM_UNIX_SOCKET=""),
                         capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=60)
    assert out.returncode == 1 and "run this from a WezTerm window" in out.stderr, out.stderr
    assert not [c for c in calls(tmp_path) if "spawn" in c or "send-text" in c], calls(tmp_path)


def test_no_session_script_names_a_terminal_outside_term_sh():
    """girsa-architect's Q5 answer: the three scripts call no tmux or wezterm command themselves - read as the role
    guard reads a command (its mask: words in quotes, comments and heredocs' bodies are not commands)."""
    import role_guard
    for name in ("agents.sh", "agents-morning.sh", "agents-lib.sh"):
        text = open(os.path.join(PKG, name), encoding="utf-8").read()
        found = [m.group(0) for m in re.finditer(r"(?<![\w.-])(tmux|wezterm)(?![\w-])", role_guard.mask(text))]
        assert found == [], (name, found)
    assert 'term_kill() {' in open(os.path.join(PKG, "term.sh"), encoding="utf-8").read()
