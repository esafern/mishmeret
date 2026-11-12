"""The sessions: the night and morning runs, agents.sh, the resume finder, moved from Girsa's tests/test_pipeline_logic.py at 2aba11b0 (its history there). A placeholder project
(tests/conftest.py): its roles are Girsa's shapes under the prefix "ex-"."""
import json
import os
import subprocess
import sys

import pytest

from conftest import PKG, REPO  # noqa: F401  (REPO: the placeholder project's root, written by the fixture)


def test_role_sessions_finds_each_roles_latest_session_for_agents_sh_resume(tmp_path, capsys, monkeypatch):
    """The reviewer, 2026-10-11: "build the agents.sh resume option". tools/role_sessions.py names each role's LATEST
    transcript (by its agent-setting record): resumable, "live" when that session is running - never an older one of
    a running role - or "none". Placeholder roles and ids."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("role_sessions", os.path.join(PKG, "role_sessions.py"))
    rs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rs)

    def transcript(sid, role, mtime):
        recs = [{"type": "custom-title", "customTitle": role or "x", "sessionId": sid}]
        if role:
            recs.append({"type": "agent-setting", "agentSetting": role, "sessionId": sid})
        recs.append({"type": "user", "message": {"role": "user", "content": "placeholder"}, "sessionId": sid})
        path = tmp_path / f"{sid}.jsonl"
        path.write_text("".join(json.dumps(r) + "\n" for r in recs), encoding="utf-8")
        os.utime(path, (mtime, mtime))

    transcript("aaaa-old", "role-a", 1000)
    transcript("aaaa-new", "role-a", 3000)          # role-a's latest: resumed
    transcript("bbbb-old", "role-b", 1000)
    transcript("bbbb-run", "role-b", 2000)          # role-b's latest is running: never fall back to bbbb-old
    transcript("cccc-none", None, 4000)             # a session with no role is no role's
    monkeypatch.setenv("MISHMERET_TRANSCRIPTS", str(tmp_path))   # the project's folder (the config's rule, audit items 5, 16)
    stub = tmp_path / "bin"
    stub.mkdir()

    def claude_prints(text):                        # `claude agents --json --all`, stubbed first on PATH
        (stub / "claude").write_text(f"#!/bin/sh\nprintf '%s' '{text}'\n", encoding="utf-8")
        (stub / "claude").chmod(0o755)
    monkeypatch.setenv("PATH", f"{stub}{os.pathsep}{os.environ['PATH']}")
    claude_prints(json.dumps([{"sessionId": "bbbb-run"}]))
    assert rs.main(["role-a", "role-b", "role-c"]) == 0
    rows = [line.split("\t") for line in capsys.readouterr().out.splitlines()]
    assert rows[0][:2] == ["role-a", "aaaa-new"]
    assert rows[1] == ["role-b", "live", "bbbb-run"]
    assert rows[2] == ["role-c", "none"]
    # the running sessions unreadable: none counts as running, and it says so
    claude_prints("not json")
    assert rs.main(["role-b"]) == 0
    out = capsys.readouterr()
    assert out.out.split("\t")[:2] == ["role-b", "bbbb-run"] and "could not read" in out.err


def test_the_night_run_does_not_land_a_role_waiting_for_another_roles_work(tmp_path, monkeypatch, capsys):
    """The reviewer, 2026-10-11: "night run should not have told the ver to land when it had work to do. it should not
    have been idle." The verifier's corner said it waited for the builder's build; the night run sent it /land anyway,
    and the builder's HANDOFF came 37 s later. board.py's `waiting_on` (and `waiting-for ROLE`) reads a corner's wait;
    agents-morning.sh asks it before /land and leaves a role waiting for a role still running. Placeholder board."""
    import importlib.util
    monkeypatch.setenv("MISHMERET_BOARD_DIR", str(tmp_path / "board"))
    spec = importlib.util.spec_from_file_location("board", os.path.join(PKG, "board.py"))
    bd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bd)
    assert bd.waiting_on("ex-verifier") is None                          # no corner yet
    bd.set_status("ex-verifier", "waiting-agent", "ex-builder", "Waiting for a placeholder build")
    assert bd.waiting_on("ex-verifier") == "ex-builder"
    assert bd.main(["waiting-for", "ex-verifier"]) == 0 and capsys.readouterr().out.strip() == "ex-builder"
    bd.set_status("ex-verifier", now="still waiting, the words changed only")     # a text-only update keeps the wait
    assert bd.waiting_on("ex-verifier") == "ex-builder"
    bd.set_status("ex-verifier", "idle")
    assert bd.waiting_on("ex-verifier") is None
    assert bd.main(["waiting-for", "ex-verifier"]) == 0 and capsys.readouterr().out == ""
    # the night run asks it before /land, and lets a kept, left or closed role's wait go
    script = open(os.path.join(PKG, "agents-morning.sh"), encoding="utf-8").read()
    ask, land = script.index('board.py" waiting-for "$r"'), script.index('type_in "$pane" "$FINISH_EXIT"')
    assert ask < land
    check = script[ask:land]
    for marker in ('"$NIGHT/$w.kept"', '"$NIGHT/$w.left"', '"$NIGHT/$w.closed"', "still running - not idle"):
        assert marker in check, marker


def test_the_night_run_lands_a_role_under_the_limit_and_keeps_it_uncleared():
    """The reviewer, the Board #31, 2026-10-13: "c lower the limit to 200k so most times roles will be closed. if less
    than that - just land but not clear" (at 500,000 the operator was kept at 486,593 tokens, unlanded). Read from
    agents-morning.sh: the limit; a role under it is sent /land and marked land-only; each place that clears on "ready to
    clear" keeps a land-only role instead; a role so kept is not cleared on a later pass, and is looked at afresh once
    someone works with it again."""
    script = open(os.path.join(PKG, "agents-morning.sh"), encoding="utf-8").read()
    assert "CONTEXT_LIMIT=$MM_NIGHT_CONTEXT_LIMIT" in script
    under = script[script.index('if [ "${ctx:-0}" -lt "$CONTEXT_LIMIT" ]'):]
    under = under[:under.index("\n      fi\n")]
    assert 'type_in "$pane" "$FINISH_EXIT"' in under and '"$NIGHT/$r.land-only"' in under and "/clear" not in under
    # under the limit and over it, what is typed is the config's night.finish_exit_command - no name in the script
    assert script.count('type_in "$pane" "$FINISH_EXIT"') == 2 and '"/land"' not in script and '"/finish' not in script
    clears = [i for i in range(len(script)) if script.startswith('type_in "$pane" "/clear"', i)]
    assert len(clears) == 2, "a new place that clears must keep a land-only role too"
    for at in clears:                                                       # the check stands just before each
        assert 'if [ -e "$NIGHT/$r.land-only" ]; then keep_landed "$r"; continue; fi' in script[at - 300:at]
    assert '[ ! -e "$NIGHT/$r.landed-kept" ]' in script                    # kept after landing: not cleared next pass
    assert 'rm -f "$NIGHT/$r.kept" "$NIGHT/$r.landed-kept"' in script       # worked with again: looked at afresh


@pytest.mark.parametrize("kind", ["notice", "notice while waiting", "old notice", "no record", "landed"])
def test_the_night_run_does_not_take_a_land_answered_by_a_notice_for_a_landing(tmp_path, kind):
    """2026-10-30 and 10-31 (the Mishmeret audit's item 1, re-scoped by girsa-verifier): every role's /land was answered
    by a `<synthetic>` record, "You've hit your weekly limit", or left no record at all; the run read each as landed,
    typed the ask-ready sentence, and left it open. Now a notice is named in the night log and a transcript unchanged
    since /land is said not to have got it - neither asked to report back, nor, when the role waits, said to be asking
    you something (girsa-verifier's LOW 1: 2 of the 10-30 notices); a notice from BEFORE /land, the transcript changed
    after it, is no answer to it (LOW 2: on 10-31 three roles' newest assistant record was 10-30's notice) - that role,
    as a real landing, is asked to report back. A whole night run,
    not a dry one, behind stub claude, tmux, sleep, caffeinate and osascript: one role idle, its /land sent 20 minutes
    ago, its pane this test's parent process.
    SINCE 2026-11-10 (the reviewer, the first project's Board #183): what the run types and names is the config's
    night.finish_exit_command (the placeholder's /done-and-out), never a name written in the script; and THE RUN ENDS
    WHEN THE ROLES ARE CLOSED ("in the even [evening] after I'm idle I want the night run to exit and not restart") -
    four roles closed here, and no alert is shown, no Go waited for, no agents.sh started."""
    import datetime
    import time
    from conftest import write_project
    cfg = write_project(tmp_path)
    now = time.time()
    night = tmp_path / "scratch" / "state" / "night" / datetime.date.today().isoformat()
    night.mkdir(parents=True)
    (night / "ex-builder.land-sent").touch()
    os.utime(night / "ex-builder.land-sent", (now - 1200, now - 1200))
    def rec(kind_, at, **extra):
        stamp = datetime.datetime.fromtimestamp(now + at, datetime.timezone.utc).isoformat().replace("+00:00", "Z")
        return json.dumps({"type": kind_, "timestamp": stamp, **extra})
    notice = lambda at: rec("assistant", at, isApiErrorMessage=True, message={
        "model": "<synthetic>", "content": [{"type": "text", "text": "You've hit your weekly limit"}],
        "usage": {"input_tokens": 0, "output_tokens": 0}})
    records = [notice(-1300)] if kind == "old notice" else []
    records.append(rec("user", -1199, message={"role": "user", "content": "/land"}))
    if kind.startswith("notice"):
        records.append(notice(-1198))
    elif kind == "landed":
        records.append(rec("assistant", -1100, message={
            "model": "placeholder-model", "content": [{"type": "text", "text": "Landed."}],
            "usage": {"input_tokens": 10, "output_tokens": 5}}))
    transcript = tmp_path / "projects" / "the-project" / "s-1.jsonl"
    transcript.parent.mkdir(parents=True)
    transcript.write_text("\n".join(records if kind != "no record" else records[:0]) + "\n", encoding="utf-8")
    written = now - (1800 if kind == "no record" else 600)                 # before /land, or after it
    os.utime(transcript, (written, written))
    status = "waiting" if kind == "notice while waiting" else "idle"
    rows = json.dumps([{"name": "ex-builder", "status": status, "sessionId": "s-1", "pid": os.getpid()}])
    typed, shown = tmp_path / "typed.txt", tmp_path / "shown.txt"
    stubs = {"claude": f"if [ \"$1\" = agents ]; then echo '{rows}'; fi",
             "tmux": f"case \"$1\" in list-panes) echo '{os.getppid()} %1' ;; send-keys) echo \"$*\" >> '{typed}' ;; esac",
             "sleep": "exit 0", "caffeinate": "exit 0",
             "osascript": f"for a in \"$@\"; do printf '%s\\n' \"$a\"; done >> '{shown}'"}     # an argument a line
    (tmp_path / "bin").mkdir()
    for name, body in stubs.items():
        (tmp_path / "bin" / name).write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
        (tmp_path / "bin" / name).chmod(0o755)
    env = dict(os.environ, MISHMERET_CONFIG=cfg, PATH=f"{tmp_path / 'bin'}{os.pathsep}{os.environ['PATH']}")
    out = subprocess.run(["bash", os.path.join(PKG, "agents-morning.sh"), "--night"], env=env,
                         stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8", timeout=60)
    log = (night / "log.txt").read_text(encoding="utf-8")
    assert out.returncode == 0, out.stdout + out.stderr + log
    sent = typed.read_text(encoding="utf-8") if typed.exists() else ""
    named = ("ex-builder: /done-and-out was answered by a notice, not a finish - You've hit your weekly limit - left "
             "open for you")
    asked = "ex-builder: finished without saying it is ready to clear - asked to report back"
    expected = {"notice": named, "notice while waiting": named, "old notice": asked,
                "no record": "ex-builder: its transcript has not changed since /done-and-out was typed - it did not "
                             "reach the session", "landed": asked}[kind]
    assert expected in log, log
    assert "stopped to ask you something" not in log and (named in log) == kind.startswith("notice"), log
    assert ("Has this session finished every step of /done-and-out?" in sent) == (expected == asked), sent
    assert "/land" not in sent + log, "no command's name is written in the script"
    assert (night / "ex-builder.left").exists()
    # the night's end: four roles closed - the count, and the run is over
    said = shown.read_text(encoding="utf-8") if shown.exists() else ""
    assert "4 closed and not started again - start them, each in its pane, with: bash agents.sh" in log, log
    assert "display alert" not in said and "iTerm" not in said and "agents.sh" not in said + sent, said
    # the alert's text is osascript's argument, whole, never spliced into its script (notes/PLAN-AUDIT-FIXES.md, item
    # 4: agents-lib.sh's `alert`, the night run's and agents.sh's one form)
    assert (named in said.splitlines()) == kind.startswith("notice"), said
    assert "display notification (item 1 of a) with title (item 2 of a)" in said or not said, said
    assert not (night / ".running").exists(), "the lock, with the run's process id in it, goes with the run"


@pytest.mark.parametrize("percent", [100, 60])
def test_the_night_run_sends_no_land_while_a_plan_window_is_at_its_limit(tmp_path, percent):
    """The Board's #118, A, with girsa-verifier's ANSWER: on 2026-10-30 the night run sent /land into five sessions at the
    weekly limit, and each answered with a notice. A window at its limit in the Board's usage record (board.usage(),
    which drops a window once its reset has passed): the role is named "not landed - limit" with the reset, and no
    /land typed - the first night run after the reset lands it. Under the limit, /land as before. A whole night run
    behind stubs (ioreg saying you are idle), one role idle 20 minutes, a placeholder Board."""
    import datetime
    import time
    from conftest import write_project
    cfg = write_project(tmp_path)
    now = time.time()
    night = tmp_path / "scratch" / "state" / "night" / datetime.date.today().isoformat()
    (tmp_path / "board").mkdir()
    (tmp_path / "board" / "usage.json").write_text(json.dumps({
        "seven_day": {"used_percentage": percent, "resets_at": int(now) + 86400}, "seen_at": int(now), "session": None}),
        encoding="utf-8")
    transcript = tmp_path / "projects" / "the-project" / "s-1.jsonl"
    transcript.parent.mkdir(parents=True)
    transcript.write_text(json.dumps({"type": "assistant", "timestamp": "2026-01-01T00:00:00Z", "message": {
        "model": "placeholder-model", "usage": {"input_tokens": 10}}}) + "\n", encoding="utf-8")
    os.utime(transcript, (now - 1200, now - 1200))
    rows = json.dumps([{"name": "ex-builder", "status": "idle", "sessionId": "s-1", "pid": os.getpid()}])
    typed = tmp_path / "typed.txt"
    stubs = {"claude": f"if [ \"$1\" = agents ]; then echo '{rows}'; fi",
             "tmux": f"case \"$1\" in list-panes) echo '{os.getppid()} %1' ;; send-keys) echo \"$*\" >> '{typed}' ;; esac",
             "ioreg": "echo '  \"HIDIdleTime\" = 9000000000000'", "sleep": "exit 0", "caffeinate": "exit 0",
             "osascript": "exit 0"}
    (tmp_path / "bin").mkdir()
    for name, body in stubs.items():
        (tmp_path / "bin" / name).write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
        (tmp_path / "bin" / name).chmod(0o755)
    env = dict(os.environ, MISHMERET_CONFIG=cfg, PATH=f"{tmp_path / 'bin'}{os.pathsep}{os.environ['PATH']}")
    env.pop("MISHMERET_BOARD_DIR", None)
    out = subprocess.run(["bash", os.path.join(PKG, "agents-morning.sh"), "--night"], env=env,
                         stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8", timeout=60)
    log = (night / "log.txt").read_text(encoding="utf-8")
    assert out.returncode == 0, out.stdout + out.stderr + log
    sent = typed.read_text(encoding="utf-8") if typed.exists() else ""
    limited = "ex-builder: not finished - limit, the 7-day window, resets " in log
    assert limited == (percent == 100), log
    assert ("/done-and-out" in sent) == (percent < 100), sent      # the config's night.finish_exit_command
    if limited:
        assert "1 not finished for the plan's limit" in log, log


@pytest.mark.parametrize("kind", ["cleared", "worked"])
def test_the_night_run_sends_exit_not_land_to_a_pane_holding_only_a_clear(tmp_path, kind):
    """2026-11-04, the architect's finding: a pane cleared by hand and left open - its transcript the /clear alone, no
    assistant turn - was sent a whole /land ("its context could not be read"). Now it is sent /exit, never /land, and
    counted closed; a session with an assistant turn is sent /land as before. A whole night run behind stubs (ioreg
    saying you are idle; claude listing the role until /exit is typed), one role idle 20 minutes."""
    import datetime
    import time
    from conftest import write_project
    cfg = write_project(tmp_path)
    now = time.time()
    night = tmp_path / "scratch" / "state" / "night" / datetime.date.today().isoformat()
    (tmp_path / "board").mkdir()
    records = [{"type": "custom-title", "customTitle": "ex-builder", "sessionId": "s-1"},
               {"type": "user", "isMeta": True, "message": {"role": "user", "content": "<local-command-caveat>"}},
               {"type": "user", "message": {"role": "user", "content": "<command-name>/clear</command-name>"}}]
    if kind == "worked":
        records.append({"type": "assistant", "timestamp": "2026-01-01T00:00:00Z", "message": {
            "model": "placeholder-model", "usage": {"input_tokens": 10}}})
    transcript = tmp_path / "projects" / "the-project" / "s-1.jsonl"
    transcript.parent.mkdir(parents=True)
    # compact, as Claude Code writes its transcripts (girsa-verifier's MEDIUM 1 on f4edc08: 273 of 438 real ones hold
    # `"type":"assistant"`, none the spaced form); the limit tests keep json.dumps's spaced form, so each half of the
    # guard's ` ?` has a test
    transcript.write_text("".join(json.dumps(r, separators=(",", ":")) + "\n" for r in records), encoding="utf-8")
    os.utime(transcript, (now - 1200, now - 1200))
    rows = json.dumps([{"name": "ex-builder", "status": "idle", "sessionId": "s-1", "pid": os.getpid()}])
    typed = tmp_path / "typed.txt"
    stubs = {"claude": f"if [ \"$1\" = agents ]; then grep -qs /exit '{typed}' && echo '[]' || echo '{rows}'; fi",
             "tmux": f"case \"$1\" in list-panes) echo '{os.getppid()} %1' ;; send-keys) echo \"$*\" >> '{typed}' ;; esac",
             "ioreg": "echo '  \"HIDIdleTime\" = 9000000000000'", "sleep": "exit 0", "caffeinate": "exit 0",
             "osascript": "exit 0"}
    (tmp_path / "bin").mkdir()
    for name, body in stubs.items():
        (tmp_path / "bin" / name).write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
        (tmp_path / "bin" / name).chmod(0o755)
    env = dict(os.environ, MISHMERET_CONFIG=cfg, PATH=f"{tmp_path / 'bin'}{os.pathsep}{os.environ['PATH']}")
    env.pop("MISHMERET_BOARD_DIR", None)
    out = subprocess.run(["bash", os.path.join(PKG, "agents-morning.sh"), "--night"], env=env,
                         stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8", timeout=60)
    log = (night / "log.txt").read_text(encoding="utf-8")
    assert out.returncode == 0, out.stdout + out.stderr + log
    sent = typed.read_text(encoding="utf-8") if typed.exists() else ""
    assert ("/done-and-out" in sent) == (kind == "worked") and ("/exit" in sent) == (kind == "cleared"), sent
    assert ("ex-builder: its pane holds only a /clear - nothing to finish; /exit" in log) == (kind == "cleared"), log
    if kind == "cleared":
        assert "ex-builder: not running - closed by this run (cleared, then /exit)" in log, log


def test_the_night_run_can_be_skipped_without_turning_it_off(tmp_path):
    """The reviewer, 2026-10-21: "give me a clean way to tell it not to run w/o turning it off". --skip-tonight holds
    today's run, --skip every run, --resume removes both; a held run ends before it looks at anything (a dry run in a
    placeholder folder: no dry-run folder made)."""
    import datetime
    import subprocess
    from conftest import write_project
    night = tmp_path / "scratch" / "state" / "night"
    cfg = write_project(tmp_path)
    def run(*args, dry=False):
        env = dict(os.environ, MISHMERET_CONFIG=cfg, **({"MISHMERET_NIGHT_DRY_RUN": "1"} if dry else {}))
        return subprocess.run(["bash", os.path.join(PKG, "agents-morning.sh"), *args], env=env, capture_output=True,
                              text=True, encoding="utf-8", timeout=30)
    for hold, file in (("--skip-tonight", f"skip-{datetime.date.today().isoformat()}"), ("--skip", "skip")):
        assert run(hold).returncode == 0 and (night / file).exists(), hold
        held = run("--night", dry=True)
        assert held.returncode == 0 and f"skipped: {night / file}" in held.stdout, held.stdout + held.stderr
        assert not list(night.glob("dry-*")), "a held run looked at the roles"
        assert run("--resume").returncode == 0 and not (night / file).exists(), hold
    # A RUN ALREADY GOING stops at its next look (ex-verifier's LOW on 7ba22ad8): the loop's first line reads the files
    script = open(os.path.join(PKG, "agents-morning.sh"), encoding="utf-8").read()
    loop = script.index("  while :; do\n", script.index('if [ "${1:-}" = "--night" ]'))
    first = [l.strip() for l in script[loop:].split("\n")[1:4] if not l.strip().startswith("#")][0]
    assert first.startswith('if f=$(skip_file "$RUN_DATE"); then') and first.endswith("break; fi"), first   # the end runs
    # TYPED AFTER MIDNIGHT: a run going since the evening before is held by its own date's file too
    (night / "2026-01-01" / ".running").mkdir(parents=True)
    assert "going since 2026-01-01 18:00 stops" in run("--skip-tonight").stdout and (night / "skip-2026-01-01").exists()
    assert run("--resume").returncode == 0 and not list(night.glob("skip-*")), "--resume removes every dated hold"


@pytest.mark.parametrize("script", ["agents.sh", "agents-morning.sh"])
def test_a_start_script_with_no_project_named_says_where_to_run_it(tmp_path, script):
    """Two runs of 2026-11-05, both Mishmeret's scripts run directly, not through the project's own: (1) in Mishmeret's
    folder, refused with "the project's Mishmeret config cannot be read" - not saying where to run it from; (2) from the
    project's folder, where it read the project's config, exported it to every role it started with no mark that
    Mishmeret had set it - so the project's shim in a role's worktree kept the main clone's config - and ran Mishmeret's
    checkout, not the commit the project pins. With no config named (MISHMERET_CONFIG unset: no shim, no person set it),
    a start script now stops before anything, saying to run the project's own script from its folder. Placeholder
    projects in git repositories, a stub tmux recording what it would pass to the roles' panes."""
    record = tmp_path / "tmux-env.txt"
    stub = tmp_path / "bin"
    stub.mkdir()
    (stub / "tmux").write_text(f"#!/bin/sh\nenv | grep '^MISHMERET_CONFIG' >> '{record}'\nexit 0\n", encoding="utf-8")
    (stub / "tmux").chmod(0o755)
    env = {k: v for k, v in os.environ.items() if k not in ("MISHMERET_CONFIG", "MISHMERET_CONFIG_BY_SHIM", "CLAUDE_PROJECT_DIR")}
    env["PATH"] = f"{stub}{os.pathsep}{env['PATH']}"
    from conftest import write_project
    project, bare = tmp_path / "project", tmp_path / "no-config"
    for repo in (project, bare):
        repo.mkdir()
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
    write_project(project)
    for where in (project, bare):           # (2), and (1): a repository with no project config, as Mishmeret's was
        out = subprocess.run(["bash", os.path.join(PKG, script)], cwd=where, env=env, capture_output=True, text=True,
                             stdin=subprocess.DEVNULL, timeout=60)
        assert out.returncode == 1 and f"run the project's own {script} from its folder" in out.stderr, \
            (where.name, out.returncode, out.stderr)
        assert not record.exists(), f"tmux reached from {where.name}: {record.read_text()}"
    # a config named by hand (a test's placeholder project, a person who means it) still runs
    named = subprocess.run(["bash", os.path.join(PKG, "agents.sh")], cwd=bare, env=dict(env, MISHMERET_CONFIG=str(project / ".claude" / "mishmeret.json")),
                           capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=60)
    assert named.returncode == 0 and record.read_text().startswith("MISHMERET_CONFIG="), (named.stderr, record.read_text())


def test_a_role_starts_with_no_project_config_inherited(tmp_path):
    """girsa-architect's answer 2 on notes/PLAN-START-SCRIPTS.md: a pane's shell holds the tmux server's environment -
    a config there, unmarked, was kept by the shim in every role's worktree (2026-11-05). agents.sh types each role's
    start with both variables dropped, so its own shim sets its own. A fresh start behind a stub tmux (no session
    running) recording what is typed into each pane; the config named by hand, as R leaves it."""
    typed = tmp_path / "typed.txt"
    stub = tmp_path / "bin"
    stub.mkdir()
    (stub / "tmux").write_text("#!/bin/sh\ncase \"$1\" in has-session) exit 1 ;; new-session|split-window) echo %1 ;;"
                               f" send-keys) echo \"$*\" >> '{typed}' ;; esac\nexit 0\n", encoding="utf-8")
    (stub / "tmux").chmod(0o755)
    env = dict(os.environ, PATH=f"{stub}{os.pathsep}{os.environ['PATH']}", TERM="dumb")
    out = subprocess.run(["bash", os.path.join(PKG, "agents.sh")], env=env, capture_output=True, text=True,
                         stdin=subprocess.DEVNULL, timeout=60)
    starts = [line for line in typed.read_text().splitlines() if "claude --agent" in line]
    assert out.returncode == 0 and len(starts) == 5, (out.returncode, out.stderr, starts)
    assert all("&& env -u MISHMERET_CONFIG -u MISHMERET_CONFIG_BY_SHIM claude --agent ex-" in s for s in starts), starts
    assert "$CLEAN claude --resume $sid" in open(os.path.join(PKG, "agents.sh"), encoding="utf-8").read(), "the resume too"


def test_the_agents_scripts_share_one_clone_one_role_list_and_one_pane_lookup():
    """The duplication audit's E26 (the reviewer, Board #82 A, 2026-10-26: the scripts in the operator's lane): agents.sh
    and agents-morning.sh each kept the role list, the clone, the session-to-pane lookup and the transcript lookup, and
    with the clone set the night run read one clone while its Go started the roles, through agents.sh, in another. Both
    source agents-lib.sh; it alone holds them and reads the project's config - named by the project's shim or by hand,
    never guessed from the current folder. The Go itself went on 2026-11-10 (the night run starts nothing), and with
    it the new window that had to be given the config and the shim's mark."""
    read = lambda name: open(os.path.join(PKG, name), encoding="utf-8").read()
    lib, start, night = read("agents-lib.sh"), read("agents.sh"), read("agents-morning.sh")
    source = '. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/agents-lib.sh"'
    assert source in start and source in night
    assert 'MM_CFG=$(python3 "$HERE/config.py" --shell)' in lib and 'DIR="$MM_ROOT"' in lib
    assert '[ -n "${MISHMERET_CONFIG:-}" ] ||' in lib and "MISHMERET_CONFIG:-$DIR" not in lib, "no config guessed, none set"
    for copy in ("ROLES=", "\nDIR=\"", "claude agents --json", '.jsonl 2>/dev/null', 'list-panes -s -t "$SESSION" -F \'#{pane_pid} #{pane_id}\'',
                 "PROJECTS=", "config.py --shell"):
        assert copy in lib, copy
        assert copy not in start and copy not in night, f"a second copy of {copy!r}"
    for gone in ("create window", "Go starts", 'buttons {\\"Not today\\"', 'agents.sh" --restart'):
        assert gone not in night, f"the night run and the morning run start nothing: {gone!r}"
    # ONE HOME FOR THE CLOSING SENTENCE'S RULE (girsa-architect, 2026-11-10): role_usage.py's, asked by the night run
    # here and by the Stop hook - no second copy of the transcript reader in the shell
    assert '"$PY" "$HERE/role_usage.py" closing "$f"' in night and "READY_END" not in night
    assert "role_usage.closing(" in read("finish_hook.py")


def test_the_morning_run_counts_a_role_idle_once_its_turn_has_ended(tmp_path):
    """0NA, 2026-10-26: agents-morning.sh's morning wait counted a role busy while `claude agents` called it busy only
    for a background task of its own (the operator's keep-alive loop, a `board.py wait`), though its turn had ended - so
    the wait could not end. The Board (1e318c4a) and keepalive_due.py read role_usage.turn_ended; agents-lib.sh's
    role_state does the same, and the morning's states() reads it. A stub `claude` and placeholder transcripts."""
    import subprocess
    bin_dir, tx = tmp_path / "bin", tmp_path / "tx"
    bin_dir.mkdir()
    tx.mkdir()
    rows = [{"name": "ex-builder", "status": "busy", "sessionId": "ended", "pid": 1},
            {"name": "ex-verifier", "status": "busy", "sessionId": "open", "pid": 2},
            {"name": "ex-architect", "status": "busy", "sessionId": "none", "pid": 3},
            {"name": "ex-ui-steward", "status": "idle", "sessionId": "idle", "pid": 4}]
    stub = bin_dir / "claude"
    stub.write_text("#!/bin/sh\ncat <<'EOF'\n" + json.dumps(rows) + "\nEOF\n", encoding="utf-8")
    stub.chmod(0o755)
    closing = {"type": "system", "subtype": "turn_duration"}
    for sid, recs in (("ended", ({"type": "user"}, {"type": "assistant"}, closing)), ("open", (closing, {"type": "user"}))):
        (tx / f"{sid}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in recs), encoding="utf-8")
    env = dict(os.environ, MISHMERET_TRANSCRIPTS=str(tx), PATH=f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    lib = os.path.join(PKG, "agents-lib.sh")
    out = subprocess.run(["bash", "-c", f'. "{lib}"; for r in $ROLES; do echo "$r $(role_state "$r")"; done'], env=env,
                         capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert out.returncode == 0, out.stderr
    assert sorted(out.stdout.split("\n")[:5]) == ["ex-architect busy",    # busy, no transcript: unknown is not ended
                                                   "ex-builder idle",       # busy, its turn ended: idle
                                                   "ex-operator absent",
                                                   "ex-ui-steward idle",
                                                   "ex-verifier busy"], out.stdout   # busy, a prompt after the close
    morning = open(os.path.join(PKG, "agents-morning.sh"), encoding="utf-8").read()
    assert 'echo "$r $(role_state "$r")"' in morning, "the morning's states() reads role_state"


def test_the_morning_run_starts_the_roles_when_none_is_running(tmp_path):
    """The reviewer, 2026-10-27: "agents_morning should just call agents when appr. [appropriate] rather than tell me to
    do it" - after a restart of the Mac, with none of the five running, it said "Start them with: bash agents.sh" and
    stopped. It now runs plain agents.sh itself (never --restart) - at step 1 only: gone during step 2's landing, the
    roles stopped without landing, and the run stops naming --resume rather than start fresh sessions over them
    (ex-verifier's LOW on c524fb2e). A stub `claude` (five idle until its `update`, then none), stub tmux and sleep,
    and a placeholder agents.sh in a temporary clone."""
    import subprocess
    from conftest import write_project
    (tmp_path / "bin").mkdir()
    cfg = write_project(tmp_path)
    stub = tmp_path / "bin" / "claude"
    stub.write_text("#!/bin/sh\necho '[]'\n", encoding="utf-8")
    stub.chmod(0o755)
    (tmp_path / "agents.sh").write_text('echo "placeholder agents.sh ran with: [$*]"\n', encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k != "TMUX"}           # not inside the roles' own tmux session
    env.update(MISHMERET_CONFIG=cfg, PATH=f"{tmp_path / 'bin'}{os.pathsep}{os.environ['PATH']}")
    out = subprocess.run(["bash", os.path.join(PKG, "agents-morning.sh")], env=env, stdin=subprocess.DEVNULL,
                         capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert out.returncode == 0, out.stdout + out.stderr
    assert "starting them: bash agents.sh" in out.stdout and "placeholder agents.sh ran with: []" in out.stdout, out.stdout
    # A PROJECT OF FOUR ROLES, none running, is started too (the Mishmeret audit's item 2: `-eq 5` sent it on to step 2)
    from conftest import project_config
    four = tmp_path / "four"
    roles = [dict(r, tmux=False, colour="") if r["short"] == "architect" else r for r in project_config(four)["roles"]]
    env4 = dict(env, MISHMERET_CONFIG=write_project(four, roles=roles))
    (four / "agents.sh").write_text('echo "placeholder agents.sh ran with: [$*]"\n', encoding="utf-8")
    out = subprocess.run(["bash", os.path.join(PKG, "agents-morning.sh")], env=env4, stdin=subprocess.DEVNULL,
                         capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert out.returncode == 0 and "starting them: bash agents.sh" in out.stdout, out.stdout + out.stderr
    # ALL FIVE IDLE AT STEP 1, NONE AFTER STEP 2'S `claude update`: a stop that names --resume, agents.sh not run
    rows = json.dumps([{"name": r, "status": "idle", "sessionId": "-", "pid": 1} for r in
                       ("ex-operator", "ex-builder", "ex-verifier", "ex-ui-steward", "ex-architect")])
    stub.write_text(f"#!/bin/sh\nif [ \"$1\" = update ]; then touch '{tmp_path / 'updated'}'; exit 0; fi\n"
                    f"if [ -e '{tmp_path / 'updated'}' ]; then echo '[]'; else echo '{rows}'; fi\n", encoding="utf-8")
    for name in ("tmux", "sleep"):
        (tmp_path / "bin" / name).write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        (tmp_path / "bin" / name).chmod(0o755)
    out = subprocess.run(["bash", os.path.join(PKG, "agents-morning.sh")], env=env, input="yes\n",
                         capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert out.returncode == 1, out.stdout + out.stderr
    assert "they stopped during step 2" in out.stdout and "bash agents.sh --resume" in out.stdout, out.stdout
    assert "starting them" not in out.stdout and "placeholder agents.sh ran" not in out.stdout, out.stdout


def test_the_morning_run_types_the_projects_finish_command_and_names_each_role_starting_nothing(tmp_path):
    """The reviewer, 2026-11-10 (the first project's Board #183): a finished session is cleared, exited and started
    again by the Stop hook - so the morning run's old step 3, `agents.sh --restart`, would end the sessions the hook
    had just started. It now types the config's night.finish_command (the placeholder's /done-for-now), and step 3
    only names each role BY ITS SESSION, not by its process (girsa-architect: a role the hook did not reach is
    running and idle - in the session it had). A stub `claude` (five idle; after `update`, one gone, two in a new
    session, two in the session they had), a stub tmux whose one pane - found for ex-verifier alone - shows the
    closing sentence, and a placeholder agents.sh that must not run."""
    from conftest import write_project
    (tmp_path / "bin").mkdir()
    cfg = write_project(tmp_path)
    (tmp_path / "agents.sh").write_text('echo "placeholder agents.sh ran with: [$*]"\n', encoding="utf-8")
    row = lambda name, sid, pid=1: {"name": name, "status": "idle", "sessionId": sid, "pid": pid}
    before = json.dumps([row("ex-operator", "o1"), row("ex-builder", "b1"), row("ex-verifier", "v1", os.getpid()),
                         row("ex-ui-steward", "u1"), row("ex-architect", "a1")])
    after = json.dumps([row("ex-builder", "b2"), row("ex-verifier", "v1", os.getpid()), row("ex-ui-steward", "u2"),
                        row("ex-architect", "a1")])
    typed = tmp_path / "typed.txt"
    stubs = {"claude": f"if [ \"$1\" = update ]; then touch '{tmp_path / 'updated'}'; exit 0; fi\n"
                       f"if [ -e '{tmp_path / 'updated'}' ]; then echo '{after}'; else echo '{before}'; fi",
             "tmux": f"case \"$1\" in list-panes) echo '{os.getppid()} %1' ;; send-keys) echo \"$*\" >> '{typed}' ;;\n"
                     " capture-pane) printf 'Done.\\n  The session is ready to clear.\\n' ;; esac",
             "sleep": "exit 0"}
    for name, body in stubs.items():
        (tmp_path / "bin" / name).write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
        (tmp_path / "bin" / name).chmod(0o755)
    env = dict(os.environ, MISHMERET_CONFIG=cfg, PATH=f"{tmp_path / 'bin'}{os.pathsep}{os.environ['PATH']}")
    out = subprocess.run(["bash", os.path.join(PKG, "agents-morning.sh")], env=env, input="yes\n",
                         capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert out.returncode == 0, out.stdout + out.stderr
    sent = typed.read_text(encoding="utf-8")
    assert "/done-for-now" in sent and "/land" not in sent + out.stdout and "/done-and-out" not in sent, sent
    said = out.stdout[out.stdout.index("Step 3 - each role now:"):]
    assert "ex-operator: not running - bash agents.sh starts it in its pane" in said, said
    for started in ("ex-builder", "ex-ui-steward"):
        assert f"{started}: finished, and started again in a new session" in said, said
    assert "ex-verifier: said it is ready to clear and is still in the session it had" in said and \
        "the Stop hook (finish_hook.py)" in said, said
    assert "ex-architect: still in the session it had - it did not finish; look at its pane" in said, said
    assert "placeholder agents.sh ran" not in out.stdout, "the morning run starts nothing"
    # a project whose config names no finish command: said, and nothing typed
    from conftest import project_config
    bare = tmp_path / "bare"
    night = {k: v for k, v in project_config(bare)["night"].items() if not k.startswith("finish")}
    typed.unlink()
    for args, key in (([], "night.finish_command"), (["--night"], "night.finish_exit_command")):
        out = subprocess.run(["bash", os.path.join(PKG, "agents-morning.sh"), *args], input="yes\n", capture_output=True,
                             env=dict(env, MISHMERET_CONFIG=write_project(bare, night=night)), text=True, timeout=60)
        assert out.returncode == 1 and f"the project's config names no {key}" in out.stderr, (args, out.stderr)
    assert not typed.exists(), typed.read_text()


def test_the_keepalive_check_says_a_crash_and_pings_a_due_role_once(tmp_path):
    """The Mishmeret audit's item 4: the operator runs `until keepalive_due.py --self <id>; do sleep 300; done`, exit 1
    meaning none due - and a crash (an empty `claude agents` answer) exited 1 too, so the loop slept on and no role was
    ever pinged. A crash now prints KEEPALIVE CHECK FAILED and exits 0. And the check itself, its first test: one idle
    role 50 minutes past its last call with 30k context is due, and not again for the same call. Placeholder project,
    stub `claude`, placeholder transcripts."""
    import datetime
    from conftest import write_project
    cfg = write_project(tmp_path)
    (tmp_path / "scratch" / "state").mkdir(parents=True)
    tx = tmp_path / "tx"
    tx.mkdir()
    (tmp_path / "bin").mkdir()
    claude = tmp_path / "bin" / "claude"
    env = dict(os.environ, MISHMERET_CONFIG=cfg, MISHMERET_TRANSCRIPTS=str(tx),
               MISHMERET_BOARD_DIR=str(tmp_path / "board"), PATH=f"{tmp_path / 'bin'}{os.pathsep}{os.environ['PATH']}")
    def run(answer):
        claude.write_text(f"#!/bin/sh\ncat <<'END'\n{answer}\nEND\n", encoding="utf-8")
        claude.chmod(0o755)
        return subprocess.run([sys.executable, os.path.join(PKG, "keepalive_due.py"), "--self", "me"], env=env,
                              capture_output=True, text=True, encoding="utf-8", timeout=60)
    out = run("")
    assert out.returncode == 0 and out.stdout.startswith("KEEPALIVE CHECK FAILED: JSONDecodeError"), out.stdout + out.stderr
    # a bad config is said the same way: it was read at import, before main's catch, and exited 1 ("none due")
    # (Girsa's loose ends E4, Board #131 B)
    bad = tmp_path / "bad.json"
    bad.write_text("{ not json", encoding="utf-8")
    good, env["MISHMERET_CONFIG"] = env["MISHMERET_CONFIG"], str(bad)
    out = run("[]")
    assert out.returncode == 0 and out.stdout.startswith("KEEPALIVE CHECK FAILED: ConfigError"), out.stdout + out.stderr
    env["MISHMERET_CONFIG"] = good
    when = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=50)).isoformat()
    (tx / "s-1.jsonl").write_text(json.dumps({"type": "assistant", "timestamp": when, "message": {
        "usage": {"input_tokens": 10, "cache_read_input_tokens": 30000, "cache_creation_input_tokens": 0}}}) + "\n",
        encoding="utf-8")
    rows = json.dumps([{"name": "ex-builder", "kind": "interactive", "sessionId": "s-1", "status": "idle",
                        "pid": os.getpid()}])
    out = run(rows)
    assert out.returncode == 0 and out.stdout.startswith("PING ex-builder s-1 idle 50 min, context 30k, idle"), out.stdout + out.stderr
    out = run(rows)
    assert out.returncode == 1 and out.stdout == "", "pinged twice for the same call"


def test_one_reader_of_a_transcripts_last_call_passes_over_a_notices_zeros(tmp_path, monkeypatch):
    """The Mishmeret audit's item 9: the night run, the status line and the keep-alive check each read a transcript's
    last call their own way, and two disagreed with the first - at a usage-limit notice (a `<synthetic>` record whose
    usage is all zeros) the status line lost the corner's "it was Nk at" line and the keep-alive took the notice as the
    last call, so that role was never pinged. role_usage.last_call is the one reader; each of the three gives the call
    before the notice. Placeholder transcript."""
    import importlib.util
    path = tmp_path / "s-1.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in (
        {"type": "assistant", "timestamp": "2030-01-02T10:00:00Z", "message": {"usage": {
            "input_tokens": 5, "cache_read_input_tokens": 40000, "cache_creation_input_tokens": 0}}},
        {"type": "assistant", "timestamp": "2030-01-02T10:05:00Z", "isSidechain": True, "message": {"usage": {
            "input_tokens": 9}}},
        {"type": "assistant", "timestamp": "2030-01-02T10:10:00Z", "message": {"model": "<synthetic>", "usage": {
            "input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}}},
    )) + "\n", encoding="utf-8")
    sys.path.insert(0, PKG)
    import role_usage
    at, ctx = role_usage.last_call(str(path))
    assert (at.isoformat(), ctx) == ("2030-01-02T10:00:00+00:00", 40005)
    out = subprocess.run([sys.executable, os.path.join(PKG, "role_usage.py"), "context", str(path)],
                         capture_output=True, text=True, encoding="utf-8")
    assert out.stdout == "40005\n", out                                              # the night run's context_of
    spec = importlib.util.spec_from_file_location("statusline", os.path.join(PKG, "statusline.py"))
    sl = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sl)
    assert sl.last_turn(str(path)) == {"context": 40005, "at": int(at.timestamp())}  # the corner's "it was Nk at"
    spec = importlib.util.spec_from_file_location("keepalive_due", os.path.join(PKG, "keepalive_due.py"))
    kd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(kd)
    monkeypatch.setenv("MISHMERET_TRANSCRIPTS", str(tmp_path))     # last_call asks role_usage.project_dir() when called
    assert kd.last_call("s-1") == (at, 40005)                                        # the keep-alive's


SHORT, LONG = "The session is ready to clear.", "The session is ready to clear and exit."


def test_the_closing_sentences_rule_has_one_home_and_reads_a_message_and_a_transcript(tmp_path):
    """The reviewer, 2026-11-10 (the first project's Board #183, and "add finish-and-exit and have the night run use
    that"): two closing sentences - after the short one the session is cleared, exited and started again ("again"),
    after the longer cleared and exited and nothing started ("exit"). role_usage.closing is the rule, whole and as the
    last line (girsa-verifier, 2026-10-11: "I am not ready to clear yet" matched a loose one): the Stop hook asks it
    of a message, the night run of a transcript (said_closing, `role_usage.py closing PATH`, the shell reader moved)."""
    import role_usage
    for text, want in ((SHORT, "again"), (LONG, "exit"), ("Done:\n- a\n\n**" + SHORT + "**\n\n", "again"),
                       ("All steps done.\n`" + LONG + "`", "exit"),
                       ("I am not ready to clear yet.", None), (SHORT + " Then I rest.", None),
                       (SHORT + "\nOne more thing: x is left.", None), ("The rule: end with \"" + SHORT + "\"", None),
                       ("Not finished: the state file is left.", None), (LONG.replace(" and exit", " and exit now"), None),
                       ("", None), (None, None)):
        assert role_usage.closing(text) == want, text
    said = lambda text: {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}
    prompt = {"type": "user", "message": {"content": "one more thing"}}
    tool = {"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok"}]}}
    side = dict(said("a subagent's words"), isSidechain=True)
    path = tmp_path / "s.jsonl"
    for records, want in (([said("x"), said("Done.\n" + LONG)], "exit"), ([said(SHORT), tool, side], "again"),
                          ([said(SHORT), prompt], None), ([said(SHORT), said("More work done.")], None), ([], None)):
        path.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
        assert role_usage.said_closing(str(path)) == want, records
        out = subprocess.run([sys.executable, os.path.join(PKG, "role_usage.py"), "closing", str(path)],
                             capture_output=True, text=True)
        assert (out.returncode, out.stdout.strip()) == ((0, want) if want else (1, "")), (records, out.stderr)
    # the pane's form of the same rule, for text tmux captured: either sentence on a line of its own
    morning = open(os.path.join(PKG, "agents-morning.sh"), encoding="utf-8").read()
    assert r"The session is ready to clear( and exit)?\.[*_`]*[[:space:]]*$'" in morning


@pytest.mark.parametrize("case, message, role, pane, started", [
    ("the short sentence", "Done.\n" + SHORT, "ex-builder", "%3", ["ex-builder", "%3"]),
    ("the longer sentence", "Done.\n**" + LONG + "**", "ex-builder", "%3", ["ex-builder", "%3", "exit"]),
    ("not said", "I am not ready to clear yet.", "ex-builder", "%3", None),
    ("a step undone", "Not finished: the state file is left.", "ex-builder", "%3", None),
    ("inside a line", "Its rule: " + SHORT, "ex-builder", "%3", None),
    ("no message", None, "ex-builder", "%3", None),
    ("not in tmux", SHORT, "ex-builder", None, None),
    ("a role with no pane", SHORT, "ex-demo-operator", "%3", None),
    ("no role's session", SHORT, None, "%3", None),
    ("a name that is no role", SHORT, "someone", "%3", None)])
def test_the_stop_hook_hands_a_finished_roles_pane_to_agents_sh_next(monkeypatch, case, message, role, pane, started):
    """The reviewer, 2026-11-10: "during the day I want to clear a session after landing, then exit and start a new
    one." finish_hook.py, on Stop: the turn's last message (the hook's own `last_assistant_message` - the transcript
    does not hold it yet, measured) ending with a closing sentence, in the session of a role with a pane, running in
    one - `agents.sh --next ROLE PANE`, with `exit` after the longer sentence, started detached. Anything else:
    nothing started, nothing printed. The start is recorded here, never run."""
    import importlib.util
    import io
    spec = importlib.util.spec_from_file_location("finish_hook", os.path.join(PKG, "finish_hook.py"))
    hook = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hook)
    calls = []
    monkeypatch.setattr(hook.subprocess, "Popen", lambda args, **kw: calls.append((args, kw)))
    for name, value in (("CLAUDE_CODE_AGENT", role), ("TMUX_PANE", pane)):
        monkeypatch.setenv(name, value) if value else monkeypatch.delenv(name, raising=False)
    data = {"hook_event_name": "Stop", "session_id": "s-1"}
    if message is not None:
        data["last_assistant_message"] = message
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(data)))
    assert hook.main() is None
    if started is None:
        assert calls == [], case
    else:
        (args, kw), = calls
        assert args == ["bash", os.path.join(PKG, "agents.sh"), "--next"] + started, case
        assert kw["start_new_session"] is True, "detached: it outlives the session it exits"
    monkeypatch.setattr(sys, "stdin", io.StringIO("not json"))
    assert hook.main() is None and len(calls) == (started is not None)


@pytest.mark.parametrize("case", ["again", "exit", "another's pane", "night run going", "the run asked it",
                                  "a lock left behind", "never at its shell", "a run begun meanwhile",
                                  "words in the prompt", "no prompt found", "finished twice",
                                  "words typed after /clear"])
def test_agents_sh_next_clears_exits_and_starts_the_role_again_in_its_own_pane(tmp_path, case):
    """`agents.sh --next ROLE PANE [exit]`, the Stop hook's (the reviewer, 2026-11-10; the rules' home here is
    girsa-architect's answer): /clear, /exit, and - the pane back at its shell - the role's fresh start, its config
    dropped as every start's; with `exit` (the longer sentence) nothing started. Only in the pane agents.sh gave that
    role. With a night run going it types nothing - that run closes the session and starts nothing - and says so to
    you unless the run had asked the role; a lock whose run is gone is no lock; a run begun while it typed: cleared
    and exited, not started. A pane not back at its shell a minute after /exit is not typed a start.
    girsa-verifier's two MEDIUMs on the plan: nothing is typed over words standing in the pane's prompt (the prompt's
    line is the last with "❯" and a no-break space - a message already sent has a plain space - and dim text there is
    Claude Code's own suggestion; measured on 2.1.322), nor when no prompt is found; and a role this script started
    less than ten minutes ago is cleared and exited but not started a second time. The prompt is read TWICE
    (girsa-verifier's MEDIUM on 51499da: the second read, before /exit, was held by no test): words typed in the
    `night.gap` seconds after /clear are not typed over either - /exit is not typed. Behind stub tmux, sleep and
    osascript; the lock's live process is this test's."""
    from conftest import write_project
    cfg = write_project(tmp_path)
    state = tmp_path / "scratch" / "state"
    lock = state / "night" / "2030-01-01" / ".running"
    typed, shown = tmp_path / "typed.txt", tmp_path / "shown.txt"
    gone = subprocess.Popen(["true"])
    gone.wait()
    if case in ("night run going", "the run asked it", "a lock left behind"):
        lock.mkdir(parents=True)
        (lock / "pid").write_text(f"{gone.pid if case == 'a lock left behind' else os.getpid()}\n", encoding="utf-8")
    if case == "the run asked it":
        (lock.parent / "ex-builder.land-sent").touch()
    begun = f"mkdir -p '{lock}'; echo {os.getpid()} > '{lock}/pid'" if case == "a run begun meanwhile" else ":"
    owner = "ex-verifier" if case == "another's pane" else "ex-builder"
    running = "node" if case == "never at its shell" else "zsh"
    if case == "finished twice":
        state.mkdir(parents=True)
        (state / "ex-builder.next-started").touch()
    # the pane as tmux captures it (octal: "❯" is \342\235\257, the no-break space \302\240, \033 the escape): a
    # message sent earlier, then the prompt - empty but for a dim suggestion, or holding typed words; or no prompt
    sent_before = r"\033[38;5;246m\342\235\257 words sent an hour ago\033[39m\n"
    prompt = {"words in the prompt": sent_before + r"\033[39m\342\235\257\302\240my half typed\n",
              "no prompt found": sent_before}.get(case, sent_before + r"\033[39m\342\235\257\302\240\033[2mTry something\033[0m\n")
    capture = f"printf '{prompt}'"
    if case == "words typed after /clear":      # the pane's second look: the prompt empty until /clear was typed
        capture = (f"if grep -qs ' /clear ' '{typed}'; then printf '" + sent_before +
                   r"\033[39m\342\235\257\302\240typed meanwhile\n" + f"'; else {capture}; fi")
    stubs = {"tmux": "case \"$1\" in\n"
                     f" show-options) case \"$*\" in *@role*) echo '{owner}' ;; *) echo '#0891b2' ;; esac ;;\n"
                     f" display-message) echo '{running}' ;;\n"
                     f" capture-pane) {capture} ;;\n"
                     f" send-keys) echo \"$*\" >> '{typed}'; case \"$*\" in *' /exit '*) {begun} ;; esac ;;\n"
                     "esac",
             "sleep": "exit 0", "claude": "echo '[]'",
             "osascript": f"for a in \"$@\"; do printf '%s\\n' \"$a\"; done >> '{shown}'"}     # an argument a line
    (tmp_path / "bin").mkdir()
    for name, body in stubs.items():
        (tmp_path / "bin" / name).write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
        (tmp_path / "bin" / name).chmod(0o755)
    env = dict(os.environ, MISHMERET_CONFIG=cfg, PATH=f"{tmp_path / 'bin'}{os.pathsep}{os.environ['PATH']}")
    out = subprocess.run(["bash", os.path.join(PKG, "agents.sh"), "--next", "ex-builder", "%3"] + ["exit"] * (case == "exit"),
                         env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stdout + out.stderr
    sent = typed.read_text(encoding="utf-8").splitlines() if typed.exists() else []
    said = shown.read_text(encoding="utf-8") if shown.exists() else ""
    log = (state / "next.log").read_text(encoding="utf-8")
    closes = ["-t %3 /clear Enter", "-t %3 /exit Enter"]
    if case in ("again", "a lock left behind"):
        assert [s.split("send-keys ")[1] for s in sent[:2]] == closes and len(sent) == 3, sent
        assert "-t %3 cd '" in sent[2] and "&& env -u MISHMERET_CONFIG -u MISHMERET_CONFIG_BY_SHIM claude --agent " \
            "ex-builder --name ex-builder" in sent[2] and "--resume" not in sent[2], sent[2]
        assert "ex-builder: cleared, exited and started again in %3" in log and said == "", (log, said)
        assert (state / "ex-builder.next-started").exists(), "its start marked, for the bound"
    elif case in ("words in the prompt", "no prompt found"):
        assert sent == [], sent
        assert ("words are standing in its prompt - /clear not typed over them" if case == "words in the prompt"
                else "its prompt could not be read - /clear not typed") in said, said
        if case == "words in the prompt":   # osascript's argument, whole (agents-lib.sh's `alert`, item 4)
            assert "ex-builder: words are standing in its prompt - /clear not typed over them; type /clear and /exit " \
                   "there, then: bash agents.sh" in said.splitlines(), said
    elif case == "words typed after /clear":
        assert [s.split("send-keys ")[1] for s in sent] == closes[:1], sent
        assert "words are standing in its prompt - /exit not typed over them" in said, said
    elif case == "finished twice":
        assert [s.split("send-keys ")[1] for s in sent] == closes, sent
        assert "finished again within ten minutes of being started here" in said and "not started a second time" in said, said
    elif case == "exit":
        assert [s.split("send-keys ")[1] for s in sent] == closes, sent
        assert "ex-builder: cleared and exited - not started again" in log and said == "", (log, said)
    elif case == "another's pane":
        assert sent == [] and "ex-builder: pane %3 was not given to it by agents.sh - nothing typed" in log, (sent, log)
    elif case == "night run going":
        assert sent == [], sent
        assert f"finished while a night run is going ({lock})" in said and "ex-builder" in said, said
    elif case == "the run asked it":
        assert sent == [] and said == "" and f"the night run ({lock}) asked it to finish" in log, (sent, said, log)
    elif case == "never at its shell":
        assert [s.split("send-keys ")[1] for s in sent] == closes, sent
        assert "its pane is not back at its shell a minute after /exit - not started again" in said, said
    else:
        assert [s.split("send-keys ")[1] for s in sent] == closes, sent
        assert f"a night run began meanwhile ({lock}) - not started again" in said, said
