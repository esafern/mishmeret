#!/usr/bin/env python3
"""Each role's most recent Claude Code session in a clone, for `bash agents.sh --resume`.

The reviewer, 2026-10-11: "build the agents.sh resume option" - after the roles' tmux server stopped at 17:51 that
day and all five sessions ended mid-work, none landed. Their transcripts stay on disk, so each can be resumed
(`claude --resume <id>`) with its context; this finds which transcript is each role's latest.

A role's sessions are the transcripts Claude Code keeps for the project's tree, where the roles start
(`role_usage.project_dir()`: `<claude_projects>/<the tree's path, every character but a letter or digit made
"-">/<session id>.jsonl`), whose `agent-setting` record names the role (`claude --agent <role>` writes it near the
top). The latest is the one written last. A role whose latest session is still running (`claude agents --json --all` lists it) is marked live:
agents.sh never starts a second copy of it, and never falls back to an older session of a role that is running.

usage:  python3 role_sessions.py ROLE...
prints one line per ROLE, tab-separated:
  ROLE  SESSION_ID  LAST_WRITTEN       its latest session, not running - the one to resume
  ROLE  live  SESSION_ID               its latest session is running
  ROLE  none                           no session of this role in the clone
When the running sessions cannot be read, every session counts as not running and a warning goes to stderr.
"""
import argparse
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import role_usage  # noqa: E402

HEAD_LINES = 200        # the agent-setting record is among a transcript's first lines


def role_of(path):
    """The role a transcript's `agent-setting` record names, or None."""
    try:
        with open(path, encoding="utf-8") as fh:
            for n, line in enumerate(fh):
                if n >= HEAD_LINES:
                    break
                if '"agent-setting"' not in line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                if rec.get("type") == "agent-setting":
                    return rec.get("agentSetting")
    except OSError:
        return None
    return None


def live_sessions():
    """The ids of the sessions running now; None when the list cannot be read."""
    try:
        rows = json.loads(subprocess.run(["claude", "agents", "--json", "--all"], capture_output=True, text=True,
                                         timeout=30).stdout)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    if isinstance(rows, dict):
        rows = rows.get("agents") or rows.get("sessions") or []
    return {r.get("sessionId") for r in rows if isinstance(r, dict) and r.get("sessionId")}


def latest_sessions(folder, roles):
    """{role: (session id, mtime)} of each role's latest transcript in `folder`."""
    found = {}
    try:
        names = [n for n in os.listdir(folder) if n.endswith(".jsonl")]
    except OSError:
        return found
    paths = sorted((os.path.join(folder, n) for n in names), key=os.path.getmtime, reverse=True)
    for path in paths:
        if len(found) == len(roles):
            break
        role = role_of(path)
        if role in roles and role not in found:
            found[role] = (os.path.basename(path)[:-len(".jsonl")], os.path.getmtime(path))
    return found


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("roles", nargs="+")
    args = ap.parse_args(argv)
    found = latest_sessions(role_usage.project_dir(), set(args.roles))
    live = live_sessions()
    if live is None:
        print("role_sessions: could not read the running sessions (claude agents) - none counted as running",
              file=sys.stderr)
        live = set()
    for role in args.roles:
        if role not in found:
            print(f"{role}\tnone")
        elif found[role][0] in live:
            print(f"{role}\tlive\t{found[role][0]}")
        else:
            sid, mtime = found[role]
            print(f"{role}\t{sid}\t{time.strftime('%Y-%m-%d %H:%M', time.localtime(mtime))}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
