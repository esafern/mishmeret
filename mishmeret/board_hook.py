#!/usr/bin/env python3
"""What each session tells the Board, and the Board's budget notice (Q&A #56; the reviewer, 2026-10-25: "a and c - good.
go", then "1. 2. 3. 4. 5. go"). Runs on Notification, PostToolUse and UserPromptSubmit (.claude/settings.json):

- Notification asking for the reviewer in the pane (a permission prompt, a question dialog): recorded as the session's
  `prompt`, which the page shows on the role's corner; the next tool run or prompt clears it (idea 1).
- PostToolUse of Edit, Write or NotebookEdit: the file, recorded as the session's `editing` (idea 5).
- PostToolUse and UserPromptSubmit: once per plan window and reset at board.BUDGET_WARN percent, a sentence telling the
  session to land (A).

Silent otherwise; never blocks."""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "board"))
import board  # noqa: E402

FOR_THE_REVIEWER = ("permission_prompt", "elicitation_dialog")
EDITS = ("Edit", "Write", "NotebookEdit")


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return
    sid, event = data.get("session_id"), data.get("hook_event_name", "PostToolUse")
    try:
        if event == "Notification":
            if data.get("notification_type") in FOR_THE_REVIEWER:
                board.record_session(sid, prompt={"message": str(data.get("message") or "")[:200], "ts": int(time.time())})
            return
        fields = {"prompt": None}
        path = (data.get("tool_input") or {}).get("file_path") or (data.get("tool_input") or {}).get("notebook_path")
        if event == "PostToolUse" and data.get("tool_name") in EDITS and path:
            fields["editing"] = {"path": path, "ts": int(time.time())}
        if board.session_record(sid).get("prompt") or "editing" in fields:
            board.record_session(sid, **fields)
        said = board.budget_notice(sid)
    except (OSError, ValueError, KeyError, TypeError):
        return
    if said:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": said}}))


if __name__ == "__main__":
    main()
