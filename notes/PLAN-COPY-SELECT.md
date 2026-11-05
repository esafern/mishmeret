# Copy-on-select on the Board: the plan (mishmeret-builder, 2026-11-05)

Written 15:55, revised 15:59 (`date`) with girsa-ui-steward's answer. On girsa-operator's REQUEST (its first message
to this role, item 3). The look is girsa-ui-steward's (its answer: beside the pointer, the look as prototyped, the
refused copy's words "Not copied" alone - Mishmeret is not the Mac's alone); the plan goes to girsa-verifier for one
review.

## The case

- The reviewer, 2026-11-05 14:03: "girsa board should auto-copy highlighted text inthe c-b [clipboard]". Today a
  selection on the Board needs Cmd-C; the reviewer copies from the page into the roles' panes.
- The ask: selected text is on the clipboard with no keystroke.

## The behaviour

- On the mouse button coming up (the left one) with text selected, the selection's text is written to the clipboard
  (`navigator.clipboard.writeText`: plain text, what a pane takes; the page is on 127.0.0.1 or localhost only, both
  secure contexts, so the API is there). A double- or triple-click's word or line is a selection too.
- NOT copied: a selection in an answer's box (a textarea, or the token table's date field), or a mouse-up on a button
  or a link - selecting a draft to replace it would overwrite what the reviewer brought to paste; a click on an
  answer's option would copy again what is still selected.
- The sign: "Copied" beside the pointer, for 1.2 s, kept inside the window; when the browser refuses the write,
  "Not copied" there instead, so a refused copy never reads as done.
- No guard for a page without `navigator.clipboard` (girsa-ui-steward's reading: an insecure context throws before
  the refusal path): the page is never served to one. Measured on the live Board (8451): Host 127.0.0.1 and localhost
  200, the machine's name and a LAN address as Host 403 (`ALLOWED_HOSTS`), and the LAN address itself no connection
  (bound to 127.0.0.1). Both served hosts are secure contexts. A one-line comment at the call says so.
- Not done: a selection made with the keyboard (copying it is a keystroke anyway); rich text.
- And girsa-verifier's LOW 1 on 59178bf, at the page's next touch (this one): a `#qa-N` link with the list open,
  pinned in the drill-down's test - 9c9fa8b, red at both sizes without `goToQA`'s `showMsgs =`.

## The measure (the prototype, uncommitted in `~/work/mishmeret-builder`, 15:54)

- Headless Chromium, its clipboard granted, at 1229x673 and 1864x1033: a double-click on a question's first word puts
  exactly that word on the clipboard ("Placeholder"); the sign is 47 x 17 px, muted (rgb 107,112,117), at the pointer.
  A word at a line's right end: the sign at x 1178 of 1229 and 1813 of 1864 - inside the window.
- The header, the steward's other place: 0 px free at 1229 with "Main held" and "Nothing is moving" showing (both
  wrap to two lines already), 160 px at 1864.
- The new browser test: the selection copied, the sign shown then gone, a selection in an answer's box leaving the
  clipboard as it was - red without that rule (Chromium's `getSelection()` holds a textarea's selected text) - and a
  refused write saying "Not copied" - red with the refusal path empty. Suite 107 passed.
- NOT MEASURED: Safari and Firefox (no browser here but Chromium). Each lets a page write the clipboard inside a
  user's gesture, which a mouse-up is in Chromium; if one refuses, the sign says "Not copied".

## The look, answered by girsa-ui-steward

1. Beside the pointer, as prototyped (the header has no room at 1229; the sign where the eye is).
2. As prototyped: 11.5 px muted, the page's background behind it (a small grey patch on a white card: acceptable),
   no border, 1.2 s. It covers what is just above the pointer for that time - any spot there would.
3. "Not copied" alone (the reviewer's to change).

## Files

- `mishmeret/board_server.py`: the sign's CSS rule and element (the look, a commit of its own); the mouse-up handler
  (the behaviour).
- `tests/test_board.py`: the browser test above.
- `notes/`: this plan, the state file, the log.

## After

girsa-verifier checks at the piece's final commit; girsa-operator merges main; Girsa's pin bump is girsa-builder's,
the Board's restart girsa-operator's.
