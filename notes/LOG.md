# Mishmeret's builder - the log

Findings, decisions and open work, each the moment it is known; a time from `date`. One item per run of work, newest
first (`M01.`, `M02.` ...); what git records (what each commit did) is not repeated here.

M04. **[2026-11-05, the start scripts with no project named (notes/PLAN-START-SCRIPTS.md)]**
    * **[16:34]** 31ac716 VERIFIED (girsa-verifier: P1-P8 as meant, three mutations red) and merged (main 31ac716).
      girsa-operator's REQUEST, live: the two start-script defects of the first project's 2026-11-05 (10:40, 11:22).
    * FOUND, in planning: since piece B the 10:40 run no longer refuses - Mishmeret's own config is read, and the run
      goes on silently on a project with no tmux role; the night run's Go types the config into a new window without
      the shim's mark, so the leak of 11:22 comes back on every Go, through the shim. The role guard refused my first
      reproduction (agents.sh holds `tmux kill-session`; a stub on PATH is not seen): rerun with `env -u TMUX
      TMUX_TMPDIR=<own folder>`, BSD env taking each `-u` before any assignment.
    * To send at this commit, live: the design question to girsa-architect; the plan's HANDOFF to girsa-verifier.
    * **[16:40]** girsa-architect's ANSWER, live (its record Girsa 45416b48): R; and every role launched with the
      config dropped. Its correction, girsa-verifier's too: the "marking ... or a clear message" sentence is
      girsa-operator's, in #157's body - the reviewer answered B, no note; MY SLIP, the plan quoted it as the
      reviewer's from the operator's REQUEST without reading the Board. girsa-verifier, live: ACCEPTED with the
      addition. Built: `start_role`'s two launches; the test of a fresh start, red on today's line. Suite 110 passed.
    * **[16:46]** 8738b21 VERIFIED (girsa-verifier: no findings; stop_out, go_unmarked, clean_fresh, clean_resume each
      red over the suite; the night job's plist read again, unchanged) and merged (main 8738b21, not pushed). Sent,
      live: the merge's REQUEST. girsa-operator: no more Mishmeret work agreed or queued. The session ends here.

M03. **[2026-11-05, copy-on-select (notes/PLAN-COPY-SELECT.md)]**
    * **[15:55]** The drill-down VERIFIED (girsa-verifier, one LOW at the page's next touch) and merged by girsa-operator
      (main 59178bf, not pushed). Sent, live: the merge's REQUEST to girsa-operator. The LOW pinned first, 9c9fa8b.
    * FOUND, in the prototype's measure: Chromium's `getSelection()` holds a textarea's selected text, so without the
      box's rule a draft's word overwrote the clipboard (red). The sign shows when the write resolves, after the
      mouse-up: a test reading it at once reads the one before - the test waits for it.
    * To send at this commit, live: the look's QUESTION to girsa-ui-steward (three, with pictures); the plan's HANDOFF
      to girsa-verifier.
    * **[15:59]** girsa-verifier, live: received at its session's landing, not started - in its state's Next for its
      next session. girsa-ui-steward's ANSWER, live: beside the pointer, the look as prototyped, "Not copied" alone;
      and a bug read from the diff (no `navigator.clipboard` off a secure context). NOT TAKEN, the guard: measured on
      the live Board, the page is served to 127.0.0.1 and localhost alone (others 403, the LAN address no connection)
      - both secure contexts; a comment at the call says so. The words changed; a refused write now tested (red with
      its path empty). Suite 107 passed. Sent, live: the guard's answer to girsa-ui-steward; a NOTE of the revised
      plan to girsa-verifier.
    * **[16:10]** girsa-verifier (its next session), live: the plan ACCEPTED, LOW 1 to fix in the build - P3, one click
      inside a word still highlighted copied it again over what a pane had copied since. FOUND: its idea (a
      selectionchange between the press's two ends) fails a quick double-click - the event comes after its mouseup,
      every run red. Built instead: the selection read at each end of the press, copied only when it moved; P3 in the
      test, red without it; 5 runs of 5 green. Its probe (P1-P3, copied to scratch) on the build: P1 copied, P2
      nothing, P3 nothing. The look alone in 24d0246 (its suite at it, a scratch clone: 106 passed); the behaviour next.
    * **[16:24]** VERIFIED at 8f6771d (girsa-verifier), merged by girsa-operator (main 8f6771d, not pushed; Board 8451
      restarted at it). Sent, live: the merge's REQUEST. Its LOW 1, the answer's box and the right button unpinned -
      MY SLIP: I showed the box rule red before the press check existed, and did not run it again after; the press
      check then returned first on the test's gesture (`fill()` leaves the selection on the box, so a drag in it moves
      nothing). The round, branch `builder-copy-pins` from 8f6771d: the drag in the box starts with a word held (its
      P6b), a right click (P5) - each red with its rule out (both box rules together; each alone is covered by the
      other). And `button, a` dropped from the target rule: measured, a drag across a question ending over its link
      selected the text and copied nothing; the click on an option it was for is the press check's (P7). The link
      drag is in the test, red with the rule back. Its probes P1-P7 on the round: as meant. Suite 107 passed.

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
