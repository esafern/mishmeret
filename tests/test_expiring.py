"""What expires, on a calendar feed the Board serves (mishmeret/expiring.py; notes/PLAN-EXPIRING.md). Placeholder
items, a placeholder token and a placeholder project; no network."""
import base64
import importlib
import json
import os
import ssl
import time
from datetime import date, datetime, timezone

import pytest

from conftest import PKG, write_project  # noqa: F401


def _seg(obj):
    return base64.urlsafe_b64encode(json.dumps(obj).encode()).decode().rstrip("=")


EXP = 1893592156                                     # 2030-01-02T13:49:16Z
TOKEN = f"{_seg({'alg': 'none', 'typ': 'JWT'})}.{_seg({'exp': EXP, 'aud': 'placeholder'})}.placeholder-signature"


def _project(tmp_path, monkeypatch, items=None):
    """The placeholder project with `items` as its `expiring` (absent when None); returns (config, expiring)."""
    over = {} if items is None else {"expiring": items}
    monkeypatch.setenv("MISHMERET_CONFIG", write_project(tmp_path, **over))
    import config
    import expiring
    importlib.reload(config)
    return config, importlib.reload(expiring)


def _item(name, source, who="the reviewer", how="placeholder steps"):
    return {"name": name, "who": who, "how": how, "source": source}


def test_every_source_reads_its_date_and_says_why_it_cannot_never_with_the_token(tmp_path, monkeypatch):
    """Each of SOURCES, the list config.py checks and expiring.READERS reads (WRITE THE ENUMERATION DOWN): a date by
    hand, the one JWT under its keys ({root} the project's root), a certificate's notAfter. What cannot be read is not
    known, with why - never a guess (two tokens) and never the token's text (girsa-verifier's LOW 3); an expired
    certificate says its verification failed (LOW 2); the tls read has its timeout (girsa-architect)."""
    config, ex = _project(tmp_path, monkeypatch)
    assert set(ex.READERS) == set(config.SOURCES)
    assert ex.READERS["date"]("2030-01-02") == date(2030, 1, 2)
    assert ex.READERS["date"]("2030-01-02T13:49:16+00:00") == datetime.fromtimestamp(EXP, timezone.utc)
    whys = []
    for bad, why in ((None, "not known"), ("2030-01-02T13:49:16", "no UTC offset"), ("soon", "is not YYYY-MM-DD")):
        with pytest.raises(ex.Unknown, match=why):
            ex.READERS["date"](bad)
    root = os.path.dirname(os.path.dirname(os.environ["MISHMERET_CONFIG"]))
    store = tmp_path / "claude.json"

    def at(value):
        store.write_text(json.dumps({"projects": {root: {"mcpServers": {"s": {"headers": {"Authorization": value}}}}}}),
                         encoding="utf-8")
        return ex.read(_item("t", {"jwt": [str(store), "projects", "{root}", "mcpServers", "s"]}))
    assert at("Bearer " + TOKEN) == (datetime.fromtimestamp(EXP, timezone.utc), None)
    for value, why in (([TOKEN, TOKEN], "2 tokens"), ("Bearer " + TOKEN[:-30] + "." + TOKEN[-30:], "0 tokens"),
                       ("not a token at all", "0 tokens"), ("a.b.c", "0 tokens")):
        got, said = at(value)
        assert got is None and why in said, (value, said)
        whys.append(said)
    store.write_text("{not json", encoding="utf-8")
    whys += [ex.read(_item("t", {"jwt": [str(store), "projects"]}))[1],
             ex.read(_item("t", {"jwt": [str(tmp_path / "none.json"), "projects"]}))[1]]
    at("Bearer " + TOKEN)
    whys.append(ex.read(_item("t", {"jwt": [str(store), "projects", "elsewhere", "mcpServers"]}))[1])
    assert "is not JSON" in whys[-3] and "cannot be read" in whys[-2] and "no 'elsewhere'" in whys[-1], whys
    for part in TOKEN.split("."):
        assert not any(part in w for w in whys), "no part of the token in any why"
    # tls: the timeout reaches the connection; a host not reached, a certificate that fails verification, one read
    seen = []

    def refuse(address, timeout):
        seen.append(timeout)
        raise TimeoutError("placeholder")
    monkeypatch.setattr(ex.socket, "create_connection", refuse)
    got, why = ex.read(_item("c", {"tls": "placeholder.example"}))
    assert got is None and seen == [ex.TLS_TIMEOUT] == [5] and "not reached (TimeoutError)" in why, (seen, why)
    expired = ssl.SSLCertVerificationError(1, "certificate verify failed")
    expired.verify_message = "certificate has expired"

    def fails(host, timeout):
        raise expired
    monkeypatch.setattr(ex, "_peer_cert", fails)
    assert "certificate failed verification: certificate has expired" in ex.read(_item("c", {"tls": "x.example"}))[1]
    monkeypatch.setattr(ex, "_peer_cert", lambda host, timeout: {"notAfter": "Jan 15 19:18:21 2027 GMT"})
    assert ex.read(_item("c", {"tls": "x.example"})) == (datetime(2027, 1, 15, 19, 18, 21, tzinfo=timezone.utc), None)


def test_the_feed_reminds_on_the_local_day_and_shows_what_is_expired_or_not_known(tmp_path, monkeypatch, capsys):
    """The feed: a dated item's expiry and its reminders 7 and 1 days before on the machine's local day - here a zone
    whose day differs from UTC's at the token's hour (girsa-verifier's LOW 1); on today, EXPIRED for an item past its
    date (MEDIUM 2) and "Expiry not known" for one not known. CRLF lines folded at 75 octets, never inside a character;
    one UID each; no part of the token in the feed or the listing."""
    store = tmp_path / "claude.json"
    store.write_text(json.dumps({"s": {"headers": {"Authorization": "Bearer " + TOKEN}}}), encoding="utf-8")
    long_name = "a placeholder login whose name runs long enough to fold, with Hebrew in it: משמרת משמרת משמרת"
    items = [_item("the placeholder token", {"jwt": [str(store), "s"]}), _item(long_name, {"date": "2029-12-25"}),
             _item("the placeholder domain", {"date": None})]
    config, ex = _project(tmp_path, monkeypatch, items)
    monkeypatch.setenv("TZ", "Pacific/Kiritimati")             # UTC+14: 13:49 UTC is the next day's 03:49
    time.tzset()
    try:
        now = datetime(2030, 1, 1, 0, 0, tzinfo=timezone.utc)   # 14:00 on 2030-01-01 there
        feed = ex.ics(now=now)
        ex.main(now)
    finally:
        monkeypatch.delenv("TZ")
        time.tzset()
    listing = capsys.readouterr().out
    raw = feed.encode("utf-8")
    assert raw.endswith(b"\r\n") and b"\n" not in raw.replace(b"\r\n", b""), "CRLF only"
    assert max(len(line) for line in raw.split(b"\r\n")) <= 75
    lines = feed.replace("\r\n ", "").split("\r\n")                      # unfolded: whole characters again
    events = feed.replace("\r\n ", "").split("BEGIN:VEVENT")[1:]
    by_uid = {next(x for x in e.split("\r\n") if x.startswith("UID:")): e for e in events}
    assert len(by_uid) == len(events) == 3 + 3 + 1 + 1, list(by_uid)
    day = lambda uid: next(x for x in by_uid[f"UID:{uid}@example.mishmeret"].split("\r\n") if x.startswith("DTSTART"))
    assert day("the-placeholder-token-expires") == "DTSTART:20300102T134916Z"
    assert day("the-placeholder-token-lead-7") == "DTSTART;VALUE=DATE:20291227", "the local day, not UTC's 12-26"
    assert day("the-placeholder-token-lead-1") == "DTSTART;VALUE=DATE:20300102"
    slug = "a-placeholder-login-whose-name-runs-long-enough-to-fold-with-hebrew-in-it"
    assert day(f"{slug}-expired") == "DTSTART;VALUE=DATE:20300101", "EXPIRED on today"
    assert f"SUMMARY:EXPIRED: {long_name.replace(',', chr(92) + ',')} (since 2029-12-25)" in lines
    assert day("the-placeholder-domain-unknown") == "DTSTART;VALUE=DATE:20300101"
    assert any(x.startswith("SUMMARY:Expiry not known: the placeholder domain") for x in lines)
    assert "DESCRIPTION:Who acts: the reviewer. How: placeholder steps" in lines
    assert all("TRIGGER:" in e for e in events)
    for part in TOKEN.split("."):
        assert part not in feed and part not in listing
    assert "EXPIRED     " + long_name in listing and "NOT KNOWN   the placeholder domain" in listing, listing


def test_the_config_takes_no_expiring_items_and_refuses_a_bad_one_by_name(tmp_path, monkeypatch):
    """`expiring` is OPTIONAL: absent, nothing is tracked and the feed has no event. An item without its keys, with a
    source not of SOURCES, or a name given twice (its events' UIDs would be one: girsa-architect) is refused."""
    config, ex = _project(tmp_path, monkeypatch)
    assert ex.rows() == [] and "BEGIN:VEVENT" not in ex.ics()
    for items, said in (([{"name": "x", "who": "y", "source": {"date": None}}], "missing how"),
                        ([_item("x", {"when": "2030-01-01"})], "must be one of"),
                        ([_item("x", {"date": None, "tls": "h"})], "must be one of"),
                        ([_item("x", {"jwt": ["only-a-file"]})], "must be one of"),
                        ([_item("x", {"tls": 443})], "must be one of"),
                        ([_item("x", {"date": None}), _item("x", {"tls": "h"})], "names 'x' more than once")):
        monkeypatch.setenv("MISHMERET_CONFIG", write_project(tmp_path / str(len(said)) / said[:4], expiring=items))
        importlib.reload(config)
        with pytest.raises(config.ConfigError, match=said):
            config.load()


def test_the_board_serves_the_feed_to_its_own_host_alone(tmp_path, monkeypatch):
    """/expiring.ics: 200, text/calendar, read at the request; another Host refused, as every route."""
    import http.client
    import importlib.util
    import threading
    _project(tmp_path, monkeypatch, [_item("the placeholder domain", {"date": None})])
    monkeypatch.setenv("MISHMERET_BOARD_DIR", str(tmp_path / "board"))
    monkeypatch.syspath_prepend(PKG)
    spec = importlib.util.spec_from_file_location("board_server", os.path.join(PKG, "board_server.py"))
    bs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bs)
    srv = bs.ThreadingHTTPServer(("127.0.0.1", 0), bs.Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        def get(host):
            c = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=5)
            c.request("GET", "/expiring.ics", headers={"Host": host})
            r = c.getresponse()
            return r.status, r.getheader("Content-Type"), r.read().decode("utf-8")
        status, kind, body = get(f"127.0.0.1:{srv.server_address[1]}")
        assert status == 200 and kind.startswith("text/calendar") and body.startswith("BEGIN:VCALENDAR\r\n")
        assert "Expiry not known: the placeholder domain" in body
        assert get("elsewhere.example")[0] == 403
    finally:
        srv.shutdown()
