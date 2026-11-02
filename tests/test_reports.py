"""The reports (size_report, start_reading_report, effort_report) and the draft hook: Girsa's tests of these files,
moved from Girsa at e87b092a, their mechanism's share - against the placeholder project of tests/conftest.py. Their
assertions on the project's own files (its briefs, its agent files, its documents' sizes, its draft check and its
settings.json) stay in the project."""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.join(os.path.dirname(HERE), "mishmeret")
sys.path.insert(0, PKG)
import draft_check_hook  # noqa: E402
import effort_report  # noqa: E402
import size_report  # noqa: E402
import start_reading_report  # noqa: E402


def test_the_size_report_warns_before_a_limit_and_names_where_a_whole_block_goes(tmp_path):
    """The reviewer in Girsa, 2026-10-06: "i've seen a session rewriting some wording to squeeze a few kb out of text
    to make it just barely fit - that is not a good process". size_report flags a start-up document at the config's
    warn_percent of its limit, with the home a WHOLE block goes to. Placeholder files: one at 50% is quiet, one at 90%
    "near", one past its limit "OVER" (and --check fails), a status item past its limit is named, and a role's state
    file past its own limit."""
    sr = size_report
    (tmp_path / "RULES.md").write_text("a" * int(sr.FILES["RULES.md"][0] * 0.9), encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "LANES.md").write_text("a" * (sr.FILES["docs/LANES.md"][0] + 1), encoding="utf-8")
    (tmp_path / "docs" / "STATE-ex-builder.md").write_text("s" * (sr.STATE_LIMIT + 1), encoding="utf-8")
    (tmp_path / "docs" / "STATE-ex-operator.md").write_text("s" * (sr.STATE_LIMIT // 2), encoding="utf-8")
    (tmp_path / "STATUS.md").write_text(
        "## Open items\n\nX01. **placeholder**\n" + ("x" * 80 + "\n") * (sr.ITEM_LIMIT // 80 + 10)
        + "\nX02. **small**\n\n## Carried forward\nX03. **not open**\n" + "y" * (sr.ITEM_LIMIT + 1) + "\n",
        encoding="utf-8")
    lines, over = sr.report(str(tmp_path))
    text = "\n".join(lines)
    assert re.search(r"^near RULES\.md: .* move a whole block to RULES-HISTORY\.md$", text, re.M), text
    assert re.search(r"^OVER docs/LANES\.md: .* move a whole block to docs/LANES-PLAN\.md$", text, re.M), text
    assert "status item X01" in text and "a new item" in text and "X02" not in text and "X03" not in text, text
    assert set(over) == {"docs/LANES.md", "status item X01", "docs/STATE-ex-builder.md"}, over
    assert "STATE-ex-operator" not in text, text
    (tmp_path / "docs" / "LANES.md").write_text("a", encoding="utf-8")
    assert sr.report(str(tmp_path / "docs"))[0] == ["every start-up document is under 80% of its limit"]


def test_each_reports_check_exits_1_on_what_it_finds_and_0_without_it(tmp_path, monkeypatch):
    """`--check` is what the project's gate and lane check run: exit 1 when a document is over its limit, a START READS
    line is faulty, or an agent file's effort differs from the recommendation; 0 with nothing found, and 0 without
    `--check` either way."""
    monkeypatch.setattr(size_report, "report", lambda: (["OVER x"], ["x"]))
    assert size_report.main(["--check"]) == 1 and size_report.main([]) == 0
    monkeypatch.setattr(size_report, "report", lambda: (["fine"], []))
    assert size_report.main(["--check"]) == 0
    monkeypatch.setattr(start_reading_report, "report", lambda: (["a"], ["a fault"]))
    assert start_reading_report.main(["--check"]) == 1 and start_reading_report.main([]) == 0
    monkeypatch.setattr(effort_report, "report", lambda: (["a"], ["ex-operator"]))
    assert effort_report.main(["--check"]) == 1 and effort_report.main([]) == 0


def test_the_start_reading_report_sums_each_roles_start_and_refuses_a_log_on_it(tmp_path):
    """Each brief the config's `start_reads.briefs` matches names what its role reads at start on one START READS line;
    the report sums it with what Claude Code loads by itself, and a log (`start_reads.logs`) on the line is a fault.
    Placeholder briefs: a role with the line is summed, one without it is "not moved yet", a log or a missing file is a
    fault, two lines are a fault, a `*` takes the newest match, and an automatic load not found is named."""
    sr = start_reading_report
    roles = tmp_path / ".claude" / "roles"
    roles.mkdir(parents=True)
    (tmp_path / "RULES.md").write_text("r" * 1000, encoding="utf-8")
    (tmp_path / "notes").mkdir()
    for i, name in enumerate(("STEP1-HANDOVER.md", "STEP2-HANDOVER.md")):
        f = tmp_path / "notes" / name
        f.write_text("h" * (100 * (i + 1)), encoding="utf-8")
        os.utime(f, (1_000_000 + i, 1_000_000 + i))
    (roles / "ex-alpha.md").write_text("brief\nSTART READS: RULES.md, notes/STEP*-HANDOVER.md\n", encoding="utf-8")
    (roles / "ex-beta.md").write_text("brief, nothing listed\n", encoding="utf-8")
    (roles / "ex-gamma.md").write_text("START READS: RULES.md, STATUS.md, MISSING.md\n", encoding="utf-8")
    (roles / "ex-delta.md").write_text("START READS: RULES.md\nSTART READS: RULES.md\n", encoding="utf-8")
    (roles / "other-epsilon.md").write_text("START READS: MISSING.md\n", encoding="utf-8")   # not the config's glob
    (tmp_path / "STATUS.md").write_text("log", encoding="utf-8")
    lines, faults = sr.report(str(tmp_path), home=str(tmp_path / "home"))
    alpha = next(line for line in lines if line.startswith("ex-alpha"))
    assert "RULES.md 1.0" in alpha and "notes/STEP*-HANDOVER.md 0.2" in alpha, alpha
    assert any(line.startswith("ex-beta") and "not moved yet" in line for line in lines), lines
    assert any("STATUS.md is a log" in f for f in faults) and any("MISSING.md names no file" in f for f in faults)
    assert "ex-delta: 2 START READS lines - one only" in faults, faults
    # the memory index in the config's transcripts folder for the tree, by the one rule (the audit's item 5)
    memory = dict(sr.auto_loaded(str(tmp_path), home=str(tmp_path / "home")))["the memory index"]
    assert memory == os.path.join(sr.config.transcripts(str(tmp_path)), "memory", "MEMORY.md"), memory
    assert not any(f.startswith("ex-alpha") or "epsilon" in f for f in faults), faults
    assert any(line.startswith("(not counted - the memory index not found at") for line in lines), lines


def test_the_effort_report_reads_the_configs_roles_and_flags_a_file_that_differs(tmp_path):
    """The reviewer in Girsa, 2026-10-06: "can you add a gate that checks effort and informs me how each agent is set
    and if you recommend a change?". effort_report lists the model and effort of each agent file of a role the config
    names - in its roles or its `effort` table - beside the user setting and the recommendation, and flags an agent file
    whose effort differs. Placeholder agent files: a differing effort flagged, an equal one not, a role with no
    recommendation shown so, a file of a role the config does not name not read."""
    er = effort_report
    agents = tmp_path / "agents"
    agents.mkdir()
    (agents / "ex-operator.md").write_text("---\nname: ex-operator\nmodel: opus\neffort: max\n---\n", encoding="utf-8")
    (agents / "ex-builder.md").write_text("---\nname: ex-builder\nmodel: opus\neffort: %s\n---\n"
                                          % er.RECOMMENDED["ex-builder"][0], encoding="utf-8")
    (agents / "ex-verifier.md").write_text("---\nmodel: fable\neffort: low\n---\n", encoding="utf-8")
    (agents / "stranger.md").write_text("---\nmodel: opus\neffort: low\n---\n", encoding="utf-8")
    (agents / "LANES.md").write_text("# not an agent file\n", encoding="utf-8")
    assert list(er.agent_files(str(agents))) == ["ex-builder", "ex-operator", "ex-verifier"]
    settings = tmp_path / "settings.json"
    settings.write_text(json.dumps({"modelSettings": {"claude-opus-5-5": {"effortLevel": "low"}}}), encoding="utf-8")
    lines, mismatches = er.report(str(agents), str(settings), env={"CLAUDE_EFFORT": "low"})
    assert mismatches == ["ex-operator"], mismatches
    row = next(line for line in lines if line.startswith("ex-operator"))
    assert "agent file max to %s" % er.RECOMMENDED["ex-operator"][0] in row and "user setting low to" not in row, row
    assert "low" in row.split()[3], row          # the user setting, read for the file's model
    assert any(line.startswith("ex-verifier") and "not in the operator's table" in line for line in lines), lines
    assert any("role (none - started without --agent), running at low" in line for line in lines), lines
    assert er.AGENTS_DIR.endswith(os.path.join(".claude", "agents")) and er.AGENT_FILE == "{role}.md"


def test_the_draft_hook_runs_the_projects_check_on_a_written_draft_and_blocks_a_failure(tmp_path):
    """The draft hook runs the project's check (`drafts.check`) on a written file whose name `drafts.pattern` matches:
    a failure answers 2 with the config's `failed` sentence (the path in it) and the check's own lines; a pass 0 with
    its `passed` note, sent as the PostToolUse context; any other file, a missing one or bad input 0 and nothing."""
    hook = draft_check_hook
    bad = tmp_path / "draft_placeholder.txt"
    bad.write_text("Hello, a BAD word.\n", encoding="utf-8")
    status, message = hook.run({"tool_input": {"file_path": str(bad)}})
    assert status == 2 and message.startswith(f"the check failed on {bad} - fix the draft:\n"), message
    assert "BAD found in the draft" in message, message
    good = tmp_path / "draft_clean.txt"
    good.write_text("Hello.\n", encoding="utf-8")
    assert hook.run({"tool_input": {"file_path": str(good)}}) == (0, "A draft: its rules are ex's.")
    other = tmp_path / "notes.txt"
    other.write_text("BAD\n", encoding="utf-8")
    assert hook.run({"tool_input": {"file_path": str(other)}}) == (0, "")
    assert hook.run({"tool_input": {"file_path": str(tmp_path / "draft_gone.txt")}}) == (0, "")
    run = lambda event: subprocess.run([sys.executable, os.path.join(PKG, "draft_check_hook.py")], input=event,
                                       capture_output=True, text=True)
    out = run(json.dumps({"tool_input": {"file_path": str(good)}}))
    assert out.returncode == 0 and json.loads(out.stdout)["hookSpecificOutput"] == {
        "hookEventName": "PostToolUse", "additionalContext": "A draft: its rules are ex's."}, out
    out = run(json.dumps({"tool_input": {"file_path": str(bad)}}))
    assert out.returncode == 2 and "BAD found in the draft" in out.stderr and out.stdout == "", out
    out = run("not json")
    assert (out.returncode, out.stdout, out.stderr) == (0, "", ""), out
