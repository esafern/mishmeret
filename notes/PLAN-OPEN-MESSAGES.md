# The Board's open-messages drill-down: the plan (mishmeret-builder, 2026-11-05)

Written 15:38 (`date`). On girsa-operator's REQUEST (its first message to this role, item 2). The look is
girsa-ui-steward's, asked with this plan; the plan goes to girsa-verifier for one review.

## The case

- The reviewer, 2026-11-05 13:44: "nothing on my board. agent boards show open mess [messages] w/o [without]
  drill-down". A corner's "N open messages" pill (Board #150 B), and the cornerless line's (message #14), show a
  count; the texts are only in the pill's hover title - one tooltip, not selectable, not scrollable. `board.py inbox
  --role R` prints them; the page does not.
- The ask: from the count, each open message - its number, sender, time and text.

## The behaviour

- The pill becomes a `<button>` (Tab, then Enter, reaches it too). A click lists that role's open messages in the
  questions' place, as Landings, Tokens and Visitors do: the title "Open messages to ROLE (N)", Back returns.
- Each message a card in the Q&A card's look: its sender (the sender's colour on the card's top edge), "message #N",
  its time, then the text - line breaks kept, links live, a long path broken anywhere (without that rule the list
  scrolled sideways: 2076 px of text in a 1201 px list, measured).
- Oldest first, as `inbox`. Redrawn with the page every 5 s: a message marked done leaves the list; with none left,
  "No message to ROLE is open."
- The hover title stays as it is.
- No server, record or config change: `board_view` already gives every role's `unacted`, corner or not. So there is
  no design question for girsa-architect.
- Not done: marking a message done from the page (its receiver alone marks it, `board.done`); one list of every
  role's messages; a link to the list.

## The measure (the prototype, uncommitted in `~/work/mishmeret-builder`, 15:37)

- The closed page is unchanged, at 1229x673 and 1864x1033: the pill 113.28 x 19.25 px as a span (main) and as the
  button, the corner's head 19.5 px, the cornerless line 25.5 px. The button needed `font-feature-settings:inherit`
  (without it, it lost the page's tabular figures and was 0.33 px narrower).
- The list's cards: 1201 px wide at 1229, 1836 at 1864; 59 px for a one-line text, 78 for two.
- The new browser test passes at both sizes, and is red at both without the long-path rule.

## The look, asked of girsa-ui-steward

1. Where the list goes: the questions' place (the prototype), or open under the pill.
2. The pill as a button: whether hover shows more than the pointer cursor, and whether the pill shows that its list
   is open.
3. The card: the Q&A card's look, sender first, then the number and the time.
4. The empty list's words.

## Files

- `mishmeret/board_server.py`: two CSS rules (the button's reset, the long-path break); `openPill` a button naming
  its role; `msgCard`; the list's branch in `draw()`; the click handlers and `goToQA` closing it.
- `tests/test_board.py`: the source assert names `</button>`; a browser test at both sizes - the list from the corner's
  pill by Enter and from the cornerless line's by a click, each text whole and escaped, oldest first, no sideways
  scroll, Back, and a message marked done leaving.
- `notes/`: this plan, the state file, the log.

## After

girsa-verifier checks at the piece's final commit; girsa-operator merges main; Girsa's pin bump is girsa-builder's, and
the Board's restart girsa-operator's. Next: copy-on-select.
