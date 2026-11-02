"""keepalive_due.py --self SESSION_ID: which roles are due a KEEPALIVE now (Q&A #51; the reviewer, 2026-10-23: "keep-alive
go"). The prompt cache lives one hour from the start of a session's last call (measured: 58 minutes warm, every gap
over 60 cold); a cold wake rewrites the whole context at 40 times the price of a warm read (Opus 5.5).

A role (a live session of one of the config's roles) is due when it is idle, its last call is 45 to 58 minutes old and its context is 20k
tokens or more - waiting or not (the reviewer, 2026-10-23: "ui steward has been idle two+ hours. no keepalive"; a
ping costs a fortieth of a cold wake on Opus 5.5, an eightieth on Fable 5.1). The line says why it is idle when it is
waiting. The operator itself (--self) is due on the same age and size when any other role is due, so the session
that sends the pings is warm when it wakes. NOT AT NIGHT AFTER THE NIGHT RUN HAS LANDED A ROLE (the reviewer, 2026-10-25:
"nightly run keeps sessions below 200k - certainly don't run the keep-alive after that at night when idle"): between
18:00 and 06:00, a role whose night-run mark (agents-morning.sh: kept, landed-kept, left, cleared) is newer than its
last call is not pinged; once someone works with it again its last call is newer and the pings resume. Prints one line per due session; exit 0
if any, 1 if none (for an `until` loop). Remembers each (session, last call) it reported, so a session that did not
answer is not reported twice for the same call."""
import argparse, datetime, glob, json, os, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config  # noqa: E402
import board  # noqa: E402
import role_usage  # noqa: E402

PROJECT = role_usage.project_dir()          # the project tree's transcripts (the config)
REPO = config.root()
STATE = config.expand(config.load()["state_dir"])
SEEN = os.path.join(STATE, "keepalive_seen.json")
MIN_AGE, MAX_AGE, MIN_CTX = 45, 58, 20_000
NIGHT_DIR = os.path.join(STATE, "night")
NIGHT_MARKS = ("kept", "landed-kept", "left", "cleared")



def last_call(session_id):
    """(time, context tokens) of the transcript's last main-chain API call, or None."""
    path = os.path.join(PROJECT, session_id + ".jsonl")
    if not os.path.exists(path):
        return None
    found = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            if '"usage"' not in line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            u = (r.get("message") or {}).get("usage")
            if r.get("type") != "assistant" or r.get("isSidechain") or not u:
                continue
            ctx = u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
            found = (datetime.datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00")), ctx)
    return found


def landed_tonight(role, last):
    """True between 18:00 and 06:00 when tonight's night run marked `role` after its last call (`last`, aware UTC)."""
    now = datetime.datetime.now()
    if 6 <= now.hour < 18:
        return False
    night = (now if now.hour >= 18 else now - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    for mark in NIGHT_MARKS:
        path = os.path.join(NIGHT_DIR, night, f"{role}.{mark}")
        if os.path.exists(path) and os.path.getmtime(path) >= last.timestamp():
            return True
    return False


def has_background_run(pid):
    """A Bash tool shell (sourced from a shell snapshot) still alive under the role's process: its own run."""
    out = subprocess.run(["ps", "-axo", "pid=,ppid=,command="], capture_output=True, text=True).stdout
    kids, cmd = {}, {}
    for line in out.splitlines():
        p, pp, c = line.strip().split(None, 2) + [""] * (3 - len(line.strip().split(None, 2)))
        kids.setdefault(int(pp), []).append(int(p)); cmd[int(p)] = c
    todo = list(kids.get(pid, []))
    while todo:
        p = todo.pop()
        if "shell-snapshots" in cmd.get(p, ""):
            return True
        todo += kids.get(p, [])
    return False


def main():
    """A crash is said, and ends the operator's `until` loop (exit 0): its exit 1 read as "none due", and the loop slept
    on with no role ever pinged (the audit's item 4). `_main`'s own exits, and argparse's, pass through."""
    try:
        _main()
    except Exception as e:
        print(f"KEEPALIVE CHECK FAILED: {type(e).__name__}: {e}", flush=True)
        sys.exit(0)


def _main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self", dest="me", required=True, help="the operator's own session id")
    a = ap.parse_args()
    now = datetime.datetime.now(datetime.timezone.utc)
    sessions = json.loads(subprocess.run(["claude", "agents", "--json", "--all"], capture_output=True, text=True).stdout)
    seen = json.load(open(SEEN, encoding="utf-8")) if os.path.exists(SEEN) else {}
    due, waiting_any, me_row = [], False, None
    for s in sessions:
        if s.get("kind") != "interactive" or not s.get("sessionId"):
            continue
        lc = last_call(s["sessionId"])
        if not lc:
            continue
        age = (now - lc[0]).total_seconds() / 60
        row = (s.get("name"), s["sessionId"], age, lc[1], lc[0].isoformat())
        if s["sessionId"] == a.me:
            me_row = row
            continue
        # busy only for a background task of its own (a Board wait, a watcher): its turn has ended, and its cache cools
        # like any idle role's (2026-10-26: the builder, busy so, was compacted idle before its landing)
        idle = s.get("status") == "idle" or (s.get("status") == "busy" and role_usage.turn_ended(s["sessionId"]))
        if not idle or (s.get("name") or "") not in config.role_names():
            continue
        if landed_tonight(s.get("name"), lc[0]):
            continue
        why = ("waiting for " + board.waiting_on(s.get("name"))) if board.waiting_on(s.get("name")) else \
              ("its own run in the background" if has_background_run(s["pid"]) else "idle")
        waiting_any = True
        if MIN_AGE <= age < MAX_AGE and lc[1] >= MIN_CTX and seen.get(s["sessionId"]) != row[4]:
            due.append(("PING",) + row + (why,))
    if me_row and (due or waiting_any) and MIN_AGE <= me_row[2] < MAX_AGE and me_row[3] >= MIN_CTX \
            and seen.get(me_row[1]) != me_row[4]:
        due.append(("SELF",) + me_row + ("another role is waiting",))
    for kind, name, sid, age, ctx, ts, why in due:
        print(f"{kind} {name} {sid[:8]} idle {age:.0f} min, context {ctx // 1000}k, {why}", flush=True)
        seen[sid] = ts
    if due:
        with open(SEEN, "w", encoding="utf-8", newline="\n") as f:
            json.dump(seen, f, indent=1)
    sys.exit(0 if due else 1)


if __name__ == "__main__":
    main()
