#!/usr/bin/env python3
"""Run tools/check_draft.py on a draft the moment a session writes it - a PostToolUse hook on Edit and Write
(`.claude/settings.json`; Board #63 A, step 5: a rule that governs one action is delivered at that action).

The drafts rules (skill operator-drafts; WRITING.md's until Board #85 A) say: "Run `python3 tools/check_draft.py <draft>`
on every draft before handing it over." Read
at start, it was still skipped; here it runs on every write of a file named `draft_*.txt` (the corpus root's drafts and
any other), and a failure is shown to the session that wrote it (exit 2), with check_draft's own lines. A clean draft
passes with one line naming skill operator-drafts, where the drafts rules live since Board #85 A (step 5: delivered
when a draft is written, not read at every start); any other file passes silently. Needs only Python's standard
library.
"""
import json
import os
import re
import subprocess
import sys

import config  # noqa: E402  (the project's config: mishmeret/config.py)

_DRAFTS = config.load()["drafts"]   # the project's: which files are drafts, its check, what a pass and a failure say
CHECK = config.expand(_DRAFTS["check"])
DRAFT = re.compile(_DRAFTS["pattern"])
SKILL_NOTE = _DRAFTS["passed"]


def run(event, check=CHECK):
    """(exit status, message) for one hook event: 2 and check_draft's lines when a written draft fails, 0 and the skill's
    name when it passes, 0 and nothing for any other file."""
    path = (event.get("tool_input") or {}).get("file_path") or ""
    if not DRAFT.match(os.path.basename(path)) or not os.path.isfile(path):
        return 0, ""
    out = subprocess.run([sys.executable, check, path], capture_output=True, text=True)
    if out.returncode == 0:
        return 0, SKILL_NOTE
    return 2, _DRAFTS["failed"].format(path=path) + f"\n{out.stdout}{out.stderr}"


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 0
    status, message = run(event)
    if message and status == 0:   # a passing draft: the note reaches the session as context, not as an error
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": message}}))
    elif message:
        print(message, file=sys.stderr)
    return status


if __name__ == "__main__":
    sys.exit(main())
