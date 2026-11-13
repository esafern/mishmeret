# Plan: the known gaps

## The case

The reviewer, 2026-11-13 15:39, in this session: "fix the known gaps now" - the open list read to them (the state
file's Open and Not given; M07's smaller items; girsa-verifier's gap on the frozen gate). Each item below was measured
on this branch's code (main f031698) with probe scripts on the guard's own functions and placeholder paths (from a
worktree `/work/book-builder` of the main tree `/work/book`, role ex-builder unless named), or read in the first
project's Board folder. A NEW FINDING made while measuring is item 1, and it is the worst one.

Not in this piece, and why:
- The night run and the morning run live. A live run types into the first project's live role panes. It is the
  reviewer's to schedule; the code is tested behind stubs.
- Linux. The session scripts are macOS-only by design (osascript, launchd, BSD `find`). Making them work on Linux is a
  feature, not a gap.
- A `!` command the reviewer types: Claude Code runs no hook for it (the reviewer's own run, 2026-11-12).
- The Edit and Write side "under an escaped quote": those tools are judged by their path (`edit_refusal`). No shell
  text is read there, so the mask does not reach them. Nothing to fix.

## The change

### The guard (mishmeret/role_guard.py)

1. A QUOTED WORD BEFORE git OR IN ITS OPTIONS HIDES IT (new, found measuring item 5). In the masked text a quoted word
   is its quotes around spaces, and GIT's and PREFIX's `\S+` stop at the first space. GIT then does not match at all,
   so no rule sees the command. Let through, measured:
   - `git -C "." push origin main` (a builder's push)
   - `git -C "/work/book" commit -m x` (from the main tree)
   - `git -C "." push --force origin main` (the operator's force)
   - `git -c 'user.name=x' push origin main` and `git --git-dir=".git" push origin main`
   - `X="a b" git push origin main`, `X='a' git push origin main`, `env X="a b" git push origin main`
   - `GIT_DIR="/work/book/.git" git reset --hard`
   - `sudo -u "me" git push origin main`
   - `X="a b" tmux kill-server` (the tmux check uses the same prefix)
   Fix: one shell word, `WORD = (?:"[^"]*"|'[^']*'|[^\s"'])+`, for every option argument and prefix word in GIT,
   PREFIX, TMUX_PREFIX and the tmux options, and for `-C`, `--git-dir` and `--work-tree` in `_git_trees`. A quoted
   path is then read like an unquoted one, `$VAR` expanded from the environment as a cd's already is.
   Measured: `git -C "$MAINTREE" reset --hard` let through while `cd "$MAINTREE"` is refused - the same fix.
2. A COMMAND INSIDE "$(...)" OR "`...`" IS READ AS WORDS. `echo "$(git push origin main)"` and
   ``echo "`git push origin main`"`` are let through, and so is `echo "$(pytest x | tail)"`. The shell runs them.
   Fix in `mask`: inside "...", a `$(` (not `$((`) or a backtick opens a stretch of commands that closes at its own `)`
   or backtick. Quotes inside it are their own, and the "..." resumes after it.
3. TWO -C. `git -C /work -C book reset --hard` from a worktree is let through. git takes each -C from where the one
   before left, and `_git_trees` read the first only. Fix: every -C, in order.
4. `cd -` AND A BARE `cd`. `cd /work/book; cd /work/book-builder; cd -; git reset --hard` is let through (`-` was read
   as a folder named "-"), and the other way round is refused. A bare `cd` (to $HOME) is not read at all, so
   `cd; git reset --hard` from the main tree is refused. Fix in `_places_before`: `cd -` goes to the place before the
   last cd, and a bare cd goes to $HOME.
5. A `case` PATTERN'S `)`. `case x in x) git push origin main;; esac` is let through, and so is a cd there. Fix: after
   `in` or `;;`, a pattern and its `)` are a boundary (BASE_BOUNDARY).
6. AN ALIAS, AND A FORCE FROM GIT'S CONFIG. `git -c alias.p='push --force' p origin main` (the operator) is let through,
   as is `git p origin main` for any role once `alias.p` is set. A plain `git push` forces when the remote's config says
   `mirror = true` or its push refspec starts with `+`. Fix: a verb the guard does not know is looked up as an alias.
   It is looked up from `-c alias.VERB=...` on the line, else `git -C <tree> config --get alias.VERB`, and the command
   is judged as what the alias runs (one level; a `!` alias as a shell command). For the operator's push, the
   remote's `mirror` and `push` keys are read the same two ways, and a force refused as on the line.
   DESIGN QUESTION to girsa-architect: the guard runs `git config` (about 5 ms) only for an unknown verb and for the
   operator's push.
7. TESTS FOR WHAT ALREADY HOLDS, measured green, pinned by no test: `$"..."` and a backtick string holding an escaped
   quote, then a push; the piped-check rule after each escaped-quote form.
8. The module header's WHO paragraph says a subagent is judged as no role (girsa-verifier's LOW on 5aa9a0a).

### The rest

9. AN ADDED LINE THAT BEGINS "++ " IS READ AS A FILE'S HEADER, in `.claude/lane_check.py` and
   `mishmeret/time_precommit.py`. The diff shows such a line as `+++ ...`. It is not scanned, and the file's later
   lines are filed under a wrong path. In this PUBLIC repository the lane check's address scan therefore misses that
   line. Fix in both: a `+++ ` line is a header only between `diff --git` and the first `@@`.
10. `--effort` WITH NOTHING NAMED (agents.sh:66, 72). A role whose agent file names no effort is started with a bare
    `--effort`. The next word becomes its value; at `--resume` that word is the prompt itself. Fix: `--effort X` only
    when X is named.
11. `agents.sh --next` runs `role_sessions.py` (line 45), and its answer is dropped (line 131 sets `SESSIONS=""`).
    Fix: not run for `--next`.
12. THE BOARD'S FOLDER ONLY GROWS. The first project's `server.log` is 5,539,679 bytes, and `sessions/` holds 800
    files, 1.6 MB (read 15:43). Fix, at the server's start:
    - A `server.log` over 5 MB moves to `server.log.1` (one kept).
    - A session record (and its `.lock`) not written in 30 days is removed.
    `started_since` reads only records written after a landing, so this changes only a landing over 30 days old. Its
    role has then run no session for 30 days, and the corner keeps that landing.
13. `/api/board` SENDS THE WHOLE RECORD EVERY 5 s: 1,504,177 bytes there, 0.14 s. The page then parses it and
    stringifies it to compare. Fix: the page sends the hash of the answer it last drew (`?have=`), and the server
    answers 204 when the new body hashes the same. The look is unchanged.
14. THE FOUR LESSON NUMBERS IN THE CODE, read in the first project's LESSONS.md:51, 96, 120, 122. Each name is in
    this repository's LESSONS.md. Each citation becomes the lesson's name:
    - Lesson 21: FLAT COORDINATE KEYS (config.py:13)
    - Lesson 47: WIRED TO NOTHING (config.py:26)
    - Lesson 59: A WRONG VALUE IS WORSE THAN A "?" (board.py:190, 227; agents-morning.sh:129; board_server.py:376;
      role_usage.py:130)
    - Lesson 60: DON'T REINVENT THE WHEEL (land.py:7)
15. THE FROZEN GATE'S NARROWER GAP (girsa-verifier, M12: "a file torn at the clone and unchanged after"). Suppose a
    tracked file is mid-write at the clone and still in that state at the compare. The copy and the main tree then hold
    the same torn bytes and the compare passes, so the gate runs on a half-written file. Fix: after the gate, the same
    compare runs again. A file changed since then is refused ("changed in the main tree during the gate: gate main
    again"), the merge standing, as the first compare's refusal does.

## Files

- mishmeret/role_guard.py, tests/test_guard.py (items 1-8)
- mishmeret/land.py, tests/test_guard.py (item 15)
- .claude/lane_check.py, mishmeret/time_precommit.py, tests/test_own_project.py and tests/test_guard.py (item 9)
- mishmeret/agents.sh (items 10, 11), tests/test_sessions.py
- mishmeret/board_server.py, mishmeret/board.py, tests/test_board.py (items 12, 13)
- mishmeret/config.py, board.py, agents-morning.sh, board_server.py, role_usage.py, land.py (item 14: comments)
- notes/PLAN-KNOWN-GAPS.md, notes/LOG.md, notes/STATE-mishmeret-builder.md

## Tests (each rule's test shown red with the rule taken out)

- Items 1-6: each form measured above is refused, alone and after a keyword. The existing fine lists stay fine, plus
  `git log --format="%h %s"`, `X="a b" git status`, `echo "$(date)"`, `cd -` back to a worktree, and a bare `cd`.
- Item 6: an alias from the line and from a placeholder repository's config, and a mirror remote's plain push for the
  operator.
- Item 9: a staged added line "++ <a placeholder address>" fails the lane check, and the file's next line is filed
  under its own path. The same line holding a time ahead of the clock fails the time check.
- Items 10 and 11: the stub-driven agents.sh tests - no bare `--effort`, and no `role_sessions.py` run for `--next`.
- Item 12: an old record removed and a new one kept; a large log moved.
- Item 13: the second ask with the first answer's hash gets 204, and a changed record gets 200.
- Item 15: a gate stub that finishes a main-tree write while it runs is refused.

## For the first project

Nothing in its config. Each change reaches it at its next pin bump, and fully once every tree has passed it. Its own
finish.md:51 ("Landed") and its trees' old pins went to girsa-operator on 2026-11-13, after 15:39.
