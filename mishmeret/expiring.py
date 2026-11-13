#!/usr/bin/env python3
"""WHAT EXPIRES, ON A CALENDAR FEED THE BOARD SERVES (notes/PLAN-EXPIRING.md; girsa-demo-operator's REQUEST, 2026-11-12,
the reviewer's words: "mishmeret should keep track of tokens, secrets and other things that expire - and set calendar
alerts so the user can take timely action"; the reviewer, 2026-11-13: "Board-served .ics feed", "7 days and 1 day").

The items are the project's - its config's `expiring` (OPTIONAL; config.py checks each): {"name", "who", "how",
"source"}, the source one of
    {"date": "YYYY-MM-DD" | an ISO time with its offset | null}   known by hand; null, not known
    {"jwt": [FILE, KEY, ...]}   the `exp` of the one JWT standing in that JSON file under those keys ("{root}": the
                                project's root) - decoded and dropped: never printed, kept, served or put in a why
    {"tls": HOST}               the certificate's notAfter on HOST:443
Each date is read at each ask, so a renewal moves it; one that cannot be read is not known, with why.

The feed: a dated item's expiry, and an all-day reminder LEAD_DAYS before it on the machine's local day, each with its
alarm; on today, "EXPIRED: NAME" for an item past its date and "Expiry not known: NAME" for one not known - so neither
reads as nothing due (girsa-verifier's MEDIUM 2: the first project's 10-31 lapse went unnoticed for three days).

    python3 expiring.py         each item: the days left, EXPIRED, or why it is not known
The Board serves the feed at /expiring.ics: subscribe to it once in Calendar, its location "On My Mac". Needs only
Python's standard library."""
import base64
import json
import os
import re
import socket
import ssl
import sys
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config  # noqa: E402

LEAD_DAYS = (7, 1)          # the reviewer, 2026-11-13: "7 days and 1 day"
REMINDER_ALARM = "PT9H"     # 09:00 on a reminder's day
TLS_TIMEOUT = 5             # seconds: the Mac is sometimes offline (girsa-architect), so a poll stays quick


class Unknown(Exception):
    """A date that cannot be read, and why - never with a secret's text."""


def _b64(part):
    return base64.urlsafe_b64decode(part + "=" * (-len(part) % 4))


def _exps(node):
    """The `exp` of each JWT standing in a JSON value, in order (a string's words, "Bearer" and the rest, each tried)."""
    if isinstance(node, dict):
        return [e for v in node.values() for e in _exps(v)]
    if isinstance(node, list):
        return [e for v in node for e in _exps(v)]
    found = []
    for word in node.split() if isinstance(node, str) else ():
        parts = word.split(".")
        if len(parts) != 3:
            continue
        try:
            head, body = json.loads(_b64(parts[0])), json.loads(_b64(parts[1]))
        except ValueError:                  # not base64, not JSON, not text: not a JWT
            continue
        exp = body.get("exp") if isinstance(body, dict) else None
        if isinstance(head, dict) and "alg" in head and isinstance(exp, (int, float)) and not isinstance(exp, bool):
            found.append(exp)
    return found


def _jwt(spec):
    path, *keys = spec
    try:
        with open(os.path.expanduser(path), encoding="utf-8") as fh:
            node = json.load(fh)
    except OSError as e:
        raise Unknown(f"{path} cannot be read ({e.strerror})") from None
    except ValueError:
        raise Unknown(f"{path} is not JSON") from None
    for key in keys:
        key = config.root() if key == "{root}" else key
        if not isinstance(node, dict) or key not in node:
            raise Unknown(f"{path} has no {key!r} under the keys before it")
        node = node[key]
    exps = _exps(node)
    if len(exps) != 1:
        raise Unknown(f"{len(exps)} tokens with an expiry under its keys in {path}, not one")
    return datetime.fromtimestamp(exps[0], timezone.utc)


def _peer_cert(host, timeout):
    with socket.create_connection((host, 443), timeout=timeout) as raw, \
            ssl.create_default_context().wrap_socket(raw, server_hostname=host) as tls:
        return tls.getpeercert()


def _tls(host):
    try:
        after = _peer_cert(host, TLS_TIMEOUT)["notAfter"]
    except ssl.SSLCertVerificationError as e:     # an expired certificate is one (girsa-verifier's LOW 2)
        raise Unknown(f"{host}'s certificate failed verification: {e.verify_message}") from None
    except OSError as e:
        raise Unknown(f"{host}:443 not reached ({type(e).__name__})") from None
    return datetime.fromtimestamp(ssl.cert_time_to_seconds(after), timezone.utc)


def _date(value):
    if value is None:
        raise Unknown("its date is not known - give it in the config")
    try:
        at = date.fromisoformat(value) if len(value) == 10 else datetime.fromisoformat(value)
    except ValueError:
        raise Unknown(f"{value!r} is not YYYY-MM-DD or an ISO time with its offset") from None
    if isinstance(at, datetime) and at.tzinfo is None:
        raise Unknown(f"{value!r} has no UTC offset")
    return at


# EVERY SOURCE, ITS READER: config.SOURCES names the same kinds (a test holds them to one list)
READERS = {"date": _date, "jwt": _jwt, "tls": _tls}


def read(item):
    """(at, why): the item's expiry - an aware datetime, or a date given alone - or None and why it is not known."""
    (kind, value), = item["source"].items()
    try:
        return READERS[kind](value), None
    except Unknown as e:
        return None, str(e)


def rows():
    """[(item, at, why)] for every item in the config, each read now."""
    return [(item, *read(item)) for item in config.load().get("expiring", [])]


def _day(at):
    """The local calendar day of an expiry: the machine's own zone, none named here (girsa-verifier's LOW 1)."""
    return at.astimezone().date() if isinstance(at, datetime) else at


def _said(at):
    return at.astimezone().strftime("%Y-%m-%d %H:%M %Z") if isinstance(at, datetime) else at.isoformat()


def _passed(at, now):
    return at <= now if isinstance(at, datetime) else at < _day(now)


def events(items, now):
    """The feed's events, each {uid, summary, description, start (aware datetime) or day (date)}."""
    out, today = [], _day(now)
    for item, at, why in items:
        slug = re.sub(r"[^a-z0-9]+", "-", item["name"].lower()).strip("-")
        said = f"Who acts: {item['who']}. How: {item['how']}"
        ev = lambda kind, summary, **when: out.append(dict(uid=f"{slug}-{kind}", summary=summary, description=said, **when))
        if at is None:
            ev("unknown", f"Expiry not known: {item['name']} ({why})", day=today)
            continue
        ev("expires", f"EXPIRES: {item['name']}", **({"start": at} if isinstance(at, datetime) else {"day": at}))
        for n in LEAD_DAYS:
            ev(f"lead-{n}", f"Renew {item['name']}: expires {_said(at)}, in {n} day{'s' * (n != 1)}",
               day=_day(at) - timedelta(days=n))
        if _passed(at, now):
            ev("expired", f"EXPIRED: {item['name']} (since {_said(at)})", day=today)
    return out


def _text(s):
    """A TEXT value (RFC 5545 3.3.11)."""
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _fold(line):
    """A content line folded at 75 octets, never inside a character (RFC 5545 3.1)."""
    raw, parts = line.encode("utf-8"), []
    while len(raw) > 75:
        cut = 75 if not parts else 74
        while raw[cut] & 0xC0 == 0x80:
            cut -= 1
        parts.append(raw[:cut])
        raw = raw[cut:]
    return b"\r\n ".join(parts + [raw]).decode("utf-8")


def ics(items=None, now=None):
    """The feed, as text/calendar."""
    now = now or datetime.now(timezone.utc)
    items = rows() if items is None else items
    host = re.sub(r"[^a-z0-9]+", "-", config.load()["project"].lower())
    stamp = now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Mishmeret//what expires//EN", "CALSCALE:GREGORIAN",
             f"X-WR-CALNAME:{_text(config.load()['project'])}: what expires"]
    for e in events(items, now):
        lines += ["BEGIN:VEVENT", f"UID:{e['uid']}@{host}.mishmeret", f"DTSTAMP:{stamp}"]
        if "start" in e:
            lines += [f"DTSTART:{e['start'].astimezone(timezone.utc):%Y%m%dT%H%M%SZ}", "DURATION:PT15M"]
        else:
            lines += [f"DTSTART;VALUE=DATE:{e['day']:%Y%m%d}", f"DTEND;VALUE=DATE:{e['day'] + timedelta(days=1):%Y%m%d}"]
        lines += [f"SUMMARY:{_text(e['summary'])}", f"DESCRIPTION:{_text(e['description'])}", "BEGIN:VALARM",
                  "ACTION:DISPLAY", f"DESCRIPTION:{_text(e['summary'])}",
                  f"TRIGGER:{'-PT1H' if 'start' in e else REMINDER_ALARM}", "END:VALARM", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "".join(_fold(line) + "\r\n" for line in lines)


def main(now=None):
    now = now or datetime.now(timezone.utc)
    for item, at, why in rows():
        if at is None:
            print(f"NOT KNOWN   {item['name']}: {why}")
        elif _passed(at, now):
            print(f"EXPIRED     {item['name']}: since {_said(at)} - {item['who']}; {item['how']}")
        else:
            print(f"{(_day(at) - _day(now)).days:>4} days   {item['name']}: {_said(at)}")


if __name__ == "__main__":
    main()
