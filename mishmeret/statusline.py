#!/usr/bin/env python3
"""The status line of every session in this project (.claude/settings.json `statusLine`; Q&A #56 A, the reviewer,
2026-10-25: "a and c - good. go"). Claude Code passes the session's data on stdin; the plan's usage windows in it
(`rate_limits`, claude.ai plans only, after the session's first response) are recorded for the Board's meter and the
budget hook (board.record_usage), the session's context and prompt cache for its corner (board.record_session), and one
line is printed:

    context 123k · plan: 5-hour 42% (resets 16:00) · 7-day 18% (resets Thu 09:00)

A window at board.BUDGET_WARN percent or more is written in capitals. A second row, when there is something to say,
gives the Board's state (board_row; refreshed every minute by `refreshInterval`). Never fails the line: a fault prints what it can."""
import json
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # board.py is beside it
import board  # noqa: E402
import role_usage  # noqa: E402


def line(data):
    parts = []
    cw = data.get("context_window") or {}
    used = (cw.get("current_usage") or {})
    ctx = sum(used.get(k) or 0 for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
    if ctx:
        parts.append(f"context {ctx // 1000}k")
    rl = data.get("rate_limits") or {}
    plan = []
    for key, label in board.WINDOWS:
        w = rl.get(key)
        if not w or w.get("used_percentage") is None:
            continue
        pct = float(w["used_percentage"])
        reset = datetime.fromtimestamp(int(w["resets_at"])).strftime("%H:%M" if key == "five_hour" else "%a %H:%M")
        text = f"{label} {pct:.0f}% (resets {reset})"
        plan.append(text.upper() if pct >= board.BUDGET_WARN else text)   # the capitals the eye-catcher; never "land"
    if plan:
        parts.append("plan: " + " · ".join(plan))
    return " · ".join(parts)


def board_row(role):
    """The Board's state on a second row (Q&A #56 B; Board #73 A, "Build it"): questions waiting for the reviewer, who
    holds main, and what this role waits on; "" when there is none of it."""
    events = board.read_events()
    waiting = sorted((it for it in board.items(events).values() if board.is_waiting(it)), key=lambda it: it["id"])
    parts = []
    if waiting:
        parts.append(f"{len(waiting)} question{'s' if len(waiting) > 1 else ''} for you ("
                     + ", ".join(f"#{it['id']} {it['role']}" for it in waiting) + ")")
    h = board.held(events)
    if h:
        since = datetime.fromisoformat(h["ts"]).strftime("%H:%M")
        parts.append(f"main held by {h['role']} since {since} - {h.get('why') or ''}".rstrip(" -"))
    st = board.statuses(events).get(role) or {}
    if st.get("state") == "waiting-agent" and st.get("waiting_for"):
        parts.append(f"this role waits for {st['waiting_for']}")
    elif st.get("state") == "waiting-reviewer":
        parts.append("this role waits for you")
    return "Board: " + " · ".join(parts) if parts else ""


CACHE_FIELDS = ("warm", "hit_ratio", "misses", "expires_at", "recache_tokens_if_cold", "last_miss_cause")


def last_turn(transcript_path, tail=4_000_000):
    """{"context", "at"} of the session's last call in its transcript, or None. A session compacted while idle reports
    no context until its next turn (the reviewer, 2026-10-28: "where are the context numbers on the board?"), so the
    corner says what it was at the last turn; read once per compaction, from the transcript's tail."""
    try:
        lc = role_usage.last_call(transcript_path, tail)
    except (OSError, TypeError, ValueError):
        return None
    return {"context": lc[1], "at": int(lc[0].timestamp())} if lc else None


def session_fields(data):
    """What the Board's corner shows of this session (Q&A #56 idea 2): its name, context and prompt cache - and, while
    it reports no context (compacted, not yet called again), the context of its last turn."""
    pc = data.get("prompt_cache") or {}
    used = (data.get("context_window") or {}).get("current_usage") or {}
    ctx = sum(used.get(k) or 0 for k in role_usage.USAGE_KEYS)
    before = None
    if not ctx:
        before = board.session_record(data.get("session_id")).get("last_turn") or last_turn(data.get("transcript_path"))
    return {"name": data.get("session_name"), "seen_at": int(time.time()), "context": ctx, "last_turn": before,
            "cache": {k: pc.get(k) for k in CACHE_FIELDS if k in pc} or None}


def changed(rate_limits):
    """True when the plan's figures differ from the last recorded - a refresh of an idle session passes the same
    figures again, and recording them would move the page's "as of" to a time nothing was read."""
    old = board.usage() or {}
    return any((rate_limits or {}).get(k) and (
        not old.get(k) or float(rate_limits[k]["used_percentage"]) != old[k]["used_percentage"]
        or int(rate_limits[k]["resets_at"]) != old[k]["resets_at"]) for k, _ in board.WINDOWS)


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return
    try:
        if changed(data.get("rate_limits")):
            board.record_usage(data.get("rate_limits"), data.get("session_name"))
        board.record_session(data.get("session_id"), **session_fields(data))
    except (OSError, ValueError, KeyError, TypeError):
        pass
    print(line(data))
    try:
        row = board_row(data.get("session_name"))
    except (OSError, ValueError, KeyError, TypeError):
        row = ""
    if row:
        print(row)


if __name__ == "__main__":
    main()
