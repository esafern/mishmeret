"""The skills Mishmeret ships (mishmeret/skills/; notes/PLAN-SHIPPED-SKILLS.md), kept true to the code they describe
(THE SECOND COPY OF THE TRUTH; girsa-architect's Q3): each name a skill uses in backticks - a land.py or board.py
subcommand, an option of land.py, board.py or agents.sh, a config field, a script - exists in the code. Each says it is
Mishmeret's general procedure (Q1). And, reported without failing, a skill whose named scripts changed after it last
did, for a pin bump's operator to re-read."""
import ast
import os
import re
import subprocess
import warnings

import config
from conftest import PKG

SKILLS = os.path.join(PKG, "skills")
TABLES = {"night": config.NIGHT, "sizes": config.SIZES, "start_reads": config.START_READS, "land": config.LAND,
          "guard": config.GUARD, "budget": config.BUDGET, "drafts": config.DRAFTS}


def read(name):
    return open(os.path.join(PKG, name), encoding="utf-8").read()


def parsers(name):
    """The subcommand names a script's argparse defines (`add_parser("x")`)."""
    return {n.args[0].value for n in ast.walk(ast.parse(read(name))) if isinstance(n, ast.Call)
            and getattr(n.func, "attr", "") == "add_parser" and n.args and isinstance(n.args[0], ast.Constant)}


def shipped():
    return sorted(d for d in os.listdir(SKILLS) if os.path.isfile(os.path.join(SKILLS, d, "SKILL.md")))


def misnamed(text):
    """Each name `text` uses in backticks that the code lacks."""
    subs = {"land.py": parsers("land.py"), "board.py": parsers("board.py")}
    bad = []
    for span in re.findall(r"`([^`]+)`", text):
        for script in ("land.py", "board.py", "agents.sh"):
            if re.search(r"(?<![\w-])" + re.escape(script) + r"\b", span):
                after = re.search(re.escape(script) + r"\s+([a-z][\w-]*)", span)
                if script in subs and after and after.group(1) not in subs[script]:
                    bad.append(f"{script} {after.group(1)}")
                bad += [f"{script} {o}" for o in re.findall(r"(?<![\w-])(--[a-z][\w-]*)", span)
                        if o != "--help" and o not in read(script)]          # --help is argparse's own
        for token in re.findall(r"(?<![\w./-])([a-z_]+)\.([a-z_]+)(?![\w./-])", span):
            if token[0] in TABLES and token[1] not in TABLES[token[0]] and token[1] not in ("py", "sh", "ts", "md"):
                bad.append(".".join(token))
        for script in re.findall(r"(?<![\w-])([a-z][\w-]*\.(?:py|sh|ts))\b", span):
            if not os.path.exists(os.path.join(PKG, script)):
                bad.append(script)
    return bad


def test_each_shipped_skill_names_only_what_the_code_has_and_says_it_is_mishmerets():
    names = shipped()
    assert names == ["mishmeret-landing", "mishmeret-push-and-pin", "mishmeret-sessions", "mishmeret-status-report"]
    for name in names:
        text = open(os.path.join(SKILLS, name, "SKILL.md"), encoding="utf-8").read()
        head = text.split("---")[1]
        assert re.search(r"^name: " + re.escape(name) + "$", head, re.M), name
        description = re.search(r"^description: (.*)$", head, re.M).group(1)
        assert "Mishmeret's general procedure" in description and "the project's own skill" in description, name
        assert misnamed(text) == [], (name, misnamed(text))


def test_the_drift_check_sees_a_name_the_code_lacks():
    """A SIGNAL THAT CANNOT DISAGREE: the check fails on each kind of name that is not there."""
    for wrong in ("`land.py commit ROLE --no-such-option`", "`land.py fly ROLE`", "`board.py fly`",
                  "`agents.sh --no-such-mode`", "the config's `night.no_such_key`", "`no_such_script.py`"):
        assert misnamed(wrong), wrong
    assert misnamed("`land.py commit ROLE notes|code -F MESSAGE NAME...` and the config's `land.verifier`") == []


def test_a_skill_older_than_the_scripts_it_names_is_reported():
    """Reported, not failed (girsa-architect's Q3): a name that still exists may mean something else now. By git's
    dates; nothing to report where the tree has no git."""
    root = os.path.dirname(PKG)
    when = lambda path: subprocess.run(["git", "-C", root, "log", "-1", "--format=%ct", "--", path],
                                       capture_output=True, text=True).stdout.strip()
    for name in shipped():
        skill = os.path.join("mishmeret", "skills", name, "SKILL.md")
        text = open(os.path.join(root, skill), encoding="utf-8").read()
        scripts = sorted(set(re.findall(r"(?<![\w-])([a-z][\w-]*\.(?:py|sh|ts))\b", text)))
        if not when(skill):
            continue
        later = [s for s in scripts if os.path.exists(os.path.join(PKG, s))
                 and (when(os.path.join("mishmeret", s)) or "0") > when(skill)]
        if later:
            warnings.warn(f"re-read the shipped skill {name}: {', '.join(later)} changed after it")
