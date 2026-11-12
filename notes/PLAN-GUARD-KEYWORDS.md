# The guard sees git after a shell keyword, behind git's own options, and written quoted: the plan (mishmeret-builder, 2026-11-12)

Written 12:13 (`date`). This is M07's item 1, the second in the reviewer's order ("A" on the first project's
Board #201, 09:38), taken after girsa-verifier verified item 4 at 21cb9ba. It is on branch `builder-guard-keywords`
from 21cb9ba, not main: it changes the same two files, and 21cb9ba waits for girsa-operator's merge. It is rebased
on main once that lands. The log and the state file record it once `builder-lessons` is merged; until then the
messages are recorded here. Sent, live, at 46b378b: the plan's HANDOFF to girsa-verifier, the QUESTION to
girsa-architect, and a NOTE to girsa-operator of the path and the merge order (builder-push-forms first).
12:20: girsa-architect's ANSWER (under "The behaviour"), taken. Sent, live, at 2324302: a NOTE to girsa-verifier
of the revision.

## The case

The guard reads a command only where it finds the command's name in COMMAND POSITION: `BOUNDARY` (a line's start,
or after `; & | ( `` ` or `$(`), then `PREFIX` (assignments, `env`, `time`, `sudo`...), then `git`. Then `GIT`
takes `-C`/`-c` alone as git's options before the verb. Measured with `refusal` asked on text as a non-operator
role, the tests' placeholder project, a scratch script (nothing in the repository run). ALL 26 LET THROUGH:

- after a shell keyword: `then`, `do`, `else`, `elif`, `if`, `while`, `until`, `!` and `{`, in 10 forms
  (`if true; then git push origin main; fi`, `{ git push origin main; }`, `! git push origin main`, ...);
- behind git's own options: `--no-pager`, `-p`, `-P`, `--paginate`, `--git-dir=.git`, `--git-dir .git`,
  `--work-tree=.`, `--no-optional-locks`, `--literal-pathspecs`, `-C . --no-pager`, `/usr/bin/git --no-pager`,
  `env git --no-pager`;
- written quoted or escaped: `\git`, `"git"`, `'git'`, `then \git --no-pager` (the shell runs each as git; the mask
  turns `\git` into `\ it`, and `"git"` into quotes around spaces).

The same with git pointed at the main tree from a worktree: `git --git-dir=<main>/.git --work-tree=<main> reset
--hard` is LET THROUGH from `<main>-builder` (3 forms), because `_git_where` reads `-C` alone. `-C <main>` is
refused.

THE SIBLING (the lesson SWEEP THE SIBLINGS): the tmux check has the same gap. `tmux kill-server` after `then`,
`do`, `{` or `!`, and `\tmux` or `"tmux"`: 6 of 7 forms let through.

## The behaviour

- `BOUNDARY` gains the keywords, so that every check built on it reads them, in one place: git, `cd`, a script,
  `cp`, the tmux kill, `pkill`. After its separator, any run of `then`, `do`, `else`, `elif`, `if`, `while`,
  `until`, `!` or `{`, each followed by white space.
- `GIT`'s options before the verb: `-C`/`-c` with their argument; `--git-dir`, `--work-tree`, `--namespace`,
  `--config-env` and `--super-prefix` with an argument after a space; and any other word starting with `-`.
- `mask` gives back, at the same length, a command name written `\name`, `"name"` or `'name'`, for git, tmux,
  pkill, killall and cp. It does this only where the mask left that text as it was: a name inside another quote, a
  comment or a heredoc's body stays masked. `\git` becomes ` git`, and `"git"` becomes ` git `.
- `_git_where` becomes `_git_trees`: it returns git's work tree and its repository's tree, or one of them when
  they are the same. The work tree is `--work-tree` or `GIT_WORK_TREE=` before git. The repository's tree is
  `--git-dir` or `GIT_DIR=` before git, its parent if it ends in `.git`. Either one, when not named, is the
  directory git runs in (`-C`, else the last `cd`, else the cwd, as today). Each of the five callers asks whether
  ANY of the trees is the main tree (or a pin, a foreign tree, a project tree).

QUESTION to girsa-architect: is `--git-dir`/`--work-tree` as "where" inside item 1? ANSWERED (12:20; its
MISHMERET-GUARD-KEYWORDS-ARCHITECT.md, the first project's main 5814c995):
- In, but judged by BOTH trees: git uses the repository for HEAD, the index and the branch, and the work tree for
  the files. So `git --git-dir=<main>/.git --work-tree=. commit`, from a worktree, commits onto the main clone's
  branch. The plan's first rule judged that at `.` and let it through. Now a command is the main tree's if either
  tree is.
- `GIT_DIR=` / `GIT_WORK_TREE=` before git are the same two settings by another name, so they are read the same way.
- The keywords in `BOUNDARY`: yes. It has SEVEN users, not six (`GIT`, `CD`, `SCRIPT`, `CP`, `TMUX_KILL`, `PKILL`,
  `TMUX_SCRIPT`); the tests hold one keyword form of each. Its note, kept: `CD` reading `then cd <main>` moves
  "where" for what follows, even on a branch the shell does not take. That refuses more, never less.

## The measure (the prototype: the behaviour above in a scratch copy of the build at 21cb9ba, one probe)

- The 26 forms: ALL REFUSED. The where forms: all 3 refused, and `-C <main>` still refused.
- 14 that must run, NONE REFUSED: `echo then git push`, `echo "git" push`, `grep -n 'git' push.txt`, `echo \git
  push`, `git --no-pager log`, `if true; then git status; fi`, `ls {a,b}`, `echo '"git" push'`, `x="git push"`,
  `git --git-dir=.git log`, `! git diff --quiet`, `echo 'then git push origin main'`, `git --no-pager diff | cat`,
  `echo "a" git push`.
- tmux: the 7 forms and `then pkill tmux`, `'pkill' tmux`, all refused. NONE REFUSED of `tmux ls`, `then tmux ls`,
  `echo "tmux" kill-server`, `echo \tmux kill-server`, `grep -n 'tmux kill-server' f`.
- REVISED PROTOTYPE (12:20, both trees): 10 where forms, all let through today but the two by `-C`, ALL REFUSED.
  Among them are girsa-architect's `--git-dir=<main>/.git --work-tree=. commit`, `GIT_DIR=<main>/.git git commit`
  and `GIT_DIR=... GIT_WORK_TREE=... git reset --hard`. NONE REFUSED from a worktree of `--git-dir=.git log`,
  `commit -m x`, `reset --hard`, `GIT_DIR=.git git reset --hard` and `--work-tree=. reset --hard`. Each BOUNDARY
  user with a keyword before it, all let through today and all refused: `then cd <main>; ...; git commit`
  (`CD`), `then bash x.sh` (`SCRIPT`, a commit in it), `then cp -r <worktree>` (`CP`), `then bash k.sh` (`TMUX_SCRIPT`,
  a kill in it), and the tmux kill and `pkill` forms above. `tests/test_guard.py` in the copy: 30 passed.
- The whole suite in the first copy: 136 passed. The 3 that failed are the copy's own, not the change's: the copy has no
  `.claude/` (the lane check and Mishmeret's own config).

## Tests

- In `tests/test_guard.py`: the 26 forms (and the 3 where forms) refused as a non-operator role; the 14 let
  through; the tmux forms refused and the five fine ones let through.
- Each part shown red with it out, with the red script's baseline row and its `__pycache__` cleared before each
  run: each keyword, the `--` options with a spaced argument, the generic `-` option, the name restore's `\`, its
  quotes, the "only where unmasked" check (red on `echo '"git" push'`, refused), `--work-tree`, `--git-dir`,
  `GIT_WORK_TREE=`, `GIT_DIR=`, the `.git` parent, and "either tree" (one tree only: red on `--work-tree=.`).
- The tests also hold the ten where forms and five fine ones, and one keyword form for each of BOUNDARY's seven
  users.

## Files

- `mishmeret/role_guard.py`, `tests/test_guard.py`, this plan. One code commit, `land.py commit mishmeret-builder
  code --tests "tests/test_guard.py"`, then the suite.

## Not in this piece

- A `case` pattern's `)` before git (`case x in a) git push;; esac`): `)` is not a boundary today, and making it
  one would read `$(date) git` and the like as command position. Not changed.
- git written any other way (`g\it`, `gi''t`, `"$(which git)"`), behind a variable, an alias or another
  interpreter: as the docstring says, "a guard on the ordinary forms, not a sandbox".
- `coproc`, `time -p` and `exec -a name` before git: not measured.
- `export GIT_DIR=...` earlier in the command, or `GIT_DIR` set in the session's environment: not read. Only an
  assignment standing before git on the same command is.
