#!/usr/bin/env python3
"""How each role's model and effort are set, and whether the operator recommends a change - a report, not a hook
(it lives here because .claude/ is where the roles' settings are; the reviewer, 2026-10-06: "can you add a gate that
checks effort and informs me how each agent is set and if you recommend a change?").

    venv/bin/python .claude/hooks/effort_report.py            the report; the operator runs it at every start
    venv/bin/python .claude/hooks/effort_report.py --check    exit 1 when an agent file's effort is not RECOMMENDED

WHERE EFFORT COMES FROM, as observed 2026-10-06 (Claude Code 2.1.291), not as documented: every agent file said
`effort: xhigh`, the reviewer's user settings (~/.claude/settings.json, `modelSettings.<model>.effortLevel`) said
`high`, and every running role reported CLAUDE_EFFORT=high. So the user settings (or /effort) decide, and an agent
file's effort is not applied. `claude --effort LEVEL` does override the user settings for that session (tested the same
day on Opus: xhigh and medium each reported as asked; Haiku stays at high). A session's own effort is the CLAUDE_EFFORT
in its shell; another session's cannot be read from outside it - ask the role to `echo $CLAUDE_EFFORT`. Since 2026-10-06 agents.sh starts each role with `--effort`
taken from its agent file, so the files are the authority again for a role started that way.
"""
import json
import os
import re
import sys

LEVELS = ("low", "medium", "high", "xhigh", "max")

# The operator's recommendation, and why. A change here is the reviewer's to make.
RECOMMENDED = {
    "girsa-operator": ("high", "mostly bookkeeping - landings, gates, restarts, records"),
    "girsa-demo-operator": ("high", "the operator's, pinned equal by a gate test - the demo's builds and the hosting"),
    "girsa-ui-steward": ("high", "look-only changes, each checked by its own browser suite"),
    "girsa-builder": ("high", "the heaviest user; every step is verified and double-reviewed after it"),
    "girsa-verifier": ("xhigh", "the check on everyone else's work, and a modest user - the most value per token"),
    "girsa-architect": ("xhigh", "few, long answers on design; a modest user"),
    "girsa-auditor": ("high", "a one-off read-only audit"),
}
# The models' ids as user settings name them, by the agent file's short name.
MODEL_IDS = {"opus": ("claude-opus-5-5", "claude-opus-5"), "fable": ("claude-fable-5-1",), "sonnet": ("claude-sonnet-5-5",)}

HERE = os.path.dirname(os.path.abspath(__file__))
AGENTS_DIR = os.path.join(os.path.dirname(HERE), "agents")
USER_SETTINGS = os.path.expanduser("~/.claude/settings.json")


def agent_files(agents_dir):
    """{role: {"model": ..., "effort": ...}} from each girsa-*.md file's front matter."""
    out = {}
    for name in sorted(os.listdir(agents_dir)):
        if not re.fullmatch(r"girsa-[a-z-]+\.md", name):
            continue
        text = open(os.path.join(agents_dir, name), encoding="utf-8").read()
        m = re.match(r"---\n(.*?)\n---", text, re.S)
        fields = dict(re.findall(r"^(\w+):\s*(\S+)\s*$", m.group(1), re.M)) if m else {}
        out[name[:-3]] = {"model": fields.get("model"), "effort": fields.get("effort")}
    return out


def user_effort(settings_path, model):
    """The user settings' effortLevel for a model short name, or None."""
    try:
        settings = json.load(open(settings_path, encoding="utf-8"))
    except (OSError, ValueError):
        return None
    per_model = settings.get("modelSettings") or {}
    for mid in MODEL_IDS.get(model or "", ()):
        level = (per_model.get(mid) or {}).get("effortLevel")
        if level:
            return level
    return None


def report(agents_dir=AGENTS_DIR, settings_path=USER_SETTINGS, env=os.environ):
    """(lines, mismatches): the table, and the roles whose agent file's effort differs from RECOMMENDED."""
    files = agent_files(agents_dir)
    lines = [f"{'role':18} {'model (file)':13} {'effort (file)':14} {'user setting':13} {'recommended':12} change?"]
    mismatches = []
    for role, f in files.items():
        rec, why = RECOMMENDED.get(role, (None, "not in the operator's table"))
        user = user_effort(settings_path, f["model"])
        change = []
        if rec and f["effort"] != rec:
            change.append(f"agent file {f['effort']} to {rec}")
            mismatches.append(role)
        lines.append(f"{role:18} {str(f['model']):13} {str(f['effort']):14} {str(user):13} {str(rec):12} "
                     + ("; ".join(change) if change else "none") + f"  ({why})")
    me, mine = env.get("CLAUDE_CODE_AGENT"), env.get("CLAUDE_EFFORT")
    if mine:
        lines.append(f"this session: role {me or '(none - started without --agent)'}, running at {mine}")
    lines.append("in effect: for a role started by agents.sh, its agent file's effort (passed as --effort); for any other "
                 "session, the user setting or /effort - the user setting is every session's, so it is not suggested here")
    return lines, mismatches


def main(argv):
    lines, mismatches = report()
    print("\n".join(lines))
    if "--check" in argv and mismatches:
        print("agent files differ from the recommendation: " + ", ".join(mismatches))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
