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
    ask, land = script.index('board.py" waiting-for "$r"'), script.index('type_in "$pane" "/land"')
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
    assert 'type_in "$pane" "/land"' in under and '"$NIGHT/$r.land-only"' in under and "/clear" not in under
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
    ago, its pane this test's parent process."""
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
    typed = tmp_path / "typed.txt"
    stubs = {"claude": f"if [ \"$1\" = agents ]; then echo '{rows}'; fi",
             "tmux": f"case \"$1\" in list-panes) echo '{os.getppid()} %1' ;; send-keys) echo \"$*\" >> '{typed}' ;; esac",
             "sleep": "exit 0", "caffeinate": "exit 0", "osascript": "exit 0"}
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
    named = "ex-builder: /land was answered by a notice, not a landing - You've hit your weekly limit - left open for you"
    asked = "ex-builder: landed without saying it is ready to clear - asked to report back"
    expected = {"notice": named, "notice while waiting": named, "old notice": asked,
                "no record": "ex-builder: its transcript has not changed since /land was typed - /land did not reach it",
                "landed": asked}[kind]
    assert expected in log, log
    assert "stopped to ask you something" not in log and (named in log) == kind.startswith("notice"), log
    assert ("Has this session finished every step of /land?" in sent) == (expected == asked), sent
    assert (night / "ex-builder.left").exists()


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
    limited = "ex-builder: not landed - limit, the 7-day window, resets " in log
    assert limited == (percent == 100), log
    assert ("/land" in sent) == (percent < 100), sent
    if limited:
        assert "1 not landed for the plan's limit" in log, log


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


def test_the_agents_scripts_share_one_clone_one_role_list_and_one_pane_lookup():
    """The duplication audit's E26 (the reviewer, Board #82 A, 2026-10-26: the scripts in the operator's lane): agents.sh
    and agents-morning.sh each kept the role list, the clone, the session-to-pane lookup and the transcript lookup, and
    with the clone set the night run read one clone while its Go started the roles, through agents.sh, in another. Both
    source agents-lib.sh; it alone holds them, reads the project's config and exports MISHMERET_CONFIG, and the Go's new
    window is given it."""
    read = lambda name: open(os.path.join(PKG, name), encoding="utf-8").read()
    lib, start, night = read("agents-lib.sh"), read("agents.sh"), read("agents-morning.sh")
    source = '. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/agents-lib.sh"'
    assert source in start and source in night
    assert 'MM_CFG=$(python3 "$HERE/config.py" --shell)' in lib and 'DIR="$MM_ROOT"' in lib
    assert 'export MISHMERET_CONFIG="${MISHMERET_CONFIG:-$DIR/.claude/mishmeret.json}"' in lib
    for copy in ("ROLES=", "\nDIR=\"", "claude agents --json", '.jsonl 2>/dev/null', 'list-panes -s -t "$SESSION" -F \'#{pane_pid} #{pane_id}\'',
                 "PROJECTS=", "config.py --shell"):
        assert copy in lib, copy
        assert copy not in start and copy not in night, f"a second copy of {copy!r}"
    assert "write text \\\"MISHMERET_CONFIG='$MISHMERET_CONFIG' bash '$DIR/agents.sh'\\\"" in night, \
        "the Go starts the roles in the same clone"


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
    assert "they stopped during the landing" in out.stdout and "bash agents.sh --resume" in out.stdout, out.stdout
    assert "starting them" not in out.stdout and "placeholder agents.sh ran" not in out.stdout, out.stdout


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
    monkeypatch.setattr(kd, "PROJECT", str(tmp_path))
    assert kd.last_call("s-1") == (at, 40005)                                        # the keep-alive's
