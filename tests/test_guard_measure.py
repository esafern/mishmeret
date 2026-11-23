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
    (pi / "s.jsonl").write_text(json.dumps({"type": "session", "cwd": "/work/book"}) + "\n" + json.dumps(
        {"type": "message", "message": {"content": [{"type": "toolCall", "name": "bash",
                                                     "arguments": {"command": "git status"}}]}}) + "\n")
    cmds = tmp_path / "cmds.jsonl"
    r = run("extract.py", str(cmds), str(claude), str(pi))
    assert r.returncode == 0 and "transcripts: 2, distinct command-and-cwd pairs: 3" in r.stdout, (r.stdout, r.stderr)
    rows = [json.loads(line) for line in cmds.read_text().splitlines()]
    assert {(x["command"], x["cwd"]) for x in rows} == {("git push origin main", "/work/book-builder"),
                                                        ("echo hi", "/work/book-builder"), ("git status", "/work/book")}
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

    def mutate(*rows):
        mutations.write_text(json.dumps(list(rows)))
        r = run("mutate.py", str(tree), "mishmeret/x.py", str(mutations), str(tmp_path / "scratch"), "--", "tests", "-q")
        return r.returncode, r.stdout.splitlines()
    red, green, absent = ["the rule", "return 1", "return 2"], ["a comment", "# the rule", "# a word"], ["absent", "nowhere", "x"]
    rc, lines = mutate(red)
    assert rc == 0 and lines[0].startswith("RED   the rule") and "assert 2 == 1" in lines[0], lines
    assert mutate(red, green) == (1, [lines[0], "GREEN a comment  "]), "a rule whose test stays green fails the run"
    assert mutate(absent) == (1, ["NOT FOUND ONCE (0): absent"])
    assert (tree / "mishmeret" / "x.py").read_text().endswith("return 1  # the rule\n"), "the tree itself untouched"
    cases = tmp_path / "cases.json"
    cases.write_text(json.dumps([["ex-builder", "/work/book-builder", "git -C /work -C book reset --hard"],
                                 ["ex-builder", "/work/book-builder", "git status"]]))
    r = run("probe.py", os.path.dirname(PKG), str(cases))
    assert r.returncode == 0, r.stderr
    assert [line.split()[0] for line in r.stdout.splitlines()] == ["REFUSED", "let"], r.stdout
