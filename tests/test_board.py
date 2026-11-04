"""The Board, its page, its hook and the status line, moved from Girsa's tests/test_pipeline_logic.py at 2aba11b0 (its history there). A placeholder project
(tests/conftest.py): its roles are Girsa's shapes under the prefix "ex-"."""
import json
import os
import sys

import pytest

from conftest import PKG, REPO  # noqa: F401  (REPO: the placeholder project's root, written by the fixture)


def test_the_board_takes_a_roles_question_and_hands_back_the_reviewers_answer(tmp_path, monkeypatch):
    """The reviewer, 2026-10-09: "we need a special screen where each agent can supply answers to my questions and present
    decisions to me. it does not work to have them flow past in each window". .claude/board/board.py: a role asks (a
    question, or a decision with options, a recommendation, links and mock-up images), the reviewer answers on the page,
    the role reads the answer; an append-only record, every event a line. Placeholder questions in a temporary board."""
    import importlib.util
    monkeypatch.setenv("MISHMERET_BOARD_DIR", str(tmp_path / "board"))
    spec = importlib.util.spec_from_file_location("board", os.path.join(PKG, "board.py"))
    bd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bd)
    pic = tmp_path / "mock.png"
    pic.write_bytes(b"\x89PNG placeholder")
    one = bd.ask("ex-builder", "Placeholder decision", "Today: X.", "decision",
                 ["a=Do Y | the page shows Y", "b=Leave it"], "a", ["http://127.0.0.1:8421/entry/1"], [str(pic)])
    two = bd.ask("ex-verifier", "Placeholder question")
    assert (one["id"], two["id"]) == (1, 2)
    for refused in (lambda: bd.ask("ex-nobody", "x"), lambda: bd.set_status("ex-nobody", "idle"),
                    lambda: bd.hold("ex-nobody", "x"), lambda: bd.landed("ex-nobody", "- x")):
        with pytest.raises(ValueError, match="unknown role 'ex-nobody': one of ex-operator, "):
            refused()
    assert one["options"] == [{"key": "a", "label": "Do Y", "detail": "the page shows Y"},
                              {"key": "b", "label": "Leave it", "detail": ""}]
    for bad in (dict(role="someone", title="t"), dict(role="ex-builder", title=" "),
                dict(role="ex-builder", title="t", options=["a=x"], recommend="z"),
                dict(role="ex-builder", title="t", options=["=no key"]),
                dict(role="ex-builder", title="t", images=[str(tmp_path / "nothing.png")]),
                dict(role="ex-builder", title="t", links=["javascript:alert(1)"])):    # a link is a web address only
        try:
            bd.ask(**bad)
        except ValueError:
            continue
        raise AssertionError(f"accepted {bad}")
    bd.answer(1, "a", "placeholder note")
    bd.withdraw(2, "no longer needed")
    got = bd.items()
    assert got[1]["answer"]["answer"] == "a" and got[1]["answer"]["note"] == "placeholder note"
    assert got[2]["withdrawn"]["why"] == "no longer needed" and got[2]["answer"] is None
    assert "answered: a - Do Y" in bd.describe(got[1])
    lines = (tmp_path / "board" / "board.jsonl").read_text(encoding="utf-8").splitlines()
    assert [json.loads(x)["type"] for x in lines] == ["item", "item", "answer", "withdraw"]     # append-only
    assert bd.main(["wait", "1", "--timeout", "1"]) == 0
    page = open(os.path.join(PKG, "board_server.py"), encoding="utf-8").read()
    assert "filter(l => /^https?:" in page, "the page draws only http(s) links, whatever the record holds"


def test_the_reviewer_can_change_an_answer_on_the_board(tmp_path, monkeypatch):
    """The reviewer, 2026-10-11: "change #13 answer to B. no option to do that on the board". An answered item takes a
    new answer from the page only when the page asks for a change; the earlier answer is kept and said; a withdrawn item
    is never answered. Placeholder questions in a temporary board, through the page's own route."""
    import importlib.util
    import threading
    import urllib.request
    import urllib.error
    monkeypatch.setenv("MISHMERET_BOARD_DIR", str(tmp_path / "board"))
    monkeypatch.syspath_prepend(PKG)
    spec = importlib.util.spec_from_file_location("board_server", os.path.join(PKG, "board_server.py"))
    bs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bs)
    bd = bs.board
    one = bd.ask("ex-builder", "Placeholder decision", "", "decision", ["a=Do Y", "b=Do Z"], "a")
    two = bd.ask("ex-verifier", "Placeholder question")
    srv = bs.ThreadingHTTPServer(("127.0.0.1", 0), bs.Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]

    def post(body):
        req = urllib.request.Request(f"http://127.0.0.1:{port}/api/answer", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json", "Origin": f"http://127.0.0.1:{port}"})
        try:
            return urllib.request.urlopen(req, timeout=5).status
        except urllib.error.HTTPError as e:
            return e.code
    try:
        assert post({"id": one["id"], "answer": "a"}) == 200
        assert post({"id": one["id"], "answer": "b"}) == 409, "an answered item is not answered again unasked"
        assert bd.items()[one["id"]]["answer"]["answer"] == "a"
        assert post({"id": one["id"], "answer": "b", "note": "on second thought", "change": True}) == 200
        got = bd.items()[one["id"]]
        assert got["answer"]["answer"] == "b" and [x["answer"] for x in got["earlier"]] == ["a"]
        bd.withdraw(two["id"], "no longer needed")
        assert post({"id": two["id"], "answer": "x", "change": True}) == 409, "a withdrawn item is never answered"
        assert post({"id": 99, "answer": "x", "change": True}) == 409
    finally:
        srv.shutdown()
    page = open(os.path.join(PKG, "board_server.py"), encoding="utf-8").read()
    assert "data-change=" in page and "body.change = true" in page and "Changed from" in page


def test_the_board_takes_answers_only_from_its_own_page_and_only_as_a_json_object(tmp_path, monkeypatch):
    """The Mishmeret audit's items 8 and 18 (2026-11-01): the guard that keeps another website the reviewer visits from
    answering a role's question had no test - switched off, every test passed; and a JSON list sent to either route
    dropped the connection (AttributeError). Another Origin, another Host, or a body not sent as JSON is refused and the
    item stays open; a list is refused with each route's own code."""
    import importlib.util
    import threading
    import urllib.request
    import urllib.error
    monkeypatch.setenv("MISHMERET_BOARD_DIR", str(tmp_path / "board"))
    monkeypatch.syspath_prepend(PKG)
    spec = importlib.util.spec_from_file_location("board_server", os.path.join(PKG, "board_server.py"))
    bs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bs)
    bd = bs.board
    one = bd.ask("ex-builder", "Placeholder question")
    srv = bs.ThreadingHTTPServer(("127.0.0.1", 0), bs.Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]
    own = {"Content-Type": "application/json", "Origin": f"http://127.0.0.1:{port}"}

    def post(route, body, **headers):
        req = urllib.request.Request(f"http://127.0.0.1:{port}{route}", data=json.dumps(body).encode(),
                                     headers={**own, **headers})
        try:
            return urllib.request.urlopen(req, timeout=5).status
        except urllib.error.HTTPError as e:
            return e.code
    try:
        answer = {"id": one["id"], "answer": "placeholder"}
        for headers in ({"Origin": "http://evil.example"}, {"Content-Type": "text/plain"}, {"Host": "evil.example"}):
            assert post("/api/answer", answer, **headers) == 403, headers
            assert bd.items()[one["id"]]["answer"] is None, headers
        assert post("/api/defer", []) == 409 and post("/api/answer", []) == 400
        assert post("/api/answer", answer) == 200, "the page's own answer is still taken"
    finally:
        srv.shutdown()


def test_a_cut_off_line_in_the_record_stops_no_board_command(tmp_path, monkeypatch, capsys):
    """The Mishmeret audit's item 7: a write cut off mid-line (power loss, a full disk) made every later read raise -
    every command, every landing's hold and the page. The line is skipped and named; the next event starts a line of its
    own; nothing is rewritten. A temporary board."""
    import importlib.util
    monkeypatch.setenv("MISHMERET_BOARD_DIR", str(tmp_path / "board"))
    spec = importlib.util.spec_from_file_location("board", os.path.join(PKG, "board.py"))
    bd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bd)
    one = bd.ask("ex-builder", "Placeholder question")
    with open(bd._path(), "a", encoding="utf-8") as fh:
        fh.write('{"type": "item", "id"')
    assert [e["id"] for e in bd.read_events()] == [one["id"]]
    assert "line 2 of" in capsys.readouterr().err
    two = bd.ask("ex-verifier", "Another placeholder question")
    lines = open(bd._path(), encoding="utf-8").read().splitlines()
    assert lines[1] == '{"type": "item", "id"' and json.loads(lines[2])["id"] == two["id"]
    assert [e["id"] for e in bd.read_events()] == [one["id"], two["id"]]


def test_the_board_keeps_the_reviewers_own_questions_and_the_answers(tmp_path, monkeypatch, capsys):
    """The reviewer, 2026-10-13: "create another sub-board for my questions and agents answers - so they won't scroll
    away. if i ask the q in the session, each agent should copy the q and a to the board, and point me there with a quick
    summary in the session". board.py qa / qa-more: numbered on their own, follow-ups kept in order, the link printed for
    the pane; the page's "Your questions" view and its #qa-N link. Placeholder questions in a temporary board."""
    import importlib.util
    monkeypatch.setenv("MISHMERET_BOARD_DIR", str(tmp_path / "board"))
    spec = importlib.util.spec_from_file_location("board", os.path.join(PKG, "board.py"))
    bd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bd)
    bd.ask("ex-builder", "Placeholder decision")                   # an item does not take a Q&A number
    one = bd.qa("ex-verifier", "Placeholder question?", "Placeholder answer.", ["http://127.0.0.1:8420/entry/1"])
    assert one["qa"] == 1
    ans = tmp_path / "answer.txt"
    ans.write_text("A longer placeholder answer,\non two lines.", encoding="utf-8")
    assert bd.main(["qa", "--role", "ex-builder", "--question", "Second placeholder?", "--answer-file", str(ans)]) == 0
    assert "http://127.0.0.1:8450/#qa-2" in capsys.readouterr().out, "the pane is given the link"
    assert bd.main(["qa-more", "1", "--role", "ex-verifier", "--question", "And then?", "--answer", "Then this."]) == 0
    bd.qa_more(1, "ex-architect", "A further placeholder note.")
    got = bd.qas()
    assert sorted(got) == [1, 2] and got[2]["answer"] == "A longer placeholder answer,\non two lines."
    assert [(m["role"], m["question"], m["answer"]) for m in got[1]["more"]] == \
        [("ex-verifier", "And then?", "Then this."), ("ex-architect", "", "A further placeholder note.")]
    for bad in (lambda: bd.qa("someone", "q", "a"), lambda: bd.qa("ex-builder", " ", "a"),
                lambda: bd.qa("ex-builder", "q", " "), lambda: bd.qa("ex-builder", "q", "a", ["javascript:x"]),
                lambda: bd.qa_more(9, "ex-builder", "a"), lambda: bd.qa_more(1, "ex-builder", " ")):
        try:
            bad()
        except ValueError:
            continue
        raise AssertionError("a Q&A with no role, question or answer, a bad link, or a follow-up to nothing was kept")
    assert bd.main(["qa", "--role", "ex-builder", "--question", "q"]) == 2, "no answer given"
    assert sorted(bd.qas()) == [1, 2] and len(bd.items()) == 1
    page = open(os.path.join(PKG, "board_server.py"), encoding="utf-8").read()
    for needed in ('"qa": list(board.qas(events).values())', 'id="qatoggle"', "Your questions (${qa.length})",
                   'id="qa-${q.qa}"', 'addEventListener("hashchange", goToQA)', "refresh(true).then(goToQA)",
                   "const linksOf = ls => (ls || []).filter(l => /^https?:"):
        assert needed in page, needed


def test_a_message_between_roles_is_kept_until_its_receiver_marks_it_done(tmp_path, monkeypatch, capsys):
    """Board #150 B (the reviewer, 2026-11-04: "B"): messages sent to a role were lost when its session ended - three in
    one day. board.py send keeps each with its receiver, numbered on its own; inbox gives a role's next session what is
    still open for it; done is marked by the receiver alone, once; the corner counts the unacted, the texts on hover.
    Placeholder messages in a temporary board, read back through a fresh module, as a new session would."""
    import importlib.util
    monkeypatch.setenv("MISHMERET_BOARD_DIR", str(tmp_path / "board"))
    monkeypatch.syspath_prepend(PKG)

    def load(name):
        spec = importlib.util.spec_from_file_location(name, os.path.join(PKG, name + ".py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    bd = load("board")
    bd.ask("ex-builder", "Placeholder decision")                   # an item does not take a message number
    assert bd.send("ex-operator", "ex-builder", " REQUEST: placeholder one ")["msg"] == 1
    text = tmp_path / "msg.txt"
    text.write_text("LANDED placeholder,\non two lines.", encoding="utf-8")
    assert bd.main(["send", "--role", "ex-architect", "--to", "ex-builder", "--text-file", str(text)]) == 0
    assert 'headed "message #2"' in capsys.readouterr().out, "the sender is told to ring the doorbell with the number"
    bd.send("ex-builder", "ex-verifier", "HANDOFF placeholder")
    for bad in (lambda: bd.send("someone", "ex-builder", "x"), lambda: bd.send("ex-builder", "someone", "x"),
                lambda: bd.send("ex-builder", "ex-builder", "x"), lambda: bd.send("ex-operator", "ex-builder", " "),
                lambda: bd.done(9, "ex-builder"), lambda: bd.done(1, "ex-verifier")):
        with pytest.raises(ValueError):
            bad()
    assert bd.main(["send", "--role", "ex-operator", "--to", "ex-builder"]) == 2, "no text given"
    capsys.readouterr()
    # the receiver's next session: a fresh module over the same record
    bd = load("board")
    assert bd.main(["inbox", "--role", "ex-builder"]) == 0
    out = capsys.readouterr().out
    assert "message #1 from ex-operator" in out and "REQUEST: placeholder one" in out
    assert "LANDED placeholder,\non two lines." in out and "HANDOFF" not in out and "2 open - mark each done" in out
    assert bd.main(["done", "1", "--role", "ex-builder"]) == 0
    assert bd.main(["done", "1", "--role", "ex-builder"]) == 2, "marked done twice"
    assert [m["msg"] for m in bd.unacted("ex-builder")] == [2] and bd.messages()[1]["done"]
    bd.done(2, "ex-builder")
    capsys.readouterr()
    assert bd.main(["inbox", "--role", "ex-builder"]) == 0 and capsys.readouterr().out == "0 open\n"
    # the corner: the unacted messages to each role, whatever its state
    bs = load("board_server")
    monkeypatch.setattr(bs.LIVE, "get", lambda: {})
    roles = bs.board_view()["roles"]
    assert roles["ex-builder"]["unacted"] == [] and [m["text"] for m in roles["ex-verifier"]["unacted"]] == \
        ["HANDOFF placeholder"], "not running, and the message still shown"
    # a role with no corner (the config's "corner": false): its open messages for the header, by the config alone
    assert bs.board_view()["no_corner"] == {}
    bd.send("ex-operator", "ex-demo-operator", "REQUEST placeholder two")
    assert {r: [m["text"] for m in ms] for r, ms in bs.board_view()["no_corner"].items()} == \
        {"ex-demo-operator": ["REQUEST placeholder two"]}, "only the role with no corner, and only while one is open"
    assert "${esc(who)}${ms.length} open message${ms.length > 1 ? \"s\" : \"\"}</span>" in bs.PAGE
    assert 'title="${esc(ms.map(' in bs.PAGE, "a role's text escaped in the title (the browser test reads it)"
    assert "openPill(r.unacted || [], \"\")" in bs.PAGE and "openPill(ms, role + \": \")" in bs.PAGE, "one pill, two places"


def test_a_corners_name_and_state_stay_whole_beside_two_pills(tmp_path, monkeypatch):
    """The UI steward's measure of the mailbox's pill (2026-11-04), at the reviewer's smaller window, 1229x673: a stall
    pill and the messages' pill, each kept whole at up to 45% of the head, squeezed the state to 0 px and wrapped the
    role's name onto two lines. The name and the state now keep their width and the pills shorten, their text on hover.
    A role with no corner has its pill in the header, with its name (message #14). The real page from a scratch Board,
    in a headless browser; skipped where Playwright is not installed."""
    sync_api = pytest.importorskip("playwright.sync_api")
    import importlib.util
    import threading
    monkeypatch.setenv("MISHMERET_BOARD_DIR", str(tmp_path / "board"))
    monkeypatch.syspath_prepend(PKG)
    spec = importlib.util.spec_from_file_location("board_server", os.path.join(PKG, "board_server.py"))
    bs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bs)
    said = 'REQUEST "placeholder" <b>x</b>'        # a role's text, a quote and a tag in it, into a title attribute
    bs.board.send("ex-operator", "ex-architect", said)
    bs.board.send("ex-operator", "ex-demo-operator", "REQUEST placeholder")      # a role with no corner: the header
    monkeypatch.setattr(bs.LIVE, "get", lambda: {"ex-architect": {"status": "idle", "last_prompt": None, "session_id": None}})
    monkeypatch.setattr(bs, "stalled", lambda st, lv, shown, also: "waiting for ex-builder for 3 h 12 min"
                        if lv else None)
    server = bs.ThreadingHTTPServer(("127.0.0.1", 0), bs.Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with sync_api.sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1229, "height": 673}, device_scale_factor=2)
            page.goto(f"http://127.0.0.1:{server.server_address[1]}/")
            corner = page.locator(".corner", has=page.locator(".rname", has_text="ex-architect"))
            corner.locator(".stall").nth(1).wait_for()
            got = corner.evaluate("""c => { const r = c.querySelector(".rname"), b = c.querySelector(".badge");
                return {name: r.getBoundingClientRect().height, line: parseFloat(getComputedStyle(r).lineHeight),
                        badge: b.clientWidth, needs: b.scrollWidth,
                        pills: [...c.querySelectorAll(".stall")].map(s => s.title)}; }""")
            header = page.locator("#nocorner .stall").evaluate_all("els => els.map(e => [e.textContent, e.title])")
            browser.close()
    finally:
        server.shutdown()
    assert got["pills"] == ["waiting for ex-builder for 3 h 12 min", got["pills"][1]] and \
        got["pills"][1].startswith("message #1 from ex-operator") and got["pills"][1].endswith(": " + said), got
    assert got["name"] < 1.5 * got["line"], f"the role's name wrapped: {got}"
    assert 0 < got["needs"] <= got["badge"], f"the state cut: {got}"
    assert [t for t, _ in header] == ["ex-demo-operator: 1 open message"] and \
        header[0][1].startswith("message #2 from ex-operator"), header


def test_the_boards_corners_and_mockup_pages(tmp_path, monkeypatch):
    """The reviewer, 2026-10-10: "divide it up like these screens, so each agent has it's own corner to report status -
    what it is working on, what just finished and what is next - always in the same place, no scrolling. status should
    be Idle / Working / Waiting for agent X / waiting for input from Reviewer - each with a color ... mockups are in a sep
    window - always A on left B on right with arrow keys left and right for multiple pages." Placeholder reports."""
    import importlib.util
    monkeypatch.setenv("MISHMERET_BOARD_DIR", str(tmp_path / "board"))
    spec = importlib.util.spec_from_file_location("board", os.path.join(PKG, "board.py"))
    bd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bd)
    # a corner keeps each field's last value; a report changes only what it names
    bd.set_status("ex-builder", now="placeholder work", next_="placeholder next")
    bd.set_status("ex-builder", done="placeholder done", state="waiting-agent", waiting_for="ex-verifier")
    st = bd.statuses()["ex-builder"]
    assert (st["now"], st["done"], st["next"], st["state"], st["waiting_for"]) == \
        ("placeholder work", "placeholder done", "placeholder next", "waiting-agent", "ex-verifier")
    for bad in (dict(role="someone", now="x"), dict(role="ex-builder"), dict(role="ex-builder", state="asleep"),
                dict(role="ex-builder", state="waiting-agent"), dict(role="ex-builder", waiting_for="ex-verifier"),
                dict(role="ex-builder", state="waiting-agent", waiting_for="ex-builder")):
        try:
            bd.set_status(**bad)
        except ValueError:
            continue
        raise AssertionError(f"accepted {bad}")
    # the running session decides first; a reported wait shows only while idle, and only until a prompt comes after it
    assert bd.shown_state(st, None, [])[0] == "not-running"
    assert bd.shown_state(st, "busy", [3])[0] == "working"
    assert bd.shown_state(st, "waiting", [])[0] == "waiting-reviewer"
    assert bd.shown_state(st, "idle", [3]) == ("waiting-reviewer", "Waiting for the Reviewer - #3 below")
    assert bd.shown_state(st, "idle", [], last_prompt=None) == ("waiting-agent", "Waiting for ex-verifier")
    assert bd.shown_state(st, "idle", [], last_prompt="2000-01-01T00:00:00Z")[0] == "waiting-agent"
    assert bd.shown_state(st, "idle", [], last_prompt="2999-01-01T00:00:00Z")[0] == "idle", "a stale report shown"
    assert bd.shown_state(bd.statuses()["ex-operator"], "idle", [])[0] == "idle"
    # the Board #6, "A - Add a second badge": a working role's fresh reported wait shows beside Working
    assert bd.also_waiting(st, "busy", "2000-01-01T00:00:00Z") == "and waiting for ex-verifier"
    assert bd.also_waiting(st, "busy", "2999-01-01T00:00:00Z") is None, "a stale wait shown"
    assert bd.also_waiting(st, "idle") is None and bd.also_waiting(bd.statuses()["ex-operator"], "busy") is None
    # mock-ups: KEY=PATH ties an image to its option; page k shows A's and B's k-th images, A on the left
    pics = []
    for n in range(5):
        pic = tmp_path / f"m{n}.png"
        pic.write_bytes(b"\x89PNG placeholder")
        pics.append(str(pic))
    it = bd.ask("ex-builder", "Placeholder decision", "", "decision", ["A=One", "B=Two"], "A", [],
                [f"B={pics[0]}", f"A={pics[1]}", f"A={pics[2]}", f"B={pics[3]}", pics[4]])
    assert it["image_options"] == ["B", "A", "A", "B", None]
    assert [[(x["key"], x["n"]) for x in page] for page in bd.mockup_pages(it)] == \
        [[("A", 1), ("B", 0)], [("A", 2), ("B", 3)], [(None, 4)]]
    old = {"options": [], "images": ["a.png", "b.png", "c.png"]}          # an item written before images had options
    # a multi-day effort's plan: the whole list each time, the last publish counts; ended, it leaves the Board
    bd.set_plan("ex-builder", "Placeholder effort", ["done=one", "now=two", "next:1=three"])
    bd.set_plan("ex-builder", "Placeholder effort", ["done=one", "done=two", "now=three"], "placeholder note")
    got = bd.plans()
    assert len(got) == 1 and [(s["state"], s["depth"]) for s in got[0]["steps"]] == [("done", 0), ("done", 0), ("now", 0)]
    for bad in (["soon=x"], ["now:2=x"], ["now="], []):
        try:
            bd.set_plan("ex-builder", "Placeholder effort", bad)
        except ValueError:
            continue
        raise AssertionError(f"accepted {bad}")
    bd.end_plan("ex-builder", "Placeholder effort")
    assert bd.plans() == []
    # main held: one role at a time, released only by its holder (the Board #11, D3)
    assert bd.held() is None
    bd.hold("ex-builder", "placeholder landing")
    assert bd.held()["role"] == "ex-builder"
    for bad in (lambda: bd.hold("ex-verifier", "another landing"), lambda: bd.release("ex-verifier"),
                lambda: bd.hold("ex-builder", " ")):
        try:
            bad()
        except ValueError:
            continue
        raise AssertionError("a second hold, a release by another role, or a hold with no reason was accepted")
    bd.release("ex-builder")
    assert bd.held() is None
    bd.hold("ex-verifier", "placeholder landing")
    assert bd.held()["role"] == "ex-verifier"
    assert [[x["n"] for x in page] for page in bd.mockup_pages(old)] == [[0, 1], [2]]
    # the page: the corners in the tmux window's order, the arrow keys in the mock-up window, the states' colours
    page = open(os.path.join(PKG, "board_server.py"), encoding="utf-8").read()
    for needed in ('"ui-steward architect" "operator verifier" "builder builder"', 'e.key === "ArrowRight"',
                   'e.key === "ArrowLeft"', "--st-working", "--st-idle", "--st-waiting-agent", "--st-waiting-reviewer",
                   "!showDone && !showDeferred && !open.length && (data.plans || []).length"):   # the plan only while no question waits
        assert needed in page, needed
    # a corner's line boxes are never squeezed; a corner whose two-line entries do not fit shows one line each (the
    # reviewer, 2026-10-12: "on the architect corner of the board, second lines are cut off")
    for needed in ("grid-auto-rows:max-content", "fitCorners();", 'addEventListener("resize", fitCorners)',
                   'if (c.scrollHeight > c.clientHeight + 1) c.style.setProperty("--clamp", 1)'):
        assert needed in page, needed
    assert page.count("fitCorners();") == 2, "both places that draw the corners fit them"


def test_the_board_shows_the_visitors_report(tmp_path, monkeypatch):
    """The reviewer, 2026-10-28: "show the visitor stats on the board. updated twice a day for now" (Board #96): the
    Board serves traffic.json from its folder as written, says there is none before the first, and names a file it
    cannot read; the page's Visitors view draws it. A placeholder report in a temporary board."""
    import importlib.util
    monkeypatch.setenv("MISHMERET_BOARD_DIR", str(tmp_path / "board"))
    monkeypatch.syspath_prepend(PKG)
    spec = importlib.util.spec_from_file_location("board_server", os.path.join(PKG, "board_server.py"))
    bs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bs)
    assert bs.visitors() == {"missing": True}
    (tmp_path / "board").mkdir(exist_ok=True)
    report = {"made": "2026-01-01T06:30:00Z", "logs_through": "2026-01-01T06:29:00Z", "sites": [
        {"site": "a demo", "kind": "demo", "days": [{"day": "2026-01-01", "visits": 2, "ours": 1, "phones": 1, "minutes_total": 9,
                                                    "minutes_median": 4.5, "minutes_longest": 6, "saved": 1, "saves": 3,
                                                    "checked": 0}]}]}
    (tmp_path / "board" / "traffic.json").write_text(json.dumps(report), encoding="utf-8")
    assert bs.visitors() == report
    (tmp_path / "board" / "traffic.json").write_text("{", encoding="utf-8")
    assert "could not be read" in bs.visitors()["error"]
    page = open(os.path.join(PKG, "board_server.py"), encoding="utf-8").read()
    assert 'id="visittoggle"' in page and 'fetch("/api/visitors")' in page and "visitorsTable()" in page
    assert 'self.path == "/api/visitors"' in page
    view = page[page.index("function visitorsTable()"):page.index("document.addEventListener(\"change\"")]
    assert 'x == null ? "?"' in view and "|| 0" not in view, "a number the report lacks is drawn ?, never 0 (Lesson 59)"


def test_the_board_says_when_nothing_is_moving(tmp_path, monkeypatch, capsys):
    """The reviewer, 2026-10-28: "why are we stuck? not waiting for me" (every role idle 10:56-14:34, the builder's next
    piece held on conditions met hours before), then "go": no role working, nothing on the reviewer, no transcript
    written for QUIET_MIN minutes - the banner, and `board.py quiet`, which ends and so wakes the operator."""
    import importlib.util
    import threading
    from http.server import ThreadingHTTPServer
    monkeypatch.setenv("MISHMERET_BOARD_DIR", str(tmp_path / "board"))
    monkeypatch.setenv("MISHMERET_TRANSCRIPTS", str(tmp_path))
    monkeypatch.syspath_prepend(PKG)
    spec = importlib.util.spec_from_file_location("board_server", os.path.join(PKG, "board_server.py"))
    bs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bs)
    now = 2_000_000_000
    for sid, age in (("s1", 45), ("s2", 31)):
        (tmp_path / f"{sid}.jsonl").write_text("{}\n", encoding="utf-8")
        os.utime(tmp_path / f"{sid}.jsonl", (now - age * 60, now - age * 60))
    live = {"ex-builder": {"status": "idle", "session_id": "s1"}, "ex-verifier": {"status": "idle", "session_id": "s2"}}
    roles = {"ex-builder": {"shown": "idle", "next": "the land.py piece, after the steward's check"},
             "ex-verifier": {"shown": "waiting-agent", "next": None}}
    q = bs.quiet(roles, live, {}, None, now=now)
    assert q == {"since": now - 31 * 60, "minutes": 31, "next": {"ex-builder": "the land.py piece, after the steward's check",
                                                                 "ex-verifier": None},
                 "stuck": {"ex-verifier": None}}, q
    assert bs.quiet(roles, live, {}, None, now=now - 2 * 60) is None, "under QUIET_MIN since the last write"
    assert bs.quiet(dict(roles, **{"ex-verifier": {"shown": "working"}}), live, {}, None, now=now) is None
    unstuck = dict(roles, **{"ex-verifier": {"shown": "idle"}})
    assert bs.quiet(dict(roles, **{"ex-verifier": {"shown": "waiting-reviewer"}}), live, {}, None, now=now) is None
    item = {"answer": None, "withdrawn": None, "deferred": None}
    assert bs.quiet(unstuck, live, {1: item}, None, now=now) is None, "a question waits for the reviewer"
    assert bs.quiet(unstuck, live, {1: dict(item, deferred={"ts": "x"})}, None, now=now), "a deferred one does not"
    # 2026-10-30, 09:13-11:00: the verifier waited for the builder, whose turn had ended, while #108 waited for the
    # reviewer and the steward showed it - a wait on a role not working is stuck whatever waits for the reviewer
    morning = {"ex-builder": {"shown": "idle", "next": "land E M1"},
               "ex-verifier": {"shown": "waiting-agent", "waiting_for": "ex-builder", "next": None},
               "ex-ui-steward": {"shown": "waiting-reviewer", "next": None}}
    q2 = bs.quiet(morning, live, {108: item}, None, now=now)
    assert q2 and q2["stuck"] == {"ex-verifier": "ex-builder"}, q2
    # a chain that ends at the reviewer is no stall (ex-verifier's LOW on ff051e8e; 10-27 11:31: four roles waited
    # on the architect while it waited for the reviewer); a cycle is one
    chain = dict(morning, **{"ex-builder": {"shown": "waiting-agent", "waiting_for": "ex-architect", "next": None},
                             "ex-architect": {"shown": "waiting-reviewer", "next": None}})
    assert bs.quiet(chain, live, {108: item}, None, now=now) is None, "verifier on builder on architect on the reviewer"
    cycle = dict(morning, **{"ex-builder": {"shown": "waiting-agent", "waiting_for": "ex-verifier", "next": None}})
    assert bs.quiet(cycle, live, {108: item}, None, now=now)["stuck"] == {"ex-verifier": "ex-builder",
                                                                          "ex-builder": "ex-verifier"}
    assert bs.quiet(roles, live, {}, {"role": "ex-operator"}, now=now) is None, "main held: a landing runs"
    assert bs.quiet({}, {}, {}, None, now=now) is None, "no role running (the night): nothing to say"
    page = bs.PAGE
    assert '<div id="quiet"></div>' in page and "drawHeld(); drawUsage(); drawQuiet();" in page
    assert "`Nothing is moving since ${" in page and "waits for ${" in page
    # board.py quiet: reads the running Board, ends when it says quiet
    views = iter([{"quiet": None}, {"quiet": q2}])
    monkeypatch.setattr(bs, "board_view", lambda: next(views))
    monkeypatch.setattr(bs.board.time, "sleep", lambda s: None)
    server = ThreadingHTTPServer(("127.0.0.1", 0), bs.Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        assert bs.board.main(["quiet", "--port", str(server.server_address[1])]) == 0
        out = capsys.readouterr().out
        assert out.startswith("NOTHING IS MOVING since ") and "(31 min)" in out
        assert "ex-verifier waits for ex-builder" in out, out
        # A TIMEOUT ON EVERY WATCHER (the reviewer, 2026-10-30): with no quiet, quiet ends after its timeout, and wait
        # does on an open item - each by default within the prompt cache's hour
        monkeypatch.setattr(bs, "board_view", lambda: {"quiet": None})
        clock = iter(range(0, 10_000, 30))
        monkeypatch.setattr(bs.board.time, "time", lambda: next(clock))
        assert bs.board.main(["quiet", "--port", str(server.server_address[1]), "--timeout", "90"]) == 1
        assert capsys.readouterr().out.startswith("NO QUIET after 1 min")
    finally:
        server.shutdown()
    assert 0 < bs.board.WATCH_TIMEOUT < 60 * 60
    parser_defaults = open(os.path.join(PKG, "board.py"), encoding="utf-8").read()
    assert parser_defaults.count("type=float, default=WATCH_TIMEOUT)") == 2, "wait and quiet both time out"
    assert "  ex-builder: land E M1" in out and "  ex-verifier: nothing reported" in out


def test_a_session_tells_the_board_its_prompt_its_file_and_its_cache(tmp_path, monkeypatch):
    """Q&A #56 ideas 1, 2 and 5 (the reviewer, 2026-10-25: "1. 2. 3. 4. 5. go"): a permission prompt or a question dialog
    is recorded for the role's corner and cleared by the next tool run or prompt (an idle notice is not recorded); an
    Edit's file is recorded; the status line records the session's context and prompt cache; the corner draws them.
    Placeholder sessions in a temporary board."""
    import importlib.util
    import subprocess
    monkeypatch.setenv("MISHMERET_BOARD_DIR", str(tmp_path / "board"))
    monkeypatch.syspath_prepend(PKG)
    spec = importlib.util.spec_from_file_location("board_server", os.path.join(PKG, "board_server.py"))
    bs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bs)
    bd = bs.board
    hook = PKG
    env = dict(os.environ, MISHMERET_BOARD_DIR=str(tmp_path / "board"))

    def run(script, **data):
        return subprocess.run([sys.executable, os.path.join(hook, script)], env=env, capture_output=True, text=True,
                              input=json.dumps(data))
    run("board_hook.py", session_id="s1", hook_event_name="Notification", notification_type="idle_prompt", message="idle")
    assert "prompt" not in bd.session_record("s1"), "an idle notice is not a prompt waiting for the reviewer"
    run("board_hook.py", session_id="s1", hook_event_name="Notification", notification_type="permission_prompt",
        message="Claude needs your permission to use Bash")
    assert bd.session_record("s1")["prompt"]["message"] == "Claude needs your permission to use Bash"
    run("board_hook.py", session_id="s1", hook_event_name="PostToolUse", tool_name="Edit",
        tool_input={"file_path": "/placeholder/tree/pipeline/x.py"})
    rec = bd.session_record("s1")
    assert "prompt" not in rec and rec["editing"]["path"] == "/placeholder/tree/pipeline/x.py"
    run("board_hook.py", session_id="s1", hook_event_name="Notification", notification_type="elicitation_dialog", message="Q")
    run("board_hook.py", session_id="s1", hook_event_name="UserPromptSubmit")
    assert "prompt" not in bd.session_record("s1") and "editing" in bd.session_record("s1")
    run("statusline.py", session_id="s1", session_name="ex-builder",
        context_window={"current_usage": {"input_tokens": 1, "cache_read_input_tokens": 99999}},
        prompt_cache={"warm": True, "hit_ratio": 0.9, "misses": 2, "expires_at": 2000000000, "requests": 7})
    rec = bd.session_record("s1")
    assert rec["context"] == 100000 and rec["cache"] == {"warm": True, "hit_ratio": 0.9, "misses": 2, "expires_at": 2000000000}
    assert "editing" in rec, "the status line keeps what the hook recorded"
    monkeypatch.setattr(bs.LIVE, "get", lambda: {"ex-builder": {"status": "idle", "last_prompt": None, "session_id": "s1"}})
    assert bs.board_view()["roles"]["ex-builder"]["session"]["context"] == 100000
    assert "last_turn" not in rec, "a session reporting its context has no last turn to show"
    # COMPACTED WHILE IDLE (the reviewer, 2026-10-28): no context until the next turn - the transcript's last main-chain
    # call says what it was; a subagent's call and a call with no usage are passed over
    transcript = tmp_path / "s1.jsonl"
    transcript.write_text("\n".join(json.dumps(e) for e in (
        {"type": "assistant", "timestamp": "2026-10-28T08:56:36.784Z",
         "message": {"usage": {"input_tokens": 6, "cache_creation_input_tokens": 280, "cache_read_input_tokens": 517000}}},
        {"type": "assistant", "isSidechain": True, "timestamp": "2026-10-28T08:57:00Z",
         "message": {"usage": {"input_tokens": 9000}}},
        {"type": "user", "message": {"content": "x"}}, "not json")) + "\n", encoding="utf-8")
    run("statusline.py", session_id="s1", session_name="ex-builder", transcript_path=str(transcript),
        context_window={"current_usage": None})
    rec = bd.session_record("s1")
    assert rec["context"] == 0 and rec["last_turn"] == {"context": 517286, "at": 1793177796}, rec
    transcript.write_text("", encoding="utf-8")
    run("statusline.py", session_id="s1", session_name="ex-builder", transcript_path=str(transcript))
    assert bd.session_record("s1")["last_turn"]["context"] == 517286, "read once per compaction, then kept"
    run("statusline.py", session_id="s1", session_name="ex-builder",
        context_window={"current_usage": {"input_tokens": 1, "cache_read_input_tokens": 89999}})
    assert "last_turn" not in bd.session_record("s1"), "called again: its context is known, the last turn goes"
    run("statusline.py", session_id="s2", session_name="ex-verifier", transcript_path=str(tmp_path / "none.jsonl"))
    assert "last_turn" not in bd.session_record("s2"), "a new session with no call yet says nothing"
    page = open(os.path.join(PKG, "board_server.py"), encoding="utf-8").read()
    assert "${tele(r.session || {})}" in page and "Waiting for you in its pane since" in page
    assert "else if (s.last_turn) parts.push(`compacted: context not known until its next turn (it was " in page


def test_the_status_line_gives_the_boards_state_on_a_second_row(tmp_path, monkeypatch):
    """Q&A #56 B (Board #73 A, "Build it"): a second row with the questions waiting for the reviewer, who holds main and
    what this role waits on - none of it, no second row; a refresh with the same plan figures records nothing new; the
    line refreshes every minute. Placeholder items in a temporary board."""
    import subprocess
    monkeypatch.setenv("MISHMERET_BOARD_DIR", str(tmp_path / "board"))
    monkeypatch.syspath_prepend(PKG)
    import importlib
    bd = importlib.import_module("board")
    env = dict(os.environ, MISHMERET_BOARD_DIR=str(tmp_path / "board"))

    def rows(**data):
        out = subprocess.run([sys.executable, os.path.join(PKG, "statusline.py")], env=env,
                             capture_output=True, text=True, input=json.dumps(dict({"session_name": "ex-builder"}, **data)))
        return out.stdout.splitlines()
    assert rows() == [""], "nothing on the Board: one row"
    one = bd.ask("ex-verifier", "Placeholder question")
    bd.ask("ex-architect", "Placeholder decision", "", "decision", ["a=Do Y"], "a")
    bd.hold("ex-ui-steward", "landing a placeholder")
    bd.set_status("ex-builder", state="waiting-agent", waiting_for="ex-verifier")
    got = rows()[1]
    assert got.startswith(f"Board: 2 questions for you (#{one['id']} ex-verifier, #{one['id'] + 1} ex-architect)"), got
    assert "main held by ex-ui-steward since " in got and got.endswith(" - landing a placeholder · this role waits for ex-verifier")
    bd.withdraw(one["id"], "no longer needed")
    bd.release("ex-ui-steward")
    assert rows()[1].startswith("Board: 1 question for you (#") and "main held" not in rows()[1]
    soon = int(__import__("time").time()) + 3600
    rl = {"five_hour": {"used_percentage": 10, "resets_at": soon}}
    rows(rate_limits=rl)
    first = bd.usage()["seen_at"]
    os.utime(os.path.join(str(tmp_path / "board"), "usage.json"))
    with open(os.path.join(str(tmp_path / "board"), "usage.json"), encoding="utf-8") as f:
        rec = json.load(f)
    rec["seen_at"] = first - 100
    with open(os.path.join(str(tmp_path / "board"), "usage.json"), "w", encoding="utf-8") as f:
        json.dump(rec, f)
    rows(rate_limits=rl)
    assert bd.usage()["seen_at"] == first - 100, "the same figures again are not recorded"
    rows(rate_limits={"five_hour": {"used_percentage": 11, "resets_at": soon}})
    assert bd.usage()["five_hour"]["used_percentage"] == 11
    # the project's settings.json refreshes the line every 60 s: Girsa's configuration test


def test_a_landing_shows_on_its_corner_until_the_next_session_and_stays_in_the_history(tmp_path, monkeypatch):
    """The reviewer, 2026-10-25: a session's landing summary goes on the Board - its corner says Landed, not Not running,
    and shows the summary until the role's next session starts; every landing is kept, newest first under Landings; and
    /land writes bullet points of what was accomplished. Placeholder sessions in a temporary board."""
    import importlib.util
    monkeypatch.setenv("MISHMERET_BOARD_DIR", str(tmp_path / "board"))
    monkeypatch.syspath_prepend(PKG)
    spec = importlib.util.spec_from_file_location("board_server", os.path.join(PKG, "board_server.py"))
    bs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bs)
    bd = bs.board
    with pytest.raises(ValueError):
        bd.landed("ex-builder", "  ")
    bd.landed("ex-builder", "- built X (abc123)\n- open: Y", "s1")
    live = {}
    monkeypatch.setattr(bs.LIVE, "get", lambda: live)
    r = bs.board_view()["roles"]["ex-builder"]
    assert r["shown"] == "landed" and r["landing"]["summary"].startswith("- built X"), "closed: Landed, not Not running"
    live["ex-builder"] = {"status": "idle", "last_prompt": None, "session_id": "s1"}
    assert bs.board_view()["roles"]["ex-builder"]["shown"] == "landed", "the landed session still open"
    live["ex-builder"] = {"status": "busy", "last_prompt": None, "session_id": "s1"}
    assert bs.board_view()["roles"]["ex-builder"]["shown"] == "working", "worked with again"
    live["ex-builder"] = {"status": "idle", "last_prompt": None, "session_id": "s2"}
    r = bs.board_view()["roles"]["ex-builder"]
    assert r["shown"] == "idle" and r["landing"] is None, "the next session: the corner moves on"
    # ...AND STAYS MOVED ON when that session stops without landing (ex-verifier's MEDIUM 2): its own record (the
    # status line's) names the role and was seen after the landing; the landed session's own record does not count
    import time as _time
    bd.record_session("s1", name="ex-builder", seen_at=int(_time.time()) + 5)
    del live["ex-builder"]
    assert bs.board_view()["roles"]["ex-builder"]["shown"] == "landed", "the landed session's own record"
    bd.record_session("s2", name="ex-builder", seen_at=int(_time.time()) + 5)
    r = bs.board_view()["roles"]["ex-builder"]
    assert r["shown"] == "not-running" and r["landing"] is None, "s2 ran and stopped: Not running, not s1's Landed"
    bd.landed("ex-builder", "- second", "s2")
    assert [l["summary"] for l in bs.board_view()["landings"]] == ["- built X (abc123)\n- open: Y", "- second"]
    # posted again for the same session: its last posting only; `at` is when it landed
    # - an ISO time with its offset (the audit's item 3: one without broke every board_view() for good), stored in the
    # local form the other landings have
    for bad in ("2030-01-02T12:30", "yesterday"):
        with pytest.raises(ValueError, match="UTC offset"):
            bd.landed("ex-builder", "- second, fuller", "s2", at=bad)
    bd.landed("ex-builder", "- second, fuller", "s2", at="2030-01-02T10:30:00Z")
    got = bs.board_view()["landings"]
    assert [l["summary"] for l in got][-1] == "- second, fuller" and len(got) == 2
    from datetime import datetime
    assert got[-1]["ts"] == datetime.fromisoformat("2030-01-02T10:30:00+00:00").astimezone().isoformat(), got[-1]["ts"]
    # how long the session ran, and which of its role's sessions that day: from the transcripts (placeholders)
    tx = tmp_path / "tx"
    tx.mkdir()
    monkeypatch.setenv("MISHMERET_TRANSCRIPTS", str(tx))
    for sid, start in (("s0", "2030-01-02T07:00:00+02:00"), ("s2", "2030-01-02T09:00:00+02:00")):
        (tx / f"{sid}.jsonl").write_text(json.dumps({"type": "agent-name", "agentName": "ex-builder"}) + "\n" +
                                         json.dumps({"type": "user", "timestamp": start}) + "\n", encoding="utf-8")
        os.utime(tx / f"{sid}.jsonl", (1893600000, 1893600000))        # written in 2030
    bs.FACTS.clear()
    last = bs.board_view()["landings"][-1]
    assert last["length"] == "3 h 30 min" and last["nth_words"] == "session 2 of the day", last
    page = open(os.path.join(PKG, "board_server.py"), encoding="utf-8").read()
    assert 'id="landtoggle"' in page and "landed-sum" in page and '["landed", "Landed"]' in page
    # the project's /land calls `board.py landed --role`: Girsa's configuration test


def test_the_board_shows_a_role_idle_once_its_turn_ended_and_a_keepalive_refreshes_its_corner(tmp_path, monkeypatch):
    """The reviewer, 2026-10-26: "ui says working in the title bar but idle in the body" - `claude agents` calls a
    session busy while a background task of its own runs (a `board.py wait`, a watcher loop), so the corner said
    Working over a role whose turn had ended. role_usage.turn_ended reads the transcript: the turn's closing record
    with nothing after it is idle; a prompt or an answer after it, or no transcript, is not (Lesson 59). And "keepalive
    is a good opp. for a session to report to the board that it is still idle": `status --still` reports the corner
    again as it stands. Placeholder transcripts and sessions."""
    import importlib.util
    import json as _json
    monkeypatch.setenv("MISHMERET_BOARD_DIR", str(tmp_path / "board"))
    monkeypatch.syspath_prepend(PKG)
    spec = importlib.util.spec_from_file_location("board_server", os.path.join(PKG, "board_server.py"))
    bs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bs)
    sdir = tmp_path / "stx"
    sdir.mkdir()
    monkeypatch.setenv("MISHMERET_TRANSCRIPTS", str(sdir))
    rec = lambda **r: _json.dumps(r)
    ended = [rec(type="user", message={"content": "placeholder"}), rec(type="assistant", message={"stop_reason": "end_turn"}),
             rec(type="system", subtype="stop_hook_summary"), rec(type="system", subtype="turn_duration")]
    cases = {"ended": ended, "ended-then-sidechain": ended + [rec(type="assistant", isSidechain=True)],
             "prompted": ended + [rec(type="user", message={"content": "a new prompt"})],
             "mid-turn": ended[:2] + [rec(type="assistant", message={"stop_reason": "tool_use"})]}
    for name, lines in cases.items():
        (sdir / f"{name}.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    ru = bs.role_usage
    assert ru.turn_ended("ended") and ru.turn_ended("ended-then-sidechain")
    assert not ru.turn_ended("prompted") and not ru.turn_ended("mid-turn") and not ru.turn_ended("no-such-session")
    rows = [{"name": "ex-ui-steward", "status": "busy", "sessionId": "ended"},
            {"name": "ex-builder", "status": "busy", "sessionId": "mid-turn"},
            {"name": "ex-architect", "status": "idle", "sessionId": "ended"}]
    monkeypatch.setattr(bs.board, "live_agents", lambda: rows)
    live = bs.Live._read()
    assert (live["ex-ui-steward"]["status"], live["ex-builder"]["status"], live["ex-architect"]["status"]) \
        == ("idle", "busy", "idle")
    # status --still: the corner again as it stands, its time now; a role that never gave a state is idle
    bd = bs.board
    bd.set_status("ex-builder", now="placeholder", state="waiting-agent", waiting_for="ex-verifier")
    before = bd.statuses()["ex-builder"]
    bd.still("ex-builder")
    after = bd.statuses()["ex-builder"]
    assert (after["now"], after["state"], after["waiting_for"]) == ("placeholder", "waiting-agent", "ex-verifier")
    assert after["ts"] >= before["ts"] and after["state_ts"] >= before["state_ts"]
    bd.still("ex-architect")
    assert bd.statuses()["ex-architect"]["state"] == "idle"
    # "ver says Working - but on nothing": a working role's corner reported before its current prompt is marked so
    corner = {"ts": "2026-10-26T21:21:00+02:00"}
    assert bd.behind_its_work(corner, "busy", "2026-10-26T21:30:00+02:00")
    assert not bd.behind_its_work(corner, "busy", "2026-10-26T21:10:00+02:00")      # reported after the prompt
    assert not bd.behind_its_work(corner, "idle", "2026-10-26T21:30:00+02:00")      # not working: its own report stands
    assert bd.behind_its_work({"ts": None}, "busy", "2026-10-26T21:30:00+02:00")
    assert "before its current work" in open(os.path.join(PKG, "board_server.py"), encoding="utf-8").read()


def test_the_board_flags_a_stalled_role_and_counts_errors_and_a_week(tmp_path, monkeypatch):
    """Q&A #56 ideas 1-3 (the reviewer, 2026-10-25: "build 1 - 4"): a role working with nothing new in its transcript for
    20 minutes, or waiting for another role for an hour, is flagged on its corner; each role's errors per day (a hook
    that failed, an API error, a call the role guard refused, any other failed tool call) are counted; and the last
    seven days' weighted tokens are listed per role. Placeholder transcripts and sessions."""
    import importlib.util
    import time as _time
    from datetime import datetime as _dt
    monkeypatch.setenv("MISHMERET_BOARD_DIR", str(tmp_path / "board"))
    monkeypatch.syspath_prepend(PKG)
    spec = importlib.util.spec_from_file_location("board_server", os.path.join(PKG, "board_server.py"))
    bs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bs)
    sdir = tmp_path / "stx"
    sdir.mkdir()
    tx = sdir / "s1.jsonl"
    tx.write_text("{}\n", encoding="utf-8")
    busy = {"status": "busy", "session_id": "s1", "last_prompt": None}
    with monkeypatch.context() as m:
        m.setenv("MISHMERET_TRANSCRIPTS", str(sdir))         # found where role_usage finds every transcript (LOW 3)
        assert bs.stalled({}, busy, "working", None) is None
        old = _time.time() - 25 * 60
        os.utime(tx, (old, old))
        assert bs.stalled({}, busy, "working", None).startswith("working, but nothing new for 25 min")
        assert bs.stalled({}, {"status": "idle", "session_id": "s1"}, "idle", None) is None
    an_hour_ago = _dt.fromtimestamp(_time.time() - 75 * 60).astimezone().isoformat()
    st = {"state": "waiting-agent", "waiting_for": "ex-verifier", "state_ts": an_hour_ago}
    # THE WAIT ONLY WHERE THE CORNER SHOWS IT (ex-verifier's MEDIUM 1): shown_state and also_waiting decide, so a
    # report the role moved on from, a role not running, landed or working with a newer prompt is not flagged
    idle = {"status": "idle", "session_id": "s1", "last_prompt": None}
    words = "waiting for ex-verifier for 1 h 15 min"
    shown = lambda lv: bs.board.shown_state(st, lv and lv["status"], [], lv and lv["last_prompt"])[0]
    also = lambda lv: bs.board.also_waiting(st, lv and lv["status"], lv and lv["last_prompt"])
    assert bs.stalled(st, idle, shown(idle), also(idle)) == words, "idle, the report standing: Waiting, and flagged"
    prompted = dict(idle, last_prompt=_dt.fromtimestamp(_time.time() - 10 * 60).astimezone().isoformat())
    assert shown(prompted) == "idle" and bs.stalled(st, prompted, shown(prompted), also(prompted)) is None
    assert shown(None) == "not-running" and bs.stalled(st, None, shown(None), also(None)) is None
    assert bs.stalled(st, None, "landed", None) is None
    with monkeypatch.context() as m:
        m.setenv("MISHMERET_TRANSCRIPTS", str(sdir))
        os.utime(tx, None)                               # written just now: not stalled as working
        assert also(busy) and bs.stalled(st, busy, shown(busy), also(busy)) == words, "working, and its wait standing"
        working = dict(busy, last_prompt=prompted["last_prompt"])
        assert bs.stalled(st, working, shown(working), also(working)) is None, "worked with since the report"
    page = open(os.path.join(PKG, "board_server.py"), encoding="utf-8").read()
    assert 'class="stall"' in page and "weekTable()" in page and "errWords(r.errors)" in page
    # errors and the week, from placeholder transcripts
    ru = bs.role_usage
    tdir = tmp_path / "tx"
    tdir.mkdir()
    monkeypatch.setenv("MISHMERET_TRANSCRIPTS", str(tdir))
    ts = _dt(2030, 1, 2, 12, 0).astimezone().isoformat()
    rows = [{"type": "agent-name", "agentName": "ex-builder"},
            {"type": "attachment", "timestamp": ts, "attachment": {"type": "hook_blocking_error"}},
            {"type": "attachment", "timestamp": ts, "attachment": {"type": "hook_success"}},
            {"type": "assistant", "timestamp": ts, "isApiErrorMessage": True, "message": {"id": "e1"}},
            {"type": "user", "timestamp": ts, "message": {"content": [
                {"type": "tool_result", "is_error": True, "content": "refused by the role guard: no"},
                {"type": "tool_result", "is_error": True, "content": "Exit code 1"},
                {"type": "tool_result", "content": "fine"}]}},
            {"type": "assistant", "timestamp": ts, "message": {"id": "m1", "model": "claude-opus-5-5", "usage": {
                "input_tokens": 10, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": 0}}}]
    (tdir / "s9.jsonl").write_text("\n".join(json.dumps(r, separators=(",", ":")) for r in rows) + "\n",
                                   encoding="utf-8")                  # as Claude Code writes them, with no spaces
    os.utime(tdir / "s9.jsonl", (1893700000, 1893700000))
    got = ru.role_usage("2030-01-02")["ex-builder"]
    assert got["errors"] == {"api": 1, "hook": 1, "refused": 1, "tool": 1}
    week = ru.role_week("2030-01-03", n=2)
    assert [d for d, _ in week] == ["2030-01-02", "2030-01-03"] and week[0][1] == {"ex-builder": 10} and week[1][1] == {}


def test_the_reviewer_defers_a_question_and_its_role_is_told_once(tmp_path, monkeypatch, capsys):
    """The reviewer, 2026-10-13: "i need a way to defer questions on the board". Later (the page's /api/defer) moves an
    open question to Deferred: the role's corner no longer waits on the reviewer for it, a wait running when it is
    deferred says so once and returns 3 (the role goes on with other work), a wait started on it afterwards waits for the
    answer, it can still be answered, and Bring back returns it. An answered or withdrawn item is not deferred.
    Placeholder questions in a temporary board, through the page's own route."""
    import importlib.util
    import threading
    import urllib.request
    import urllib.error
    monkeypatch.setenv("MISHMERET_BOARD_DIR", str(tmp_path / "board"))
    monkeypatch.syspath_prepend(PKG)
    spec = importlib.util.spec_from_file_location("board_server", os.path.join(PKG, "board_server.py"))
    bs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bs)
    bd = bs.board
    monkeypatch.setattr(bs.LIVE, "get", lambda: {"ex-builder": {"status": "idle", "last_prompt": None}})
    one = bd.ask("ex-builder", "Placeholder question")
    assert bs.board_view()["roles"]["ex-builder"]["shown"] == "waiting-reviewer"    # the check below can fail
    two = bd.ask("ex-verifier", "Placeholder decision", "", "decision", ["a=Do Y"], "a")
    srv = bs.ThreadingHTTPServer(("127.0.0.1", 0), bs.Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]

    def post(route, body):
        req = urllib.request.Request(f"http://127.0.0.1:{port}{route}", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json", "Origin": f"http://127.0.0.1:{port}"})
        try:
            return urllib.request.urlopen(req, timeout=5).status
        except urllib.error.HTTPError as e:
            return e.code
    try:
        # a wait already running when the reviewer presses Later: told once, exit 3
        monkeypatch.setattr(bd.time, "sleep", lambda s: post("/api/defer", {"id": one["id"], "defer": True}))
        assert bd.main(["wait", str(one["id"])]) == 3
        assert "deferred by the reviewer - go on with other work" in capsys.readouterr().out
        assert bd.items()[one["id"]]["deferred"] and not bd.is_waiting(bd.items()[one["id"]])
        assert "[deferred]" in bd.describe(bd.items()[one["id"]])
        assert bs.board_view()["roles"]["ex-builder"]["shown"] == "idle", "a deferred question still held its corner"
        # a wait started on a deferred item waits for its answer, which the page still takes
        monkeypatch.setattr(bd.time, "sleep", lambda s: post("/api/answer", {"id": one["id"], "answer": "placeholder"}))
        assert bd.main(["wait", str(one["id"])]) == 0
        assert "answered: placeholder" in capsys.readouterr().out
        assert post("/api/defer", {"id": one["id"], "defer": True}) == 409, "an answered item is not deferred"
        # Bring back
        assert post("/api/defer", {"id": two["id"], "defer": True}) == 200 and bd.items()[two["id"]]["deferred"]
        assert post("/api/defer", {"id": two["id"], "defer": False}) == 200 and bd.is_waiting(bd.items()[two["id"]])
        bd.withdraw(two["id"], "no longer needed")
        assert post("/api/defer", {"id": two["id"], "defer": True}) == 409, "a withdrawn item is not deferred"
        assert post("/api/defer", {"id": 99, "defer": True}) == 409
    finally:
        srv.shutdown()
    page = open(os.path.join(PKG, "board_server.py"), encoding="utf-8").read()
    assert "data-defer=" in page and "data-undefer=" in page and "Deferred (${deferred.length})" in page


def test_the_plans_budget_is_recorded_shown_and_told_once_at_80_percent(tmp_path, monkeypatch):
    """Q&A #56 A (the reviewer, 2026-10-25: "a and c - good. go"): every session's status line records the plan's usage
    windows for the Board's meter; at BUDGET_WARN percent (the config's budget.warn_percent) a hook tells each session
    once per window and reset to keep its work landable and keep working - never to land for the budget (the Board's
    #118, A; the Mishmeret audit's item 6: the status line still said LAND). Placeholder readings in a temporary board."""
    import importlib.util
    import subprocess
    import time as _time
    monkeypatch.setenv("MISHMERET_BOARD_DIR", str(tmp_path / "board"))
    monkeypatch.syspath_prepend(PKG)
    spec = importlib.util.spec_from_file_location("board_server", os.path.join(PKG, "board_server.py"))
    bs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bs)
    bd = bs.board
    soon, gone = int(_time.time()) + 3600, int(_time.time()) - 60
    assert bd.record_usage(None) is None and bd.usage() is None
    bd.record_usage({"five_hour": {"used_percentage": 42, "resets_at": soon}, "seven_day": {"used_percentage": 50, "resets_at": gone}})
    assert set(bd.usage()) == {"five_hour", "seen_at", "session"}, "a window whose reset has passed is left out"
    assert bd.budget_notice("s1") is None, "under the line, nothing is said"
    assert bs.board_view()["usage"]["five_hour"]["used_percentage"] == 42
    bd.record_usage({"five_hour": {"used_percentage": 80, "resets_at": soon}})
    said = bd.budget_notice("s1")
    assert said and "5-hour window is at 80%" in said and "never for the budget alone" in said, said
    assert "land early" not in said and "2026-" not in said, "no project's dated words in the code"
    assert bd.budget_notice("s1") is None, "told once per session, window and reset"
    assert bd.budget_notice("s2"), "each session is told"
    bd.record_usage({"five_hour": {"used_percentage": 85, "resets_at": soon + 18000}})
    assert bd.budget_notice("s1"), "a new window is told again"
    hook = PKG
    env = dict(os.environ, MISHMERET_BOARD_DIR=str(tmp_path / "board"))
    out = subprocess.run([sys.executable, os.path.join(hook, "statusline.py")], env=env, capture_output=True, text=True,
                         input=json.dumps({"session_name": "ex-builder", "context_window": {"current_usage": {
                             "input_tokens": 5, "cache_read_input_tokens": 120000}},
                             "rate_limits": {"five_hour": {"used_percentage": 90, "resets_at": soon}}})).stdout
    assert out.startswith("context 120k · plan: 5-HOUR 90% (RESETS ") and "LAND" not in out, out
    # the threshold is the project's: at 95, 90% is written as any other reading
    from conftest import write_project
    env95 = dict(env, MISHMERET_CONFIG=write_project(tmp_path / "p95", budget={"warn_percent": 95}))
    out = subprocess.run([sys.executable, os.path.join(hook, "statusline.py")], env=env95, capture_output=True,
                         text=True, input=json.dumps({"rate_limits": {"five_hour": {"used_percentage": 90,
                                                                                   "resets_at": soon}}})).stdout
    assert "plan: 5-hour 90% (resets " in out, out
    assert bd.usage()["five_hour"]["used_percentage"] == 90 and bd.usage()["session"] == "ex-builder"
    def run_hook(**data):
        return subprocess.run([sys.executable, os.path.join(hook, "board_hook.py")], env=env, capture_output=True,
                              text=True, input=json.dumps(data)).stdout
    got = run_hook(session_id="s3", hook_event_name="UserPromptSubmit")
    assert json.loads(got)["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    assert bd.session_record("ex-builder") == {}, "the status line keys its record by session id, not name"
    # the project's settings.json runs statusline.py and board_hook.py on its three events: Girsa's configuration test
    page = open(os.path.join(PKG, "board_server.py"), encoding="utf-8").read()
    assert 'id="usage"' in page and "drawUsage()" in page


def test_tokens_per_role_per_day_from_the_transcripts(tmp_path, monkeypatch):
    """Q&A #56 ideas 3 and 4: a transcript's role is its agent-name record; a call counts once by message id on its local
    date; a compaction is a compact_boundary record; subagents are kept by model; weighted = input 1, cache write 2,
    cache read 0.1, output 5. Placeholder transcripts."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("role_usage", os.path.join(PKG, "role_usage.py"))
    ru = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ru)
    monkeypatch.setenv("MISHMERET_TRANSCRIPTS", str(tmp_path))
    from datetime import datetime as _dt
    ts = _dt(2030, 1, 2, 12, 0).astimezone().isoformat()
    other = _dt(2030, 1, 3, 12, 0).astimezone().isoformat()
    call = lambda mid, t, model="claude-opus-5-5": {"type": "assistant", "timestamp": t, "message": {
        "id": mid, "model": model, "usage": {"input_tokens": 10, "cache_creation_input_tokens": 100,
                                             "cache_read_input_tokens": 1000, "output_tokens": 20}}}
    rows = [{"type": "agent-name", "agentName": "ex-builder"}, call("m1", ts), call("m1", ts), call("m2", other),
            {"type": "system", "subtype": "compact_boundary", "timestamp": ts}]
    (tmp_path / "s1.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    (tmp_path / "s1" / "subagents").mkdir(parents=True)
    (tmp_path / "s1" / "subagents" / "a.jsonl").write_text(json.dumps(call("h1", ts, "claude-haiku-5-5")) + "\n", encoding="utf-8")
    later = _dt(2030, 1, 4).timestamp()    # a file last written before the day holds none of it, and is skipped
    for f in (tmp_path / "s1.jsonl", tmp_path / "s1" / "subagents" / "a.jsonl"):
        os.utime(f, (later, later))
    assert ru.role_usage("2030-01-05") == {}
    got = ru.role_usage("2030-01-02")["ex-builder"]
    assert got["main"] == {"calls": 1, "inp": 10, "cw": 100, "cr": 1000, "out": 20, "weighted": 410}
    assert got["compactions"] == 1 and got["sessions"] == 1
    assert got["sub"] == {"claude-haiku-5-5": {"calls": 1, "inp": 10, "cw": 100, "cr": 1000, "out": 20, "weighted": 410}}
    assert ru.role_usage("2030-01-03")["ex-builder"]["main"]["calls"] == 1


def test_a_sessions_number_that_day_counts_its_own_roles_sessions_of_its_own_day(tmp_path, monkeypatch):
    """session_facts' two filters (ex-verifier, 2026-10-26, LOW 6: mutating either passed the whole file): which of
    its role's sessions begun that day a session was counts only that role's, only that local day's. Placeholder
    transcripts: builders at 08:00, 13:00 and 23:30 (written past midnight) one day and 00:10 the next, an architect at 09:00; and a role named
    after line 400 (a session resumed into it, LOW 5) is still that role."""
    import importlib.util
    from datetime import datetime as _dt
    spec = importlib.util.spec_from_file_location("role_usage", os.path.join(PKG, "role_usage.py"))
    ru = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ru)
    monkeypatch.setenv("MISHMERET_TRANSCRIPTS", str(tmp_path))
    def session(sid, role, when, late=False, ran=600):
        start = _dt(*when).astimezone()
        head = [json.dumps({"type": "user", "timestamp": start.isoformat()})]
        name = [json.dumps({"type": "agent-name", "agentName": role})]
        filler = [json.dumps({"type": "progress"})] * (450 if late else 0)
        (tmp_path / f"{sid}.jsonl").write_text("\n".join(head + filler + name if late else name + head) + "\n",
                                               encoding="utf-8")
        os.utime(tmp_path / f"{sid}.jsonl", (start.timestamp() + ran, start.timestamp() + ran))
    session("b1", "ex-builder", (2030, 1, 2, 8, 0))
    session("b2", "ex-builder", (2030, 1, 2, 13, 0), late=True)
    session("b3", "ex-builder", (2030, 1, 2, 23, 30), ran=90 * 60)       # still written after midnight
    session("b4", "ex-builder", (2030, 1, 3, 0, 10))
    session("a1", "ex-architect", (2030, 1, 2, 9, 0))
    got = {sid: ru.session_facts(sid)["nth_today"] for sid in ("b1", "b2", "b3", "b4", "a1")}
    assert got == {"b1": 1, "b2": 2, "b3": 3, "b4": 1, "a1": 1}
    assert ru.session_facts("nobody") == {}
