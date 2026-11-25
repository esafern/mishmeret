# Plan: the Board's tab icon

## The case

The reviewer, in the first project: "girsa and mishmeret need favicons" - its Board #249, answered "B - Hebrew initial,
white on a color tile". girsa-ui-steward made both icons and landed Girsa's (gimel on the review page's accent blue,
the first project's 484284feb, b6fa30c85); Mishmeret's it kept as a REQUEST to mishmeret-builder, never delivered
(its state: "owed to mishmeret-builder when it next runs"). The reviewer, 2026-11-25, in this pane: "add the
favicon". Today the Board's page and its mock-up window have no icon: the browser draws its blank one.

The icon is girsa-ui-steward's, as made: 128 x 128 PNG, mem in white (Frank Ruhl Libre 800) on slate #334155, its
corners at 20% of the side, transparent outside; 3,715 bytes, image data only (no text chunk).

## The change

`mishmeret/favicon.png`, read once at the server's start; `/favicon.png` served as `image/png`; `<link rel="icon">` in
both pages board_server.py writes. No content-security header stands in the way. Every project's Board shows it: the
Board is Mishmeret's.

## Files

- mishmeret/favicon.png (new), mishmeret/board_server.py
- tests/test_board.py
- notes/PLAN-FAVICON.md, notes/LOG.md

## Tests

Both pages carry the link; the route answers 200, `image/png`, the file's own bytes. Each of the three red with it
taken out (mutate.py). Not seen in a browser's tab here: the live Board runs its project's pin, so the icon shows
after the merge, the pin's move and the server's restart.
