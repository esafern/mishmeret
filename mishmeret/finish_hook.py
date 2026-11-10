#!/usr/bin/env python3
"""A finished session is cleared, exited and started again in its pane - no hand step (the reviewer, 2026-11-10, the
first project's Board #183: "during the day I want to clear a session after landing, then exit and start a new one";
then "add finish-and-exit": after that command's sentence it is cleared and exited and nothing is started). Runs on
Stop (the project's .claude/settings.json).

When the turn's last message ends with a closing sentence (role_usage.closing, the rule's one home) and this is the
session of a role with a tmux pane, running in one, it starts `agents.sh --next ROLE PANE [exit]` detached and
returns. Every rule about what is then typed is that script's: only the pane agents.sh gave the role, and never while
a night run is going. A finish with a step undone ends with what is left, not with a sentence, and is left alone.

The message is the hook's own `last_assistant_message`: measured on Claude Code 2.1.322, the transcript does not yet
hold it when Stop runs. Silent always; never blocks."""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)   # config.py and role_usage.py are beside it
import config  # noqa: E402
import role_usage  # noqa: E402


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return
    message = data.get("last_assistant_message") if isinstance(data, dict) else None
    said = role_usage.closing(message) if isinstance(message, str) else None
    role, pane = os.environ.get("CLAUDE_CODE_AGENT"), os.environ.get("TMUX_PANE")
    try:
        if not said or not pane or role not in config.role_names(tmux=True):
            return
    except config.ConfigError:
        return
    subprocess.Popen(["bash", os.path.join(HERE, "agents.sh"), "--next", role, pane] + ["exit"] * (said == "exit"),
                     start_new_session=True,    # its own session: it outlives the session it exits
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
