# Plan: the terminal adapter - the session scripts' tmux behind one library, WezTerm beside it

## The case

The reviewer, 2026-11-25, in mishmeret-builder's pane: "what can repl tmux on win and mac / elsewhere" (answered:
WezTerm runs on macOS, Linux and Windows, and its `wezterm cli` has a verb for most of tmux's), then "small terminal
adapter", and asked which second terminal: "wezterm".

Today every terminal step of Mishmeret is tmux's, written into the session scripts: `agents.sh` 16 verbs (has-session,
kill-session, new-session, split-window, select-layout, select-pane, send-keys 6, capture-pane, display-message,
list-panes, set-option 4, show-options 3, source-file, attach-session 2), `agents-morning.sh` capture-pane 2 and
send-keys 2, `agents-lib.sh` list-panes. tmux has no native Windows build. The guard's tmux rule (role_guard.py: the
live server's kill-server) stays the guard's.

THE PROBE (2026-11-25): WezTerm 20240203-110809-5046fc22, installed by Homebrew on the reviewer's word; a private
headless `wezterm-mux-server` on its own socket (a scratch config's `unix_domains`; the socket in a short folder of the
per-user temp directory - macOS refuses a socket path longer than its SUN_LEN, which the scratchpad's is), reached by
`WEZTERM_UNIX_SOCKET`, stopped and removed after. Each verb's form, run:
- has-session / list-panes: `wezterm cli list --format json` - each pane's `pane_id`, `workspace` (tmux's session),
  `size`, `title`, `cwd`, `tty_name`.
- new-session: `spawn --new-window --workspace S --cwd D`; split-window: `split-pane --pane-id P --right|--bottom
  --cwd D` - each prints the new pane's id.
- send-keys TEXT Enter: `send-text --pane-id P --no-paste "TEXT\r"`.
- capture-pane: `get-text --pane-id P --start-line -N [--escapes]` - no join of a wrapped line (tmux's `-J`).
- pane_current_command: the pane's `tty_name`, then `ps -t TTY`, the process marked `+` (the pane's title is the
  program's own to set); pane_pid -> pane: the process's tty, the same way.
- kill-session: `kill-pane` for each pane of the workspace; select-pane: `activate-pane`; a label: `set-tab-title`.
- NONE: a pane's own options (tmux's `@role`, `@colour`); the pane border's label; the `tiled` layout; source-file.

GIRSA-ARCHITECT'S ANSWER (the first project's design-study/MISHMERET-TERMINAL-ADAPTER-ARCHITECT.md at 83c414ef4,
written before any review of this plan): the case holds.
- Q1 agreed. The cost, for the README: the sessions part keeps tmux's names for both terminals (`tmux_session`,
  `tmux_conf`, the roles' `tmux`); `tmux_conf` stays required and is read by nothing under WezTerm. Their renaming
  waits for the next change of a required key.
- Q2 agreed, the file WRITTEN AFRESH BY `term_new`: measured there (paneids.sh), two private servers one after the
  other each listed pane ids [1, 2] - ids repeat across servers, so a file a server left behind (the GUI closed, a
  crash) gives the next session's untagged panes a role not their own. My measure removed the file itself first, so
  could not see it. A test: a file left with ids the next session reuses, only the new tags read.
- Q3 NOT DEFERRED, IN THIS PIECE: the tmux rule's case (2026-10-11, a test of agents.sh reached the live server, five
  roles in it, by the pane's `$TMUX`) returns with WezTerm, whose pane holds `WEZTERM_UNIX_SOCKET`; `term_kill`'s
  form closes every role. And the refactor takes the kill out of agents.sh, so the guard's reading of a script
  (test_guard.py's `"in the script agents.sh"`) fails: the guard reads a script with the files it sources by a
  literal path, as the shell does. The WezTerm form, in the tmux rule's scope: `wezterm cli kill-pane`, and pkill or
  killall naming wezterm, let through when the command sets `WEZTERM_UNIX_SOCKET` to a socket of its own.
  `send-text` into another pane is not in the tmux rule, so not in this one.
- Q4 agreed. Q5 agreed, with a test: no `tmux` or `wezterm` command in the three scripts outside term.sh.
- THE PLATFORM THE CASE NAMES is Windows, unmeasured: under WSL tmux runs, so the need is native Windows, where bash
  is Git Bash's; `term_cmd` and `term_pane_of_pid` rest on a pane's `tty_name` and `ps -t`, and a Windows pane is a
  ConPTY. The plan names the bash, and the Windows run is the reviewer's own measure, on the Windows test machine,
  before the piece is called done for its case.
So the change gains items 5 and 6 below, and the guard's part is measured (the guard-measure skill) before the review.

THE GUARD'S PART, BUILT ON THE BRANCH AND MEASURED (2026-11-27, the guard-measure skill; committed at 654db02, the
branch's first code; the cases, extracts, decisions and prototype scripts in this session's scratchpad, ta/):
- THE HOLE, main 57b87b2's guard (probe.py, 29 cases on placeholder paths): every form of `wezterm cli kill-pane` let
  through - no --pane-id, behind wezterm's and cli's own options, by a path, `wezterm.exe`, in a loop, in `bash -c`,
  the operator's - and pkill, killall and taskkill naming wezterm. And with the kill moved into term.sh (a prototype:
  agents-lib.sh sourcing term.sh, agents.sh calling `term_kill`), main's guard lets `bash agents.sh --resume` through
  from a live pane.
- ON THE RECORD (extract.py, 2026-11-27: the first project's 1,142 transcripts with its pi sessions, 174,150
  command-cwd-role triples; Mishmeret's 13, 2,277): `wezterm cli ... kill-pane` 0 and 0; pkill, killall or taskkill
  naming wezterm 0 and 5 (this lane's own measure, each a `pkill -f` of the private server's config path); a command
  naming wezterm at all 6 and 16 (girsa-architect's Q2 probe and its notes, a look at the terminals; this lane's probe
  and measure); `bash agents-morning.sh` 63 (girsa-operator's 53) and 7.
- ITEM 5 AS BUILT (`_script`, `_sourced`, `_called`; for every rule that reads a script - the git rules, the tmux
  rule, the check-status and piped-check rules): a script's `.sh` sources and theirs, each once; a relative path from
  where the shell is; a folder the guard cannot read (`"$HERE"`, the `$(cd "$(dirname ...)" && pwd)` form) taken for
  the script's own - a `shortcut:` in the code. AND A LIBRARY'S FUNCTION IS READ ONLY WHEN WHAT RUNS NAMES IT (the
  script, a library's top-level code, a function so named): rule 45 on the first build refused 20 of the first
  project's runs of agents-morning.sh (`--install-night`, `--install-reminder`, `--skip`, `--skip-tonight`, `--resume`,
  the night's dry run, a stubbed test; girsa-operator's but 2 of girsa-verifier's), which sources term.sh for its
  capture and never calls its kill - the shell runs a sourced function only when called. Not read: a function called
  by a name the guard cannot read.
- ITEM 6 AS BUILT, with two changes to girsa-architect's form: pkill and killall naming wezterm are refused OUTRIGHT,
  not let through on a socket of the command's own - they match processes by name, which no socket narrows; a test
  server is stopped by its pid, as girsa-architect's own measure did. And taskkill with them (Windows's, the case's
  platform; unmeasured there). `wezterm cli kill-pane` is let through where the command sets WEZTERM_UNIX_SOCKET (a
  prefix, `env`, an earlier `export` outside quotes) to a value not empty and not the variable itself - into a script
  and its `bash -c` too.
- THE TESTS (test_guard.py, one new test, placeholder scripts): two levels of sourcing, a relative path, a loop, a
  source in a heredoc, `. venv/bin/activate` and /dev/stdin not read; a library's function cut or read (not called,
  called by another, by the library's top level, `function NAME {`, a name inside another, a body that never closes,
  a definition inside another); the git rules through a sourced file; every WezTerm form refused and let through, the
  operator too. 28 RULES each red with it taken out (mutate.py, the baseline passing). The suite: 200 passed.
- THE BUILD'S RUN OF RULE 45, main 57b87b2 (its guard and scripts) against the branch's guard with the prototype
  scripts, by role (a builder, the operator, `each`): the first project's 174,150 - newly refused 1, newly let through
  0, faults 0, in each of the three; Mishmeret's 2,277 - 5, 0, 0 in each. The 1: girsa-operator's run of agents.sh in
  a private tmux server's environment (`env -u TMUX TMUX_TMPDIR=<folder> ... bash <the project>/agents.sh`), which now
  reaches WezTerm's kill too: the first cost below. The 5: this lane's own `pkill -f "wezterm-mux-server ...
  --config-file <scratch>/mux.lua"` - the pkill rule's cost. And main's guard against the prototype scripts (the hole,
  on the record): 5 of the first project's newly let through - `bash agents.sh` from a live pane with its tmux stubbed
  on PATH, refused today by the kill in agents.sh; the branch refuses them again.
- THE COSTS, for the README: a script holding both terminals' kills (agents.sh), run against a private server, names a
  private one for each - `env -u TMUX TMUX_TMPDIR=<folder> WEZTERM_UNIX_SOCKET=<socket> bash agents.sh`; a pkill of a
  private WezTerm server is refused whatever its pattern (stop it by its pid); a library function called by a name the
  guard cannot read is not read.
- FOR TERM.SH'S BUILD: its dispatch stays literal (`if [ "$MM_TERMINAL" = wezterm ]`, never `"_${T}_kill"`), so the
  guard reads both kills - test_guard.py's read of the real agents.sh pins it, its private-server line gaining the
  WezTerm socket.

## The measure (a prototype: `term.sh`, one function a verb, each with a tmux and a WezTerm form)

`measure.sh` runs agents.sh's sequence through it, 25 checks: no session at start; four panes, each its own id, listed
by the session; each tagged role and colour, read back; an untagged key empty; each at its shell; each runs a typed
line, captured; a capture with escapes holds the colour, one without holds none; a pane waiting on a job at its shell;
a foreground `sleep` the pane's command; a process's pane from its parent shell; the list's pane, role, command; label,
layout and focus; the session killed.
- tmux, a private server (`env -u TMUX TMUX_TMPDIR=<its own folder>`): 25 ok, 0 faults.
- WezTerm, the private server: first 23 - panes 3 and 4 (19 columns) wrapped their line, which get-text does not join;
  with a join of each line as wide as the pane to the next (tmux's `-J`, for a capture without escapes): 25 ok.
The scripts: this session's scratchpad, wez/ (term.sh, measure.sh, measure-tmux.out, measure-wez.out, mux.lua).

## The change

1. `mishmeret/term.sh`, sourced by the three session scripts: `term_has`, `term_panes`, `term_kill`, `term_new`,
   `term_split`, `term_send`, `term_capture`, `term_cmd`, `term_pane_of_pid`, `term_tag`, `term_tag_of`, `term_list`,
   `term_label`, `term_layout`, `term_focus`, `term_attach`, `term_conf` - each tmux's call as today, or WezTerm's.
   The scripts call nothing else of the terminal's.
2. The choice: the config's OPTIONAL `terminal`, `"tmux"` (absent) or `"wezterm"`, `--shell`'s `MM_TERMINAL`
   (design question 1).
3. WezTerm's pane tags: a file, `<state_dir>/panes-<session>.tsv`, written afresh by `term_new`, removed when the
   session is killed (question 2).
4. The README: the adapter, WezTerm's form and its costs (with Q1's: tmux's names kept, `tmux_conf` unread under
   WezTerm); on Windows the scripts run under Git Bash, unmeasured - the reviewer's own run on the Windows machine.
5. THE GUARD READS A SCRIPT WITH WHAT IT SOURCES (`. "$HERE/term.sh"`, `source ...`), and theirs, a library's
   function when what runs names it, so the tmux rule finds the kill where it now lives (the head: as built).
6. THE GUARD'S WEZTERM FORM, the tmux rule's scope: `wezterm cli kill-pane` refused but where the command sets
   `WEZTERM_UNIX_SOCKET` to a socket of its own; pkill, killall or taskkill naming wezterm refused outright; the
   operator too, as tmux's (the head: as built).

THE COSTS, WezTerm's (named in the README): no label on each pane's border (the tab's title alone); no tiled layout
(the splits as made); a line exactly as wide as its pane is joined to the next in a capture; the tags in a file, which
a pane closed by hand leaves behind (read against the list). Not measured: the GUI (only the headless server - attach,
and a start from inside a WezTerm window); Claude Code's own screen under send-text (bash only, as tmux's measure);
Windows and Linux.

Not in this piece: `send-text` into another role's pane (not in the tmux rule either); a session started by MISHMERET_ROLE with no agent file
(girsa-architect's Q7 on the guard alone: measured on a top-level start and a nested one first, if wanted).

## Design questions (to girsa-architect, answered at 83c414ef4 - the head; Q3 not as I recommended)

1. THE CHOICE IN THE CONFIG, an OPTIONAL top-level `terminal`, not a field of the sessions part (which is all or
   none: every config would need it). My recommendation: so.
2. WEZTERM'S TAGS IN A FILE, not the pane's user variables (set from inside the pane by an OSC 1337 sequence, and not
   read by `wezterm cli list` in 20240203). My recommendation: the file.
3. THE GUARD AND WEZTERM: tmux's live server is the guard's (kill-server refused); WezTerm's GUI holds every pane the
   same way, and `wezterm cli kill-pane`, `send-text` into another role's pane, or `pkill wezterm` reach it. The
   record holds no wezterm command yet. My recommendation: its own piece, after the first WezTerm runs are on the
   record, so its cost can be counted.
4. ATTACHING: run inside a WezTerm window, agents.sh spawns into that window's own server (its panes hold
   WEZTERM_UNIX_SOCKET); run outside one, it stops and says so - no GUI started by a script. My recommendation: so,
   the smallest; the reviewer's own run of it the measure, since I cannot watch a GUI.
5. A SHELL LIBRARY, sourced, not a Python module: the three scripts are bash, and each verb is one call. My
   recommendation: shell.

## Files

- mishmeret/term.sh (new); mishmeret/agents.sh, agents-morning.sh, agents-lib.sh (each tmux call through it)
- mishmeret/config.py (`terminal`, OPTIONAL; `--shell`'s MM_TERMINAL)
- mishmeret/role_guard.py (a script read with what it sources; the WezTerm form of the live-server rule),
  tests/test_guard.py
- tests/test_sessions.py (the scripts' tests as today under tmux's stub; under a WezTerm stub, the calls it records),
  tests/conftest.py (a `wezterm` stub beside tmux's), tests/test_config.py
- README.md
- notes/PLAN-TERMINAL-ADAPTER.md, notes/LOG.md, notes/STATE-mishmeret-builder.md

## Tests

- term.sh, each function under each terminal's stub: the call it makes, as the probe ran it.
- The session scripts' tests unchanged under tmux (the adapter a refactor there); agents.sh's start under WezTerm's
  stub: the spawn, the splits, the tags file, the lines typed.
- No test reaches a live server: the stubs first on PATH, as conftest.py has them (a real one only in measure.sh, on
  a private server).
- The tags file: one left behind with ids the next session reuses - only the new tags read.
- No `tmux` or `wezterm` command in the three scripts outside term.sh.
- The guard (built, the head): the kill read in a sourced file, a library's uncalled function not; `wezterm cli
  kill-pane` refused, the operator too, and let through with a socket of its own; pkill, killall and taskkill of
  wezterm refused; each rule red with it taken out; rule 45 by role on both records. At term.sh's build, the real
  agents.sh's line (`"in the script agents.sh"`) read through term.sh, and its private-server form with both sockets.
