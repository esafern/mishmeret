"""A role run by pi (notes/PLAN-PI-ROLE.md): mishmeret/pi_guard.ts under pi itself, with a scripted provider (tests/pi:
a fake OpenAI-compatible server on 127.0.0.1, no model) giving pi fixed tool calls in a throwaway project whose own
config guards it and whose own hook shim records what it judged. Skipped only where `pi` is not on PATH, and saying so
(girsa-architect's Q4)."""
import json
import os
import shutil
import socket
import subprocess
import sys
import time

import pytest

from conftest import PKG, write_project

HERE = os.path.dirname(os.path.abspath(__file__))
PI = shutil.which("pi")
pytestmark = pytest.mark.skipif(not PI, reason="pi is not on PATH: the guard extension is tested only where pi runs")
# the project's own hook, as a project's shim: the config its CLAUDE_PROJECT_DIR names, the guard run on the event -
# and what it was given recorded, so a test sees which hook judged and where
HOOK = """import json, os, subprocess, sys
event = sys.stdin.read()
with open(os.environ["HOOK_LOG"], "a", encoding="utf-8") as fh:
    fh.write(json.dumps({"project": os.environ.get("CLAUDE_PROJECT_DIR"), "event": json.loads(event)}) + "\\n")
env = dict(os.environ, MISHMERET_CONFIG=os.path.join(os.environ["CLAUDE_PROJECT_DIR"], ".claude", "mishmeret.json"))
sys.exit(subprocess.run([sys.executable, %r], input=event, text=True, env=env).returncode)
""" % os.path.join(PKG, "role_guard.py")


def project(root, hook=True):
    """A throwaway project at `root`: its config guards it (its main tree is a git repository), and its hook shim."""
    write_project(root)
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    if hook:
        os.makedirs(os.path.join(root, ".claude", "hooks"), exist_ok=True)
        with open(os.path.join(root, ".claude", "hooks", "role_guard.py"), "w", encoding="utf-8") as fh:
            fh.write(HOOK)
    return str(root)


def pi_run(tmp_path, proj, script, *extra, role="ex-builder", agent_env="ex-operator", more=(), first_body=False):
    """pi's tool results, in the script's order, for `script` run in `proj` with the guard extension (and `extra`)."""
    port = socket.socket()
    port.bind(("127.0.0.1", 0))
    number = port.getsockname()[1]
    port.close()
    (tmp_path / "script.json").write_text(json.dumps(script), encoding="utf-8")
    log = tmp_path / "server.log"
    log.write_text("")
    server = subprocess.Popen([sys.executable, "-I", os.path.join(HERE, "pi", "fake_server.py"), str(number),
                               str(tmp_path / "script.json"), str(log)])
    try:
        time.sleep(0.5)
        args = [PI, "-p", "--no-extensions", "--no-skills", "--no-context-files", "--no-mcp", "--offline",
                "--no-session", "-e", os.path.join(HERE, "pi", "fake.ts"), "-e", os.path.join(PKG, "pi_guard.ts")]
        for e in extra:
            args += ["-e", e]
        args += ["--provider", "fake", "--model", "fake-chat", "--name", "ex-builder"] + list(more)
        args += ["--role", role] if role else []
        env = {k: v for k, v in os.environ.items() if not k.startswith("MISHMERET_")}
        env.update(FAKE_PORT=str(number), HOOK_LOG=str(tmp_path / "hook.log"), CLAUDE_CODE_AGENT=agent_env,
                   PROBE_TOOL_FILE=str(tmp_path / "probe_tool_ran"))
        out = subprocess.run(args + ["go"], cwd=proj, env=env, capture_output=True, text=True,
                             stdin=subprocess.DEVNULL, timeout=120)
    finally:
        server.kill()
        server.wait()
    rows = [json.loads(line) for line in log.read_text().splitlines()]
    assert out.returncode == 0 and rows, (out.returncode, out.stderr[-800:])
    return rows[-1]["results"] if not first_body else rows[0]["body"]


def test_the_guard_extension_judges_each_pi_tool_call_by_the_projects_own_hook(tmp_path):
    proj = project(tmp_path / "proj")
    outside = tmp_path / "outside"
    outside.mkdir()
    script = [["bash", {"command": "echo ok-from-pi"}],
              ["bash", {"command": "git push origin main"}],
              ["write", {"path": "x.txt", "content": "into the main tree"}],
              ["write", {"path": str(outside / "ok.md"), "content": "fine\n"}],
              ["write", {"path": str(outside / "late.md"), "content": "at 10:3x\n"}],
              ["edit", {"path": str(outside / "ok.md"), "edits": [{"oldText": "fine", "newText": "finer"},
                                                                  {"oldText": "\n", "newText": " at 10:3x\n"}]}],
              ["bash", {"command": "echo pwd=$(pwd -P) sid=${PI_SESSION_ID:-none} agent=$CLAUDE_CODE_AGENT"}],
              ["probe_tool", {}]]
    results = pi_run(tmp_path, proj, script, os.path.join(HERE, "pi", "extra_tool.ts"))
    assert len(results) == len(script), results
    echo, push, main_write, ok, late, edit, env_line, probe = results
    assert echo.strip() == "ok-from-pi", echo
    assert "pushing is the operator's" in push, push
    assert "this file is in the main tree" in main_write and not (tmp_path / "proj" / "x.txt").exists(), main_write
    # a write's content and an edit's text reach the time rule (girsa-verifier's LOW 1); an edit is blocked whole
    assert (outside / "ok.md").read_text() == "fine\n", ok
    assert "leaves a minute as x" in late and not (outside / "late.md").exists(), late
    assert "leaves a minute as x" in edit and (outside / "ok.md").read_text() == "fine\n", edit
    # the role in bash's environment over the one pi was started with; pi's ctx arrived (its session id); the folder
    # bash ran in is the one the guard judged (girsa-verifier's NOTE 1)
    real = os.path.realpath(proj)
    assert env_line.strip().startswith(f"pwd={real} sid=") and " sid=none" not in env_line, env_line
    assert env_line.strip().endswith("agent=ex-builder"), env_line
    assert "is a tool it does not know" in probe and "probe_tool" in probe, probe
    assert not (tmp_path / "probe_tool_ran").exists()
    # every judged call reached the project's own hook, CLAUDE_PROJECT_DIR the folder pi started in (its LOW 2), as the
    # session's role; the bash that printed its folder was judged at that folder
    judged = [json.loads(line) for line in (tmp_path / "hook.log").read_text().splitlines()]
    # (the edit's two edits each judged: the first passes, the second is refused)
    assert [j["event"]["tool_name"] for j in judged] == ["Bash", "Bash", "Write", "Write", "Write", "Edit", "Edit",
                                                         "Bash"], judged
    assert [j["event"]["tool_input"]["new_string"] for j in judged[5:7]] == ["finer", " at 10:3x\n"], judged[5:7]
    assert all(j["project"] == proj and j["event"]["agent_type"] == "ex-builder" for j in judged), judged
    assert os.path.realpath(judged[-1]["event"]["cwd"]) == real, judged[-1]


def test_no_role_is_judged_as_no_role_and_no_hook_runs_nothing(tmp_path):
    proj = project(tmp_path / "proj")
    script = [["bash", {"command": "echo ok"}], ["bash", {"command": "git push origin main"}]]
    echo, push = pi_run(tmp_path, proj, script, role="")
    assert echo.strip() == "ok" and "pushing is the operator's" in push and "started without a role" in push, push
    bare = project(tmp_path / "bare", hook=False)
    (tmp_path / "hook.log").unlink(missing_ok=True)
    echo, = pi_run(tmp_path, bare, [["bash", {"command": "echo should-not-run"}]])
    assert "should-not-run" not in echo and echo.strip(), echo                     # fail closed: no hook, no command


def test_the_shipped_skills_reach_pi_by_their_tree(tmp_path):
    """notes/PLAN-SHIPPED-SKILLS.md: pi reads a skill by an explicit `--skill` path, trusted or not, as agents.sh's pi
    line gives the shipped ones (measured on 2026-11-23: a link in .agents/skills/ is not read untrusted). Each shipped
    skill's description is in pi's first request, once."""
    proj = project(tmp_path / "proj")
    body = pi_run(tmp_path, proj, [], more=("--skill", os.path.join(PKG, "skills")), first_body=True)
    for name in sorted(os.listdir(os.path.join(PKG, "skills"))):
        head = open(os.path.join(PKG, "skills", name, "SKILL.md"), encoding="utf-8").read().split("---")[1]
        said = head.split("description: ", 1)[1].split("\n")[0][:60].replace("'", "&apos;")    # pi's list escapes it
        assert said in body, name
    assert body.count("<name>mishmeret-landing</name>") == 1, "each shipped skill once"
