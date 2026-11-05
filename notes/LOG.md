# Mishmeret's builder - the log

Findings, decisions and open work, each the moment it is known; a time from `date`. One item per run of work, newest
first (`M01.`, `M02.` ...); what git records (what each commit did) is not repeated here.

M03. **[2026-11-05, copy-on-select (notes/PLAN-COPY-SELECT.md)]**
    * **[15:55]** The drill-down VERIFIED (girsa-verifier, one LOW at the page's next touch) and merged by girsa-operator
      (main 59178bf, not pushed). Sent, live: the merge's REQUEST to girsa-operator. The LOW pinned first, 9c9fa8b.
    * FOUND, in the prototype's measure: Chromium's `getSelection()` holds a textarea's selected text, so without the
      box's rule a draft's word overwrote the clipboard (red). The sign shows when the write resolves, after the
      mouse-up: a test reading it at once reads the one before - the test waits for it.
    * To send at this commit, live: the look's QUESTION to girsa-ui-steward (three, with pictures); the plan's HANDOFF
      to girsa-verifier.

M02. **[2026-11-05, the Board's open-messages drill-down (notes/PLAN-OPEN-MESSAGES.md)]**
    * **[15:38]** The first session as mishmeret-builder, started in `~/work/mishmeret`. Received, live: girsa-operator's
      NOTE that the Board on 8451 runs (Girsa's Board #160 A) and the next work is the two Board asks. The reviewer's
      words for both are in Girsa's PROJECT-STATUS-OPEN.md (13:44, 14:03), its operator's first message to this role
      item 2 and 3.
    * FOUND, in the prototype's measure: a `<button>` drops the page's `font-feature-settings` (tabular figures; the
      pill 0.33 px narrower) - inherited now, the pill the span's size to the 1/64 px. A placeholder path with hyphens
      did not show the sideways scroll (the browser breaks at a hyphen): the test's path has none.
    * To send at this commit, live: the look's QUESTION to girsa-ui-steward (the plan's four, with pictures); the plan's
      HANDOFF to girsa-verifier.
    * **[15:42]** girsa-ui-steward's ANSWER, live: build as prototyped - the questions' place (one pattern; the page
      measured exactly the window's height on 8450, the title in view below every pill), the pointer cursor only, the
      card and the empty words as they are; 2a a `:focus-visible` outline (1px currentColor, 2px off), 2b `aria-pressed`
      on the open role's pill. Built, with two of mine that follow: the pill a toggle (pressed again, the list closes),
      and the focus given back to the new pill after the redraw (it fell to the body on Enter). Each shown red with its
      rule out (focus: none; outline: the browser's blue ring). Suite 106 passed. Sent, live: a NOTE to it of the two.
      NOT CHANGED: the 5 s refresh redraws the corners, so a pill focused then loses it - true of the corners today.
    * **[15:45]** girsa-verifier, live: the plan ACCEPTED (its REVIEW.md in Girsa, at 9a1c80fb); its 2 failed were
      its copy taken mid-red-check (the outline rule out). Its note, the look and the behaviour in two commits: the
      three CSS rules alone in 4e1ac02 (they match nothing until the pill is a button; main's whole suite at it, in a
      scratch clone: 104 passed), the behaviour in the next. girsa-ui-steward, live: the toggle and the focus kept
      stand, the 5 s redraw's focus loss left alone (page-wide). The closed page re-measured on the final code: as
      main's. Not taken (its note 2): one view variable for the seven flags - not this piece's.

M01. **[2026-11-05, Mishmeret's own .claude/ (Board #156 B, #153 B; notes/PLAN-OWN-CLAUDE.md)]**
    * **[14:48]** Started as a session of the first project's builder role, in that project's main clone; took that
      role's own next item by mistake and committed it in that role's worktree (952cf591, there), then stopped and handed
      it back. Since then, only Mishmeret's trees. Messages sent, live: the handover of 952cf591 and a QUESTION to
      girsa-builder; the plan's QUESTION to girsa-architect and HANDOFF to girsa-verifier; an ANSWER to girsa-operator
      (its REQUEST: the Board's open-messages drill-down, then copy-on-select - after this piece); a NOTE to
      girsa-builder (its pin bump: `guard.foreign` optional at a5faac2, not yet checked).
    * FOUND, in planning (each in the plan, answered): started from its worktree, a builder reads that worktree's
      `.claude/`, which it may edit - so it starts in the main clone; under its own config the guard refuses a plain
      `git commit` (THROUGH_LAND), so `land.py commit` and a lane check are needed; six config fields only one
      project could fill were required (now optional, A2).
    * A VERIFIED (girsa-verifier), merged to main 96d073d. Its LOW 1 and the recommendation (foreign optional): a5faac2.
    * **[15:04]** A2 and B VERIFIED at 37f9e61 (girsa-verifier: 104 passed, the guard end to end 12 of 12, Girsa's
      config unchanged loads under a5faac2 - its bump is the pin alone). Its LOW 1, the lane check let the login pass
      folded into one word (`-Users-<login>-work-...`): the bare login added, on word boundaries; red without it. Sent:
      the HANDOFF of A2 and B; this round back to it. NOT RUN by anyone: `land.py commit mishmeret-builder` through the
      shim (another role's session may not name this role) - the builder's first commit is its first run.
