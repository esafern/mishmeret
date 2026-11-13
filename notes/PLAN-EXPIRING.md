# Plan: what expires, on a calendar feed the Board serves

## The case

girsa-demo-operator's REQUEST, 2026-11-12, passing on the reviewer's words: "mishmeret should keep track of tokens,
secrets and other things that expire - and set calendar alerts so the user can take timely action"; then, on the
reviewer's word, that it holds a hosting key whose alert must follow each renewal. Mishmeret is general: the items
are the project's config, never the first project's names in code. The reviewer, 2026-11-13, in my pane: the alerts
on "a calendar feed the Board serves" (subscribed once in macOS Calendar), "7 days and 1 day" ahead.

The first project's items, each measured at its source today (scratch scripts, read only; no secret printed):
1. The hosting MCP token (mcpServers "spaceship-shared-hosting-server59" in ~/.claude.json, the first project's
   entry): one JWT, at `headers.Authorization`; its `exp` 2026-11-17T13:49:16Z, as girsa-demo-operator said. Lasts 14
   days and lapses silently; every host action stops with it.
2. The Claude login of the Board's stats fetch: 2026-12-07 - a date by hand, second-hand (girsa-demo-operator's state
   file, quoting girsa-operator); no machine source read.
3. and 4. The TLS certificates of app.girsa.net and girsa.net: `notAfter` 2027-01-15 19:18:21Z and 15:28:34Z (Python's
   ssl, a verified connection to :443). Renewed by the host; watched, not acted on.
5. The girsa.net domain: its expiry is not known.

Prototype (`ics_proto.py`, scratch): the five items from those sources make a feed of 13 events - each dated item its
expiry and its two reminders, the domain one "Expiry not known" event on today - 4,487 bytes, CRLF only, no line over
75 octets, every UID unique, no part of the token in it (`eyJ`: 0). Found by it: a date given by hand printed as
"00:00 UTC", and the reminders dated in UTC where the reviewer's day is local (Asia/Jerusalem) - both fixed in the
build. Not measured: macOS Calendar subscribing to `http://127.0.0.1:<board_port>/expiring.ics` - the reviewer's own
step (below).

## The change

1. `mishmeret/expiring.py`, the one reader of the config's `expiring` (OPTIONAL: absent, nothing is tracked): a list of
   items `{"name", "who", "how", "source"}`, the source one of `SOURCES` (a list in code, one test over all of it):
   - `{"date": "YYYY-MM-DD"}` or `{"date": "YYYY-MM-DDTHH:MM:SS+00:00"}` - known by hand; `{"date": null}` - not known;
   - `{"jwt": [FILE, KEY, ...]}` - the `exp` of the one JWT in that JSON file under those keys (`{root}`: the project's
     root); zero or several there is "not known", never a guess. The token is read, decoded and dropped: never
     printed, kept or put in the feed;
   - `{"tls": HOST}` - the certificate's `notAfter` on HOST:443, with a 5-second connect timeout (girsa-architect: this
     Mac is sometimes offline - the certificates then read "not known" and the poll stays quick).
   Read at each ask, so a renewal moves the date. A source that cannot be read is "not known", with why. TWO ITEMS
   WITH ONE NAME ARE REFUSED (girsa-architect, the first project's design-study/MISHMERET-EXPIRING-ARCHITECT.md,
   2fb0a626): their events' UIDs would be one, and Calendar would keep one - the loader's rule for `roles`.
2. The feed: for a dated item, an event at its expiry ("EXPIRES: NAME") and an all-day reminder 7 days and 1 day
   before it, on the local calendar day - the machine's own zone (`astimezone()`), no zone named in the code - each
   with an alarm at 09:00 (a subscription may drop alarms; the reminder events show either way); for an item not
   known, one all-day event on today, "Expiry not known: NAME (why)", so the gap is in sight and not read as nothing
   due; and AN ITEM PAST ITS DATE, one all-day event on today, "EXPIRED: NAME (since DATE)" (girsa-verifier's MEDIUM 2,
   the first project's review c87fee8f: the 10-31 lapse went "unnoticed for three days", handover/web/README.md:118).
   Each description says who acts and how. UIDs fixed per item and kind, so a moved date moves its events. A why
   never holds the token's text (a malformed JWT, another string at the keys, two JWTs); a certificate that fails
   verification - an expired one does - says so (ssl's `verify_message`).
3. `board_server.py` serves it at `/expiring.ics` (text/calendar), behind the same Host check as every route, read
   fresh at each request (Calendar polls it).
4. `python3 expiring.py` lists each item, its date and days left, or why it is not known.
5. config.py: `expiring` in FIELDS and OPTIONAL. The README: one line under the Board.

## Files

- mishmeret/expiring.py (new), mishmeret/board_server.py, mishmeret/config.py, README.md
- tests/test_expiring.py (new)
- notes/PLAN-EXPIRING.md, notes/LOG.md, notes/STATE-mishmeret-builder.md

## Tests (each rule's test shown red with the rule taken out)

1. Over every source of SOURCES, placeholders only: a date, a date-time, a null; a JSON file holding one placeholder
   JWT (exp fixed) under the keys, `{root}` among them; none there and two there, "not known"; a missing file, "not
   known"; `tls` with the connection replaced (no network), and failing.
2. The feed: a dated item's three events and their days, under a TZ where the UTC day and the local day differ at the
   item's hour; an unknown item's one event on today; a past item's "EXPIRED" on today; CRLF, folded lines, unique
   UIDs; the placeholder token's text nowhere in the feed, the listing or any why (a malformed JWT, a plain string,
   two JWTs); an expired certificate's why naming the verification's failure.
   Mutations (girsa-verifier's list, each run alone): the first of two JWTs taken; `{root}` unexpanded; the reminder's
   day in UTC; the EXPIRED branch removed; the timeout removed (a stub that blocks); the token's text in a why; the
   repeated-name refusal removed.
3. The route: 200 and text/calendar; 403 for another Host.
4. The config: absent, nothing tracked and the feed has no event; an item without its keys, an unknown source, or a
   name given twice, refused by name; the `tls` read's timeout passed to the connection.

## For the first project (its config, at its pin bump - girsa-builder's and girsa-operator's)

THE PIN BUMP FIRST, WITH NO ROWS; THE ROWS IN A LATER COMMIT, once every one of its trees pins a commit with this
piece (girsa-verifier's MEDIUM 1: every tree there pins 8818221 or older, whose config.py refuses a key it does not
know - a row landing with the bump meets old code in each tree that lands after it; 2026-11-02: refused, the hold not
released). Or the older-worktree landing run on the bump's patch first
(step5-verification/mishmeret-audit-round-2026-11-02/older_worktree_landing.sh there); girsa-verifier checks it.

The five items above as config rows (girsa-architect: the token's keys run to its server's `headers`,
`Authorization`; nothing there reads these dates ahead; the token's `how` should carry the stats fetch's own words,
`.claude/board/fetch_traffic.py:159`, "renew it in Spaceship's Hosting Manager, Manage, Access"; a run with no
`MISHMERET_CONFIG` or `CLAUDE_PROJECT_DIR` from a worktree finds no token there and says "not known"); then the
reviewer subscribes once: Calendar, File, New Calendar Subscription,
`http://127.0.0.1:8450/expiring.ics`, Location "On My Mac" (iCloud cannot reach 127.0.0.1), refresh every hour, and
"Remove: Alerts" unticked to keep the alarms. Only on that Mac: the phone sees none of it.

## Not in this piece

The Board page showing what is due (a look: girsa-ui-steward's); a notification by the night run or a hook; the
domain's date (the reviewer's or the demo operator's to find); the login's date read from a machine source.
