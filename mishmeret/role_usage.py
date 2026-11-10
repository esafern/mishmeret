#!/usr/bin/env python3
"""Tokens per role per day, and each role's compactions (Q&A #56 ideas 3 and 4; the reviewer, 2026-10-25: "1. 2. 3. 4.
5. go"). Read from the project's session transcripts (<claude_projects>/<the project tree's path>/*.jsonl): a transcript's
role is its `agent-name` record, its subagents' transcripts sit in <session>/subagents/, an API call counts once (by
message id) on the local date of its timestamp, and a compaction is a `compact_boundary` record. `weighted` puts the
token kinds on one scale at their relative list prices on one model - input 1, cache write 2 (one-hour cache), cache read
0.1, output 5 - so roles compare; subagents are kept by model, since a Haiku or Sonnet token costs less (C).

    python3 role_usage.py [YYYY-MM-DD]      # the table, for that day (default today)

Each transcript is parsed again only when its size or mtime changed. Needs only Python's standard library."""
import glob
import json
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config  # noqa: E402

WEIGHTS = {"inp": 1, "cw": 2, "cr": 0.1, "out": 5}
_CACHE = {}   # path: ((size, mtime), parsed)


def project_dir():
    """Claude Code's transcripts folder for the project's tree (the config's root, so each worktree its own), under the
    config's claude_projects; MISHMERET_TRANSCRIPTS names the folder itself (a test's)."""
    return os.environ.get("MISHMERET_TRANSCRIPTS") or config.transcripts(config.root())


def transcript(session_id):
    """The path of a session's transcript in this project, or None - the one place the Board finds it (girsa-verifier,
    2026-10-26, LOW 3)."""
    path = os.path.join(project_dir(), f"{os.path.basename(str(session_id))}.jsonl") if session_id else None
    return path if path and os.path.exists(path) else None


def tail_records(path, nbytes):
    """A transcript's main-chain records (dicts; subagents' sidechain records left out) in its last `nbytes`, newest
    first; a line that does not parse (the first, cut by the seek) is skipped."""
    with open(path, "rb") as fh:
        fh.seek(max(0, os.path.getsize(path) - nbytes))
        lines = fh.read().decode("utf-8", "replace").splitlines()
    for line in reversed(lines):
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if isinstance(rec, dict) and not rec.get("isSidechain"):
            yield rec


USAGE_KEYS = ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")


def last_call(path, tail=4 * 1024 * 1024):
    """(time, context tokens) of a transcript's newest main-chain API call, or None - the one reader the status line,
    the keep-alive check and the night run share (the audit's item 9: three copies, which disagreed). A record whose
    usage is all zeros is no call - a usage-limit or error notice Claude Code wrote itself - and is passed over: taken
    as the last call, it hid the corner's context and kept the keep-alive from ever pinging that role."""
    for rec in tail_records(path, tail):
        u = (rec.get("message") or {}).get("usage") if rec.get("type") == "assistant" else None
        ctx = sum(u.get(k) or 0 for k in USAGE_KEYS) if isinstance(u, dict) else 0
        if not ctx:
            continue
        try:
            return datetime.fromisoformat(rec["timestamp"].replace("Z", "+00:00")), ctx
        except (KeyError, ValueError, AttributeError):
            return None
    return None


def synthetic_after(path, since, tail=256 * 1024):
    """The text of a transcript's newest assistant record when Claude Code wrote it itself, no call made (model
    `<synthetic>`: a usage-limit or error notice), at or after `since` (epoch seconds) - else None. A /land so answered
    is no landing (2026-10-30 and 10-31: the night run's /land answered "You've hit your weekly limit", then read as
    landed and asked to report back)."""
    for rec in tail_records(path, tail):
        if rec.get("type") != "assistant":
            continue
        m = rec.get("message") or {}
        try:
            when = datetime.fromisoformat(rec["timestamp"].replace("Z", "+00:00")).timestamp()
        except (KeyError, ValueError, AttributeError):
            return None
        if m.get("model") != "<synthetic>" or when < since:
            return None
        blocks = m.get("content") if isinstance(m.get("content"), list) else []
        return " ".join(b.get("text", "") for b in blocks if isinstance(b, dict)).strip() or "(no text)"
    return None


# THE TWO CLOSING SENTENCES a project's finish commands end with (the reviewer, 2026-11-10: "during the day I want to
# clear a session after landing, then exit and start a new one"; "add finish-and-exit and have the night run use
# that"): what is done after each - both are cleared and exited; "again" is then started again in its pane.
CLOSING = {"The session is ready to clear.": "again", "The session is ready to clear and exit.": "exit"}


def closing(text):
    """What a message's closing sentence asks for, "again" or "exit" - or None. THE SENTENCE ITSELF, whole, as the
    message's last line, its emphasis stripped - never the phrase anywhere (girsa-verifier, 2026-10-11, on f4f82233: "I
    am not ready to clear yet ...", or a message quoting the rule, matched it). The rule's one home: the Stop hook
    (finish_hook.py) asks it of the turn's last message, the night run (said_closing) of a transcript."""
    lines = [line for line in (text or "").splitlines() if line.strip()]
    return CLOSING.get(re.sub(r"[*_`]", "", lines[-1]).strip()) if lines else None


def said_closing(path, tail=4 * 1024 * 1024):
    """closing() of the last thing in a transcript, when that is the session's own message - a prompt put to it after
    its last words, and it has not said so (the reviewer, 2026-10-11, Board #12: "If the last thing in an agent's
    transcript is landed or ready to clear, don't wait for it to be idle")."""
    for rec in tail_records(path, tail):
        if rec.get("type") not in ("user", "assistant") or rec.get("isMeta"):
            continue
        c = (rec.get("message") or {}).get("content")
        blocks = [{"type": "text", "text": c}] if isinstance(c, str) else (c if isinstance(c, list) else [])
        text = " ".join(b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text")
        if rec["type"] == "user":
            if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in blocks) or not text.strip():
                continue        # a tool's answer, not a prompt
            return None
        if text.strip():
            return closing(text)
    return None


def turn_ended(session_id, tail=256 * 1024):
    """True when a session's last turn has ended - its transcript's last main-chain record is the turn's closing `system`
    record (`turn_duration`), with no prompt or answer after it - else False, unknown included (Lesson 59). `claude
    agents` calls a session busy while a background task of its own runs (a `board.py wait`, a watcher loop), though its
    turn has ended (the reviewer, 2026-10-26: "ui says working in the title bar but idle in the body")."""
    path = transcript(session_id)
    if not path:
        return False
    for rec in tail_records(path, tail):
        if rec.get("type") in ("user", "assistant"):
            return False
        if rec.get("type") == "system" and rec.get("subtype") == "turn_duration":
            return True
    return False


def _no_errors():
    return {"api": 0, "hook": 0, "refused": 0, "tool": 0}


def _blank():
    return {"calls": 0, "inp": 0, "cw": 0, "cr": 0, "out": 0}


def _parse(path):
    """(role or None, {date: {"main": totals, "compactions": n}}, {date: {model: totals}}) for one transcript file."""
    role, days, seen = None, {}, set()
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if '"agent-name"' in line and role is None:
                try:
                    role = json.loads(line).get("agentName")
                except ValueError:
                    pass
                continue
            if not any(m in line for m in ('"usage"', '"compact_boundary"', '"is_error":true', 'isApiErrorMessage":true',
                                            '"type":"hook_')):
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            try:
                day = datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00")).astimezone().strftime("%Y-%m-%d")
            except (KeyError, ValueError, AttributeError):
                continue
            d = days.setdefault(day, {"main": _blank(), "compactions": 0, "models": {}, "errors": _no_errors()})
            if r.get("type") == "system" and r.get("subtype") == "compact_boundary":
                d["compactions"] += 1
                continue
            # ERRORS (Q&A #56 idea 2): a hook that failed, a call the API answered with an error, a tool call the role
            # guard refused, and any other tool call that failed
            att = r.get("attachment") if isinstance(r.get("attachment"), dict) else {}
            if r.get("type") == "attachment" and str(att.get("type", "")).startswith("hook_") and "error" in att["type"]:
                d["errors"]["hook"] += 1
                continue
            if r.get("type") == "assistant" and r.get("isApiErrorMessage"):
                d["errors"]["api"] += 1
                continue
            if r.get("type") == "user":
                for c in (r.get("message") or {}).get("content") or []:
                    if isinstance(c, dict) and c.get("type") == "tool_result" and c.get("is_error"):
                        d["errors"]["refused" if "refused by the role guard" in str(c.get("content")) else "tool"] += 1
                continue
            m = r.get("message") or {}
            u = m.get("usage") if r.get("type") == "assistant" else None
            if not u or m.get("id") in seen:
                continue
            seen.add(m.get("id"))
            for t in (d["main"], d["models"].setdefault(m.get("model") or "?", _blank())):
                t["calls"] += 1
                t["inp"] += u.get("input_tokens") or 0
                t["cw"] += u.get("cache_creation_input_tokens") or 0
                t["cr"] += u.get("cache_read_input_tokens") or 0
                t["out"] += u.get("output_tokens") or 0
    return role, days


def _parsed(path):
    st = os.stat(path)
    key = (st.st_size, st.st_mtime)
    if path not in _CACHE or _CACHE[path][0] != key:
        _CACHE[path] = (key, _parse(path))
    return _CACHE[path][1]


def weighted(t):
    return round(sum(t[k] * w for k, w in WEIGHTS.items()))


def _add(into, t):
    for k in t:
        into[k] += t[k]


def role_usage(day=None):
    """{role: {"main": totals + weighted, "compactions": n, "sessions": n, "sub": {model: totals + weighted}}} for `day`."""
    day = day or datetime.now().strftime("%Y-%m-%d")
    since = datetime.strptime(day, "%Y-%m-%d").timestamp()
    out = {}
    for path in glob.glob(os.path.join(project_dir(), "*.jsonl")):
        if os.path.getmtime(path) < since:
            continue
        role, days = _parsed(path)
        subs = [_parsed(p)[1].get(day) for p in glob.glob(os.path.join(path[:-6], "subagents", "*.jsonl"))
                if os.path.getmtime(p) >= since]
        mine = days.get(day)
        if not mine and not any(subs):
            continue
        r = out.setdefault(role or "(no role)", {"main": _blank(), "compactions": 0, "sessions": 0, "sub": {},
                                                  "errors": _no_errors()})
        r["sessions"] += 1
        if mine:
            _add(r["main"], mine["main"])
            r["compactions"] += mine["compactions"]
            _add(r["errors"], mine["errors"])
        for s in filter(None, subs):
            for model, t in s["models"].items():
                _add(r["sub"].setdefault(model, _blank()), t)
    for r in out.values():
        r["main"]["weighted"] = weighted(r["main"])
        for t in r["sub"].values():
            t["weighted"] = weighted(t)
    return out


def _start(path, lines=400):
    """When a transcript began: its first timestamp, read from its first lines. Its role is _parsed's, read from the whole
    file (girsa-verifier, 2026-10-26, LOW 5: a session resumed into a role names it after line 400)."""
    with open(path, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f):
            if i >= lines:
                break
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("timestamp"):
                return datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00")).astimezone()
    return None


def session_facts(session_id):
    """For a landing (the reviewer, 2026-10-25: "include session length alongside completion time - and number of
    sessions today - we run through multiple builders against one architect"): {"started": ISO, "nth_today": n} - when
    the session began, and which of its role's sessions begun that day it was - or {} when its transcript is not found."""
    path = transcript(session_id)
    if not path:
        return {}
    role, start = _parsed(path)[0], _start(path)
    if not start:
        return {}
    day0 = start.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    starts = [start]
    for p in glob.glob(os.path.join(project_dir(), "*.jsonl")):
        if p == path or os.path.getmtime(p) < day0:      # a file last written before that day began none of its sessions
            continue
        s = _start(p)
        if s and s.date() == start.date() and _parsed(p)[0] == role:
            starts.append(s)
    return {"started": start.isoformat(timespec="seconds"), "nth_today": sorted(starts).index(start) + 1}


def role_week(day=None, n=7):
    """The `n` days ending on `day` (default today), oldest first: [(day, {role: weighted})] (Q&A #56 idea 3)."""
    from datetime import timedelta
    end = datetime.strptime(day, "%Y-%m-%d") if day else datetime.now()
    days = [(end - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(n - 1, -1, -1)]
    return [(d, {role: r["main"]["weighted"] + sum(t["weighted"] for t in r["sub"].values())
                 for role, r in role_usage(d).items()}) for d in days]


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["synthetic-after"]:      # the night run's: synthetic-after PATH EPOCH - the notice's text, or nothing
        print(synthetic_after(argv[1], float(argv[2])) or "")
        return
    if argv[:1] == ["closing"]:              # the night run's: closing PATH - "again" or "exit"; exit 1 when not said
        said = said_closing(argv[1]) if os.path.exists(argv[1]) else None
        print(said or "")
        sys.exit(0 if said else 1)
    if argv[:1] == ["context"]:             # the night run's: context PATH - its last call's context, 0 when not read
        lc = last_call(argv[1]) if os.path.exists(argv[1]) else None
        print(lc[1] if lc else 0)
        return
    day = (argv or [None])[0]
    rows = sorted(role_usage(day).items(), key=lambda kv: -kv[1]["main"]["weighted"])
    print(f"{'role':24} {'sessions':>8} {'calls':>6} {'weighted':>12} {'cache write':>12} {'cache read':>12} {'output':>9} "
          f"{'compactions':>11}  subagents (model: weighted)")
    for role, r in rows:
        m = r["main"]
        subs = ", ".join(f"{k}: {t['weighted']:,}" for k, t in sorted(r["sub"].items()))
        print(f"{role:24} {r['sessions']:>8} {m['calls']:>6} {m['weighted']:>12,} {m['cw']:>12,} {m['cr']:>12,} "
              f"{m['out']:>9,} {r['compactions']:>11}  {subs}")


if __name__ == "__main__":
    main()
