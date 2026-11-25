#!/usr/bin/env python3
"""The role guard: a PreToolUse hook on Bash, Edit, Write and NotebookEdit for every session in this repository
(`.claude/settings.json`) - the file tools since 2026-10-09 (FILE_TOOLS below).

The reviewer, 2026-10-01: "i want each role to have tools explicitly set so we can prevent certain activities", then
"yes go on your tool and role recomm." A role's tool list can take Bash away but cannot stop one command inside it,
so this stops what the roles plan gives to the operator alone (`.claude/agents/LANES.md`; START_HERE "Working in
parallel"):
  * `git push` - pushing is the operator's, on the reviewer's word; and the operator never pushes `--all`,
    `--mirror`, a force or a delete, in any form (PUSH_LONG below), nor to `old-origin` (the retired repository);
  * CHANGING THE MAIN TREE through git - it is the operator's alone; every other role works in its own worktree and
    lands with `git merge --ff-only`, the one change it may make there (girsa-verifier's probe, 2026-10-01: commit,
    update-ref, merge --no-ff, cherry-pick, revert and reset --hard had all passed the first version).
  * STOPPING THE LIVE TMUX SERVER - for every role, the operator too (below, TMUX_KILL).
  * LANDING AS ANOTHER ROLE through `tools/land.py`, which runs git where this hook cannot see it (below, LAND); and
    a `git commit` or a landing `git merge` in this repository run any other way (below, THROUGH_LAND).
  * A GIT VERB THAT IS NOT GIT'S OWN - an alias or an add-on - for every role (GIT_VERBS); and WRITING A GUARDED
    REPOSITORY'S CONFIG (`git config`, `git remote add`), or the global one, for every role, the operator too.

WHAT IT READS: the command, and the text of a shell script it runs (`bash x.sh`, `sh x.sh`, `./x.sh`, its path from
a variable the same command sets) - commits here are made by script. Only git in COMMAND POSITION counts (a line's
start, or after ; & | ( ` or $(, after the shell's keywords then, do, else, elif, if, while, until, ! and {, and after
a case arm's pattern; git also written `\\git`, "git" or 'git', behind its own options, and its verb quoted or
escaped), and never what stands inside quotes or a
heredoc's body: `grep "git push"` and a
commit message saying "never git push --all" are words, not commands (the builder's and the verifier's probes). It
is a guard on the ordinary forms, not a sandbox: `bash -c "..."`'s argument and git behind env, time, command, exec,
nice, sudo or xargs, or by a path, are read; git hidden in a variable, another interpreter or a deeper script is not.
Anything it cannot judge runs - but a verb it cannot read (`git $V` with V set elsewhere) is not git's own, and is refused.

WHO: the hook input's `agent_type` - the agent a session was started as (`claude --agent girsa-builder`). A SUBAGENT
(the input carries an `agent_id`) is no role, whatever its type (`role_of`; M07 item 2). A session started without one is guarded like any role other than the operator (the reviewer, 2026-10-04, "do a and b to prevent
future misuse": an external session told to work on a branch checked it out in the main clone, blocking every landing
and putting its page under the running servers) - the main clone and the corpus roots are the operator's alone; a one-off
session works in a worktree, where nothing is refused. Hooks in an agent file's own frontmatter
do not run for a session started as that agent (probed 2026-10-01, Claude Code 2.1.286: an inline --agents hook and
a settings hook ran, an agent file's did not) - hence the settings file.

usage:  python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/role_guard.py" [ROLE]   (ROLE overrides agent_type, for a probe)
Exit 2 refuses the command and says why; exit 0 lets it run. Needs only Python's standard library.
"""
import fnmatch
import json
import os
import re
import shlex
import subprocess
import sys

import config

# THE PROJECT'S OWN (its .claude/mishmeret.json, read by config.py): the operator, the roles' tmux session, the role
# whose code landing names a plan, and the `guard` table - the corpus roots' list and its fallback, the other trees
# whose main tree is the operator's, the remotes never pushed to, the checks whose status decides a commit
_CFG = config.load()
OPERATOR = _CFG["operator"]
LANDING = "land" in _CFG        # absent (config.PARTS): no landing tool - git commits and merges as it is
PLANNED = _CFG["land"]["planned"] if LANDING else None
GUARD = _CFG["guard"]
# ONE SHELL WORD in the masked text, its quoted parts kept as quotes around spaces (notes/PLAN-KNOWN-GAPS.md, item 1):
# with `\S+` a quoted word ended at its first space, so `git -C "." push`, `X="a b" git push` and the like matched
# nothing and every rule let them through. It ends at an unquoted separator, as the shell's does (else `R=x; S=y; git`
# read as one prefix and lost the assignments), and holds a $(...) or `...` (`X=$(pwd) git push`), and an escaped
# character, which the mask leaves as a backslash and a space (`git \push`: notes/PLAN-KNOWN-GAPS-SEVEN.md, item 17)
WORD = r"""(?:"[^"]*"|'[^']*'|\$\([^()]*\)|`[^`]*`|\\.|[^\s"';&|()<>`])+"""
# COMMAND POSITION (M07 item 1, notes/PLAN-GUARD-KEYWORDS.md): after a separator, and after any run of the shell's
# keywords - `if true; then git push; fi`, `{ git push; }`, `! git push` had gone through every check built on it
BASE_BOUNDARY = r"(?:^|[;&|(`]|\$\()\s*"
KEYWORDS = ("if", "!", "then", "else", "elif", "do", "while", "until", "{", "coproc")
KEYWORD = r"(?:(?:" + "|".join(KEYWORDS) + r")\s+)"
# A CASE ARM (notes/PLAN-KNOWN-GAPS-SEVEN.md, item 5): after `in`, `;;`, `;&` or `;;&`, a pattern - its words, `|`
# between them - and its `)`. `case x in x) git push origin main;; esac` had gone through every check built on BOUNDARY;
# an arm may not run, so a cd in one is read as a cd after a keyword (KEYWORD_CD)
CASE_PATTERN = r"\(?\s*" + WORD + r"(?:\s*\|\s*" + WORD + r")*\s*\)"
CASE_ARM = r"(?:\bin|;;&?|;&)\s+" + CASE_PATTERN + r"\s*"
# A FUNCTION'S BODY (found at notes/PLAN-PROTECTED-REFS.md's build, in girsa-verifier's LOW 1 case `f(){ git tag -f
# "$@"; }`): after a definition's `()` or `function NAME`, before its `{` or `(`. `f(){ git push --force origin main;
# }; f` had gone through every check built on BOUNDARY; a body may not run, so a cd in one is read as after a keyword
FUNC = r"(?:\b(?:function|coproc)\s+[\w.:-]+\s*(?:\(\s*\)\s*)?|\(\s*\)\s*)(?=[{(])"     # coproc NAME { ... } too
BOUNDARY = r"(?:" + BASE_BOUNDARY + "|" + CASE_ARM + "|" + FUNC + ")" + KEYWORD + "*"
# the names the guard reads in command position: `mask` gives each back written `\name`, `"name"` or `'name'` (a
# path inside the quotes too), as the shell runs it
NAMES = ("git", "tmux", "pkill", "killall", "cp", "cd", "bash", "sh", "zsh", "dash", "ksh", "env", "time", "command",
         "exec", "nice", "sudo", "xargs", "land.py")
_NAME = "(?:" + "|".join(NAMES) + ")"
NAME_WORD = re.compile(r"""(?<![\w"'\\])(?:\\""" + _NAME + r"""|(["'])(?:[\w.~/-]*/)?""" + _NAME + r"""\1)(?![\w"'-])""")
SHELL = r"""(?:\\|["'])?(?:\S*/)?(?:bash|sh|zsh|dash|ksh)["']?"""     # for the patterns that read the original text
# what may stand before git and still run it (girsa-verifier's probe of 78b8088): assignments, and the prefixes env,
# time, command, exec, nice, sudo and xargs with their options; and git by a path (/usr/bin/git)
PREFIX = (r"(?:(?:[A-Za-z_]\w*=(?:" + WORD + r")?|env(?:\s+-" + WORD + r")*|time|command|exec"
          r"|nice(?:\s+-n\s*" + WORD + r"|\s+-\d+)?|sudo(?:\s+-[A-Za-z]+(?:\s+(?:[\w.-]+|\"[^\"]*\"|'[^']*'))?)*"
          r"|xargs(?:\s+-" + WORD + r"(?:\s+" + WORD + r")?)*)\s+)*")
# git's own options before the verb: those with a spaced argument, then any other word starting with `-`. THE VERB IS
# ONE WORD, read as the shell reads it (notes/PLAN-KNOWN-GAPS-SEVEN.md, item 17): as `[a-z][\w-]*` a quoted or escaped
# one (`git "push"`, `git \push`) matched nothing and every rule let it through; it is on git's line, not the next
GIT = re.compile(BOUNDARY + PREFIX + r"(?:\S*/)?git"
                 r"((?:\s+-[Cc]\s+" + WORD + r"|\s+--(?:git-dir|work-tree|namespace|config-env|attr-source)\s+" + WORD
                 + r"|\s+-" + WORD + r")*)[ \t]+(?!-)(" + WORD + r")([^;&|\n]*)", re.M)
SHELL_C = re.compile(r"(?<![\w-])" + SHELL + r"\s+(?:-\w+\s+)*-c\s+(\"(?:[^\"\\]|\\.)*\"|'[^']*')"
                     r"|(?<![\w-])" + SHELL + r"(?:\s+-\w+)*\s*<<<\s*(\"(?:[^\"\\]|\\.)*\"|'[^']*')"
                     # eval's words and trap's string are a command too (girsa-verifier's LOW 1 on 110415f: `eval "git
                     # push --force origin main"` and `trap 'git reset --hard' EXIT` passed every rule)
                     r"|(?<![\w-])eval\s+((?:[^;&|\n\"']|\"(?:[^\"\\]|\\.)*\"|'[^']*')+)"
                     r"|(?<![\w-])trap\s+(?:--\s+)?(\"(?:[^\"\\]|\\.)*\"|'[^']*'|[^\s;&|]+)")
# a heredoc that a shell reads as its script (girsa-verifier, 2026-10-11): `bash <<'EOF'`, `sh -s <<EOF`, `. /dev/stdin
# <<EOF`, or `cat <<EOF | bash` - its body is commands, not words
STDIN_SHELL = re.compile(r"^\s*(?:[A-Za-z_]\w*=(?:" + WORD + r")?\s+|env(?:\s+-" + WORD + r")*\s+|exec\s+|command\s+)*"
                         r"(?:" + SHELL + r"(?:\s+-\w+)*|(?:source|\.)\s+/dev/stdin)\s*$")
PIPED_TO_SHELL = re.compile(r"\|\s*" + SHELL + r"(?:\s+-\w+)*\s*(?:$|[;&|)])")


def shell_arg(m):
    """The command text of a SHELL_C match: `bash -c '...'`'s argument, `bash <<< '...'`'s string, eval's words as the
    shell joins them, or trap's command."""
    if m.group(3) is not None:
        return " ".join(_split(m.group(3)))
    return _unquote(m.group(1) or m.group(2) or m.group(4))


def shell_c(command, masked):
    """The SHELL_C matches standing in command text: not in a heredoc body, a quote or a comment the mask blanked (a
    probe's own heredoc quoting `bash -c '...'` is words - 2026-10-13, the check-status guard refused the operator's
    probe of it)."""
    lead = lambda m: m.start() + (command[m.start()] in "\\\"'")       # the name's first letter: a quote before it
    return [m for m in SHELL_C.finditer(command) if masked[lead(m)] == command[lead(m)]]    # is given back blank


# A cd after a keyword may stand in a branch that does not run (girsa-verifier's MEDIUM 1 on 2324302: `if false; then
# cd <worktree>; fi; git reset --hard` from the main tree had lost its refusal): it is not where the next command runs
# (CD, on today's boundary), only where git may (KEYWORD_CD, read by _git_trees beside it). The path (found while
# building M07 item 1, each let through from a worktree into the main tree): it ends at a separator (`cd <main>; ls;
# git reset --hard` had been judged at `<main>;`), it may be quoted (in the masked text a quoted path had read as a
# lone quote), it comes after cd's options (`cd -P <main>`, `cd -- <main>`), and `pushd` goes there too; one word of
# quoted and plain parts (`cd "$R"/book`: item 1 of notes/PLAN-KNOWN-GAPS.md). With no path, and `popd` (item 4 of
# notes/PLAN-KNOWN-GAPS-SEVEN.md: a bare cd and a popd had not been read, `cd -` had been a folder named "-")
CD_TO = r"""(cd|pushd|popd)(?![\w.-])(?:\s+(?:-[LPe@]+|--))*(?:\s+((?:"[^"]*"|'[^']*'|[^\s;&|)`"'<>])+))?"""
CD = re.compile(BASE_BOUNDARY + CD_TO, re.M)
KEYWORD_CD = re.compile(r"(?:" + BASE_BOUNDARY + KEYWORD + "+|(?:" + CASE_ARM + "|" + FUNC + ")" + KEYWORD + "*)" + CD_TO,
                        re.M)
SCRIPT = re.compile(BOUNDARY + r"(?:(?:bash|sh|zsh)\s+(?:-\w+\s+)*)?(\S+\.sh)(?![\w.])", re.M)
ASSIGN = re.compile(r"(?<![\w$])([A-Za-z_]\w*)=(\"[^\"]*\"|'[^']*'|[^\s;&|]+)")
HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_]\w*)\1")
# what a role other than the operator may not run against the main tree, and the forms of them that change nothing
# tools/land.py (the landing script, Board #85 A step 2) runs git add, commit and merge as Python subprocesses, which
# this hook never sees, and takes the role as its second word (`land.py commit ROLE ...`, `land.py land ROLE ...`).
# The reviewer, 2026-10-26, Board #86 A (girsa-verifier's MEDIUM 1 on the script's plan): refused - a land.py commit or
# land naming a role other than the session's own; a command that sets MISHMERET_ROLE or CLAUDE_CODE_AGENT, the
# variables land.py reads for the session's role (config.session_role); and land.py commit in the main tree for any
# session but the operator's.
LAND = re.compile(r"(?<![\w./-])(?:\S*/)?land\.py(?![\w.])\s+([a-z][\w-]*)([^;&|\n]*)")
LAND_AS_ROLE = ("commit", "land")
SETS_AGENT = re.compile(r"(?<![\w$])(CLAUDE_CODE_AGENT|MISHMERET_ROLE)=")     # config.ROLE_VARS, both names
# THE SCRIPT IS THE ONLY WAY IN (the reviewer, 2026-10-26: "add the extra guard"; the landing plan's section 6): in this
# repository - its main clone or a linked worktree, not a copy and not a corpus root - `git commit` is refused for every
# role, and `git merge` in the main tree (a landing) too, but `git merge --abort`: land.py commit and land.py land do
# both, with the lane check, the gate and the hold. A session with no role keeps its commits in a worktree (it cannot
# name a role to land.py).
THROUGH_LAND = {"commit": "`land.py commit ROLE notes|code -F MESSAGE NAME...`",
                "merge": f"`land.py land ROLE notes|code` ({PLANNED}'s code: `--plan PLAN`), from your worktree"
                } if LANDING else {}
# ...and the other git commands that make a commit on main, which CHANGES_MAIN already refuses every other role there:
# refused to the operator too in this repository's main tree (girsa-verifier's LOW on 23be3451; the reviewer, Board #87
# A), but each one's --abort.
OPERATOR_THROUGH_LAND = {"revert", "cherry-pick", "am", "rebase", "commit-tree", "update-ref"} if LANDING else set()
# GIT'S COMMANDS, EACH PLACED (notes/PLAN-GIT-CLASSIFICATION.md; the first project's Board #302 A): every name of git's
# own list in one of four sets, so the next git's command fails a test until it is placed. Only CHANGES_MAIN decides a
# refusal (where `reset --hard` is refused); the two last sets are labels. CHANGES_MAIN: what writes the checked-out
# branch, the index or the files of the tree it runs in - the guard's first 18; #302's eight (history, replay,
# symbolic-ref, read-tree, update-index, checkout-index, sparse-checkout, filter-branch), which had passed in the main
# tree; and 27 more the classification found (each in the plan).
CHANGES_MAIN = frozenset("""
commit update-ref cherry-pick revert rebase am reset stash checkout switch restore clean rm mv add apply pull merge
history replay symbolic-ref read-tree update-index checkout-index sparse-checkout filter-branch
stage bisect merge-file merge-index merge-one-file merge-octopus merge-ours merge-recursive merge-recursive-ours
merge-recursive-theirs merge-resolve merge-subtree mergetool checkout--worker rerere submodule submodule--helper subtree
fast-import p4 cvsimport archimport quiltimport cvsexportcommit cvsserver receive-pack refs
""".split())
# a rule of their own: push (the operator's), config and remote (item 6b of notes/PLAN-KNOWN-GAPS-SEVEN.md); and,
# refused for every role, a push by a verb other than `git push`, and a verb running git commands this guard cannot read
OWN_RULES = frozenset({"push", "config", "remote", "send-pack", "http-push", "for-each-repo"})
REFUSED_VERBS = {"send-pack": "pushes without `git push`, whose forms the push rule reads - the operator pushes with "
                              "`git push origin <branch>`",
                 "http-push": "pushes without `git push`, whose forms the push rule reads - the operator pushes with "
                              "`git push origin <branch>`",
                 "for-each-repo": "runs a git command in each repository a config key lists, a command this guard "
                                  "cannot read - run it in each repository by name"}
# no checked-out branch, index or tree - but the shared repository's refs, tags, objects and config are in this one
# (girsa-architect's caution on #302; the reviewer's Board #304 for a later piece)
WRITES_ELSEWHERE = frozenset("""
archive backfill branch bugreport bundle clone commit-graph commit-tree credential credential-cache
credential-cache--daemon credential-netrc credential-osxkeychain credential-store daemon diagnose difftool
difftool--helper fetch fetch-pack format-patch fsmonitor--daemon gc hash-object hook http-backend http-fetch imap-send
index-pack init init-db instaweb interpret-trailers mailsplit maintenance merge-tree mktag mktree multi-pack-index notes
pack-objects pack-refs prune prune-packed reflog remote-ext remote-fd remote-ftp remote-ftps remote-http remote-https
repack replace send-email shell tag unpack-file unpack-objects update-server-info upload-archive upload-archive--writer
upload-pack web--browse worktree write-tree
""".split())
READS = frozenset("""
annotate blame cat-file check-attr check-ignore check-mailmap check-ref-format cherry column count-objects describe diff
diff-files diff-index diff-pairs diff-tree fast-export fmt-merge-msg for-each-ref format-rev fsck fsck-objects
get-tar-commit-id grep help jump last-modified log ls-files ls-remote ls-tree mailinfo merge-base name-rev
pack-redundant patch-id pickaxe range-diff repo request-pull rev-list rev-parse sh-i18n--envsubst shortlog show
show-branch show-index show-ref status stripspace url-parse var verify-commit verify-pack verify-tag version whatchanged
""".split())
# a form of a CHANGES_MAIN verb that changes nothing there (`_leaves_it`)
LEAVES_IT = {"merge": ("--ff-only",), "stash": ("list", "show"), "apply": ("--check", "--stat", "--numstat"),
             "history": ("--dry-run",), "replay": ("--ref-action=print",), "merge-file": ("-p", "--stdout"),
             "read-tree": ("-n", "--dry-run"),
             "sparse-checkout": ("list", "check-rules"), "bisect": ("log", "visualize", "view", "help"),
             "submodule": ("status", "summary"), "refs": ("list", "verify")}
FIRST_WORD = ("stash", "sparse-checkout", "bisect", "submodule", "refs")      # LEAVES_IT's form there is the subcommand
# THE OPERATOR'S PUSH NEVER FORCES OR DELETES, in any form (the builder's review, M07 item 4: `+main`, `-uf`, `:main`
# and `--delete` had gone through; girsa-verifier on its plan: a quoted `"-f"` and a prefix `--del` too). Git takes a
# unique prefix of a long option as the option (gitcli(7)), so a prefix of one of these is refused, and `--a`,
# `--d`, `--p` with it - git takes those as ambiguous or as a force. `--force` itself is a prefix of the two below.
PUSH_LONG = ("--all", "--branches", "--mirror", "--delete", "--prune", "--force-with-lease", "--force-if-includes")


def _long(word, options):
    """True when `word` is a long option of `options`, or a prefix of one, as git takes a unique prefix (gitcli(7))."""
    opt = word.split("=", 1)[0]
    return len(opt) > 2 and opt[:2] == "--" and any(o.startswith(opt) for o in options)


def push_forces(word):
    """True when `word`, as the shell gives it to git push, forces or deletes: a `+` or `:` refspec, a long option of
    PUSH_LONG or a prefix of one, or a short cluster holding f or d (copy_refusal's reading; after an `o`, the rest is
    `-o`'s argument)."""
    return (word.startswith(("+", ":")) or _long(word, PUSH_LONG)
            or (word[:1] == "-" and word[1:2] != "-" and bool({"f", "d"} & set(word[1:].split("o", 1)[0]))))


# GIT'S OWN COMMANDS (notes/PLAN-KNOWN-GAPS-SEVEN.md, item 6a; girsa-architect's B): `git --list-cmds=main` on git
# 2.56.1, the four sets above. A verb not among them is refused for every role, in every tree - an alias (`git -c
# alias.p='push --force' p`) or an add-on on PATH runs what this guard cannot read. A test fails when the running git
# lists a name not here, and when a name is in two sets.
GIT_VERBS = CHANGES_MAIN | OWN_RULES | WRITES_ELSEWHERE | READS


def _own_index(value):
    """True when a GIT_INDEX_FILE value names a tree's own index (`.git/index`, a worktree's under `.git/worktrees/`,
    `$GIT_DIR/index`) - no temporary one (girsa-verifier's LOW 1 on notes/PLAN-GIT-CLASSIFICATION.md) - or may: a
    command substitution is unknown, so taken as the tree's own, but a `$(mktemp ...)` (its LOW 1 on 6575743:
    `$(git rev-parse --git-dir)/index` is .git/index; the record's 5 substitutions are all mktemp's)."""
    if "$(" in value or "`" in value:
        return not re.fullmatch(r"(?:\$\(\s*mktemp\b[^()`]*\)|`\s*mktemp\b[^`]*`)(?:/[^$`]*)?", value.strip())
    return "GIT_DIR" in value or (os.path.basename(value.rstrip("/")) == "index" and ".git" in value.split("/"))


def _temp_index(command, masked, m):
    """True when the GIT match `m` runs on a temporary index: GIT_INDEX_FILE set on git's own line, or exported
    earlier in the command and not unset since (`export GIT_INDEX_FILE=<scratch>; git read-tree $P; ...; unset
    GIT_INDEX_FILE` - the record's form), and naming no tree's own index."""
    setting = r"(?<![\w$])GIT_INDEX_FILE=(" + WORD + ")"
    on_line = list(re.finditer(setting, masked[m.start():m.start(1)]))
    if on_line:
        at = m.start() + on_line[-1].start(1)
    else:
        earlier = list(re.finditer(setting, masked[:m.start()]))
        unset = [u.end() for u in re.finditer(r"(?<![\w-])unset\s+(?:-v\s+)?GIT_INDEX_FILE(?!\w)", masked[:m.start()])]
        if not earlier or earlier[-1].end() < max(unset, default=-1):
            return False
        at = earlier[-1].start(1)
    end = re.match(WORD, masked[at:])
    return not _own_index(_word(command[at:at + (end.end() if end else 0)]))


def _leaves_it(verb, rest, command, masked, m, trees):
    """True when this form of a CHANGES_MAIN verb changes no branch, index or file of the tree it runs in: help, the
    forms LEAVES_IT names, and the few below. `rest`: the words after the verb, as masked; `trees`: the ones it may
    use (`_git_trees`)."""
    rest = [w for w in rest if not re.match(r"\d*[<>]", w)]            # a redirection is no word of git's
    if rest[:1] and rest[0] in ("-h", "--help"):
        return True
    if verb in FIRST_WORD:
        return bool(rest[:1]) and rest[0] in LEAVES_IT[verb]
    # -u writes the work tree, whatever index it writes (girsa-verifier's MEDIUM 1 on notes/PLAN-GIT-CLASSIFICATION.md)
    if verb == "read-tree" and any(w[:1] == "-" and w[1:2] != "-" and "u" in w for w in rest):
        return False
    if verb in ("read-tree", "update-index") and _temp_index(command, masked, m):
        return True                         # a temporary index: the tree's own is untouched
    if verb == "read-tree" and any(w.startswith("--index-output=") for w in rest):
        return True
    if verb == "update-index" and rest and all(w in ("--refresh", "--really-refresh", "-q") for w in rest):
        return True                         # the stat cache only, as `git status` refreshes it
    if verb == "symbolic-ref":
        return not any(w in ("-d", "--delete") for w in rest) and len([w for w in rest if w[:1] != "-"]) <= 1
    if verb == "checkout-index":            # into a folder outside the tree; a relative prefix is a string before
        prefixes = [w[len("--prefix="):] for w in rest if w.startswith("--prefix=")]   # each path (its MEDIUM 1)
        inside = lambda p: any((os.path.normpath(p) + "/").startswith(os.path.normpath(t) + "/") for t in trees)
        return "--temp" in rest or bool(prefixes) and all(os.path.isabs(p) and not inside(p) for p in prefixes)
    return any(w in rest for w in LEAVES_IT.get(verb, ()))
# THE REPOSITORY'S CONFIG IS WRITTEN BY NO ROLE in a guarded tree (item 6b; girsa-architect's B): the main clone and
# every worktree share it, and a key there changes what every role's git does - an alias, `remote.<name>.mirror`, a
# push refspec, a URL - while the file tools are refused that same file. `git config` in any form but these reads, and
# `git remote`'s writes; the options whose value is the next word, so it is not read as a key
CONFIG_READS = ("--get", "--get-all", "--get-regexp", "--get-urlmatch", "--get-color", "--get-colorbool", "--list")
CONFIG_WRITES = ("--add", "--unset", "--unset-all", "--replace-all", "--rename-section", "--remove-section", "--edit")
CONFIG_VALUED = ("-f", "--file", "--blob", "--type", "--default", "--comment", "--value", "--url")
REMOTE_WRITES = ("add", "set-url", "rename", "remove", "rm", "set-branches")
# ...and on the operator's push, no config from its own line (item 6c): these keys choose where a push goes or what it
# sends (`-c remote.origin.mirror=true`, `-c push.default=matching`, a bare push's `branch.<name>.pushRemote`)
PUSH_CONFIG_KEYS = ("remote.", "url.", "alias.", "branch.", "push.")
# ...and in a guarded repository, for every role, no key that switches off or moves git's hooks, nor another config
# before git (GIT_CONFIG..., HOME=, XDG_CONFIG_HOME=: a global config elsewhere) - the reference-transaction hook
# guards the refs whatever writes them (notes/PLAN-REF-HOOK.md; girsa-architect's measure: `-c core.hooksPath=/dev/null`
# and GIT_CONFIG_COUNT passed it)
HOOK_KEYS = ("core.hookspath", "include.", "includeif.")
OTHER_CONFIG = re.compile(r"(?<![\w$])(GIT_CONFIG\w*|HOME|XDG_CONFIG_HOME)=")
# ...where it reaches git: on git's own prefix (OTHER_CONFIG there), an `export`, or an assignment that is a statement
# of its own (HOME is exported already) - not one that prefixes another command (rule 45: `HOME=<x> bash -c '...'; git
# show` by girsa-verifier had been refused)
_SETS = r"(?:\s+[A-Za-z_]\w*=(?:" + WORD + r")?)*"
OTHER_CONFIG_SET = (re.compile(r"(?<![\w$-])export(?:\s+-\w+)*(?:\s+" + WORD + r")*?\s+" + OTHER_CONFIG.pattern),
                    re.compile(r"(?:^|[;&|(\n])\s*(?:[A-Za-z_]\w*=(?:" + WORD + r")?\s+)*" + OTHER_CONFIG.pattern
                               + r"(?:" + WORD + r")?" + _SETS + r"\s*(?=[;&|)\n]|$)"))


def _config_writes(verb, words):
    """True when `git config` or `git remote` with these words (as the shell gives them) writes the config: a write
    option or subcommand, or a key with a value; `remote` add, set-url, rename, remove or set-branches."""
    words = [w for w in words if not re.match(r"\d*[<>]", w)]          # a redirection is no word of git's
    if verb == "remote":
        sub = [w for w in words if w not in ("-v", "--verbose")][:1]
        return bool(sub) and sub[0] in REMOTE_WRITES
    plain, i = [], 0
    while i < len(words):
        w = words[i]
        if w == "-e" or _long(w, CONFIG_WRITES):
            return True
        if w == "-l" or _long(w, CONFIG_READS):
            return False
        if w in CONFIG_VALUED:
            i += 2
            continue
        if not w.startswith("-"):
            plain.append(w)
        i += 1
    if plain[:1] and plain[0] in ("get", "list"):
        return False
    return (bool(plain[:1]) and plain[0] in ("set", "unset", "rename-section", "remove-section", "edit")) or len(plain) > 1


def _push_config(lead, opts, keys=PUSH_CONFIG_KEYS):
    """The config git's line sets that `keys` name (the operator's push: PUSH_CONFIG_KEYS): `-c KEY=...` or
    `--config-env KEY=...` among git's options (as the shell gives them), or a GIT_CONFIG... assignment in `lead`."""
    found = re.findall(r"(?<![\w$])GIT_CONFIG\w*=", lead)
    words = _split(opts)
    for i, w in enumerate(words):
        key = (words[i + 1] if i + 1 < len(words) else "") if w in ("-c", "--config-env") else \
            w[2:] if w.startswith("-c") else w[13:] if w.startswith("--config-env=") else ""
        if key.lower().startswith(keys):
            found.append(f"{w} {key}" if w in ("-c", "--config-env") else w)
    return found


def mask(text, runs=True):
    """`text` with what stands inside quotes and every heredoc body turned to spaces, its length kept - so a span
    found in the mask reads the same span of the original. One pass, the quotes and the heredocs together: a heredoc
    opened outside quotes masks its body from the next line to the line that is its tag alone. Until 2026-10-11 the
    tag was looked for in the text already masked, where a quoted tag (`<<'EOF'`, the form every role writes) had
    become spaces - so such a body was read as commands (found by the tmux check's first probe). A comment - `#` at a
    word's start, outside quotes - is masked to its line's end: an apostrophe in a script's comment ("the role's")
    had opened a quote that hid or showed the lines after it, by the count of apostrophes above them; a `#` after an
    escaped character (`a\\ #b`) is not a word's start. A heredoc that a shell reads as its script (STDIN_SHELL,
    PIPED_TO_SHELL) is NOT masked: its body is commands (girsa-verifier's MEDIUM on bba1587e). A "$(...)" or "`...`"
    inside "..." is commands too (item 2 of notes/PLAN-KNOWN-GAPS.md) - but with `runs=False`, for the rules that read
    a pipeline's status, its body is masked once it is closed: a pipe in a check's argument (`pytest -k "$(echo $t |
    sed x)"`) is not the check's pipe (the guard run on the transcripts, girsa-verifier's rule 45)."""
    out, quote, i, n, pending, escaped = list(text), None, 0, len(text), [], -1
    subs = []           # each "$(...)" or "`...`" opened inside "...": [its closer, its open parentheses]
    while i < n:
        c = text[i]
        if quote:
            # AN ESCAPED CHARACTER IS NOT THE CLOSING QUOTE (girsa-verifier, 2026-11-10, HIGH): the quote closed at the
            # first quote character, escaped or not, so the string's real closing quote OPENED one, and the rest of the
            # command - or of a script - was masked: `echo "a \" b"; git push origin main` was let through. In "..."
            # and in $'...' a backslash and the character after it are words; in '...' a backslash is itself.
            if c == "\\" and quote != "'" and i + 1 < n:
                out[i] = " "
                if text[i + 1] != "\n":
                    out[i + 1] = " "
                i += 2
                continue
            # A COMMAND INSIDE "$(...)" OR "`...`" RUNS (notes/PLAN-KNOWN-GAPS.md, item 2): `echo "$(git push origin
            # main)"` had been masked as words. Its body is read as commands to its own `)` or backtick, and the "..."
            # goes on after it; `$((` is arithmetic, still words
            if quote == '"' and (c == "`" or (text.startswith("$(", i) and not text.startswith("$((", i))):
                subs.append(["`" if c == "`" else ")", 0, i])
                quote = None
                i += 1 if c == "`" else 2
                continue
            if c == quote[-1]:
                quote = None
            elif c != "\n":
                out[i] = " "
        elif subs and (subs[-1][0] == c == "`" or (subs[-1][0] == ")" and c == ")" and not subs[-1][1])):
            start = subs.pop()[2]
            quote = '"'
            if not runs and not subs:           # the outermost one closed: its body words, for the pipe rules
                for k in range(start, i + 1):
                    if text[k] != "\n":
                        out[k] = " "
        elif subs and subs[-1][0] == ")" and c in "()":
            subs[-1][1] += 1 if c == "(" else -1
        elif c == "#" and (i == 0 or (text[i - 1] in " \t\n;&|()" and i - 1 != escaped)):
            while i < n and text[i] != "\n":
                out[i] = " "
                i += 1
            continue
        elif c in "'\"":
            # $'...' is a kind of its own: a backslash escapes in it, as it never does in '...'. THE `$` THAT OPENS IT
            # IS A LONE ONE (girsa-verifier's MEDIUM on 0cff45c): `$$` is the shell's own id and the quote after it a
            # plain '...' - read as $'...', `echo $$'a\'; git push origin main` lost its refusal; and an escaped `$`
            # opens nothing. So the dollars straight before the quote are counted, an escaped one not: an odd run
            # ends in a lone `$`.
            j = i
            while j and text[j - 1] == "$" and j - 1 != escaped:
                j -= 1
            quote = "$'" if c == "'" and (i - j) % 2 else c
        elif c == "\\" and i + 1 < n:
            out[i + 1] = " "
            if text[i + 1] == "\n":     # a line continuation is the space the shell makes of it (item 17's sibling:
                out[i] = " "            # `git \<newline> push` had hidden the verb from every rule)
            escaped = i + 1
            i += 1
        elif c == "<" and text.startswith("<<", i) and not text.startswith("<<<", i):
            m = HEREDOC.match(text, i)
            if m:
                done = "".join(out[:i])
                start = max(done.rfind(ch) for ch in ";&|(\n") + 1
                eol = text.find("\n", m.end())
                if not (STDIN_SHELL.match(done[start:]) or STDIN_SHELL.match(text[start:i])     # `"bash" <<EOF` too
                        or PIPED_TO_SHELL.search(text[m.end():n if eol < 0 else eol])):
                    pending.append(m.group(2))
                i = m.end()
                continue
        elif c == "\n" and pending:         # the bodies of the heredocs opened on this line, in order
            j = i + 1
            for tag in pending:
                end = re.compile(r"^\s*%s\s*$" % re.escape(tag), re.M).search(text, j)
                stop = end.start() if end else n
                for k in range(j, stop):
                    if text[k] != "\n":
                        out[k] = " "
                j = end.end() if end else n
            pending, i = [], j
            continue
        i += 1
    for q in NAME_WORD.finditer(text):              # a name the shell runs, written quoted or escaped: given back
        if out[q.start()] != " ":                   # unless inside a quote, a comment or a heredoc's body
            out[q.start():q.end()] = re.sub(r"[\\\"']", " ", q.group(0))
    return "".join(out)


def _unquote(s):
    return s[1:-1] if len(s) > 1 and s[0] == s[-1] and s[0] in "\"'" else s


def _word(s):
    """A shell word as the shell reads it, its quotes taken off whatever their mix (`"$X"/sub`, `'a b'`)."""
    try:
        parts = shlex.split(s)
    except ValueError:
        return _unquote(s)
    return parts[0] if len(parts) == 1 else _unquote(s)


def _split(s):
    """`s`'s words as the shell gives them, quotes taken off; split at spaces when it leaves a quote open."""
    try:
        return shlex.split(s)
    except ValueError:
        return s.split()


def _expand(path, text):
    """`path` with ~ and the shell variables the same command sets before it (`S=...; bash $S/x.sh`), then the
    environment's. UNTIL IT STOPS CHANGING (girsa-verifier's MEDIUM 1 on notes/PLAN-KNOWN-GAPS.md): a value naming an
    earlier variable (`R=<main>; S="$R"; cd "$S"`) had stayed a name, and the cd was let through."""
    assigned = ASSIGN.findall(text)
    for _ in range(8):                      # each round follows one more link; a loop of names stops here
        was = path
        for name, value in assigned:
            path = path.replace("${%s}" % name, _unquote(value)).replace("$" + name, _unquote(value))
        if path == was:
            break
    return os.path.expanduser(os.path.expandvars(path))


# The trees only the operator changes through git: THIS repository's main clone - the project's root, from its config
# (config.root()) - and each book's corpus root, read from the one list of homes (Girsa's pipeline/book_homes.json)
# (a new book's root is one line there; the reviewer's go, 2026-10-23, on girsa-builder's REQUEST). Not a linked
# worktree of either, and not a copy (`cp -c -R`, every rehearsal), which carries its own .git. The reviewer,
# 2026-10-02: "guard - (a)" - girsa-verifier's finding: the first version took any tree whose git dir is its common dir
# for the main tree, which is every repository that is not a linked worktree, so a role could not reset its own
# rehearsal copy with git.
HOOK_REPO = config.root()
# When the list cannot be read, the root it held before it was the source - the guard never opens wider for a
# broken file.
FALLBACK_CORPUS_ROOTS = tuple(GUARD.get("fallback_roots", ()))
# THE OTHER TREES WHOSE MAIN TREE IS THE OPERATOR'S (design-study/STEP-MISHMERET-MOVE-PLAN.md in Girsa, step 4): the
# Mishmeret checkout - its worktrees anyone's, its pins (`<tree>/.pins/<sha>`) no one's (`pin_of`)
TREES = tuple(GUARD.get("trees", ()))
# REPOSITORIES NO ROLE OF THIS PROJECT CHANGES, IN ANY TREE (Board #153 B: "the guard refuses every tree of Girsa,
# worktrees included"): their main clone and every linked worktree - one git common dir - to every role, the operator
# too. A copy (`cp -c -R`, its own .git) is another repository and is not refused; a read never is.
FOREIGN = tuple(GUARD.get("foreign", ()))     # absent (config.OPTIONAL): none


def corpus_roots(path=None):
    """Every home's root in the project's list of homes (`guard.homes`, Girsa's pipeline/book_homes.json; this
    repository's own among them, which HOOK_REPO also names).
    FALLBACK_CORPUS_ROOTS is added beside the well-formed roots when any home has no root, and is all there is when
    the file is missing, unreadable or not the list's shape - a broken entry never drops a good one (girsa-verifier's
    LOW on 71175b1d)."""
    if not path and "homes" not in GUARD:       # the project keeps no list of homes (config.OPTIONAL)
        return FALLBACK_CORPUS_ROOTS
    try:
        with open(path or config.expand(GUARD["homes"]), encoding="utf-8") as fh:
            homes = json.load(fh)["homes"]
        roots = tuple(h["root"] for h in homes if isinstance(h, dict) and isinstance(h.get("root"), str) and h["root"])
        whole = len(roots) == len(homes)
    except (OSError, ValueError, KeyError, TypeError):
        return FALLBACK_CORPUS_ROOTS
    return roots if roots and whole else roots + tuple(r for r in FALLBACK_CORPUS_ROOTS if r not in roots)


CORPUS_ROOTS = corpus_roots()


def _git_dirs(path):
    """(git dir, common dir) of the repository `path` is in, both resolved; None when it is not in one."""
    try:
        out = subprocess.run(["git", "-C", path, "rev-parse", "--path-format=absolute", "--git-dir",
                              "--git-common-dir"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    lines = out.stdout.splitlines()
    if out.returncode != 0 or len(lines) != 2:
        return None
    return tuple(os.path.realpath(line) for line in lines)


def guarded_git_dirs():
    """The git dirs of the trees in the comment above: this repository's, and each corpus root's and TREES' that
    exists."""
    found = (_git_dirs(root) for root in (HOOK_REPO,) + tuple(os.path.expanduser(r) for r in CORPUS_ROOTS + TREES))
    return {dirs[1] for dirs in found if dirs}


def pin_of(path):
    """The pin `path` is in - `<tree>/.pins/<sha>` of one of TREES - or None. By path alone, no git (the shim finds a
    pin the same way): a pin is the code every hook runs, so nothing is written into one, by any role."""
    real = os.path.realpath(os.path.expanduser(path))
    for tree in TREES:
        pins = os.path.join(os.path.realpath(os.path.expanduser(tree)), ".pins") + os.sep
        if real.startswith(pins) and real[len(pins):]:
            return pins + real[len(pins):].split(os.sep)[0]
    return None


def pin_refusal(pin):
    return (f"refused by the role guard: {pin} is a pinned Mishmeret tree - every hook runs its code, so no role, the "
            "operator too, changes it: a change is a new Mishmeret commit, its own pin made from it, and the "
            "project's `mishmeret_commit` set to that sha")


def foreign_tree(path):
    """The entry of FOREIGN whose repository `path` is in - its main clone or any linked worktree - or None."""
    dirs = _git_dirs(path)
    for repo in FOREIGN if dirs else ():
        theirs = _git_dirs(os.path.expanduser(repo))
        if theirs and theirs[1] == dirs[1]:
            return repo
    return None


def foreign_refusal(repo):
    return (f"refused by the role guard: this is a tree of {repo}, a repository no role of this project changes "
            "(its config's `guard.foreign`) - not its main clone, not any worktree of it; send its own roles a REQUEST")


def is_main_tree(path, guarded=None):
    """True when `path` is inside a guarded tree's own working tree (not a linked worktree of it, not a copy), False
    in any other repository, None when not in one. `guarded`: the git dirs to guard (default `guarded_git_dirs()`)."""
    dirs = _git_dirs(path)
    if dirs is None:
        return None
    git_dir, common = dirs
    return git_dir == common and common in (guarded_git_dirs() if guarded is None else guarded)


def is_project_tree(path):
    """True when `path` is in THIS repository - its main clone or a linked worktree of it - and not in a copy (its own
    .git) or a corpus root, where git commits are made by hand."""
    dirs, own = _git_dirs(path), _git_dirs(HOOK_REPO)
    return bool(dirs and own and dirs[1] == own[1])


def in_guarded_repo(path):
    """True when `path` is in a guarded tree's repository - its main tree or any linked worktree, one common git dir -
    whose config they all read."""
    dirs = _git_dirs(path)
    return bool(dirs and dirs[1] in guarded_git_dirs())


def _read(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return None


def _places_before(text, masked, at, base, keyword_cds=True):
    """Each directory a command at position `at` may run in: every cd before it, in order, from where the one before
    it left (girsa-verifier's MEDIUM 2 on 828abdc: `cd ~/work && cd <the project> && git reset --hard` had been judged
    at `<cwd>/<the project>`). A keyword-led cd (KEYWORD_CD) may not run, so the place it leaves stays one too. Each
    place is kept with the one before it and pushd's stack (notes/PLAN-KNOWN-GAPS-SEVEN.md, item 4): `cd -` goes back,
    a bare cd home, `popd` to the stack's top, a bare `pushd` swaps the two."""
    cds = sorted([(c, False) for c in CD.finditer(masked[:at])]
                 + [(c, True) for c in KEYWORD_CD.finditer(masked[:at])] * keyword_cds, key=lambda cd: cd[0].start())
    states = [(base, None, ())]             # (a place, the place before it, pushd's stack)
    for c, maybe in cds:
        verb, path = c.group(1), c.group(2) and _expand(_word(text[c.start(2):c.end(2)]), text[:at])
        moved = []
        for here, before, stack in states:
            # shortcut: with no cd before it on the line, a `cd -` or `popd` goes where the shell was before the
            # command, which the hook's input does not hold - the place is kept; upgrade if the input ever carries it
            if verb == "popd":
                moved.append((stack[0], here, stack[1:]) if stack else (here, before, stack))
            elif path == "-" or (verb == "pushd" and not path):     # bash: `pushd -` is a pushd to the place before
                back = before if path == "-" else (stack[:1] or [None])[0]
                rest = stack if verb == "cd" else (here,) + (stack if path == "-" else stack[1:])
                moved.append((back, here, rest) if back else (here, before, stack))
            else:
                there = os.path.join(here, path) if path else os.path.expanduser("~")
                moved.append((there, here, (here,) + stack if verb == "pushd" else stack))
        states = list(dict.fromkeys(states + moved if maybe else moved))
    return list(dict.fromkeys(here for here, _, _ in states))


def _dir_before(text, masked, at, base):
    """The directory the cds before position `at` went to, each from where the one before it left, or `base`."""
    return _places_before(text, masked, at, base, keyword_cds=False)[0]


def _git_trees(command, masked, m, cwd):
    """The trees a GIT match may use - each place it may run in, its work tree and its repository's (once, when they
    are the same). A command is a tree's when any of them is (girsa-architect on 46b378b: `--git-dir=<main>/.git
    --work-tree=. commit` commits onto the main clone's branch). The places: `_places_before` - each with its `-C`
    taken from it. The work tree: `--work-tree` or
    GIT_WORK_TREE= before git, else the place; the repository's: `--git-dir` or GIT_DIR= (its parent if it ends in
    .git), else the place."""
    # each argument found in the masked text as one WORD (item 1: a quoted one, `-C "<main>"`, had hidden the command),
    # then read in the original as the shell reads it
    a, before = m.start(1), command[:m.start()]
    opts, lead = masked[a:m.end(1)], masked[m.start():a]
    said = lambda at, g: _expand(_word(command[at + g.start(1):at + g.end(1)]), before)
    places = _places_before(command, masked, m.start(), cwd)
    # a relative -C from where the cd went (girsa-verifier's MEDIUM on db7b0ff), and EVERY -C from where the one before
    # it left, as git takes them (notes/PLAN-KNOWN-GAPS-SEVEN.md, item 3: `git -C /work -C book` had read /work)
    for c in re.finditer(r"(?<!\S)-C\s+(" + WORD + ")", opts):
        places = [os.path.join(place, said(a, c)) for place in places]
    named = {}
    for flag, var in (("--work-tree", "GIT_WORK_TREE"), ("--git-dir", "GIT_DIR")):
        f = re.search(flag + r"(?:=|\s+)(" + WORD + ")", opts)
        v = re.search(r"(?<![\w$])" + var + r"=(" + WORD + ")", lead)
        named[flag] = said(a, f) if f else said(m.start(), v) if v else None
    trees = []
    for place in places:
        work, repo = (named[f] and os.path.join(place, named[f]).rstrip("/") for f in ("--work-tree", "--git-dir"))
        trees += [work or place, (os.path.dirname(repo) if os.path.basename(repo) == ".git" else repo) if repo else place]
    return tuple(dict.fromkeys(trees))


def _config_refusal(command, masked, m, cwd, verb, guarded):
    """For a GIT match whose `verb` writes the config (`_config_writes`): the reason to refuse it, for every role - a
    `--global` or `--system` write from anywhere, since every repository reads that file; else one in a guarded tree's
    repository or a foreign one, a `-f` file's by the folder it is in - or None."""
    words = _split(command[m.start(3):m.end(3)])
    if verb == "config" and any(_long(w, ("--global", "--system")) for w in words):
        return ("refused by the role guard: a `git config --global` or `--system` write is read by every repository on "
                "this machine, the guarded ones too - a change to it is the reviewer's own command: `! git config ...` "
                "in the operator's pane")
    named = [words[i + 1] for i, w in enumerate(words[:-1]) if w in ("-f", "--file")] + \
            [w[len("--file="):] for w in words if w.startswith("--file=")]
    trees = _git_trees(command, masked, m, cwd)
    if verb == "config" and named:          # the file's own folder, from where the command's cds and -C left
        trees = tuple(os.path.dirname(os.path.join(t, _expand(named[0], command[:m.start()]))) for t in trees)
    for where in trees:
        pin, repo = pin_of(where), foreign_tree(where)
        if pin:
            return pin_refusal(pin)
        if repo:
            return foreign_refusal(repo)
        if guarded(where):
            return (f"refused by the role guard: `git {verb}` here writes the config of a guarded tree's repository, "
                    "which its main clone and every worktree read - a key there changes what every role's git does "
                    "(an alias, a mirror, where a push goes), and the file tools are refused that file too; a change "
                    f"to it is the reviewer's own command: `! git {verb} ...` in the operator's pane")
    return None


# A REF IS JUDGED BY THE REPOSITORY, NOT THE FOLDER (notes/PLAN-PROTECTED-REFS.md; the first project's Board #304 A, and
# #310 A): a branch or a tag is the shared repository's, read by the main clone and every worktree, so a command that
# moves one is judged by the ref it moves, wherever in that repository it runs - not in a copy, which has its own refs.
# Main's branch (the one checked out in the main clone) is the operator's; each ref `guard.refs` names is its owner's
# alone; the branch checked out in a role's worktree (`roles[].worktrees`) is that role's, and so is the worktree - and
# the operator's too, for its cleanups and rewrites on the reviewer's word (#310 A). A branch checked out nowhere is
# no one's (girsa-architect's Q1: its named cost).
REFS = dict(GUARD.get("refs", {}))      # {ref glob: owner role}; absent (config.OPTIONAL): none
# ...and main's branch by its name too, `guard.main` (girsa-verifier's MEDIUM 1 on notes/PLAN-REF-HOOK.md: read from the
# main clone's HEAD alone, a detached or mid-rebase main clone left it no one's and a builder's script rewound it); and
# git's object replacements the operator's alone, as `git replace` is (its LOW 1: one made main read as another commit)
MAIN_REF = "refs/heads/" + GUARD["main"] if "main" in GUARD else None     # absent (config.OPTIONAL): HEAD's alone
REPLACE = "refs/replace/*"
WORKTREES = {os.path.realpath(os.path.expanduser(w)): r["name"] for r in _CFG["roles"] for w in r.get("worktrees", ())}
REF_VERBS = ("update-ref", "tag", "branch", "checkout", "switch", "worktree", "symbolic-ref", "fetch", "pull", "push")
# each verb's options whose value is the next word (or, short, the rest of its word): long, short letters
VALUED = {"update-ref": (("--message",), "m"),
          "tag": (("--message", "--file", "--local-user", "--cleanup", "--trailer", "--sort", "--format", "--contains",
                   "--no-contains", "--points-at", "--merged", "--no-merged", "--color"), "mFu"),
          "branch": (("--set-upstream-to", "--sort", "--format", "--contains", "--no-contains", "--points-at",
                      "--merged", "--no-merged", "--color"), "u"),
          "checkout": (("--orphan", "--conflict", "--pathspec-from-file"), "bB"),
          "switch": (("--create", "--force-create", "--orphan", "--conflict"), "cC"),
          "worktree": (("--reason", "--orphan"), "bB"),
          "fetch": (("--depth", "--deepen", "--shallow-since", "--shallow-exclude", "--jobs", "--upload-pack",
                     "--refmap", "--server-option", "--negotiation-tip", "--filter"), "jo"),
          "pull": (("--depth", "--deepen", "--shallow-since", "--shallow-exclude", "--jobs", "--upload-pack",
                    "--refmap", "--server-option", "--negotiation-tip", "--strategy", "--strategy-option",
                    "--filter"), "jsXo"),
          "push": (("--push-option", "--receive-pack", "--exec", "--repo"), "o")}
# a part of a name the guard cannot read - a substitution, a variable the command does not set, a brace list - may be
# any name: read as `*`, and refused where it may cover a protected ref (girsa-verifier's LOW 1 on the plan)
UNREAD = re.compile(r"\$\{[^}]*\}|\$\([^()]*\)|`[^`]*`|\$\w+|\$[@*#?!$0-9-]|\{[^{}]*(?:,|\.\.)[^{}]*\}")


def _checked_out(where):
    """[(worktree, refs/heads/<branch> or None)] of the repository `where` is in, the main clone first - or None when
    git cannot say (the guard never opens wider for what it cannot read)."""
    try:
        out = subprocess.run(["git", "-C", where, "worktree", "list", "--porcelain"], capture_output=True, text=True,
                             timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    found = []
    for line in out.stdout.splitlines():
        if line.startswith("worktree "):
            found.append([os.path.realpath(line[len("worktree "):]), None])
        elif line.startswith("branch ") and found:
            found[-1][1] = line[len("branch "):]
    return [tuple(f) for f in found] or None


def _head(where):
    """The branch checked out where `where` is (refs/heads/...), "HEAD" when detached, None when git cannot say."""
    try:
        out = subprocess.run(["git", "-C", where, "rev-parse", "--symbolic-full-name", "HEAD"], capture_output=True,
                             text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 and out.stdout.strip() else None


def worktree_owner(path):
    """The role whose worktree (`roles[].worktrees`) `path` is in, or None - a worktree's own git dir too,
    `<main>/.git/worktrees/<name>`, by its `gitdir` file (girsa-verifier's LOW 2 on 110415f: `git
    --git-dir=<that> reset` from outside every tree had moved the worktree's branch)."""
    real = os.path.realpath(path)
    admin = re.match(r"(.*/\.git/worktrees/[^/]+)(?:/|$)", real)
    if admin:
        try:
            with open(os.path.join(admin.group(1), "gitdir"), encoding="utf-8") as fh:
                real = os.path.dirname(os.path.realpath(fh.read().strip()))
        except OSError:
            pass
    return next((r for w, r in WORKTREES.items() if real == w or real.startswith(w + os.sep)), None)


def _owner(ref, listing):
    """(role, kind) - the role that may move `ref` and why: "main" (main's branch, the operator's), "refs" (a
    `guard.refs` ref, its owner's alone), "replace" (an object replacement, the operator's alone), "worktree" (the
    branch checked out in a role's worktree) - or None."""
    if ref in (listing[0][1], MAIN_REF):
        return OPERATOR, "main"
    for pattern, owner in REFS.items():
        if fnmatch.fnmatchcase(ref, pattern):
            return owner, "refs"
    if fnmatch.fnmatchcase(ref, REPLACE):
        return OPERATOR, "replace"
    for path, r in listing[1:]:
        if r == ref and worktree_owner(path):
            return worktree_owner(path), "worktree"
    return None


def may_move(role, owner, kind, forward=False):
    """True when `role` may move a ref `_owner` gives to (`owner`, `kind`) - THE ONE RULE OF WHO MOVES WHICH REF, the Bash
    guard's on the words it reads and git's reference-transaction hook's on what git is about to write (ref_hook.py;
    girsa-architect's follow-up at the first project's 350e01e37: one function, two callers). A `guard.refs` ref and a
    replacement are their owner's alone; a role's branch its own and the operator's (#310 A); main's branch the
    operator's, but a fast-forward - what a landing does - is any role's, and only the hook can tell one (`forward`)."""
    return role == owner or (role == OPERATOR and kind == "worktree") or (kind == "main" and forward)


def _overlap(a, b):
    """True when the ref globs (or names) `a` and `b` may name one ref."""
    pa, pb = a.split("*")[0], b.split("*")[0]
    return a == b if "*" not in a + b else pa.startswith(pb) or pb.startswith(pa)


def _owners(name, kind, listing):
    """Each (ref, role, kind) the written `name` may be: as given (`refs/...`), or a short name of kind heads, tags or
    either (None); a glob every protected ref it may cover."""
    found = []
    for ref in [name] if name.startswith("refs/") else [f"refs/{k}/{name}" for k in ((kind,) if kind else ("heads", "tags"))]:
        if "*" not in ref:
            o = _owner(ref, listing)
            found += [(ref, *o)] if o else []
            continue
        for r in list(REFS) + [REPLACE] + [r for _, r in listing if r] + ([MAIN_REF] if MAIN_REF else []):
            o = _overlap(r, ref) and _owner(r.replace("*", "x") if "*" in r else r, listing)
            found += [(r, *o)] if o else []
    return found


def _git_words(command, masked, m):
    """git's words after the verb, as the shell gives them: each WORD of the masked text read in the original and
    expanded (`_expand`), one the shell splits (an unquoted variable holding spaces) split, no redirection; ending at
    the `)` or backtick that closes a substitution the git call stands in (the prototype's 3 false refusals) - not at
    one inside its words (girsa-verifier's LOW 1)."""
    a, span, before = m.start(3), masked[m.start(3):m.end(3)], command[:m.start()]
    in_tick, depth, i, end = masked[:m.start(2)].count("`") % 2 == 1, 0, 0, len(span)   # its boundary's own too
    while i < len(span):
        ch = span[i]
        if ch == "`":
            if in_tick:
                end = i
                break
            close = span.find("`", i + 1)
            i = close if close > i else len(span)
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth < 0:
                end = i
                break
        i += 1
    words = []
    for w in re.finditer(WORD, span[:end]):
        lead = span[:w.start()].rstrip()
        if re.search(r"[<>]&?$", lead) or (span[w.end():w.end() + 1] in ("<", ">") and w.group().isdigit()):
            continue                        # a redirection's target, or its descriptor
        raw = command[a + w.start():a + w.end()]
        val = _expand(_word(raw), before)
        split = "$" in raw and not re.search(r"[\"'`]|\$\(", raw) and re.search(r"\s", val)
        words += val.split() if split else [val]
    return words


def _parse(words, verb):
    """(the options given, each a short letter `-x` or a long one without its value; the values of the valued ones as
    [(option, value)]; the other words, with "--" kept where it stands)."""
    long_valued, short_valued = VALUED.get(verb, ((), ""))
    flags, values, rest, i = [], [], [], 0
    while i < len(words):
        w = words[i]
        if w in ("-", "--") or not w.startswith("-"):      # git's names go on after `--` (the review's MEDIUM 2)
            rest.append(w)
        elif w.startswith("--"):
            opt = w.split("=", 1)[0]
            flags.append(opt)
            if "=" in w:
                values.append((opt, w.split("=", 1)[1]))
            elif _long(opt, long_valued) and i + 1 < len(words):
                values.append((opt, words[i + 1]))
                i += 1
        else:                               # a cluster (`-fam x`): up to a letter whose value follows (the review's MEDIUM 2)
            for j, c in enumerate(w[1:]):
                flags.append("-" + c)
                if c in short_valued:
                    if j == len(w) - 2:
                        values.append(("-" + c, words[i + 1] if i + 1 < len(words) else ""))
                        i += 1
                    else:
                        values.append(("-" + c, w[j + 2:]))
                    break
        i += 1
    return flags, values, rest


def _has(flags, *options):
    """True when an option of `options` is given: itself, or a long one by a unique prefix as git takes it."""
    return any(f == o or _long(f, (o,)) for f in flags for o in options)       # the push rule's reading (Lesson 60)


def _written(verb, words, xargs):
    """(the refs the command writes as [(name, kind)], why the guard cannot read them or None). kind: heads, tags,
    None (either), deleted (a branch deleted), HEAD (the branch checked out where it runs), or wt (a worktree, by its
    path)."""
    flags, values, rest = _parse(words, verb)
    if _has(flags, "-h", "--help"):
        return [], None
    deleting = verb == "branch" and _has(flags, "-d", "-D", "--delete")
    if xargs and deleting:
        return [("*", "deleted")], None
    if xargs and verb in REF_VERBS and not (verb == "checkout" and "--" in rest):     # after --, paths (its NOTE 2)
        return [], "takes more of its words from its input (xargs)"
    names = [w for w in rest if w != "--"]
    if verb == "update-ref":
        if _has(flags, "--stdin"):
            return [], "reads the refs it moves from its input"
        head = names[:1] == ["HEAD"] and not _has(flags, "--no-deref")
        return [(names[0], "HEAD" if head else None)] if names else [], None
    if verb == "tag":
        writes = _has(flags, "-f", "--force", "-d", "--delete", "-a", "--annotate", "-s", "--sign", "-m", "--message",
                      "-F", "--file", "-u", "--local-user", "-e", "--edit", "--create-reflog")
        reads = _has(flags, "-l", "--list", "-v", "--verify", "--contains", "--no-contains", "--points-at", "--merged",
                     "--no-merged", "-n", "--sort", "--format", "--column", "-i", "--ignore-case")
        if not names or (reads and not writes):
            return [], None
        return [(n, "tags") for n in (names if _has(flags, "-d", "--delete") else names[:1])], None
    if verb == "branch":
        if deleting:
            return [(n, "deleted") for n in names], None
        if _has(flags, "-m", "-M", "--move"):
            return ([("HEAD", "HEAD")] if len(names) == 1 else []) + [(n, "heads") for n in names[:2]], None
        if _has(flags, "-c", "-C", "--copy"):
            return [(names[-1], "heads")] if names[:2] else [], None     # a copy reads its first name (the review's NIT 1)
        reads = _has(flags, "-l", "--list", "-a", "--all", "-v", "--verbose", "--contains", "--no-contains", "--merged",
                     "--no-merged", "--points-at", "--show-current", "--format", "--sort", "--column", "-u",
                     "--set-upstream-to", "--unset-upstream", "--edit-description")
        return ([(names[0], "heads")] if names and not (reads and not _has(flags, "-f", "--force")) else []), None
    if verb in ("checkout", "switch"):
        made = [v for o, v in values if o in ("-b", "-B", "-c", "-C", "--create", "--force-create", "--orphan")]
        paths = rest.index("--") if "--" in rest else len(rest)
        second = [(rest[0], "heads")] if _has(flags, "--ignore-other-worktrees") and rest[:paths] and not made else []
        return [(n, "heads") for n in made] + second, None
    if verb == "worktree" and names[:1] == ["add"]:
        made = [v for o, v in values if o in ("-b", "-B")]
        forced = _has(flags, "-f", "--force") and len(names) > 2 and not made
        return [(n, "heads") for n in made] + ([(names[2], "heads")] if forced else []), None
    if verb == "worktree" and names[:1] in (["remove"], ["move"]) and len(names) > 1:
        return [(names[1], "wt")], None
    if verb == "symbolic-ref":
        if len(names) > 1 and names[0] == "HEAD":
            return [(names[1], None)], None     # a branch checked out here a second time (the review's MEDIUM 2)
        return [(names[0], None)] if len(names) > 1 and names[0].startswith("refs/") else [], None
    if verb in ("fetch", "pull", "push"):
        if verb == "push" and not (names and (names[0] == "." or names[0].startswith(("/", "~", "./", "../")))):
            return [], None                 # a push to a remote is the push rule's
        specs, dst = names[1:], []
        for k, s in enumerate(specs):
            if s == "tag" and k + 1 < len(specs):
                dst.append(("refs/tags/" + specs[k + 1], None))
            elif ":" in s and s.split(":", 1)[1]:
                dst.append((s.split(":", 1)[1], None))
        forced = _has(flags, "-f", "--force") or any(s.startswith("+") for s in specs)
        tags = verb != "push" and (_has(flags, "--prune-tags", "-P")
                                   or forced and _has(flags, "--tags", "-t"))
        return dst + ([("refs/tags/*", None)] if tags else []), None
    if verb == "rebase" and _has(flags, "--update-refs"):
        return [], "moves every branch that points into the commits it rebases"
    if verb in ("filter-branch", "fast-import"):
        return [], "writes whatever refs its arguments or its input name"
    if verb == "replay" and ("--ref-action", "print") not in values:
        return [], "moves the refs its range reaches (all but `--ref-action=print`)"
    return [], None


def _ref_refusal(role, verb, command, masked, m, cwd, guarded):
    """For a GIT match: the reason to refuse it as `role` - a ref or a worktree another role's, a form the guard
    cannot read, a repository-wide write - or None."""
    words = _git_words(command, masked, m)
    flags, _, rest = _parse(words, verb)
    names = [w for w in rest if w != "--"]
    if verb == "maintenance" and names[:1] in (["register"], ["unregister"], ["start"], ["stop"]):
        return ("refused by the role guard: `git maintenance register`, `start` and their undoing write the global "
                "config, which every repository on this machine reads - the reviewer's own command: `! git "
                "maintenance ...` in the operator's pane")
    places = _git_trees(command, masked, m, cwd)
    trees = [t for t in places if guarded(t)]
    if verb in ("init", "init-db") and _has(flags, "--separate-git-dir"):
        named = [os.path.join(t, n) for t in places for n in names[:1]]
        if trees or any(guarded(p) for p in named if os.path.isdir(p)):
            return ("refused by the role guard: `git init --separate-git-dir` in a guarded tree moves the repository "
                    "its main clone and every worktree share - no role's, the reviewer's own command")
    if not trees:
        return None
    moved = verb not in READS | {"clone", "init", "init-db"} and (
        _push_config("", command[m.start(1):m.end(1)], HOOK_KEYS)
        + [a.group(1) + "=" for a in OTHER_CONFIG.finditer(masked, m.start(), m.start(1))]
        + [a.group(1) + "=" for p in OTHER_CONFIG_SET for a in p.finditer(masked[:m.start()])])
    if moved:
        return (f"refused by the role guard: `git {verb}` here with {', '.join(moved)} may switch off or move git's "
                "hooks - the reference-transaction hook guards main's branch and the `guard.refs` refs, whatever "
                "writes them; run git with the repository's own config, or the reviewer runs it: `! git ...`")
    if role != OPERATOR:
        wide = (verb == "replace" and bool(words) and not _has(flags, "-l", "--list", "--format")
                or verb == "reflog" and names[:1] in (["delete"], ["expire"], ["drop"])
                or verb == "gc" and _has(flags, "--prune")
                or verb == "prune" and not _has(flags, "-n", "--dry-run"))
        if wide:
            return (f"refused by the role guard: `git {verb}` here changes the shared repository's objects or the "
                    f"history of its refs, for every worktree - the operator's ({OPERATOR}), on the reviewer's word")
    xargs = bool(re.search(r"(?<![\w-])xargs(?![\w-])", masked[m.start():m.start(1)]))
    refs, unreadable = _written(verb, words, xargs)
    if unreadable and role != OPERATOR:
        return (f"refused by the role guard: `git {verb}` here {unreadable}, and a ref in this repository is judged by "
                f"the ref it moves - name each ref, or ask the operator ({OPERATOR})")
    for where in trees:
        listing = _checked_out(where) if refs else []
        for name, kind in refs:
            name = UNREAD.sub("*", name.lstrip("+"))
            if kind == "wt":
                if "*" in name:
                    if role != OPERATOR and WORKTREES:
                        return (f"refused by the role guard: `git {verb}` here names a worktree by a part the guard "
                                "cannot read - name the worktree")
                    continue
                # a worktree by its path, or by a unique last part of it, as git takes it (the review's MEDIUM 2)
                path = os.path.realpath(os.path.join(where, name))
                tail = os.sep + os.path.normpath(name).lstrip(os.sep)
                owner = WORKTREES.get(path) or next((r for w, r in WORKTREES.items() if w.endswith(tail)), None)
                if owner and role not in (owner, OPERATOR):
                    return (f"refused by the role guard: {name} is {owner}'s worktree - its own, and the operator's to "
                            f"remove or move on the reviewer's word; send {owner} a REQUEST")
                continue
            if listing is None:
                if role != OPERATOR:
                    return (f"refused by the role guard: `git {verb}` here moves a ref, and git could not list this "
                            "repository's worktrees to say whose it is - try again, or ask the operator")
                continue
            if kind == "HEAD":               # detached, "HEAD" is no one's
                name, kind = _head(where), None
                if name is None:
                    if role != OPERATOR:
                        return (f"refused by the role guard: `git {verb}` here moves the branch checked out here, and "
                                "git could not say which it is - name the ref")
                    continue
            for ref, owner, why in _owners(name, "heads" if kind == "deleted" else kind, listing):
                if may_move(role, owner, why):
                    continue
                # git itself refuses to delete a branch checked out in any worktree (measured, git 2.56.1) - main's and
                # each role's - so a deletion by names the guard cannot read is judged by `guard.refs` alone (the
                # build's rule 45: a builder's `... | xargs git branch -d` of its own merged branches)
                if kind == "deleted" and "*" in name and why != "refs":
                    continue
                whose = {"main": "main's branch", "refs": f"a ref `guard.refs` gives to {owner}",
                         "replace": "an object replacement, as `git replace` makes",
                         "worktree": f"the branch checked out in {owner}'s worktree"}[why]
                return (f"refused by the role guard: `git {verb}` here {'may move' if '*' in name else 'moves'} {ref}, "
                        f"{whose} - {owner}'s alone, from any worktree of this repository"
                        + (" (and the operator's, on the reviewer's word)" if why == "worktree" else "")
                        + f"; name another ref, or send {owner} a REQUEST")
    return None


def refusal(role, command, cwd, main_tree=is_main_tree, read=_read, depth=0, project_tree=is_project_tree,
            guarded=in_guarded_repo):
    """None to let `command` run as `role` from `cwd`, or the reason to refuse it."""
    masked = mask(command)
    if depth == 0:                          # one level into a script the command runs
        for m in SCRIPT.finditer(masked):
            a, b = m.span(1)
            path = _expand(_unquote(command[a:b]), command[:a])
            here = _dir_before(command, masked, a, cwd)
            body = _moved(read(os.path.join(here, path)), read)
            if body:
                why = refusal(role, body, here, main_tree, read, depth + 1, project_tree, guarded)
                if why:
                    return f"{why} (in the script {path})"
    for m in shell_c(command, masked):          # `bash -c "..."`: the quoted argument is a command, read as one
        why = refusal(role, shell_arg(m), _dir_before(command, masked, m.start(), cwd), main_tree, read,
                      depth, project_tree, guarded)
        if why:
            return why
    no_role = (f" (this session was started without a role: for the main clone start it as {OPERATOR}; a one-off "
               "session works in a worktree of its own, not a role's)") if role == NO_ROLE else ""
    for m in GIT.finditer(masked):
        verb, rest = _expand(_word(command[m.start(2):m.end(2)]), command[:m.start()]), m.group(3).split()
        if verb not in GIT_VERBS:
            return (f"refused by the role guard: `git {verb}` is not one of git's own commands - an alias or an add-on "
                    "runs what this guard cannot read; write the git command it stands for" + no_role)
        if verb in REFUSED_VERBS or (verb == "submodule" and rest[:1] == ["foreach"]):
            # for every role, the operator too (notes/PLAN-GIT-CLASSIFICATION.md; `submodule foreach` for the same
            # reason as for-each-repo - girsa-verifier's NOTE 2 on the plan)
            why = REFUSED_VERBS.get(verb) or ("runs a shell command in each submodule, a command this guard cannot "
                                              "read - run it in each submodule by name")
            return f"refused by the role guard: `git {verb}` {why}" + no_role
        if verb in ("config", "remote") and _config_writes(verb, _split(command[m.start(3):m.end(3)])):
            why = _config_refusal(command, masked, m, cwd, verb, guarded)
            if why:
                return why + no_role
        why = _ref_refusal(role, verb, command, masked, m, cwd, guarded)
        if why:
            return why + no_role
        # a pin or a foreign repository: refused to every role, merge --ff-only too, but a form that changes nothing
        if verb in CHANGES_MAIN and not (verb != "merge" and _leaves_it(verb, rest, command, masked, m,
                                                                        _git_trees(command, masked, m, cwd))):
            for where in _git_trees(command, masked, m, cwd):
                pin = pin_of(where)                                 # a pin: refused to every role, merge --ff-only too
                if pin:
                    return pin_refusal(pin)
                repo = foreign_tree(where)                          # so is any tree of a foreign repository
                if repo:
                    return foreign_refusal(repo)
        if verb in THROUGH_LAND and "--abort" not in rest:
            trees = _git_trees(command, masked, m, cwd)
            in_main = any(map(main_tree, trees))
            if ((verb == "commit" or in_main) and not (role == NO_ROLE and not in_main)
                    and any(map(project_tree, trees))):
                return (f"refused by the role guard: `git {verb}` in this repository goes through {THROUGH_LAND[verb]}"
                        + no_role)
        if role == OPERATOR and verb in OPERATOR_THROUGH_LAND and "--abort" not in rest:
            if any(main_tree(w) and project_tree(w) for w in _git_trees(command, masked, m, cwd)):
                return (f"refused by the role guard: `git {verb}` in the main tree makes a commit no gate saw - make the "
                        "change in a worktree and land it with `land.py land`, or commit its result with "
                        "`land.py commit`")
        if verb == "push":
            if role != OPERATOR:
                return (f"refused by the role guard: pushing is the operator's ({OPERATOR}), on the reviewer's "
                        "word - send it a LANDED or a REQUEST instead" + no_role)
            retired = GUARD.get("retired_remotes", [])
            set_here = _push_config(command[m.start():m.start(1)], command[m.start(1):m.end(1)])
            if set_here:
                return ("refused by the role guard: the operator's push takes no config from its own line (found "
                        f"{', '.join(set_here)}) - a remote., url., alias., branch. or push. key, or GIT_CONFIG..., "
                        "changes where a push goes or what it sends; push the branch to origin by name")
            # the words as given: masked, a quoted word is spaces
            bad = [w for w in _split(command[m.start(3):m.end(3)]) if w in retired or push_forces(w)]
            if bad:
                return ("refused by the role guard: the operator never pushes --all, --mirror, a force or a delete"
                        + (f", nor to {' or '.join(retired)}" if retired else "")
                        + f" (found {' '.join(bad)}) - push the branch to origin by name; a delete on a remote runs "
                        "only as the reviewer's own command: `! git push origin --delete <branch>` in the operator's "
                        "pane")
        elif (verb == "stash" and not (rest[:1] and rest[0] in LEAVES_IT["stash"])
              and any(map(project_tree, _git_trees(command, masked, m, cwd)))):
            return ("refused by the role guard: `git stash` in this repository - its stash list is shared by the main "
                    "clone and every worktree, so a pop can take another role's work - set the work aside as a patch: `git diff > <file>.patch`" + no_role)
        elif verb in CHANGES_MAIN and role != OPERATOR:
            # another role's worktree, its branch, index and files (girsa-verifier's MEDIUM 1 on
            # notes/PLAN-PROTECTED-REFS.md: a reset there moved its branch, a `checkout --detach` left it no one's);
            # `merge --ff-only` moves its branch too, as in a pin
            leaves = _leaves_it(verb, rest, command, masked, m, _git_trees(command, masked, m, cwd))
            owner = next((o for o in map(worktree_owner, _git_trees(command, masked, m, cwd)) if o and o != role), None)
            if owner and not (leaves and verb != "merge"):
                return (f"refused by the role guard: `git {verb}` would change {owner}'s worktree - its branch, index "
                        f"and files are its own (and the operator's, on the reviewer's word); work in your own "
                        f"worktree, or send {owner} a REQUEST" + no_role)
            if leaves:
                continue
            if any(map(main_tree, _git_trees(command, masked, m, cwd))):
                return (f"refused by the role guard: `git {verb}` would change the main tree or a root the "
                        "project lists, which are the operator's alone - work in your worktree or a copy and land with `git "
                        "merge --ff-only`, or send the operator a HANDOFF" + no_role)
    sets = SETS_AGENT.search(masked)
    if sets:
        return (f"refused by the role guard: a command may not set {sets.group(1)} - the session's start sets it to "
                "the session's role, and land.py lands as that role" + no_role)
    for m in LAND.finditer(masked):
        verb = m.group(1)
        if verb not in LAND_AS_ROLE:
            continue
        # land.py runs git where this hook cannot see it: a Mishmeret session's commit reached Girsa this way (d87aa497)
        repo = foreign_tree(_dir_before(command, masked, m.start(), cwd))
        if repo:
            return foreign_refusal(repo)
        words = command[m.start(2):m.end(2)].split()
        named = _expand(_unquote(words[0]), command[:m.start()]) if words else ""
        if named != role:
            return (f"refused by the role guard: `land.py {verb}` names the role {named or '(none)'}, and this session "
                    f"is {role} - a role commits and lands only as itself" + no_role)
        if verb == "commit" and role != OPERATOR and main_tree(_dir_before(command, masked, m.start(), cwd)):
            return ("refused by the role guard: `land.py commit` in the main tree is the operator's alone - commit in "
                    "your worktree and land with `land.py land`" + no_role)
        owner = worktree_owner(_dir_before(command, masked, m.start(), cwd))
        if verb == "commit" and role != OPERATOR and owner and owner != role:
            return (f"refused by the role guard: `land.py commit` here commits onto {owner}'s branch, in its worktree - "
                    "commit in your own" + no_role)
    return None


NO_ROLE = "a session with no role"

# A REHEARSAL COPY IS OF THE MAIN CLONE, NEVER OF A WORKTREE (LANES.md; 2026-10-02: a worktree's .git is a file pointing
# into the main repository, so a copy of it shares that worktree's index and HEAD - girsa-verifier's `git checkout <rev>
# -- tests/` in such a copy staged into its worktree; the reviewer's sweep for missing gates, 2026-10-27). Refused for
# every role: a recursive `cp` whose source is a linked worktree's top folder (a `.git` that is a file).
CP = re.compile(BOUNDARY + PREFIX + r"(?:\S*/)?cp(?=\s)([^;&|\n]*)", re.M)


def _home_as_tilde(path):
    home = os.path.expanduser("~")
    return "~" + path[len(home):] if path == home or path.startswith(home + os.sep) else path


def copy_refusal(command, cwd, is_worktree=lambda p: os.path.isfile(os.path.join(p, ".git"))):
    """None, or the reason to refuse a recursive copy of a linked worktree."""
    masked = mask(command)
    for m in CP.finditer(masked):
        words = command[m.start(1):m.end(1)].split()
        opts = [w for w in words if w.startswith("-")]
        paths = [w for w in words if not w.startswith("-")]
        if not any(o == "--recursive" or (not o.startswith("--") and set(o[1:]) & {"R", "r"}) for o in opts):
            continue
        here = _dir_before(command, masked, m.start(), cwd)
        for src in paths[:-1]:
            path = os.path.join(here, _expand(_unquote(src), command[:m.start(1)]))    # an assignment may lead it
            if is_worktree(path.rstrip("/") or "/"):
                return (f"refused by the role guard: `cp` of {src}, a linked worktree - its .git is a file pointing "
                        "into the main repository, so git in the copy changes that worktree; "
                        f"a rehearsal copies the main clone: `cp -c -R {_home_as_tilde(HOOK_REPO)} <copy>`")
    return None

# THE LIVE TMUX SERVER IS NO ROLE'S TO STOP (the reviewer, 2026-10-11, the Board #14: "A - Add the guard"). Every role
# runs in a pane of the "girsa" tmux server, so $TMUX is set in its shell, and tmux follows $TMUX ahead of TMUX_TMPDIR:
# on 2026-10-11 at 17:51 the operator's test of agents.sh ran `TMUX_TMPDIR=<its folder> tmux kill-server`, meant for a
# throwaway server, and stopped the live one with all five roles in it, none landed. Refused for every role: tmux
# kill-server, and kill-session or kill-window on the "girsa" session (or with no target, which is the pane's own
# session; or a target this guard cannot read, as "$SESSION") - unless the command reaches a server of its own: a socket
# named with -S or -L (not -L default), or $TMUX cleared (`env -u TMUX`, `TMUX=`, an earlier `unset TMUX`) AND
# TMUX_TMPDIR set for it (as a prefix, or an earlier `export`). One level into a script the command runs, which inherits
# that command's environment (`env -u TMUX TMUX_TMPDIR=<folder> bash agents.sh` may test agents.sh --restart).
# The forms tmux itself takes count (girsa-verifier's LOW on bba1587e): the aliases killw and killp, a unique prefix
# (kill-serv, kill-sess), kill-pane (one role's pane); a target is read as another session only when it names one outright
# (not %N, @N, $N or ":1", which point into the server the command reaches). `pkill` / `killall` naming tmux is refused
# outright. Not covered: tmux behind a variable or another interpreter, or `kill <pid>` of the server.
TMUX_PREFIX = (r"(?:(?:[A-Za-z_]\w*=(?:" + WORD + r")?|env(?:\s+-u\s*\w+|\s+-" + WORD + r")*|time|command|exec"
               r"|nice(?:\s+-n\s*" + WORD + r"|\s+-\d+)?|sudo(?:\s+-[A-Za-z]+(?:\s+(?:[\w.-]+|\"[^\"]*\"|'[^']*'))?)*"
               r"|xargs(?:\s+-" + WORD + r"(?:\s+" + WORD + r")?)*)\s+)*")      # item 1's WORD, as PREFIX
TMUX_KILL = re.compile(BOUNDARY + "(" + TMUX_PREFIX + r")(?:\S*/)?tmux((?:\s+-(?:[2CDlNuvV]+|[cfLST]\s*" + WORD + r"))*)\s+"
                       r"(kill[\w-]*)(?![\w-])([^;&|\n]*)", re.M)
KILL_VERBS = ("kill-server", "kill-session", "kill-window", "kill-pane")
KILL_ALIASES = {"killw": "kill-window", "killp": "kill-pane"}
PKILL = re.compile(BOUNDARY + TMUX_PREFIX + r"(?:\S*/)?(?:pkill|killall)(?![\w-])([^;&|\n]*)", re.M)


def _kill_verb(word):
    """The tmux kill command `word` names (an alias, or a unique prefix - an ambiguous one read as kill-server), or
    None."""
    if word in KILL_ALIASES:
        return KILL_ALIASES[word]
    hits = [v for v in KILL_VERBS if v.startswith(word)] if word.startswith("kill-") and len(word) > 5 else []
    return hits[0] if len(hits) == 1 else ("kill-server" if hits else None)
TMUX_SCRIPT = re.compile(BOUNDARY + "(" + TMUX_PREFIX + r")(?:(?:bash|sh|zsh)((?:\s+-\w+)*)\s+)?(\S+\.sh)(?![\w.])", re.M)
# absent (config.PARTS): no roles' session, the live server still guarded
ROLES_SESSION = _CFG["tmux_session"] if "tmux_session" in _CFG else None


def _own_tmux_env(prefix, before):
    """True when a command with this `prefix` (its assignments and env), after the text `before` it, runs tmux with
    $TMUX cleared AND TMUX_TMPDIR set - so it reaches a server in that folder, never the roles' one."""
    cleared = (re.search(r"(?<![\w-])env\s+(?:-\S+\s+)*-u\s*TMUX(?!\w)", prefix)
               or re.search(r"(?<![\w$])TMUX=(?:\s|$|\"\"|'')", prefix)
               or re.search(r"(?<![\w-])unset\s+(?:-v\s+)?TMUX(?!\w)", before))
    tmpdir = (re.search(r"(?<![\w$])TMUX_TMPDIR=\S", prefix)
              or re.search(r"(?<![\w-])export\s+TMUX_TMPDIR=\S", before))
    return bool(cleared and tmpdir)


# the project's shell shim, by its form (`HELPER.py --sh NAME`), not by the helper's name - a project's own file
SHELL_SHIM = re.compile(r'\.py"?\s+--sh\s+([\w.-]+\.sh)\b')
HERE = os.path.dirname(os.path.abspath(__file__))


def _moved(body, read):
    """A SCRIPT MOVED TO MISHMERET IS READ WHERE IT RUNS (design-study/STEP-MISHMERET-MOVE-PLAN.md in Girsa, step 2): a
    project's shell shim (`.claude/mishmeret_shim.py --sh NAME`) runs Mishmeret's NAME from the pinned tree - the tree
    this guard runs from - so the guard reads that; read as the shim, `agents.sh --restart`'s kill-session would be
    hidden. A script not found here leaves the shim itself."""
    m = SHELL_SHIM.search(body or "")
    if not m:
        return body
    return read(os.path.join(HERE, m.group(1))) or body


def tmux_refusal(command, cwd, read=_read, own_env=False, depth=0):
    """None to let `command` run, or the reason to refuse it: it would stop the live tmux server or the roles' session
    (the comment above). `own_env`: the command runs in an environment already set to a server of its own."""
    masked = mask(command)
    for m in TMUX_KILL.finditer(masked):
        prefix, opts = command[m.start(1):m.end(1)], command[m.start(2):m.end(2)]
        before, verb, rest = masked[:m.start()], _kill_verb(m.group(3)), command[m.start(4):m.end(4)]
        if not verb:
            continue
        sock = re.search(r"-([LS])\s*(\S+)", opts)
        if sock and not (sock.group(1) == "L" and _unquote(sock.group(2)) == "default"):
            continue
        if own_env or _own_tmux_env(prefix, before):
            continue
        if verb != "kill-server":
            target = re.search(r"-t\s*(\S+)", rest)
            session = (_unquote(target.group(1)) if target else "").lstrip("=").split(":")[0]
            if re.fullmatch(r"[A-Za-z][\w.-]*", session) and session != ROLES_SESSION:
                continue                    # another session on the live server, named outright: not the roles'
        return (f"refused by the role guard: `tmux {verb}` here would reach the LIVE tmux server - the one every "
                f"role's session runs in. "
                "A test server is reached only as `env -u TMUX TMUX_TMPDIR=<its own folder> tmux ...` or `tmux -S "
                f"<its own socket> ...`; "
                + (f"the live server and the {ROLES_SESSION} session are" if ROLES_SESSION else "the live server is")
                + " the reviewer's to stop")
    for m in PKILL.finditer(masked):
        if re.search(r"(?<![\w-])tmux(?![\w-])", command[m.start(1):m.end(1)]):
            return ("refused by the role guard: pkill / killall of tmux would stop the LIVE tmux server with every "
                    "role's session in it - stop a test server by its own socket (`tmux -S <socket> kill-server`)")
    if depth == 0:                          # one level into a script the command runs, with that command's environment
        for m in TMUX_SCRIPT.finditer(masked):
            if re.search(r"-\w*n", m.group(2) or ""):  # `bash -n x.sh` reads it for its syntax, runs nothing
                continue
            a, b = m.span(3)
            path = _expand(_unquote(command[a:b]), command[:a])
            here = _dir_before(command, masked, a, cwd)
            body = _moved(read(os.path.join(here, path)), read)
            if body:
                why = tmux_refusal(body, here, read,
                                   own_env or _own_tmux_env(command[m.start(1):m.end(1)], masked[:m.start()]), 1)
                if why:
                    return f"{why} (in the script {path})"
    for m in shell_c(command, masked):
        why = tmux_refusal(shell_arg(m), _dir_before(command, masked, m.start(), cwd), read, own_env, depth)
        if why:
            return why
    return None

# THE FILE TOOLS TOO (the reviewer, 2026-10-09: "A" - girsa-verifier's finding: this hook ran on Bash only, so a role's
# Edit, Write and NotebookEdit changed the main tree's files unguarded; at 14:13 its Edit reached the main clone's copy of
# its own brief, which it reverted within a minute). The same trees are guarded - this repository's main clone and the
# named corpus roots, never a linked worktree or a copy - and only the operator writes there; a file that does not exist
# yet is judged by the nearest folder that does.
FILE_TOOLS = {"Edit": "file_path", "Write": "file_path", "NotebookEdit": "notebook_path"}


# A CHECK'S OWN EXIT STATUS DECIDES THE STEP AFTER IT (the reviewer, 2026-10-13: "this issue keeps biting us"). START_HERE
# has said "A check's own exit status decides a commit, never a pipe's" since 2026-10-06, and it was broken by the
# operator (e57d558, 2026-10-05: `echo "exit $?"`; 621d4699, 2026-10-12: `check_lane.py --doc-only | tail -1` committed
# over a FAIL) and by another role on 2026-10-13 (a FAIL piped through tail went on to `git merge`; git refused only
# because main had moved). Refused for every role, the operator too: a command in which a check (CHECKS) is followed
# by a commit, merge, push or tag (GATED_STEPS) that its failure cannot stop - the check piped into another command
# without `set -o pipefail` (the pipe's status is the last command's), followed by `;` or a newline without `set -e`
# before it, `check && echo ...;` (a failure in an && list does not stop even under set -e), or `check || true`. Read in
# the command and one level into a script it runs. Its status counts when the command uses it: `if ! check; then`,
# `check || { ...; exit 1; }`, `check && git commit`, or `set -e` before a check alone on its line.
CHECKS = tuple(GUARD.get("checks", ()))
GATED_STEPS = {"commit", "merge", "push", "tag", "update-ref", "cherry-pick", "am"}
STEP_SPLIT = re.compile(r"(\|\||&&|\|&?|;|(?<![<>&])&(?![>&])|\n)")
LEAD_WORDS = {*KEYWORDS, "(", "time", "command", "exec"}
# a case's head and an arm's pattern before a statement's program (item 5 of notes/PLAN-KNOWN-GAPS-SEVEN.md: `case x in
# a) pytest | tail;; esac` had passed both check rules); a pattern's `|` alternatives are split as a pipe, so `b)` too
CASE_LEAD = re.compile(r"^\s*(?:case\s.*?\sin\s+)?" + CASE_PATTERN)


def _words(stmt):
    """The statement's words with what stands before its program taken off: a case arm's pattern, keywords,
    assignments, env and its options, `timeout N`; and the keywords so taken, as a set."""
    stmt = CASE_LEAD.sub("", stmt, count=1)
    words, lead = stmt.replace("(", " ( ").replace("{", " { ").split(), set()
    while words:
        w = words[0]
        if w in LEAD_WORDS or w == "env":
            lead.add(w)
            words = words[1:]
        elif "env" in lead and w in ("-u", "--unset"):
            words = words[2:]
        elif re.match(r"[A-Za-z_]\w*=", w) or ("env" in lead and w.startswith("-")):
            words = words[1:]
        elif w == "timeout" and len(words) > 1:
            words = words[2:]
        else:
            break
    return words, lead


def _check_in(stmt):
    """The check a statement runs (one of CHECKS), or None."""
    words, _ = _words(stmt)
    if not words:
        return None
    prog = os.path.basename(words[0])
    if prog in CHECKS:
        return prog
    # a python by a variable (`$PY -m pytest`, `"$PY" ...`) is read as a python (girsa-verifier's LOW on 8ac9341b)
    # (quoted, `"$PY"` reaches here masked as `"   "`: its two quote marks are words of their own)
    if re.match(r"python(\d[\d.]*)?$", prog) or words[0][:1] in "\"'" or words[0].startswith("$"):
        rest = [w for w in words[1:] if w not in ("-I", "-u", "-B", "-q", '"', "'")]
        if rest[:2] == ["-m", "pytest"]:
            return "pytest"
        if rest and os.path.basename(rest[0]) in CHECKS:
            return os.path.basename(rest[0])
    return None


def _gated_step_in(stmt):
    """`git <verb>` when the statement is one of GATED_STEPS, else None."""
    words, _ = _words(stmt)
    if not words or os.path.basename(words[0]) != "git":
        return None
    i = 1
    while i < len(words) and words[i] in ("-C", "-c"):
        i += 2
    return f"git {words[i]}" if i < len(words) and words[i] in GATED_STEPS else None


def _pipelines(command, masked):
    """(pipes, raws): the command's pipelines - each its statements (as masked) joined by `|`, with the operator after
    its last one - and each pipeline's first statement as written."""
    stmts, at = [], 0                       # (the statement as masked, the operator after it, its own text)
    for m in STEP_SPLIT.finditer(masked):
        stmts.append((masked[at:m.start()].strip(), m.group(1), command[at:m.start()]))
        at = m.end()
    stmts.append((masked[at:].strip(), "\n", command[at:]))
    stmts = [x for x in stmts if x[0] or x[1] in ("|", "|&")]
    pipes, raws, cur = [], [], []
    for s, op, raw in stmts:
        if not cur:
            raws.append(raw)
        cur.append(s)
        if op not in ("|", "|&"):
            pipes.append((cur, op.strip() or ";"))
            cur = []
    if cur:
        pipes.append((cur, ";"))
    return pipes, raws


def check_status_refusal(command, cwd, read=_read, depth=0):
    """None to let `command` run, or the reason to refuse it: a check in it whose failure cannot stop a commit, merge,
    push or tag after it (the comment above)."""
    masked = mask(command)
    if depth == 0:
        for m in SCRIPT.finditer(masked):
            a, b = m.span(1)
            path = _expand(_unquote(command[a:b]), command[:a])
            here = _dir_before(command, masked, a, cwd)
            body = _moved(read(os.path.join(here, path)), read)
            if body:
                why = check_status_refusal(body, here, read, depth + 1)
                if why:
                    return f"{why} (in the script {path})"
    for m in shell_c(command, masked):
        why = check_status_refusal(shell_arg(m), _dir_before(command, masked, m.start(), cwd), read, depth)
        if why:
            return why
    pipes, raws = _pipelines(command, masked)
    errexit = pipefail = False
    for i, (pipe, op) in enumerate(pipes):
        first_words, lead = _words(pipe[0])
        if first_words[:1] == ["set"]:
            flags = " ".join(first_words[1:])
            if re.search(r"(?:^|\s)\+[a-z]*e|\+o\s+errexit", flags):
                errexit = False
            elif re.search(r"(?:^|\s)-[a-z]*e|-o\s+errexit", flags):
                errexit = True
            pipefail = pipefail or "pipefail" in flags
        found = [(n, c) for n, c in enumerate(_check_in(s) for s in pipe) if c]
        if not found:
            continue
        n, check = found[0]
        later = next((st for p, _ in pipes[i + 1:] for st in (_gated_step_in(x) for x in p) if st), None)
        if not later:
            continue
        # its status read at once in the next statement - `rc=$?`, `[ "${PIPESTATUS[0]}" = 0 ] || ...` - is used
        # (`$?` only where the check is not hidden in a pipe: after `check | tail` it is tail's)
        hidden = n < len(pipe) - 1 and not pipefail
        nxt_raw = raws[i + 1] if i + 1 < len(raws) else ""
        if op in (";", "\n", "&") and ("PIPESTATUS" in nxt_raw or ("$?" in nxt_raw and not hidden)):
            continue
        if hidden:
            how = f"it is piped into `{(_words(pipe[-1])[0] or ['?'])[0]}`, so the pipe's status is that command's"
        else:
            how = None
            if lead & {"if", "!", "while", "until"}:
                continue
            if op == "||":
                nxt = pipes[i + 1][0][0] if i + 1 < len(pipes) else ""
                nw, nlead = _words(nxt)
                if not nlead & {"{", "("} and nw[:1] and nw[0] in ("true", ":", "echo", "printf"):
                    how = f"`|| {nw[0]}` lets its failure through"
                else:
                    continue
            elif op == "&&":
                chain, j = [], i
                while j < len(pipes) and pipes[j][1] == "&&":
                    chain.extend(pipes[j + 1][0] if j + 1 < len(pipes) else [])
                    j += 1
                if any(_gated_step_in(x) for x in chain):
                    continue
                how = "a failure in an `&&` list does not stop the command, even under `set -e`"
            elif errexit:
                continue
            else:
                how = "it is followed by `;` or a new line with no `set -e` before it"
        return (f"refused by the role guard: `{check}` cannot stop `{later}` later in this command - {how}. A check's "
                "own exit status decides the step after it: put `set -e` first and the check alone on its line, or `if ! <check>; then ...; exit 1; "
                "fi`; send its output to a file and read the file, never through a pipe")
    return None


# A CHECK PIPED INTO ANOTHER COMMAND READS AS A PASS (Board #66 A, 2026-10-20; the reviewer: "i keep seeing agents
# messing up by picking up tail's exit status. how do we fix that properly for all?"). check_status_refusal stops such a
# pipe only before a commit, merge, push or tag; a session that READ the status went on to report a failure as a pass
# (the operator, that morning: `bash commit_step12.sh | tail -6` showed exit 0 over a red gate). Refused for every role:
# a check (CHECKS) or a shell script (`bash x.sh`, `./x.sh`) anywhere but last in a pipeline, unless `set -o pipefail`
# came first or the next statement reads `${PIPESTATUS[...]}`. Read in the command, `bash -c`, and one level into a
# script it runs. Any other pipe (`git log | head`) is untouched.
def _script_in(stmt):
    """The shell script a statement runs (`bash x.sh`, `sh -e x.sh`, `./x.sh`), or None."""
    words, _ = _words(stmt)
    if not words:
        return None
    if os.path.basename(words[0]) in ("bash", "sh", "zsh"):
        return next((w for w in words[1:] if w.endswith(".sh")), None)
    return words[0] if words[0].endswith(".sh") else None


def piped_check_refusal(command, cwd, read=_read, depth=0):
    """None to let `command` run, or the reason to refuse it: a check or a script whose status a pipe hides."""
    masked = mask(command, runs=False)          # a pipe inside "$(...)" is its own, not the check's
    if depth == 0:
        for m in SCRIPT.finditer(masked):
            a, b = m.span(1)
            path = _expand(_unquote(command[a:b]), command[:a])
            here = _dir_before(command, masked, a, cwd)
            body = _moved(read(os.path.join(here, path)), read)
            if body:
                why = piped_check_refusal(body, here, read, depth + 1)
                if why:
                    return f"{why} (in the script {path})"
    runs = lambda text: next((c for p, _ in _pipelines(text, mask(text, runs=False))[0] for c in map(_check_in, p) if c),
                             None)
    for m in shell_c(command, masked):
        why = piped_check_refusal(shell_arg(m), _dir_before(command, masked, m.start(), cwd), read, depth)
        if why:
            return why
        # `bash -c "<check>" | tail`: the argument runs the check, and the pipe hides the shell's status
        after = masked[m.end():].lstrip()
        if after.startswith("|") and not after.startswith("||") and runs(shell_arg(m)):
            return _piped_why(f"bash -c running {runs(shell_arg(m))}", (after[1:].lstrip("&").split() or ["?"])[0])
    pipes, raws = _pipelines(command, masked)
    pipefail = False
    for i, (pipe, op) in enumerate(pipes):
        first_words, _ = _words(pipe[0])
        if first_words[:1] == ["set"] and "pipefail" in " ".join(first_words[1:]):
            pipefail = not re.search(r"\+o\s+pipefail", " ".join(first_words[1:]))
        if pipefail or len(pipe) < 2:
            continue
        hidden = next((c for c in (_check_in(s) or _script_in(s) for s in pipe[:-1]) if c), None)
        if not hidden and pipe[0].lstrip().startswith(("}", ")")):
            # a group piped whole (`{ pytest x; } | tail`): the checks inside it, back to where it opened
            j = i
            while j > 0 and not (_words(pipes[j][0][0])[1] & {"{", "("}):
                j -= 1
            hidden = next((c for p, _ in pipes[j:i] for c in map(_check_in, p) if c), None)
        if not hidden or (i + 1 < len(raws) and "PIPESTATUS" in raws[i + 1]):
            continue
        return _piped_why(hidden, (_words(pipe[-1])[0] or ["?"])[0])
    return None


def _piped_why(hidden, last):
    return (f"refused by the role guard: `{hidden}` is piped into `{last}`, so the exit status you see is `{last}`'s "
            "and a failure reads as a pass. Write its output to a file and read the check's own status: "
            "`<check> > log 2>&1; echo \"rc=$?\"; tail log` - or put `set -o pipefail` first, or read "
            "`${PIPESTATUS[0]}` in the next statement")


# A TIME TYPED AHEAD OF THE CLOCK (the reviewer, 2026-10-13, Q&A #8 "go 1 and 2": "we're wasting time on this class of
# mistake. i don't part [particularly] care about time accuracy to the second, just the order of events"). Every slip
# on record was a time later than the clock - an estimate of when the work would end - or a minute left as "x". Only a
# time written after TODAY's date is judged, and every time of a range after it ("2026-10-13 14:43-15:01"); a planned
# time is written without the date. A time with an offset ("...T12:26:16+00:00") is compared as that instant.
_CLOCK = r"(\d{1,2}):(\d{2}|\d?[xX]{1,2})(?::\d{2}(?:\.\d+)?(Z|[+-]\d{2}:?\d{2})?)?"   # an offset only after seconds
_RANGE = re.compile(r"\s*(?:-|to|until)\s*" + _CLOCK)
_X_MINUTE = re.compile(r"(?<![\w:])\d{1,2}:(?:\d[xX]|[xX]{2})(?!\w)")


def future_time_refusal(text, now=None):
    """None, or the reason to refuse `text`: it holds today's date followed by a time later than `now` (a minute's
    grace), or by a minute with an x in it."""
    from datetime import datetime, timedelta
    now = now or datetime.now().astimezone()
    # A MINUTE LEFT AS X, WITH OR WITHOUT A DATE (Board #51 A, 2026-10-18: an architect's Board corner wrote one with
    # no date, the dated check let it through, and the correction cost turns) - "19:1x", "14:xx"; never a slice's "1:x"
    if (x := _X_MINUTE.search(text or "")):
        return (f"refused by the role guard: {x.group(0)!r} leaves a minute as x - read `date` or the record, "
                "and write the minute it says, or no time at all")
    stamp = re.compile(re.escape(now.strftime("%Y-%m-%d")) + r"(?:,\s*|\s+|T)" + _CLOCK)
    for m in stamp.finditer(text or ""):
        times, at = [m.groups()], m.end()
        while (r := _RANGE.match(text, at)):
            times.append(r.groups())
            at = r.end()
        for hh, mm, tz in times:
            written = text[m.start():at].strip()
            if not mm.isdigit():
                return (f"refused by the role guard: {written!r} leaves a minute as x - read `date` or the record, "
                        "and write the minute it says, or no time at all")
            try:
                t = now.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
            except ValueError:
                continue
            if tz:
                off = 0 if tz == "Z" else (1 if tz[0] == "+" else -1) * (int(tz[1:3]) * 60 + int(tz[-2:]))
                t = t.replace(tzinfo=None) - timedelta(minutes=off) + now.utcoffset()
                t = t.replace(tzinfo=now.tzinfo)
            if t > now + timedelta(minutes=1):
                return (f"refused by the role guard: {written!r} is later than the clock ({now:%H:%M}) - a time is "
                        "read from `date` or a record, never typed ahead; tell events in order and by their record "
                        "(a commit, a ruling, a Board item), and write a plan's time without the date")
    return None


# what the time check reads: the text a file tool writes into a document, a Board post, a commit message, and a
# command that writes a document (girsa-verifier's LOW on 19170cc1: `cat >>`, `sed -i` and a script's .write() were
# not read - the way most notebook and review text is written)
TIME_CHECKED_FILES = (".md", ".txt")
TIME_CHECKED_COMMAND = re.compile(r"board\.py|git\s+(?:-C\s+\S+\s+)?(?:commit|tag)\b")
NAMES_A_DOCUMENT = re.compile(r"\.(?:md|txt)\b")
WRITES = re.compile(r">|\btee\b|\bsed\s+(?:-\w+\s+)*-i|\.write\(|write_text\(")
_TEXT_FILE_ARG = re.compile(r"--(?:answer|body)-file[=\s]+(\"[^\"]+\"|'[^']+'|\S+)|(?:^|\s)-F\s+(\"[^\"]+\"|'[^']+'|[^\s-]\S*)")


def time_refusal(tool, tool_input, cwd, read=_read):
    """The time check for one tool call (every role, the operator too)."""
    if tool in ("Edit", "Write"):
        path = tool_input.get("file_path") or ""
        if not path.endswith(TIME_CHECKED_FILES):
            return None
        # ONLY THE LINES THE CALL ADDS (Board #51 A): a notebook rewritten whole, or an edit around an old line, carries
        # lines written before a check judged them (an x minute in the history) - not this call's to answer for
        new = tool_input.get("new_string") if tool == "Edit" else tool_input.get("content")
        old = tool_input.get("old_string") if tool == "Edit" else read(path)
        kept = set((old or "").splitlines())
        return future_time_refusal("\n".join(line for line in (new or "").splitlines() if line not in kept))
    if tool == "Bash":
        command = tool_input.get("command") or ""
        if not (TIME_CHECKED_COMMAND.search(command)
                or (NAMES_A_DOCUMENT.search(command) and WRITES.search(command))):
            return None
        why = future_time_refusal(command)
        for m in _TEXT_FILE_ARG.finditer(command):
            name = _expand((m.group(1) or m.group(2)).strip("\"'"), command)
            why = why or future_time_refusal(read(name if os.path.isabs(name) else os.path.join(cwd, name)) or "")
        return why
    return None


def edit_refusal(role, path, main_tree=is_main_tree):
    """None to let a file tool write `path` as `role`, or the reason to refuse it."""
    if not path:
        return None
    here = os.path.dirname(os.path.abspath(os.path.expanduser(path)))
    while here and not os.path.isdir(here):
        parent = os.path.dirname(here)
        if parent == here:
            return None
        here = parent
    repo = foreign_tree(here)                   # every role, the operator too
    if repo:
        return foreign_refusal(repo)
    if role == OPERATOR:
        return None
    if main_tree(here):
        no_role = (" (this session was started without a role: a one-off session works in a worktree)"
                   if role == NO_ROLE else "")
        return ("refused by the role guard: this file is in the main tree or a root the project lists, which only the "
                f"operator ({OPERATOR}) changes - edit your worktree's copy and land with `git merge --ff-only`, or "
                "send the operator a HANDOFF" + no_role)
    return None


def role_of(event, argv):
    """The role the guard judges: ROLE on the command line (a probe), else the session's agent_type, else NO_ROLE -
    which is refused what every role but the operator is refused (the reviewer, 2026-10-04). A SUBAGENT IS NO ROLE (M07
    item 2, notes/PLAN-SUBAGENT-ROLE.md; girsa-architect's answer): inside one, `agent_type` is the subagent's own type
    and an `agent_id` is present, so a subagent of the operator's type had the operator's rights. It is judged as a
    name no role has: refused a push, a commit and land.py. Measured (Claude Code 2.1.322): a role's own session
    carries no `agent_id`."""
    if len(argv) > 1:
        return argv[1]
    if event.get("agent_id"):
        return f"a subagent of type {event.get('agent_type') or 'unknown'}"
    return event.get("agent_type") or NO_ROLE


def main(argv):
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 0
    # THE GUARD FAILS CLOSED ON ITS OWN FAULT (girsa-architect's Mishmeret audit, item 118, 1): an exception inside a
    # rule left Python with exit 1, which Claude Code reads as a non-blocking error, so the command ran - a push whose
    # tool_input was a string went through. Now the fault is printed and the command refused.
    try:
        return check(event, argv)
    except Exception as e:
        print(f"refused by the role guard: the guard itself failed ({type(e).__name__}: {e}) - nothing was checked, so "
              f"nothing runs; tell {OPERATOR}, which owns the hooks", file=sys.stderr)
        return 2


def check(event, argv):
    tool = event.get("tool_name")
    why = time_refusal(tool, event.get("tool_input") or {}, event.get("cwd") or os.getcwd())
    if why:
        print(why, file=sys.stderr)
        return 2
    if tool in FILE_TOOLS:
        path = (event.get("tool_input") or {}).get(FILE_TOOLS[tool]) or ""
        pin = pin_of(path) if path else None
        why = pin_refusal(pin) if pin else edit_refusal(role_of(event, argv), path)
        if why:
            print(why, file=sys.stderr)
            return 2
        return 0
    if tool != "Bash":
        return 0
    role = role_of(event, argv)
    command = (event.get("tool_input") or {}).get("command") or ""
    cwd = event.get("cwd") or os.getcwd()
    why = (refusal(role, command, cwd) or tmux_refusal(command, cwd) or copy_refusal(command, cwd)
           or check_status_refusal(command, cwd)
           or piped_check_refusal(command, cwd))
    if why:
        print(why, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
