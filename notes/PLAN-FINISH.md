# Finishing a session, by day and by night: the plan (mishmeret-builder, 2026-11-10)

Written 10:57 (`date`). On girsa-operator's ANSWER of 2026-11-10: the first project's Board #183, answered A (all
three) by the reviewer with the note "A but finish instead of close. go". Not yet reviewed; two questions open (below).

## The case

The reviewer, 2026-11-10 (Board #183): "confusion btw [between] landing a change and a session"; "during the day I
want to clear a session after landing, then exit and start a new one. in the even [evening] after I'm idle I want the
night run to exit and not restart".

- "Land" names two things: a change reaching main (`land.py`, LANDED) and a session ending (`/land`, the corner's
  "Landed 09:56", `board.py landed`).
- By day a session that has ended itself stays in its pane until someone types `/clear`, `/exit` and its start. Only
  the night run reads the closing sentence.
- By night, after closing the roles, the run updates Claude Code and holds an alert whose "Go" starts them again.

## The behaviour

Three parts, built and committed in this order; one check by girsa-verifier at the last commit.

### 1. The word: a session FINISHES; a change lands

Every word a person reads or types changes:

- `night.finish_command` (config, new, required): what the night run and the morning run type - the first project's
  is `/finish`. No command's name is written in a script. `night.landed_quiet` becomes `night.finished_quiet`.
- `agents-morning.sh`: types that command; its questions, log lines, notifications and comments say "finish" where
  they mean a session's end. ASK_READY names the command. A comment's quoted words of the reviewer stay as said.
- `board.py finished` (the arguments of `landed`); `landed` stays accepted, the same function, until the first
  project's command file calls the new one. The corner's word is "Finished 09:56"; the page's legend and its list of
  them follow (the words asked of girsa-ui-steward first).
- README, the docstrings and the comments.

Not renamed, and why: the record's `"type": "landed"` (append-only - the old rows are read as they are, one reader);
the Python, JavaScript and CSS names behind the page (`landings`, `--st-landed`); the night marks' file names
(`.land-sent`, `.land-only`, `.landed-kept`), which no person reads and `keepalive_due.py` shares.

### 2. By night: the run ends when the roles are closed

- After its last look: the count line, `claude update` when a role was closed, then exit. The alert, its "Go", the
  iTerm2 window and its `agents.sh` go. The log's last line names the hand step: `bash agents.sh` starts the closed
  roles, each in its pane, when the reviewer is back (it does now).
- KEPT: `claude update` - it starts nothing, and the morning's sessions start on it. Named here so it can be refused.
- `--install-night` still removes the 06:00 reminder (that reminder names the morning run, not `agents.sh`); its
  sentence no longer names a Go.

### 3. By day: a finished session is cleared, exited and started again in its pane

- `finish_hook.py`, a Stop hook (the project's `settings.json` names it): when the turn's last message ends with the
  closing sentence on a line of its own - `said_ready`'s rule: the last non-blank line, emphasis stripped, is exactly
  `The session is ready to clear.` - and the session is one of the config's roles (`CLAUDE_CODE_AGENT`) in a tmux
  pane (`TMUX_PANE`), it starts `agents.sh --next ROLE PANE` detached and returns. Silent otherwise; never blocks.
- `agents.sh --next ROLE PANE`: only when the pane's own `@role` is ROLE (so nothing is typed into another's pane, or
  one `agents.sh` did not start): `/clear`, `night.gap` seconds, `/exit`; waits, 60 s at most, until the pane is back
  at its shell; then the role's fresh start, `start_role`'s own line. Still not at its shell: a notification, nothing
  typed.
- A finish with a step undone is not cleared: its last line is what is left, not the sentence. The command file that
  says so is the project's.
- THE NIGHT RUN GOING, THE HOOK IS SILENT (question 1): the run reads the sentence itself, clears and exits, and
  starts nothing (the reviewer, 2026-10-27: "no to restarting roles at night - they will then start working w/o
  superv. [without supervision] and burn thru tokens"). One of the two acts on a pane, never both. Going: a
  `<state_dir>/night/*/.running` folder, the run's own lock.
- THE MORNING RUN (`bash agents-morning.sh`, by hand; question 2): its step 2 types the command in every pane, and
  each role now starts again by itself as it finishes - so step 3 (`agents.sh --restart`, which would end five fresh
  sessions) goes; the run ends when every role is idle again, naming any that is not running.
- By day the corner's "Finished 09:56" gives way within seconds to the next session's state (the reviewer,
  2026-10-25: "till the next session starts"); the summary stays in the page's list.

## The measure, on a prototype (scratch folder, a tmux server of its own, Claude Code 2.1.322; uncommitted)

- A Stop hook is given `last_assistant_message` whole ("Done\nThe session is ready to clear."), and `TMUX_PANE` is in
  its environment in a pane. The transcript at that moment did not yet hold the message (`-p` run: no assistant row)
  - so the hook reads the field, not the transcript.
- End to end, an interactive session in a pane: the hook at 10:54:58; a detached script typed `/clear` at 10:55:00
  and `/exit` at 10:55:05; the pane was back at its shell 2 s later and the next session's start was typed at
  10:55:07; the new session came up in the same pane under its new name.

## Questions

1. To girsa-architect - a role that finishes with a night run going, the run not having asked it (the reviewer still
   at work at 19:00, or a role ending its piece at 23:00). A, recommended: never started again while a run is going -
   one rule, one actor, by the run's lock; the reviewer at work in the evening types `bash agents.sh`. C: started
   again unless the reviewer is idle `night.you_idle` seconds - the hook's script clears and exits it either way.
2. To girsa-architect - the morning run's step 3 with the hook in place: removed as above (recommended), or kept for a
   project whose settings do not name the hook (it would then restart sessions the hook just started).
3. To girsa-ui-steward - the page's words: the legend's "Landed" and the corner's "Landed 09:56" become "Finished";
   the list "Landings (N)" becomes "Finished sessions (N)", its rows "finished 10 Nov 09:56". Colours unchanged.

## Tests (each rule shown red with it out)

- Config: `night.finish_command` required and a string; `landed_quiet` refused as unknown.
- The night run: the command typed is the config's (a placeholder's `/done-for-now`, never `/land`); a run that
  closed a role ends with no alert and no `agents.sh` - the stub `osascript`'s record empty.
- `board.py finished` posts; `landed` still does; the corner's word is "Finished".
- The hook, `agents.sh` stubbed: the sentence starts `--next ROLE PANE`; not started for "I am not ready to clear
  yet", the sentence inside a line, a step left undone, no `TMUX_PANE`, a name that is no role, a night run going.
- `agents.sh --next` behind the stub tmux: `/clear`, `/exit`, then the start with its `env -u`; a pane whose `@role`
  is another's is typed nothing; a pane that never returns to its shell gets no start.
- The whole suite; the page's browser tests for the changed words.

## Files

- `mishmeret/finish_hook.py` (new), `mishmeret/agents.sh`, `mishmeret/agents-morning.sh`, `mishmeret/config.py`,
  `mishmeret/board.py`, `mishmeret/board_server.py`, `mishmeret/keepalive_due.py` (its comment), `README.md`
- `.claude/mishmeret.json`, `.claude/settings.json`, `.claude/hooks/finish_hook.py` (the shim) - Mishmeret's own
- `tests/test_sessions.py`, `tests/test_board.py`, `tests/test_config.py`, `tests/conftest.py` and the placeholder
  config
- `notes/PLAN-FINISH.md`, `notes/STATE-mishmeret-builder.md`, `notes/LOG.md`

## The first project's side (girsa-operator's and girsa-builder's, at the pin bump)

- Its config: `night.finish_command`, and `finished_quiet` for `landed_quiet` - in the commit that moves the pin.
- Its `settings.json`: the Stop hook, and its shim; its command file calls `board.py finished`.

## Not in this piece

- A Board state for "its own background task is running" (found 2026-11-10; the reviewer has not given it as work).
- A session outside tmux (it finishes as now, by hand).
