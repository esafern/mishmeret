# The start scripts with no project named: the plan (mishmeret-builder, 2026-11-05)

Written 16:34, revised 16:40 (`date`). On girsa-operator's REQUEST (the two defects in the first project's operator
item of 2026-11-05, 10:40 and 11:22). "The script marking what it sets, or a clear message" is girsa-operator's
sentence, the last line of its recommendation in that project's Board #157; the reviewer answered B (keep the
workaround) with no note - so the choice was open on its merits (girsa-architect's and girsa-verifier's correction).
Answered by girsa-architect (both questions: refuse; and every role launched with the config dropped), ACCEPTED by
girsa-verifier with that addition.

## The case

- 10:40: the reviewer ran `./agents-morning.sh` in `~/work/mishmeret/mishmeret`: "the project's Mishmeret config
  cannot be read" - by design (no `MISHMERET_CONFIG`, so `config.py` took the root from the current folder's git
  repository, Mishmeret's, which had no config), but the message did not say where to run it from.
- 11:22: the reviewer's direct `../mishmeret/mishmeret/agents-morning.sh` from the project's folder read the project's
  config from the current folder and exec'd agents.sh, whose `agents-lib.sh:13` exported it with no shim's mark
  (`MISHMERET_CONFIG_BY_SHIM`) - so the project's shim in a role's worktree took it as set by hand and kept the main
  clone's config: two of the project's gate tests red in a copy, every landing since under `env -u MISHMERET_CONFIG`.
  And it ran Mishmeret's checkout (main), not the commit the project pins.
- FOUND, planning: (a) since piece B Mishmeret has its own `.claude/mishmeret.json`, so the 10:40 run now goes ahead
  silently on Mishmeret's own project (root `~/work/mishmeret`, no tmux role) instead of refusing; (b) the night run's
  Go (`agents-morning.sh:418`) types `MISHMERET_CONFIG='...' bash '<root>/agents.sh'` into a new window without the
  mark, so the shim there keeps it as set by hand - the same leak on every Go, through the shim.

## The behaviour

- `agents-lib.sh`, which both scripts source first: with `MISHMERET_CONFIG` unset - no shim and no person named the
  project - it stops before anything, exit 1: "SCRIPT: no project named - run the project's own SCRIPT from its folder
  (bash SCRIPT there): it names the project's config and the Mishmeret commit the project pins. Or set
  MISHMERET_CONFIG to the project's .claude/mishmeret.json." Its own default (`:-$DIR/.claude/mishmeret.json`, line 13)
  goes: the library never sets the config, so it never exports one unmarked. A config it cannot read names its path.
- The Go's new window is given the mark with the config: `MISHMERET_CONFIG_BY_SHIM='${MISHMERET_CONFIG_BY_SHIM:-}'`.
  A shim's value stays the shim's (the project's shim there replaces it with its own and marks it); a value set by hand
  (empty mark) stays set by hand.
- ADDED on girsa-architect's answer 2: `agents.sh`'s `start_role` types each role's start, fresh and `--resume`, as
  `cd '<root>' && env -u MISHMERET_CONFIG -u MISHMERET_CONFIG_BY_SHIM claude ...` - a pane's shell holds the tmux
  server's environment (the live one holds the unmarked value now; a config set by hand, R's fallback, would give a new
  server one too), and a role's config is its own tree's, set and marked by its own shim. `MISHMERET_AS` untouched.
- Unchanged: the shim's path (it sets and marks the config, then `bash` on the pinned script); launchd's night job,
  which runs the project's own `agents-morning.sh`; a config set by hand (every test of the scripts).
- README: one sentence, the start scripts run only with a project named.
- Not done: the live tmux server keeps the environment it was started with until it ends; the roles' clean restart
  is the reviewer's (#157 B).

## The design question, answered by girsa-architect (Girsa 45416b48, design-study/MISHMERET-START-SCRIPTS-ARCHITECT.md)

1. R: the default is a second path to the config beside the shim, guessing the project and running an unpinned
   checkout; a wrong project is worse than a stop. 2. Yes: every role launched with both variables dropped (above).

As asked: this plan takes the clear message (R): a run with no project named stops.
The other, marking (M): the library sets the config from the current folder as now, and marks it as a shim would -
the direct runs then go on, on a guessed project and an unpinned checkout, the 10:40 one on Mishmeret's own. R, as
the plan's: one rule ends both runs and the guess; M keeps a direct run working. And: should a role's launch drop the
inherited config altogether (`env -u MISHMERET_CONFIG ... claude` in `start_role`), so no tmux server's environment
reaches a role? Not in this plan - the shim's mark is its designed contract.

## The measure (the prototype, uncommitted in `~/work/mishmeret-builder`, 16:32)

- Before, on placeholder projects in git repositories, a stub tmux recording its environment (and an empty
  `TMUX_TMPDIR`): agents.sh from the project's folder, no config named - exit 0, tmux given
  `MISHMERET_CONFIG=<project>/.claude/mishmeret.json` and no `MISHMERET_CONFIG_BY_SHIM`; from a repository with no
  config - "the project's Mishmeret config cannot be read", exit 1.
- After: agents-morning.sh from the project's folder, from a repository with no config, and from
  `~/work/mishmeret/mishmeret` (the 10:40 run) - each exit 1 with the message, tmux never reached.
- The new test (both scripts, both folders; a config set by hand still runs, tmux given it) red on today's scripts:
  agents.sh ran (exit 0), agents-morning.sh exec'd the project's agents.sh (exit 127). Suite 109 passed.

## Files

- `mishmeret/agents-lib.sh`: the stop and its message; the default export gone; the unreadable config's path.
- `mishmeret/agents-morning.sh`: the Go's new window given the mark.
- `mishmeret/agents.sh`: `start_role`'s two launches with the config dropped.
- `tests/test_sessions.py`: the new test; a fresh start behind a stub tmux, each of the five typed starts carrying the
  `env -u` (red on today's line); the shared-library test's two asserts to match.
- `README.md`: the sentence.
- `notes/`: this plan, the state file, the log.

## After

girsa-verifier checks at the final commit; girsa-operator merges; the project's pin bump is girsa-builder's. Then
the stopgap `env -u MISHMERET_CONFIG -u MISHMERET_AS` can go once the roles restart through the project's shim (the
operator's and the reviewer's to say).
