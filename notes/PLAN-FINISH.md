# Finishing a session, by day and by night: the plan (mishmeret-builder, 2026-11-10)

Written 10:57, revised 13:07 (`date`). On girsa-operator's ANSWER of 2026-11-10: the first project's Board #183,
answered A (all three) by the reviewer with the note "A but finish instead of close. go" (read on that Board); and its
ADDITION the same day, the reviewer's "add finish-and-exit and have the night run use that" (read in that project's
commit 1f18a04b and its two command files; no Board item carries it). Answered by girsa-architect (1: A, its home
`agents.sh --next`; 2: step 3 removed) and girsa-ui-steward (the four words as proposed); girsa-verifier: READY, two
MEDIUMs and three notes, all taken below. Built as revised here, in one commit.

## The case

The reviewer, 2026-11-10 (Board #183): "confusion btw [between] landing a change and a session"; "during the day I
want to clear a session after landing, then exit and start a new one. in the even [evening] after I'm idle I want the
night run to exit and not restart". Then: "add finish-and-exit and have the night run use that".

- "Land" named two things: a change reaching main (`land.py`, LANDED) and a session ending (`/land`, the corner's
  "Landed 09:56", `board.py landed`). girsa-verifier: two of its own sessions that day ended on "landed at" a commit
  with no session command run.
- By day a session that had ended itself stayed in its pane until someone typed `/clear`, `/exit` and its start. Only
  the night run read the closing sentence.
- By night, after closing the roles, the run updated Claude Code and held an alert whose "Go" started them again.

## The behaviour

### 1. The word: a session FINISHES; a change lands

- Two commands end a session, the project's own, named in its config and in no script: `night.finish_command` (the
  first project's `/finish`; its sentence "The session is ready to clear.": cleared, exited, started again) and
  `night.finish_exit_command` (`/finish-and-exit`; "The session is ready to clear and exit.": cleared and exited,
  nothing started, whoever typed it). The morning run types the first, the night run the second.
- BOTH OPTIONAL, AND `landed_quiet` KEEPS ITS NAME (found building; not as first planned, nor as girsa-architect read
  it): Mishmeret pins itself, so its own commit is made by the pinned reader on its own config - a required key added
  or renamed cannot be committed, the pinned reader refusing the new config and the new reader the old
  (`tests/test_own_project.py`). And by girsa-architect's rule of 2026-11-05 a field a project with no role in tmux
  cannot fill is optional. The run that finds its command absent stops and says so.
- `agents-morning.sh`: types the config's command; its questions, log lines, notifications and comments say "finish"
  where they mean a session's end. A comment's quoted words of the reviewer stay as said.
- `board.py finished` (the arguments of `landed`); `landed` stays accepted, an alias, until the first project's
  command file calls the new one - then it goes (the state file's Open; that file is not Mishmeret's to test). The
  corner's word is "Finished 09:56"; the legend "Finished"; the list "Finished sessions (N)", its rows "finished ...".
  The budget notice says "finish the session when the piece is done".
- Not renamed, and why: the record's `"type": "landed"` (append-only - old rows read as they are, one reader); the
  Python, JavaScript and CSS names behind the page; the night marks' file names (`.land-sent`, `.land-only`,
  `.landed-kept`), which no person reads and `keepalive_due.py` shares; the config's `landed_quiet` (above).

### 2. By night: the run ends when the roles are closed

- After its last look: the count line, `claude update` when a role was closed, then exit. The alert, its "Go", the
  iTerm2 window and its `agents.sh` are gone. The log's last line names the hand step: `bash agents.sh`.
- The run reads either sentence (a role that finished by itself with the short one is closed the same way).
- Its lock (`<state_dir>/night/<date>/.running`) now holds the run's process id (girsa-architect's 1b): a lock whose
  run is gone is no lock, for `agents.sh --next` and for the next night's run, which takes it over and says so.
- `--install-night` still removes the 06:00 reminder; its sentence no longer names a Go.

### 3. By day: a finished session is cleared, exited and started again in its pane

- `finish_hook.py`, a Stop hook (the project's `settings.json` names it): the turn's last message ending with a
  closing sentence, in the session of a role with a pane (`CLAUDE_CODE_AGENT`), running in one (`TMUX_PANE`) - it
  starts `agents.sh --next ROLE PANE` detached, with `exit` after the longer sentence, and returns. No other rule
  is the hook's. Silent always; never blocks.
- THE SENTENCE'S RULE HAS ONE HOME (girsa-architect): `role_usage.closing` - the sentence whole, as the last
  non-blank line, emphasis stripped. The hook asks it of the message; the night run of a transcript
  (`role_usage.py closing PATH`, the shell's own reader gone). The pane's form, for text tmux captured, is
  `READY_LINE`, now matching either sentence.
- `agents.sh --next ROLE PANE [exit]`, every rule about what is typed:
  - only in the pane `agents.sh` gave that role (its `@role`);
  - A NIGHT RUN GOING, IT STANDS DOWN (girsa-architect's A, its home here): looked for before `/clear` and again
    before the start. The run closes the session and starts nothing. Said to the reviewer unless the run had asked
    that role (its `.land-sent` mark). A reviewer back at work in the evening types `bash agents.sh`;
  - NOTHING TYPED OVER WORDS IN THE PROMPT (girsa-verifier's MEDIUM 1): the prompt is read before `/clear` and
    before `/exit`; words there, or no prompt found - it stands down and says so;
  - `/clear`, `night.gap` seconds, `/exit`; then, the pane back at its shell (60 s at most), the role's fresh start,
    `start_role`'s own line. After the longer sentence nothing is started;
  - NOT STARTED TWICE IN TEN MINUTES (its MEDIUM 2): the second time, cleared and exited, and the reviewer told.
  What it did: `<state_dir>/next.log`.
- A finish with a step undone ends with what is left, not a sentence, and is left alone.
- THE MORNING RUN (`bash agents-morning.sh`): its step 2 types the finish command, and each role is started again by
  the hook - so the old step 3 (`agents.sh --restart`) is gone. Step 3 now names each role by its session
  (girsa-architect): not running; started again; still in the session it had and saying it is ready - the Stop hook
  is missing from the project's settings; or still in it and not finished. It need no longer run outside tmux.

## The measure (scratch folders, tmux servers of their own, Claude Code 2.1.322)

- A prototype, before the plan: a Stop hook is given `last_assistant_message` whole and has `TMUX_PANE`; the
  transcript did not yet hold the message (`-p` run); a detached script typed `/clear`, `/exit` and a start, the new
  session up in the same pane 9 s after the hook.
- The prompt, as `tmux capture-pane -e` gives it: `❯` and a no-break space, then nothing, or typed words, or dim text
  (`ESC[2m`, Claude Code's suggestion). A message already sent shows `❯` and a plain space.
- THE BUILT CODE, end to end (the real hook and `agents.sh --next`, a placeholder project and role, 13:00-13:02):
  words standing in the prompt - nothing typed, the words left; an empty prompt - cleared, exited and a fresh
  `--agent` session up in the pane; finished again a minute later - cleared and exited, not started; the longer
  sentence - cleared and exited, not started. Not run live: the night run, the morning run (behind stubs only).

## Tests (each rule shown red with it out: 29 taken out in turn - 28 red at once; the night's command for a role over
the context limit was pinned by no test, and red once its assertion was added)

- Config: the two commands optional, strings, exported to the shell only when named; an unknown night key refused.
- The night run, whole, behind stubs: what it types and names is the config's command; four roles closed - no alert,
  no window, no `agents.sh`, the lock gone. No command's name in the script.
- The morning run: types the config's command; step 3's four sentences, by session; starts nothing; a config with
  no command - both runs stop, nothing typed.
- `role_usage.closing` and `said_closing`: twelve messages, five transcripts, the command's exit status.
- The hook: ten cases (both sentences; not said; a step undone; inside a line; no message; not in tmux; a role with
  no pane; no role; a name that is no role).
- `agents.sh --next`: twelve cases (again; exit; another's pane; a run going; the run asked it; a lock left behind;
  never at its shell; a run begun meanwhile; words in the prompt; no prompt found; finished twice; and, girsa-verifier's
  MEDIUM on 51499da, words typed after /clear - the prompt's second read, held by no test until then: red with it out).
- The Board: `finished` and `landed` both post; the corner's word. The page at 1229x673 and 1864x1033, every role
  finished: each corner's line whole on one line, the footer's buttons on one row, the list's title and rows.
- The whole suite: 137 passed at 51499da (girsa-verifier's copy too, sixteen of its seventeen mutations red); 138
  with the leg added.

## Files

- `mishmeret/finish_hook.py` (new), `mishmeret/agents.sh`, `mishmeret/agents-lib.sh`, `mishmeret/agents-morning.sh`,
  `mishmeret/config.py`, `mishmeret/role_usage.py`, `mishmeret/board.py`, `mishmeret/board_server.py`, `README.md`
- `tests/test_sessions.py`, `tests/test_board.py`, `tests/test_config.py`, `tests/conftest.py`
- `notes/PLAN-FINISH.md`, `notes/STATE-mishmeret-builder.md`, `notes/LOG.md`
- NOT touched, though first listed: Mishmeret's own `.claude/` (its config needs neither command - no role in tmux -
  and its settings no hook; the builder's lane does not hold them) and `keepalive_due.py` (the marks unrenamed).

## The first project's side (girsa-operator's and girsa-builder's, at the pin bump)

- Its config gains `night.finish_command` and `night.finish_exit_command`, in the commit that moves the pin. Without
  them at that pin its night run stops, saying so, and closes nothing.
- Its `settings.json` names the Stop hook, through a shim; its command files call `board.py finished`.
- `/land` may stop being a pointer once the pin is at this commit: the night run types the config's command.

## Not in this piece

- A Board state for "its own background task is running" (found 2026-11-10; the reviewer has not given it as work).
- A session outside tmux (it finishes as now, by hand). A project whose settings do not name the hook: the morning
  run names it; nothing closes its panes by day.
- The role guard's reader of a script loses every line after a quote escaped inside a quote (found building): its
  own piece, notes/PLAN-GUARD-MASK.md on `builder-guard-mask`.
- NOT RUN ON LINUX (girsa-verifier's note): `agents.sh --next` rests on `osascript`, BSD `find -mmin` and tmux, the
  night run on `stat -f` too. The sessions' scripts are macOS-only (README); the hook and `role_usage.closing` are
  plain Python, run here on macOS alone.
