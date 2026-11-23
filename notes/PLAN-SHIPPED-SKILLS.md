# Plan: skills shipped to every project

## The case

The reviewer, 2026-11-23, in mishmeret-builder's pane: "grab the status-report skill from girsa and add it to
mishmeret. what other skills are helpful here". To the question of where Mishmeret's version should live, the answer
was "Both": Mishmeret's own version (built: .claude/skills/status-report, 7c48fea, 7203f57) and one shipped to every
project. To the question of which other skills, the answer was "all of the above":
- landing, the land.py procedure;
- guard measure (built as Mishmeret's own: .claude/skills/guard-measure, 59f84a2, 5bccb49);
- sessions, agents.sh, the keep-alive and test tmux servers;
- push and pin, the operator's push and a project's pin bump.
Then: "write the skills plan".

Today a project that runs with Mishmeret has only its own skills. The first project's `.claude/skills/` holds nine,
two of them on Mishmeret's own code (`landing` for land.py, `operator-sessions` for agents.sh). They are written in that
project's words and kept by hand beside the code they describe. They also go stale at each pin bump, because the code
moves and the skill does not (THE SECOND COPY OF THE TRUTH).

THE MEASURE, 2026-11-23, in the scratchpad (skillprobe/). Can a skill kept in a pinned tree reach a session through a
link? Each tool was pointed at a local capture server that records every request and answers 400, so no model ran
and no account was charged.
- A probe skill (its description holding a word, PINNED-OK-A1) in a folder standing for a pin
  (`pin/skills/probe-skill`), linked from a scratch project's `.claude/skills/probe-skill` and
  `.agents/skills/probe-skill`. Beside it a control project with a plain skill folder (its word CTRL-OK-B2).
- CLAUDE CODE (`claude -p`, ANTHROPIC_BASE_URL at the capture server): all 6 of the probe project's requests carried
  PINNED-OK-A1, and all 6 of the control's carried CTRL-OK-B2. Claude Code follows a linked skill folder.
- PI (1.6.0, the pi tests' scripted provider pointed at the capture server):
  - the link in `.agents/skills/`, project untrusted (how a role starts): 0 of 1 requests carried the word;
  - the same with `--approve`: 1 of 1;
  - `--no-skills --skill <the pinned folder>`: 1 of 1.
  pi follows the link only in a trusted project, and loads an explicit `--skill` path in any case.

## The change

1. THE SKILLS, IN MISHMERET'S LIBRARY: `mishmeret/skills/<name>/SKILL.md`, pinned with the code they describe, each in
   general words - a project's particulars come from its config, never named. Their names carry a `mishmeret-`
   prefix, so none clashes with a project's own (the first project has a `landing` and a `status-report`):
   - `mishmeret-status-report`: the reviewer's big picture, read from the config:
     - the state files (`sizes.state_files`), the status file (`sizes.status_file`) and the logs
       (`start_reads.logs`);
     - the Board's open items and corners (`board_dir`);
     - git: main against origin, branches, worktrees;
     - the project's pin (`mishmeret_commit`) against Mishmeret's main.
     It follows Mishmeret's own status-report: the questions first, every count from its source in the same turn.
   - `mishmeret-landing`: `land.py commit`, `land`, `check-conflict` and `gate`; the hold; the lane check and
     `--because`; the gate sets; `--plan` for the config's planned role. From land.py's `--help` and its docstrings.
   - `mishmeret-sessions`:
     - `agents.sh` (no option, `--restart`, `--resume`, `--next`) and a role run by pi;
     - the night and morning runs, and the two finish commands (`night.finish_command`, `finish_exit_command`);
     - `keepalive_due.py`;
     - a test tmux server, reached only as the guard's tmux rule allows.
   - `mishmeret-push-and-pin`:
     - the operator's push: on the reviewer's word in its own pane, a branch by name; never --all, --mirror, a force,
       a delete, a retired remote, or a config key on the line;
     - a project's pin bump: `git -C <checkout> worktree add --detach .pins/<sha> <sha>`, `mishmeret_commit`, each tree
       of the project moving with it, and a new config key landing with the bump that brings it.
   The guard-measure skill stays Mishmeret's own: changing the guard is Mishmeret's work, not a project's.
2. HOW A CLAUDE CODE ROLE GETS THEM: `agents.sh`, at each start, links each `<the project>/.claude/skills/mishmeret-<name>`
   to `<the tree it runs from>/skills/mishmeret-<name>` (replacing an older link, never a file or a folder of the
   project's own). The links follow the pin: the tree agents.sh runs from is the pin the project's shim names, so a pin
   bump moves every link at the next start. They are not committed (a link holds a machine's path); the project's
   `.gitignore` lists `.claude/skills/mishmeret-*`. Roles start in the main clone, so its `.claude/skills/` is the one
   read.
3. HOW A PI ROLE GETS THEM: agents.sh's pi line passes `--skill <the tree>/skills` (measured: an explicit path loads,
   trusted or not), and `--skill <the project>/.claude/skills` for the project's own.
4. THE SKILLS KEPT TRUE (THE SECOND COPY OF THE TRUTH): a test reads each shipped skill and fails on a name it uses
   that the code lacks: a land.py subcommand or option, an agents.sh mode, a config field, a file under mishmeret/.
5. Mishmeret's README says what is shipped and how a project gets it.

## Design questions (to girsa-architect)

1. THE NAMES AND THE PROJECT'S OWN: shipped with a `mishmeret-` prefix, beside the project's own, which stay its own
   (the first project's `landing` and `operator-sessions` could then point to the shipped ones for the general part).
   Or should a shipped skill replace a project's skill of the same name? My recommendation: the prefix, and the project
   decides what its own skills keep.
2. WHO WRITES THE LINKS: agents.sh at each start, untracked, which writes into the main clone's `.claude/` (the
   operator's) whenever the reviewer starts the roles. Or a step of the pin bump, committed by the project, which would
   commit a machine's path? My recommendation: agents.sh. A role started by hand before agents.sh ever ran has no links.
3. THE DRIFT TEST: names checked against the code (item 4). Is that enough, or should each skill's procedure be
   generated from the code's own text (land.py's `--help`), as THE SECOND COPY OF THE TRUTH asks of a table?

## Files

- mishmeret/skills/mishmeret-status-report/SKILL.md, mishmeret-landing/SKILL.md, mishmeret-sessions/SKILL.md,
  mishmeret-push-and-pin/SKILL.md (new)
- mishmeret/agents.sh (the links; the pi line's `--skill`)
- tests/test_shipped_skills.py (new: the drift test), tests/test_sessions.py (the links made, an older link replaced, a
  project's own file or folder left; the pi line's `--skill`)
- README.md
- notes/PLAN-SHIPPED-SKILLS.md, notes/LOG.md, notes/STATE-mishmeret-builder.md

## Tests (each rule red with it taken out: mutate.py)

- agents.sh behind the stub tmux, in a placeholder project:
  - each shipped skill linked into `.claude/skills/`, pointing at the tree agents.sh ran from;
  - an older link to another tree replaced;
  - a file or folder of the project's own under the same name left as it is, with a line saying so;
  - the pi line holds both `--skill` paths.
- The drift test: each name a shipped skill uses exists. Shown red with a skill naming a land.py option that is not
  there.
- Under pi (skipped where pi is absent): a shipped skill reaches pi's first request through `--skill`, as measured,
  with the tests' scripted provider.

## For the first project

At its pin bump to this commit: its `.gitignore` lists `.claude/skills/mishmeret-*`, and the next `bash agents.sh`
makes the links. Its own nine skills are untouched; whether `landing` and `operator-sessions` keep their copies of the
general procedure is its owners' to decide.

Not measured: Windows (links there differ), and whether a running session picks up a link changed under it (each tool
read its skills at start in the measure).
