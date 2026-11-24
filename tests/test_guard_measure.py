"""The guard-measure skill's scripts (.claude/skills/guard-measure/): extract.py reads Claude Code's and pi's
transcripts, decide.py and compare.py are rule 45's two sides and its comparison, mutate.py takes a rule out at a
time, probe.py judges cases on placeholder paths. Each on placeholder transcripts and trees in tmp_path."""
import json
import os
import subprocess
import sys

from conftest import PKG

SKILL = os.path.join(os.path.dirname(PKG), ".claude", "skills", "guard-measure")
run = lambda *a, **kw: subprocess.run([sys.executable, os.path.join(SKILL, a[0]), *a[1:]], capture_output=True,
                                      text=True, stdin=subprocess.DEVNULL, **kw)


def test_rule_45s_scripts_read_both_runners_transcripts_and_list_each_changed_decision(tmp_path):
    claude, pi = tmp_path / "claude-folder", tmp_path / "pi-folder"
    claude.mkdir()
    pi.mkdir()
    use = lambda cmd, cwd: json.dumps({"type": "assistant", "cwd": cwd, "message": {"content": [
        {"type": "tool_use", "name": "Bash", "input": {"command": cmd}}]}})
    (claude / "a.jsonl").write_text("\n".join([use("git push origin main", "/work/book-builder"),
                                               use("git push origin main", "/work/book-builder"),     # once
                                               use("echo hi", "/work/book-builder"), "not json"]) + "\n")
    # a session with its role on the record, and its subagent's transcript under it: each command with that role
    setting = json.dumps({"type": "agent-setting", "agentSetting": "ex-operator"})
    (claude / "b.jsonl").write_text(setting + "\n" + use("git push origin main", "/work/book") + "\n")
    (claude / "b" / "subagents").mkdir(parents=True)
    (claude / "b" / "subagents" / "agent-1.jsonl").write_text(use("git tag -l", "/work/book") + "\n")
    (claude / "c.jsonl").write_text(json.dumps({"type": "agent-name", "agentName": "ex-verifier"}) + "\n"
                                    + use("git tag -l", "/work/book") + "\n")        # only the name on the record
    (pi / "s.jsonl").write_text(json.dumps({"type": "session", "cwd": "/work/book"}) + "\n" + json.dumps(
        {"type": "message", "message": {"content": [{"type": "toolCall", "name": "bash",
                                                     "arguments": {"command": "git status"}}]}}) + "\n")
    cmds = tmp_path / "cmds.jsonl"
    r = run("extract.py", str(cmds), str(claude), str(pi))
    assert r.returncode == 0 and "transcripts: 5, distinct command-cwd-role triples: 6" in r.stdout, (r.stdout, r.stderr)
    rows = [json.loads(line) for line in cmds.read_text().splitlines()]
    assert {(x["command"], x["cwd"], x["role"]) for x in rows} == {
        ("git push origin main", "/work/book-builder", None), ("echo hi", "/work/book-builder", None),
        ("git status", "/work/book", None), ("git push origin main", "/work/book", "ex-operator"),
        ("git tag -l", "/work/book", "ex-operator"), ("git tag -l", "/work/book", "ex-verifier")}
    # each command as the role that ran it: the operator's push lets through, the role-less one is refused
    each = tmp_path / "each.jsonl"
    r = run("decide.py", PKG, os.environ["MISHMERET_CONFIG"], str(cmds), "each", str(each))
    assert r.returncode == 0, r.stderr
    by = {(rows[d["i"]]["command"], rows[d["i"]]["role"]): d.get("why") for d in map(json.loads, each.read_text().splitlines())}
    assert by[("git push origin main", "ex-operator")] is None, by
    assert "operator's" in by[("git push origin main", None)], by
    rows = [x for x in rows if x["role"] is None]
    cmds.write_text("".join(json.dumps(x) + "\n" for x in rows))
    new = tmp_path / "new.jsonl"
    r = run("decide.py", PKG, os.environ["MISHMERET_CONFIG"], str(cmds), "ex-builder", str(new))
    assert r.returncode == 0, r.stderr
    decided = {rows[d["i"]]["command"]: d.get("why") for d in map(json.loads, new.read_text().splitlines())}
    assert "operator's" in decided["git push origin main"] and decided["echo hi"] is None, decided
    # an old side that let the push through and refused the echo: one newly refused, one newly let through
    old = tmp_path / "old.jsonl"
    old.write_text("".join(json.dumps({"i": i, "why": "old reason" if x["command"] == "echo hi" else None}) + "\n"
                           for i, x in enumerate(rows)))
    r = run("compare.py", str(cmds), str(old), str(new))
    assert r.returncode == 0 and "judged 3: newly refused 1, newly let through 1, faults 0" in r.stdout, r.stdout
    assert "'git push origin main'" in r.stdout.split("== NEWLY LET THROUGH")[0] and "old reason" in r.stdout, r.stdout
    old.write_text(old.read_text().splitlines()[0] + "\n")                  # the sides judged different records
    assert run("compare.py", str(cmds), str(old), str(new)).returncode == 1


def test_mutate_says_red_green_and_not_found_and_probe_judges_on_placeholder_paths(tmp_path):
    tree = tmp_path / "tree"
    (tree / "mishmeret").mkdir(parents=True)
    (tree / "tests").mkdir()
    (tree / "mishmeret" / "x.py").write_text("def f():\n    return 1  # the rule\n")
    (tree / "tests" / "test_x.py").write_text("import os, sys\nsys.path.insert(0, os.path.join(os.path.dirname("
                                              "__file__), '..', 'mishmeret'))\nfrom x import f\n\n\n"
                                              "def test_f():\n    assert f() == 1\n")
    mutations = tmp_path / "m.json"

    def mutate(*rows, select=("tests", "-q")):
        mutations.write_text(json.dumps(list(rows)))
        r = run("mutate.py", str(tree), "mishmeret/x.py", str(mutations), str(tmp_path / "scratch"), "--", *select)
        return r.returncode, r.stdout.splitlines()
    red, green, absent = ["the rule", "return 1", "return 2"], ["a comment", "# the rule", "# a word"], ["absent", "nowhere", "x"]
    rc, lines = mutate(red)
    assert rc == 0 and lines[0] == "BASELINE passed" and lines[1].startswith("RED   the rule"), lines
    assert "assert 2 == 1" in lines[1], lines
    assert mutate(red, green) == (1, lines[:2] + ["GREEN a comment  "]), "a rule whose test stays green fails the run"
    assert mutate(absent) == (1, ["BASELINE passed", "NOT FOUND ONCE (0): absent"])
    # girsa-verifier's LOW 2 on 59f84a2: only pytest's exit 1 is RED - a broken file (exit 2) is not a rule's test
    # failing, and a selection that collects nothing (exit 5) stops at the baseline
    rc, lines = mutate(["a broken file", "return 1", "return ("])
    assert rc == 1 and lines[1].startswith("EXIT 2 a broken file"), lines
    rc, lines = mutate(red, select=("tests", "-q", "-k", "nothing_has_this_name"))
    assert rc == 1 and len(lines) == 1 and lines[0].startswith("BASELINE EXIT 5"), lines
    assert (tree / "mishmeret" / "x.py").read_text().endswith("return 1  # the rule\n"), "the tree itself untouched"
    # the probe asks every Bash rule the hook runs (its LOW 1: a piped check had read as let through)
    cases = tmp_path / "cases.json"
    cases.write_text(json.dumps([["ex-builder", "/work/book-builder", "git -C /work -C book reset --hard"],
                                 ["ex-builder", "/work/book-builder", "python3 -m pytest tests | tail -3"],
                                 ["ex-builder", "/work", "cp -r /work/book-builder /tmp/c"],
                                 ["ex-builder", "/work/book-builder", "git status"]]))
    r = run("probe.py", os.path.dirname(PKG), str(cases))
    assert r.returncode == 0, r.stderr
    assert [line.split()[0] for line in r.stdout.splitlines()] == ["REFUSED", "REFUSED", "REFUSED", "let"], r.stdout


def test_both_scripts_judge_by_the_rules_the_hook_runs():
    """girsa-verifier's LOW 1 on 59f84a2: decide.py held a hand copy of check()'s rules and probe.py asked one of
    five, and nothing held them to the hook. Now both judge by rules.RULES, and check()'s own calls are read here: a
    rule in neither RULES nor LEFT_OUT fails, and RULES keeps check()'s order. A rule an older guard lacks is not
    asked."""
    import ast
    sys.path.insert(0, SKILL)
    import rules
    tree = ast.parse(open(os.path.join(PKG, "role_guard.py"), encoding="utf-8").read())
    check = next(f for f in tree.body if isinstance(f, ast.FunctionDef) and f.name == "check")
    called = [n.func.id for n in ast.walk(check) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
              and n.func.id.endswith("refusal")]
    assert set(called) == set(rules.RULES) | set(rules.LEFT_OUT), called
    assert [n for n in called if n in rules.RULES] == list(rules.RULES), called
    for script in ("decide.py", "probe.py"):
        text = open(os.path.join(SKILL, script), encoding="utf-8").read()
        assert "judge(" in text and "_refusal(" not in text, script
    # lacking the three rules between its first and its last, which alone refuses
    older = type("OlderGuard", (), {"refusal": staticmethod(lambda role, command, cwd, read=None: None),
                                    "piped_check_refusal": staticmethod(lambda command, cwd, read=None: f"piped {command}")})
    assert rules.judge(older, "ex-builder", "x", "/w", None) == "piped x"
