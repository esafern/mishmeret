#!/usr/bin/env python3
"""The Board: one place where every role puts its questions and decisions to the reviewer, and gets the answer back.

The reviewer, 2026-10-09: "we need a special screen where each agent can supply answers to my questions and present
decisions to me. it does not work to have them flow past in each window, and for me to confirm my decision to each
agent." A role ASKS here (a question, or a decision with its options, a recommendation and links); the reviewer answers
on the Board's page (board_server.py, http://127.0.0.1:<board_port>); the role WAITS on its item and is handed the answer.

The record is append-only (board.jsonl in the config's board_dir, MISHMERET_BOARD_DIR over it - outside every repository, so it
stays private and no role's tree carries it): an item, its answer, a withdrawal, each a line. Nothing is rewritten.

    python3 board.py ask --role ROLE --title "..." [--body "..." | --body-file F]
            [--kind question|decision] [--option KEY="label | what it means"]... [--recommend KEY] [--link URL]...
            [--image KEY=PATH]...      # a mock-up of option KEY (or a bare PATH); the mock-up window shows A left, B right
                                       # a decision about the page: one mock-up per option, labelled A, B ... on the
                                       # image, at the browser tests' two window sizes (WRITING.md, the steward's brief)
    python3 board.py status --role ROLE [--now "..."] [--done "..."] [--next "..."]
            [--state working|idle|waiting-agent|waiting-reviewer] [--waiting-for ROLE]
                                       # the role's corner: what it works on, what just finished, what is next
    python3 board.py status --role ROLE --still    # the same corner, reported again now: the
                                       # answer to a KEEPALIVE, so the corner's time says the role is still there
    python3 board.py plan --role ROLE --effort "Step 5 - ..." [--note "..."]
            --step "done=..." --step "now=..." --step "next=..." [--step "next:1=..." (a sub-step)]...
                                       # a multi-day effort's steps, shown while no question waits - the whole list
    python3 board.py hold --role ROLE --why "landing P3"   # main held until released
    python3 board.py release --role ROLE                   # main free again
    python3 board.py wait ID [--timeout SECONDS]   # blocks until answered; prints the answer - or, after
                                       # 55 min by default (0: never), exits 1 "still open": wait again
    python3 board.py quiet [--port PORT] [--timeout SECONDS]   # blocks until the Board says nothing is
                                       # moving; prints each role's Next and any role waiting on one not working
                                       # (the operator, in the background whenever it goes idle) - or, after 55 min
                                       # by default, exits 1 "NO QUIET": read the corners, run it again
    python3 board.py list [--role ROLE] [--open]
    python3 board.py withdraw ID --why "..."        # an item no longer needed
    python3 board.py defer ID                       # put off for later (the page also brings it back)
    python3 board.py answer ID --answer "..."       # the page's own route, for a relay or a test
    python3 board.py landed --role ROLE (--summary "..." | --summary-file F) [--session ID]
                                       # a session's landing: bullet points of what it accomplished - its corner says
                                       # Landed until the role's next session; the page's Landings keep every one
    python3 board.py qa --role ROLE --question "..." (--answer "..." | --answer-file F) [--link URL]...
                                       # a question the reviewer asked in a role's pane, and the role's answer, kept
    python3 board.py qa-more N --role ROLE [--question "..."] (--answer "..." | --answer-file F)
                                       # a follow-up to Q&A #N: the reviewer's next question on it, or more answer
Needs only Python's standard library."""
import argparse
import fcntl
import json
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config  # noqa: E402  (the project's config: mishmeret/config.py)

# every role the config names, so each holds main under its own name (girsa-demo-operator, 2026-10-18: holding as
# girsa-operator, one operator's release freed the other's hold). The page draws a corner for each role the config
# marks `corner`; a role without one reports in its own pane
ROLES = tuple(config.role_names())   # the config's roles, in its order (mishmeret/config.py)


def _url():
    """The Board's page, as every line that points a role to it prints it."""
    return f"http://127.0.0.1:{config.load()['board_port']}/"


def board_dir():
    return os.path.expanduser(config.load()["board_dir"])


def _path():
    return os.path.join(board_dir(), "board.jsonl")


def _now():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _events(lines):
    """The record's events; a line that is not whole (a write cut off by power loss or a full disk) is skipped and named,
    so one stops no Board command (the audit's item 7). The record stays append-only: nothing is rewritten."""
    out = []
    for n, line in enumerate(lines, 1):
        if line.strip():
            try:
                out.append(json.loads(line))
            except ValueError:
                print(f"board: line {n} of {_path()} is not whole - skipped", file=sys.stderr)
    return out


def read_events():
    try:
        with open(_path(), encoding="utf-8") as fh:
            return _events(fh)
    except FileNotFoundError:
        return []


def _append(make):
    """Append the event `make(events)` returns, under a lock - so two roles asking at once get two ids."""
    os.makedirs(board_dir(), exist_ok=True)
    with open(_path(), "a+", encoding="utf-8", newline="\n") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        fh.seek(0)
        lines = fh.readlines()
        event = make(_events(lines))
        fh.seek(0, os.SEEK_END)
        cut = lines and not lines[-1].endswith("\n")       # the new event on a line of its own after a cut-off one
        fh.write(("\n" if cut else "") + json.dumps(event, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
        return event


STATES = ("working", "idle", "waiting-agent", "waiting-reviewer")
STATUS_TEXT = ("now", "done", "next")
WATCH_TIMEOUT = 55 * 60   # seconds: `wait` and `quiet` end within the prompt cache's hour (main's parser says why)


def set_status(role, state=None, waiting_for=None, now=None, done=None, next_=None):
    """A role's corner (the reviewer, 2026-10-10: "each agent has it's own corner to report status - what it is working on,
    what just finished and what is next"). Only the fields given change; the rest keep their last value."""
    _check_role(role)
    if state is not None and state not in STATES:
        raise ValueError(f"a state is one of {', '.join(STATES)}, not {state!r}")
    if (state == "waiting-agent") != (waiting_for is not None):
        raise ValueError("--waiting-for goes with --state waiting-agent, and only with it")
    if waiting_for is not None and (waiting_for not in ROLES or waiting_for == role):
        raise ValueError(f"--waiting-for is another role, not {waiting_for!r}")
    event = {"type": "status", "ts": _now(), "role": role}
    for key, value in (("now", now), ("done", done), ("next", next_)):
        if value is not None:
            event[key] = value.strip()
    if state is not None:
        event["state"], event["waiting_for"] = state, waiting_for
    if len(event) == 3:
        raise ValueError("nothing to report: give --now, --done, --next or --state")
    return _append(lambda events: event)


def still(role):
    """The role's corner reported again as it stands - its state (idle if it never gave one) and its wait - so its time
    is now (the reviewer, 2026-10-26: "keepalive is a good opp. for a session to report to the board that it is still
    idle")."""
    st = statuses()[role] if role in ROLES else {}
    state = st.get("state") or "idle"
    return set_status(role, state, st.get("waiting_for") if state == "waiting-agent" else None)


def statuses(events=None):
    """{role: its corner} - the last value of each field; `state_ts` is when the state was last reported."""
    out = {r: {"now": "", "done": "", "next": "", "state": None, "waiting_for": None, "ts": None, "state_ts": None}
           for r in ROLES}
    for e in events if events is not None else read_events():
        if e.get("type") != "status" or e.get("role") not in out:
            continue
        st = out[e["role"]]
        for key in STATUS_TEXT:
            if key in e:
                st[key] = e[key]
        if "state" in e:
            st["state"], st["waiting_for"], st["state_ts"] = e["state"], e.get("waiting_for"), e["ts"]
        st["ts"] = e["ts"]
    return out


def _when(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")) if ts else None
    except ValueError:
        return None


def shown_state(st, live, open_ids, last_prompt=None):
    """What the corner says, as (key, words). The running session's own state decides first - a reported state is a
    claim, and a stale one would say the wrong thing (Lesson 59): busy is Working, a question in its pane or on the
    Board is the reviewer's; only an IDLE role shows what it reported, and only if nothing was put to it since (a new
    prompt after the report means it moved on)."""
    if live is None:
        return "not-running", "Not running"
    if live == "busy":
        return "working", "Working"
    if live == "waiting":
        return "waiting-reviewer", "Waiting for the Reviewer - in its window"
    if open_ids:
        return "waiting-reviewer", "Waiting for the Reviewer - " + ", ".join(f"#{n}" for n in open_ids) + " below"
    reported, prompt = _when(st.get("state_ts")), _when(last_prompt)
    if reported and (prompt is None or reported >= prompt):
        if st.get("state") == "waiting-agent" and st.get("waiting_for"):
            return "waiting-agent", "Waiting for " + st["waiting_for"]
        if st.get("state") == "waiting-reviewer":
            return "waiting-reviewer", "Waiting for the Reviewer"
    return "idle", "Idle"


def also_waiting(st, live, last_prompt=None):
    """A second badge for a WORKING role that has reported a wait on another role (the reviewer, 2026-10-10, the Board
    #6: "A - Add a second badge"): its words, or None. The same freshness as shown_state - only until a prompt is put
    to it after the report."""
    if live != "busy" or st.get("state") != "waiting-agent" or not st.get("waiting_for"):
        return None
    reported, prompt = _when(st.get("state_ts")), _when(last_prompt)
    if reported and (prompt is None or reported >= prompt):
        return "and waiting for " + st["waiting_for"]
    return None


def behind_its_work(st, live, last_prompt=None):
    """True when a WORKING role's corner was reported before the prompt it is working on (the reviewer, 2026-10-26: "ver
    says Working - but on nothing" - the title Working, the body its last report, "Nothing running", from before it was
    given its current task): its text is then marked as earlier than the work, not passed off as it (Lesson 59)."""
    if live != "busy":
        return False
    reported, prompt = _when(st.get("ts")), _when(last_prompt)
    return bool(prompt and (reported is None or reported < prompt))


def mockup_pages(it):
    """The mock-up window's pages (the reviewer, 2026-10-10: "always A on left B on right with arrow keys left and right
    for multiple pages"): each page two images side by side, the earlier option on the left. Page k shows each pair of
    options' k-th images - A and B, then C and D; images tied to no option are paired in the order given."""
    keys = [o["key"] for o in it.get("options") or []]
    labels = {o["key"]: o["label"] for o in it.get("options") or []}
    tied = it.get("image_options") or [None] * len(it.get("images") or [])
    groups = {k: [n for n, t in enumerate(tied) if t == k] for k in keys}
    groups = [(k, groups[k]) for k in keys if groups[k]]
    loose = [n for n, t in enumerate(tied) if t is None]
    pages = []
    for k in range(max((len(g) for _, g in groups), default=0)):
        for i in range(0, len(groups), 2):
            pair = [(key, g[k]) for key, g in groups[i:i + 2] if k < len(g)]
            if pair:
                pages.append([{"key": key, "label": labels[key], "n": n} for key, n in pair])
    for i in range(0, len(loose), 2):
        pages.append([{"key": None, "label": f"Mock-up {n + 1}", "n": n} for n in loose[i:i + 2]])
    return pages


PLAN_STATES = ("done", "now", "next")


def set_plan(role, effort, steps, note=""):
    """A multi-day effort's steps (the reviewer, 2026-10-10: "when we're working on a multi-day effort with many steps -
    show those steps in green bold and red in a window that hides when there's an active question but returns after -
    green completed bold in prog red coming"). Each publish gives the WHOLE list; the last one counts. A step is
    STATE=LABEL or STATE:DEPTH=LABEL (depth 0 or 1, a sub-step)."""
    _check_role(role)
    if not effort.strip():
        raise ValueError("an effort needs a name")
    out = []
    for raw in steps:
        head, sep, label = raw.partition("=")
        state, _, depth = head.partition(":")
        if not sep or state.strip() not in PLAN_STATES or not label.strip() or depth.strip() not in ("", "0", "1"):
            raise ValueError(f"a step is done=..., now=... or next=... (with :1 for a sub-step), not {raw!r}")
        out.append({"state": state.strip(), "depth": int(depth or 0), "label": label.strip()})
    if not out:
        raise ValueError("a plan needs its steps")
    return _append(lambda events: {"type": "plan", "ts": _now(), "role": role, "effort": effort.strip(),
                                   "note": (note or "").strip(), "steps": out})


def plans(events=None):
    """[plan] - the last publish of each effort, oldest effort first; an effort published with no steps is gone."""
    out = {}
    for e in events if events is not None else read_events():
        if e.get("type") == "plan":
            out.pop(e["effort"], None)
            out[e["effort"]] = e
        elif e.get("type") == "plan-done":
            out.pop(e.get("effort"), None)
    return list(out.values())


def end_plan(role, effort):
    if effort not in {p["effort"] for p in plans()}:
        raise ValueError(f"no plan {effort!r}")
    return _append(lambda events: {"type": "plan-done", "ts": _now(), "role": role, "effort": effort})


def held(events=None):
    """Who holds main now, as their hold event, or None (the reviewer, the Board #11, 2026-10-10: "A - All five", D3: "a
    one-line flag on the Board" in place of "hold main" and "free" messages to every role)."""
    holding = None
    for e in events if events is not None else read_events():
        if e.get("type") == "hold":
            holding = e
        elif e.get("type") == "release" and holding and e.get("role") == holding.get("role"):
            holding = None
    return holding


def hold(role, why):
    _check_role(role)
    if not why.strip():
        raise ValueError("say what the hold is for (--why)")

    def make(events):
        now = held(events)
        if now and now["role"] != role:
            raise ValueError(f"main is held by {now['role']} since {now['ts']} ({now['why']}) - wait for its release")
        return {"type": "hold", "ts": _now(), "role": role, "why": why.strip()}
    return _append(make)


def release(role):
    def make(events):
        now = held(events)
        if not now or now["role"] != role:
            raise ValueError(f"{role} does not hold main" + (f" ({now['role']} does)" if now else ""))
        return {"type": "release", "ts": _now(), "role": role}
    return _append(make)


def items(events=None):
    """{id: item} - each item with its `answer` and `withdrawn` folded in, the last of each counting; an answer the
    reviewer changed keeps the ones before it in `earlier`, oldest first (the reviewer, 2026-10-11: "change #13 answer to
    B. no option to do that on the board")."""
    out = {}
    for e in events if events is not None else read_events():
        if e.get("type") == "item":
            out[e["id"]] = dict(e, answer=None, withdrawn=None, deferred=None, earlier=[])
        elif e.get("id") in out and e.get("type") == "answer":
            if out[e["id"]]["answer"]:
                out[e["id"]]["earlier"].append(out[e["id"]]["answer"])
            out[e["id"]]["answer"] = {k: e.get(k) for k in ("ts", "answer", "note")}
        elif e.get("id") in out and e.get("type") == "withdraw":
            out[e["id"]]["withdrawn"] = {k: e.get(k) for k in ("ts", "why")}
        elif e.get("id") in out and e.get("type") == "defer":
            out[e["id"]]["deferred"] = {"ts": e.get("ts")} if e.get("on") else None
    return out


def is_waiting(it):
    """An item the reviewer still has to answer now: open, and not put off for later."""
    return not (it["answer"] or it["withdrawn"] or it["deferred"])


IMAGE_TYPES = (".png", ".jpg", ".jpeg", ".gif", ".webp")


def ask(role, title, body="", kind="question", options=(), recommend=None, links=(), images=()):
    _check_role(role)
    if not title.strip():
        raise ValueError("a title is needed")
    opts = []
    for raw in options:
        key, _, rest = raw.partition("=")
        label, _, detail = rest.partition("|")
        if not key.strip() or not label.strip():
            raise ValueError(f"an option is KEY=label | what it means, not {raw!r}")
        opts.append({"key": key.strip(), "label": label.strip(), "detail": detail.strip()})
    links = _check_links(links)
    keys = {o["key"] for o in opts}
    pics, tied = [], []
    for raw in images:
        if not raw:
            continue
        key, sep, rest = raw.partition("=")
        if sep and key.strip() in keys:     # KEY=PATH: a mock-up of that option
            tied.append(key.strip())
            raw = rest
        else:
            tied.append(None)
        pics.append(os.path.abspath(os.path.expanduser(raw.strip())))
    for x in pics:
        if not x.lower().endswith(IMAGE_TYPES) or not os.path.isfile(x):
            raise ValueError(f"an image is an existing .png, .jpg, .gif or .webp file, not {x!r}")
    if recommend is not None and recommend not in {o["key"] for o in opts}:
        raise ValueError(f"the recommendation {recommend!r} is not one of the options")
    return _append(lambda events: {"type": "item", "id": 1 + max((e["id"] for e in events if e.get("type") == "item"),
                                                                 default=0),
                                   "ts": _now(), "role": role, "kind": kind, "title": title.strip(),
                                   "body": body.strip(), "options": opts, "recommend": recommend,
                                   "links": links, "images": pics, "image_options": tied})


def answer(item_id, text, note=""):
    if item_id not in items():
        raise ValueError(f"no item {item_id}")
    if not str(text).strip():
        raise ValueError("an answer is needed")
    return _append(lambda events: {"type": "answer", "id": item_id, "ts": _now(), "answer": str(text).strip(),
                                   "note": (note or "").strip()})


def withdraw(item_id, why):
    if item_id not in items():
        raise ValueError(f"no item {item_id}")
    return _append(lambda events: {"type": "withdraw", "id": item_id, "ts": _now(), "why": why.strip()})


def defer(item_id, on=True):
    """THE REVIEWER PUTS A QUESTION OFF (the reviewer, 2026-10-13: "i need a way to defer questions on the board"): it
    leaves "Questions for you" for a list of its own, can still be answered there, and comes back when brought back.
    Only an open item is deferred; an answer or a withdrawal ends a deferral by ending the question."""
    it = items().get(item_id)
    if it is None:
        raise ValueError(f"no item {item_id}")
    if it["answer"] or it["withdrawn"]:
        raise ValueError(f"#{item_id} is not open")
    return _append(lambda events: {"type": "defer", "id": item_id, "ts": _now(), "on": bool(on)})


def _check_role(role):
    if role not in ROLES:
        raise ValueError(f"unknown role {role!r}: one of {', '.join(ROLES)}")


def _check_links(links):
    for x in links:                          # a link is a web address only (girsa-verifier: a javascript: link would run)
        if x and not x.lower().startswith(("http://", "https://")):
            raise ValueError(f"a link is an http:// or https:// address, not {x!r}")
    return [x for x in links if x]


def qa(role, question, answer_text, links=()):
    """The reviewer's own question, asked in a role's pane, and the role's answer, kept on the Board (the reviewer,
    2026-10-13: "create another sub-board for my questions and agents answers - so they won't scroll away. if i ask the q
    in the session, each agent should copy the q and a to the board, and point me there with a quick summary in the
    session"). Numbered on their own, Q&A #1, #2 ..., apart from the items the roles put to the reviewer."""
    _check_role(role)
    if not question.strip() or not answer_text.strip():
        raise ValueError("a Q&A needs the reviewer's question and the answer")
    links = _check_links(links)
    return _append(lambda events: {"type": "qa", "qa": 1 + max((e["qa"] for e in events if e.get("type") == "qa"),
                                                               default=0),
                                   "ts": _now(), "role": role, "question": question.strip(),
                                   "answer": answer_text.strip(), "links": links})


def landed(role, summary, session=None, at=None):
    """A session's landing, with its summary - bullet points of what it accomplished (the reviewer, 2026-10-25: "when a
    session lands, it produces a summary of the session's work. when the nightly job clears the session that info is not
    seen. it should be placed on the board, so the session says landed not not running - and that summary is on the board
    till the next session starts - and then kept in a history"; "more than just the one line recap - bullet points of
    accomplishments"). The role's corner shows it until a session other than `session` runs as that role; every landing
    stays in the record, listed on the page under Landings. `at`: when it landed, where that was before it was posted
    (an ISO time from a record); a session posted again keeps only its last posting."""
    _check_role(role)
    if not summary.strip():
        raise ValueError("a landing needs its summary")
    if at is not None:   # one time without its offset broke every board_view() for good (the audit's item 3)
        when = _when(at)
        if when is None or when.tzinfo is None:
            raise ValueError(f"--at is an ISO time with its UTC offset, not {at!r}")
        at = when.astimezone().isoformat(timespec="seconds")     # the form _now() writes, so landings sort by it
    return _append(lambda events: {"type": "landed", "ts": at or _now(), "posted": _now(), "role": role,
                                   "session": session, "summary": summary.strip()})


def landings(events=None):
    """Every landing, oldest first - one per session, its last posting."""
    rows = [e for e in (events if events is not None else read_events()) if e.get("type") == "landed"]
    last = {e.get("session") or id(e): e for e in rows}
    return sorted(last.values(), key=lambda e: e["ts"])


def last_landing(role, events=None):
    return next((e for e in reversed(landings(events)) if e["role"] == role), None)


def live_agents():
    """The running sessions, as `claude agents --json` lists them (a list of rows), or [] when it cannot be read - the one
    reader for the Board's page and this command (girsa-verifier, 2026-10-26, LOW 4)."""
    import shutil
    import subprocess
    exe = shutil.which("claude") or os.path.expanduser("~/.local/bin/claude")
    try:
        rows = json.loads(subprocess.run([exe, "agents", "--json"], capture_output=True, text=True, timeout=15).stdout)
    except (OSError, ValueError, subprocess.SubprocessError):
        return []
    return [r for r in rows if isinstance(r, dict)] if isinstance(rows, list) else []


def session_of_role(role):
    """The running session named `role`, or None."""
    return next((r.get("sessionId") for r in live_agents() if r.get("name") == role), None)


def started_since(role, landing):
    """Whether a session other than the landed one has run as `role` since `landing` was posted - from the sessions'
    own records (`name` and `seen_at`, kept by the status line and the hook). Then the landed summary has had its time on
    the corner, though that next session has stopped without landing (girsa-verifier, 2026-10-26, MEDIUM 2: the reviewer,
    "that summary is on the board till the next session starts")."""
    posted = _when(landing.get("posted") or landing.get("ts"))
    folder = os.path.join(board_dir(), "sessions")
    try:
        names = [n for n in os.listdir(folder) if n.endswith(".json")]
    except OSError:
        return False
    if not posted:
        return False
    for name in names:
        sid = name[:-5]
        # a record last written before the posting cannot have been seen after it (record_session writes seen_at, then
        # the file), so it is not opened - every 5 s, for every record kept (the audit's item 14)
        if sid == landing.get("session") or os.path.getmtime(os.path.join(folder, name)) <= posted.timestamp():
            continue
        rec = session_record(sid)
        if rec.get("name") == role and (rec.get("seen_at") or 0) > posted.timestamp():
            return True
    return False


def qa_more(number, role, answer_text, question="", links=()):
    """A follow-up to Q&A #number: the reviewer's next question on it (optional) and the answer."""
    _check_role(role)
    if not answer_text.strip():
        raise ValueError("a follow-up needs its answer")
    links = _check_links(links)

    def make(events):
        if not any(e.get("type") == "qa" and e.get("qa") == number for e in events):
            raise ValueError(f"no Q&A #{number}")
        return {"type": "qa-more", "qa": number, "ts": _now(), "role": role, "question": (question or "").strip(),
                "answer": answer_text.strip(), "links": links}
    return _append(make)


def qas(events=None):
    """{number: Q&A} - each with its follow-ups in `more`, oldest first."""
    out = {}
    for e in events if events is not None else read_events():
        if e.get("type") == "qa":
            out[e["qa"]] = dict(e, more=[])
        elif e.get("type") == "qa-more" and e.get("qa") in out:
            out[e["qa"]]["more"].append({k: e.get(k) for k in ("ts", "role", "question", "answer", "links")})
    return out


def describe(it):
    a = it["answer"]
    picked = next((o for o in it["options"] if a and o["key"] == a["answer"]), None)
    said = (f'{a["answer"]} - {picked["label"]}' if picked else a["answer"]) if a else None
    state = ("withdrawn: " + it["withdrawn"]["why"]) if it["withdrawn"] else (f"answered: {said}" if a
                                                                              else "deferred" if it["deferred"] else "open")
    return f'#{it["id"]} {it["role"]} [{state}] {it["title"]}' + (f' (note: {a["note"]})' if a and a["note"] else "")


def waiting_on(role, events=None):
    """The role `role`'s corner says it is waiting for, or None - the night run reads it (the reviewer, 2026-10-11, on
    the night run's /land to the verifier while its corner said "waiting for piece 1's build": "night run should not have
    told the ver to land when it had work to do. it should not have been idle.")."""
    st = statuses(events).get(role) or {}
    return st.get("waiting_for") if st.get("state") == "waiting-agent" else None


# THE PLAN'S BUDGET (Q&A #56 A; the reviewer, 2026-10-25: "a and c - good. go"): every session's status line receives
# the plan's usage windows (`rate_limits`, Claude Code's status line input) and records them here; the page shows them,
# and at BUDGET_WARN percent of a window (the config's budget.warn_percent) every role is told once, by a hook - to keep
# its work landable and keep working, never to land for the budget alone: a landing buys nothing against a limit, which
# stops the account, not the session.
BUDGET_WARN = config.load()["budget"]["warn_percent"]
WINDOWS = (("five_hour", "5-hour"), ("seven_day", "7-day"))


def record_usage(rate_limits, session=None):
    """Keep the plan's windows as a status line last received them - one account, so the newest reading wins."""
    windows = {k: {"used_percentage": float(w["used_percentage"]), "resets_at": int(w["resets_at"])}
               for k, _ in WINDOWS for w in [(rate_limits or {}).get(k)] if w and "used_percentage" in w}
    if not windows:
        return None
    rec = dict(windows, seen_at=int(time.time()), session=session)
    os.makedirs(board_dir(), exist_ok=True)
    tmp = os.path.join(board_dir(), f".usage.{os.getpid()}.json")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(rec, f)
    os.replace(tmp, os.path.join(board_dir(), "usage.json"))
    return rec


def usage():
    """The newest reading, with each window whose reset has passed left out, or None."""
    try:
        with open(os.path.join(board_dir(), "usage.json"), encoding="utf-8") as f:
            rec = json.load(f)
    except (OSError, ValueError):
        return None
    now = time.time()
    for k, _ in WINDOWS:
        if k in rec and rec[k]["resets_at"] <= now:
            del rec[k]
    return rec


def at_limit():
    """The windows at their limit now, as "the 7-day window, resets Sun 15:00", or None. The night run sends no /land
    then: a session at the limit answers it with a notice and lands nothing (2026-10-30, the audit's item 1)."""
    rec = usage() or {}
    full = [f"the {label} window, resets {datetime.fromtimestamp(rec[k]['resets_at']).strftime('%a %H:%M')}"
            for k, label in WINDOWS if k in rec and rec[k]["used_percentage"] >= 100]
    return "; ".join(full) or None


def budget_notice(session_id):
    """The sentence a session is told when a window reaches BUDGET_WARN - once per session, window and reset - or
    None."""
    rec = usage() or {}
    due = [(k, label, rec[k]) for k, label in WINDOWS if k in rec and rec[k]["used_percentage"] >= BUDGET_WARN]
    if not due or not session_id:
        return None
    told_path = os.path.join(board_dir(), "budget_told.json")
    os.makedirs(board_dir(), exist_ok=True)
    with open(told_path + ".lock", "w") as lock:     # one writer at a time, as record_session (the audit's item 12)
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            with open(told_path, encoding="utf-8") as f:
                told = json.load(f)
        except (OSError, ValueError):
            told = {}
        keys = [f"{session_id} {k} {w['resets_at']}" for k, _, w in due]
        if all(key in told for key in keys):
            return None
        told.update({key: int(time.time()) for key in keys})
        tmp = f"{told_path}.{os.getpid()}.tmp"       # whole or not at all, as usage.json (girsa-verifier's note)
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            json.dump(told, f)
        os.replace(tmp, told_path)
    said = "; ".join(f"the {label} window is at {w['used_percentage']:.0f}%, resetting "
                     f"{datetime.fromtimestamp(w['resets_at']).strftime('%a %H:%M')}" for k, label, w in due)
    return (f"THE PLAN'S BUDGET: {said}. Say so to the reviewer in your next reply. Commit what is finished, keep your "
            f"state file current, keep working; land when the piece is done or the reviewer says so, never for the "
            f"budget alone (the Board shows the meter).")


# EACH SESSION'S OWN STATE (Q&A #56, ideas 1, 2 and 5; the reviewer, 2026-10-25: "1. 2. 3. 4. 5. go"): the status line
# and the hooks keep one small record per session - the prompt it waits on in its pane, the file it last edited, its
# prompt cache and context - which the page draws in the role's corner.
def _session_path(session_id):
    return os.path.join(board_dir(), "sessions", os.path.basename(str(session_id)) + ".json")


def session_record(session_id):
    try:
        with open(_session_path(session_id), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def record_session(session_id, **fields):
    """Merge `fields` into the session's record (a None value removes the field); written whole."""
    if not session_id:
        return None
    path = _session_path(session_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # ONE WRITER AT A TIME (girsa-verifier's note): the status line and the hook both read, merge and write; unlocked,
    # one could write back a prompt the other had just cleared
    with open(path + ".lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        rec = session_record(session_id)
        for k, v in fields.items():
            if v is None:
                rec.pop(k, None)
            else:
                rec[k] = v
        tmp = f"{path}.{os.getpid()}.tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            json.dump(rec, f)
        os.replace(tmp, path)
    return rec


def main(argv=None):
    # --help prints the whole usage above: the commands' one home since Board #85 A, step 3 (START_HERE names it)
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("ask")
    a.add_argument("--role", required=True)
    a.add_argument("--title", required=True)
    a.add_argument("--body", default="")
    a.add_argument("--body-file")
    a.add_argument("--kind", choices=("question", "decision"), default="question")
    a.add_argument("--option", action="append", default=[])
    a.add_argument("--recommend")
    a.add_argument("--link", action="append", default=[])
    a.add_argument("--image", action="append", default=[])
    w = sub.add_parser("wait")
    w.add_argument("id", type=int)
    # A TIMEOUT ON EVERY WATCHER (the reviewer, 2026-10-30: "should also have a timeout on watchers"; a quiet watch ran
    # 07:46-11:00 and never ended): each ends within the prompt cache's hour, so the wake that re-arms it keeps the
    # role warm; 0, never
    w.add_argument("--timeout", type=float, default=WATCH_TIMEOUT)
    qu = sub.add_parser("quiet")
    qu.add_argument("--port", type=int, default=config.load()["board_port"])
    qu.add_argument("--timeout", type=float, default=WATCH_TIMEOUT)
    ls = sub.add_parser("list")
    ls.add_argument("--role")
    ls.add_argument("--open", action="store_true")
    wd = sub.add_parser("withdraw")
    wd.add_argument("id", type=int)
    wd.add_argument("--why", required=True)
    df = sub.add_parser("defer", help="put an item off for later (the page's own route, for a relay or a test)")
    df.add_argument("id", type=int)
    st = sub.add_parser("status")
    st.add_argument("--role", required=True)
    st.add_argument("--state", choices=STATES)
    st.add_argument("--waiting-for")
    st.add_argument("--now")
    st.add_argument("--done")
    st.add_argument("--next")
    st.add_argument("--still", action="store_true", help="report the corner again as it stands (a KEEPALIVE's answer)")
    pl = sub.add_parser("plan")
    pl.add_argument("--role", required=True)
    pl.add_argument("--effort", required=True)
    pl.add_argument("--note", default="")
    pl.add_argument("--step", action="append", default=[])
    pl.add_argument("--end", action="store_true", help="take the effort off the Board")
    ho = sub.add_parser("hold")
    ho.add_argument("--role", required=True)
    ho.add_argument("--why", required=True)
    rl = sub.add_parser("release")
    rl.add_argument("--role", required=True)
    wf = sub.add_parser("waiting-for", help="print the role ROLE's corner says it waits for (nothing if none)")
    wf.add_argument("role")
    sub.add_parser("at-limit", help="print the plan windows at their limit now (nothing if none)")
    an = sub.add_parser("answer")
    an.add_argument("id", type=int)
    an.add_argument("--answer", required=True)
    an.add_argument("--note", default="")
    ld = sub.add_parser("landed")
    ld.add_argument("--role", required=True)
    ld.add_argument("--summary")
    ld.add_argument("--summary-file")
    ld.add_argument("--session", help="the landing session's id (default: the running session named --role)")
    ld.add_argument("--at", help="when it landed, if before now (an ISO time read from a record)")
    q = sub.add_parser("qa")
    q.add_argument("--role", required=True)
    q.add_argument("--question", required=True)
    q.add_argument("--answer")
    q.add_argument("--answer-file")
    q.add_argument("--link", action="append", default=[])
    qm = sub.add_parser("qa-more")
    qm.add_argument("number", type=int)
    qm.add_argument("--role", required=True)
    qm.add_argument("--question", default="")
    qm.add_argument("--answer")
    qm.add_argument("--answer-file")
    qm.add_argument("--link", action="append", default=[])
    args = ap.parse_args(argv)
    try:
        if args.cmd == "ask":
            body = open(args.body_file, encoding="utf-8").read() if args.body_file else args.body
            it = ask(args.role, args.title, body, args.kind, args.option, args.recommend, args.link, args.image)
            print(f'#{it["id"]} on the Board ({_url()}#item-{it["id"]}) - wait for it: '
                  f'python3 {os.environ.get("MISHMERET_AS", "board.py")} wait {it["id"]}')
        elif args.cmd == "wait":
            start = time.time()
            first = items().get(args.id)
            put_off_before = bool(first and first["deferred"])
            while True:
                it = items().get(args.id)
                if it is None:
                    raise ValueError(f"no item {args.id}")
                if it["answer"] or it["withdrawn"]:
                    print(describe(it))
                    return 0
                # deferred while this wait ran: said once, so the role goes on with other work (a wait started on an
                # item already deferred keeps waiting for its answer)
                if it["deferred"] and not put_off_before:
                    print(f"#{args.id} deferred by the reviewer - go on with other work; its answer comes later "
                          f"(wait {args.id} again to receive it)")
                    return 3
                if args.timeout and time.time() - start >= args.timeout:
                    print(f"#{args.id} still open after {int(args.timeout)} s - wait {args.id} again")
                    return 1
                time.sleep(5)
        elif args.cmd == "quiet":
            # NOTHING IS MOVING (the reviewer, 2026-10-28: "why are we stuck? not waiting for me"; "go"): the page's own
            # rule (board_server.quiet), read from the running Board each minute - a background wait that ends wakes
            # the operator, where the banner waits for someone to look
            import urllib.request
            start = time.time()
            while True:
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{args.port}/api/board", timeout=60) as r:
                        q = json.load(r).get("quiet")
                except (OSError, ValueError):
                    q = None
                if q:
                    since = datetime.fromtimestamp(q["since"]).strftime("%H:%M")
                    stuck = "; ".join(f"{role} waits for {w or '?'}" for role, w in (q.get("stuck") or {}).items())
                    print(f"NOTHING IS MOVING since {since} ({q['minutes']} min): no role working, "
                          f"{stuck or 'nothing waiting for the reviewer'}. Read each role's Next - is it waiting on "
                          f"something already done?")
                    for role, nxt in q["next"].items():
                        print(f"  {role}: {nxt or 'nothing reported'}")
                    return 0
                if args.timeout and time.time() - start >= args.timeout:
                    print(f"NO QUIET after {int(args.timeout // 60)} min - read each role's corner for a wait on a wait, "
                          f"then run quiet again")
                    return 1
                time.sleep(60)
        elif args.cmd == "list":
            for it in sorted(items().values(), key=lambda x: x["id"]):
                if (not args.role or it["role"] == args.role) and (not args.open or not (it["answer"] or it["withdrawn"])):
                    print(describe(it))
        elif args.cmd == "landed":
            if bool(args.summary) == bool(args.summary_file):
                raise ValueError("give the summary as --summary or --summary-file")
            text = args.summary or open(args.summary_file, encoding="utf-8").read()
            landed(args.role, text, args.session or session_of_role(args.role), args.at)
            print(f"{args.role}'s landing is on the Board ({_url()}): its corner says Landed until its "
                  f"next session starts; the page's Landings keep it")
        elif args.cmd == "status":
            if args.still:
                still(args.role)
            else:
                set_status(args.role, args.state, args.waiting_for, args.now, args.done, args.next)
            print(f"{args.role}'s corner updated ({_url()})")
        elif args.cmd == "plan":
            if args.end:
                end_plan(args.role, args.effort)
                print(f"{args.effort!r} taken off the Board")
            else:
                p = set_plan(args.role, args.effort, args.step, args.note)
                print(f"{args.effort!r}: {len(p['steps'])} steps on the Board ({_url()})")
        elif args.cmd == "hold":
            hold(args.role, args.why)
            print(f"main held by {args.role} - release it after the landing: board.py release --role {args.role}")
        elif args.cmd == "release":
            release(args.role)
            print("main released")
        elif args.cmd == "withdraw":
            withdraw(args.id, args.why)
            print(f"#{args.id} withdrawn")
        elif args.cmd == "defer":
            defer(args.id)
            print(describe(items()[args.id]))
        elif args.cmd == "waiting-for":
            w = waiting_on(args.role)
            if w:
                print(w)
        elif args.cmd == "at-limit":
            lim = at_limit()
            if lim:
                print(lim)
        elif args.cmd == "answer":
            answer(args.id, args.answer, args.note)
            print(describe(items()[args.id]))
        elif args.cmd in ("qa", "qa-more"):
            if (args.answer is None) == (args.answer_file is None):
                raise ValueError("give the answer once: --answer or --answer-file")
            text = open(args.answer_file, encoding="utf-8").read() if args.answer_file else args.answer
            if args.cmd == "qa":
                n = qa(args.role, args.question, text, args.link)["qa"]
            else:
                n = qa_more(args.number, args.role, text, args.question, args.link)["qa"]
            print(f"Q&A #{n} on the Board: {_url()}#qa-{n} - give the reviewer this link and a short summary")
    except ValueError as e:
        print(f"board: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
