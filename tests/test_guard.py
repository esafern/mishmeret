"""The guard, the time check at a commit, and the landing (mishmeret/role_guard.py, time_precommit.py, land.py),
with their tests, moved from Girsa at 6fdfe821 (design-study/STEP-MISHMERET-MOVE-PLAN.md there, step 4): each on
placeholder input against the placeholder project (conftest.py) - its roles `ex-*`, its tmux session `ex`, its ledger
`rulings.jsonl`. The halves of these tests that read Girsa's own files stayed there."""
import json
import os
import re
import sys

import pytest

from conftest import PKG, REPO  # noqa: F401  (REPO: the placeholder project's root)


def _land():
    import land
    return land


def test_what_the_server_loads_is_found_in_every_code_folder(tmp_path):
    """land.server_loads looks for an import in every folder the project names (Girsa's pipeline/, citations/ and tools/; here app/, lib/ and tools/) (2026-10-27: the server's lazy import
    of citations/adjudicate_against_verse.py went unseen, and 959e1e23's landing said "none of it changed"): an import
    inside a function, and onwards from the module it finds; a name in two folders counts both; a module nothing
    imports, and a standard-library import, are not counted. Placeholder repository."""
    land = _land()
    for folder, name, text in (
            ("app", "server.py", "import json\nimport kept\n\ndef notes():\n    from refs import parse\n"),
            ("app", "kept.py", "import os\n"),
            ("app", "unread.py", ""),
            ("lib", "refs.py", "import shared\n"),
            ("lib", "shared.py", ""),
            ("tools", "shared.py", ""),
            ("tools", "json.py", "")):          # a tool's file named as a library would be: counted - a restart too many
        (tmp_path / folder).mkdir(exist_ok=True)
        (tmp_path / folder / name).write_text(text, encoding="utf-8")
    assert land.server_loads(str(tmp_path)) == {
        "app/server.py", "app/kept.py", "lib/refs.py", "lib/shared.py", "tools/shared.py",
        "tools/json.py"}


def test_the_role_guard_fails_closed_on_its_own_fault(tmp_path):
    """girsa-architect's Mishmeret audit (item 118, 1; the reviewer, 2026-10-30: "start your work for mish"): a fault
    inside one of the guard's rules left Python with exit 1, which Claude Code reads as a non-blocking error, so the
    command ran - constructed as a push whose tool_input is a string. Run as the hook runs, on stdin: such an event is
    refused (exit 2) with the fault named; a well-formed harmless one still passes."""
    import subprocess
    guard = os.path.join(PKG, "role_guard.py")
    run = lambda event: subprocess.run([sys.executable, guard], input=json.dumps(event), capture_output=True, text=True)
    bad = run({"tool_name": "Bash", "tool_input": "git push origin main", "cwd": str(tmp_path)})
    assert bad.returncode == 2, (bad.returncode, bad.stderr)
    assert "the guard itself failed (AttributeError" in bad.stderr and "nothing runs" in bad.stderr, bad.stderr
    good = run({"tool_name": "Bash", "tool_input": {"command": "ls"}, "cwd": str(tmp_path)})
    assert good.returncode == 0, (good.returncode, good.stderr)


def test_the_role_guard_keeps_push_and_main_tree_commits_to_the_operator():
    """The reviewer, 2026-10-01: "i want each role to have tools explicitly set so we can prevent certain activities",
    then "yes go on your tool and role recomm." A tool list cannot stop one Bash command, so each role's file names
    `.claude/hooks/role_guard.py`: no `git push` but the operator's, and never --all, --mirror, --force or old-origin;
    no commit in the main tree but the operator's - also inside a script the command runs, with the variables the
    same command sets. Placeholder paths; the main tree is a fake predicate."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("role_guard", os.path.join(PKG, "role_guard.py"))
    rg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rg)
    main = lambda p: os.path.normpath(p).startswith("/work/book") and "/work/book-" not in os.path.normpath(p)
    scripts = {"/work/book/scratch/c.sh": "cd /work/book || exit 1\ngit add -- a\ngit commit -q -m x\n",
               "/work/book-builder/c.sh": "git commit -q -m x\n"}
    read = scripts.get
    no = lambda role, cmd, cwd="/work/book": rg.refusal(role, cmd, cwd, main_tree=main, read=read)
    # pushing: the operator's, by name, never --all/--mirror/--force/old-origin
    assert no("ex-operator", "git push origin some-branch") is None
    assert "operator's" in no("ex-builder", "git push origin some-branch")
    assert "operator's" in no("ex-verifier", "cd /work/book && git -C /work/book push")
    for bad in ("git push --all origin", "git push --force origin b", "git push -f origin b", "git push retired b",
                "git push --mirror origin"):
        assert "never pushes" in no("ex-operator", bad), bad
    # M07 item 4 (PLAN-PUSH-FORMS.md): never a force or a delete in any form - a `+` or `:` refspec, a short cluster
    # holding f or d, a long option by its unique prefix (git takes one as the option), a quoted word (the shell takes
    # the quotes off), and a comment after the push read as words (refused: the safe side)
    for bad in ("origin +main", "origin +HEAD:main", "-uf origin main", "-fu origin b", "-df origin b", "origin :main",
                "--delete origin main", "-d origin main", "-ud origin b", "--prune origin", "--force-with-lease origin b",
                "--force-if-includes origin b", "--branches origin", 'origin "+main"', "origin ':main'", '"-f" origin b',
                '"--force" origin b', 'origin +"main"', "origin '+'main", '"retired" b', "--mirr origin", "--mi origin",
                "--al origin", "--bra origin", "--b origin", "--de origin b", "--del origin b", "--delet origin b",
                "--pru origin", "--prun origin", "--forc origin b", "--fo origin b", "--force-with-lease=main origin main",
                "origin b # --force later"):
        why = no("ex-operator", "git push " + bad)
        assert why and "never pushes" in why, bad
    assert "`! git push origin --delete <branch>` in the operator's pane" in no("ex-operator", "git push -d origin b")
    for fine in ("origin some-branch", "-u origin some-branch", "origin HEAD:refs/heads/b", "-o ci.skip origin b",
                 "-ofix origin b", "-uofix origin b", "--follow-tags origin b", "--fol origin b", "-v -n origin b",
                 "origin b:b", "--set-upstream origin b", "origin 158993f5e2:refs/heads/main",
                 "origin 158993f:refs/heads/some-branch", "--dry-run origin b", "--porcelain origin b",
                 "--progress origin b", "--push-option=x origin b", "--atomic origin b", "--tags origin",
                 "--no-verify origin b", "--recurse-submodules=check origin b", "--repo=origin b", "-- origin b",
                 "--quiet origin b", "--verbose origin b", "origin refs/tags/v1", 'origin "unclosed b'):
        assert no("ex-operator", "git push " + fine) is None, fine
    # committing: anywhere for the operator; in a worktree for the others; never in the main tree for them
    assert no("ex-operator", "git commit -m x") is None
    assert "main tree" in no("ex-ui-steward", "git commit -m x")
    assert no("ex-ui-steward", "git commit -m x", cwd="/work/book-steward") is None
    assert "main tree" in no("ex-builder", "git -C /work/book commit -m x", cwd="/work/book-builder")
    assert "main tree" in no("ex-builder", "cd /work/book && git commit -m x", cwd="/work/book-builder")
    assert no("ex-builder", "git merge --ff-only builder", cwd="/work/book") is None    # landing is not a commit
    # inside a script the command runs, its path from a variable the same command sets
    assert "in the script" in no("ex-architect", "S=/work/book/scratch; bash $S/c.sh", cwd="/tmp")
    assert no("ex-builder", "bash c.sh", cwd="/work/book-builder") is None
    assert no("ex-operator", "bash /work/book/scratch/c.sh") is None
    # what is not a commit or a push is not refused
    for fine in ("git status", "git commit-tree HEAD^{tree} -m x", "git log --grep commit", "echo push",
                 'grep -n "git commit" START_HERE.md', "echo 'then git push it'"):     # the words, not a command
        assert no("ex-builder", fine) is None, fine
    for refused in ("echo hi; git commit -m x", "true && git commit -m x", "X=1 git commit -m x",
                    "(git commit -m x)", "command git push origin b"):
        assert no("ex-builder", refused), refused
    # a heredoc's body and a quoted string are words (girsa-verifier's probe): a worktree commit whose message talks
    # of pushing runs, and so does an echo of the rule
    msg = "git commit -q -F - <<'MSG'\nnever git push --all; and git commit in the main tree is the operator's\nMSG\n"
    assert no("ex-builder", msg, cwd="/work/book-builder") is None
    assert no("ex-builder", 'echo "never git commit in the main tree"') is None
    # every other way to change the main tree is refused too; landing by fast-forward, and reading, are not
    for change in ("git update-ref refs/heads/b HEAD", "git merge --no-ff builder", "git cherry-pick abc",
                   "git revert abc", "git reset --hard HEAD~1", "git stash", "git checkout -- part1.json",
                   "git add -- part1.json", "git pull"):
        assert "change the main tree" in no("ex-verifier", change), change
        assert no("ex-operator", change) is None, change
        assert no("ex-verifier", change, cwd="/work/book-verifier") is None, change
    # git behind a prefix, by a path, or inside `bash -c` (girsa-verifier's probe of the second version)
    for hidden in ("env git -C /work/book commit -m x", "time git commit -m x", "/usr/bin/git commit -m x",
                   "sudo -u me git commit -m x", 'bash -c "git -C /work/book commit -m x"',
                   "git commit-tree t -m x | xargs git -C /work/book update-ref refs/heads/b",
                   "nice -n 5 git push origin b", "xargs -I{} git push origin {}"):
        assert no("ex-builder", hidden), hidden
    assert no("ex-builder", 'bash -c "git status"') is None
    for fine in ("git -C /work/book merge --ff-only verifier", "git stash list", "git apply --check p.patch",
                 "git worktree add ../book-builder -b builder-step5", "git diff --stat", "git fetch origin"):
        assert no("ex-verifier", fine) is None, fine
    # A SESSION WITH NO ROLE is refused what every role but the operator is (the reviewer, 2026-10-04, "do a and b to
    # prevent future misuse": an external session checked its branch out in the main clone): the hook takes the
    # session's agent_type, else NO_ROLE; a probe's ROLE argument wins. Refused in the main tree, with the hint that
    # names the two ways out; free in a worktree or a copy; reading is never refused.
    assert rg.role_of({"agent_type": "ex-builder"}, ["hook"]) == "ex-builder"
    assert rg.role_of({}, ["hook"]) == rg.NO_ROLE and rg.role_of({"agent_type": ""}, ["hook"]) == rg.NO_ROLE
    assert rg.role_of({"agent_type": "ex-builder"}, ["hook", "ex-verifier"]) == "ex-verifier"
    # A SUBAGENT IS NO ROLE (M07 item 2): its hook input, as measured on Claude Code 2.1.322 - its own type and an
    # agent_id - whatever its type and whether or not its session has a role
    for sub in ({"agent_type": "ex-operator", "agent_id": "a1"}, {"agent_type": "general-purpose", "agent_id": "a2"},
                {"agent_id": "a3"}):
        role = rg.role_of(sub, ["hook"])
        assert role not in ("ex-operator", "ex-builder", rg.NO_ROLE), role
        for cmd, cwd in (("git push origin main", "/work/book"), ("git commit -m x", "/work/book"),
                         ("git commit -m x", "/work/book-builder"),
                         ("python3 tools/land.py commit ex-operator code -F m a.py", "/work/book")):
            assert rg.refusal(role, cmd, cwd, main_tree=main, read=read, project_tree=lambda p: True), (sub, cmd, cwd)
    assert rg.role_of({"agent_type": "ex-operator"}, ["hook"]) == "ex-operator"     # the operator's own session
    for refused in ("git commit -m x", "git checkout -b feature/x", "git switch other", "git push origin b"):
        why = no(rg.NO_ROLE, refused)
        assert why and "without a role" in why and "worktree" in why, refused
    assert no(rg.NO_ROLE, "git commit -m x", cwd="/work/book-builder") is None
    for fine in ("git status", "git log --oneline -3", "git diff", "git worktree add ../book-x -b feature/x"):
        assert no(rg.NO_ROLE, fine) is None, fine
    assert no("ex-operator", "git checkout hashorashim-nli-rebuild-and-review") is None


def test_the_role_guard_sees_git_after_a_keyword_behind_its_options_and_quoted():
    """M07 item 1 (notes/PLAN-GUARD-KEYWORDS.md): git after a shell keyword, behind git's own options, or written
    quoted, had gone through; so had the main tree reached by --git-dir / --work-tree / GIT_DIR= from a worktree, a
    shell or a prefix word written quoted, and a quoted land.py path. A cd after a keyword is where git MAY run, never
    where the next command does (girsa-verifier's MEDIUM 1 on 2324302). Placeholder paths; the main tree is a fake
    predicate."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("role_guard", os.path.join(PKG, "role_guard.py"))
    rg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rg)
    main = lambda p: (os.path.normpath(p) + "/").startswith("/work/book/") and "/work/book/.git" not in p
    scripts = {"/work/book/scratch/c.sh": "git commit -q -m x\n", "/work/book/x.sh": "git commit -q -m x\n",
               "/work/book/k.sh": "tmux kill-server\n"}
    no = lambda cmd, cwd="/work/book": rg.refusal("ex-builder", cmd, cwd, main_tree=main, read=scripts.get)
    p = "git push origin main"
    for bad in (f"if true; then {p}; fi", f"for i in 1; do {p}; done", f"{{ {p}; }}", f"! {p}", f"if {p}; then :; fi",
                f"while {p}; do :; done", f"until {p}; do :; done", f"if false; then :; else {p}; fi",
                f"if false; then :; elif {p}; then :; fi", f"then ! {p}",
                f"git --no-pager {p[4:]}", f"git -p {p[4:]}", f"git -P {p[4:]}", f"git --paginate {p[4:]}",
                f"git --git-dir=.git {p[4:]}", f"git --git-dir .git {p[4:]}", f"git --work-tree=. {p[4:]}",
                f"git --no-optional-locks {p[4:]}", f"git --literal-pathspecs {p[4:]}", f"git -C . --no-pager {p[4:]}",
                f"\\{p}", f'"git" {p[4:]}', f"'git' {p[4:]}", f"then \\git --no-pager {p[4:]}",
                f"/usr/bin/git --no-pager {p[4:]}", f"env git --no-pager {p[4:]}", f"git -c core.pager=cat {p[4:]}",
                f"git --namespace x {p[4:]}", f"git --config-env x=Y {p[4:]}"):
        why = no(bad)
        assert why and "operator's" in why, bad
    for fine in ("echo then git push", 'echo "git" push', "grep -n 'git' push.txt", "echo \\git push", "git --no-pager log",
                 "if true; then git status; fi", "ls {a,b}", "echo '\"git\" push'", 'x="git push"', "git --git-dir=.git log",
                 "! git diff --quiet", "echo 'then git push origin main'", "git --no-pager diff | cat", 'echo "a" git push',
                 'echo "bash" -c x', "cat <<'EOF'\n\"bash\" -c 'git commit -m x'\nEOF", 'echo "env" "sudo" "git"',
                 "git --attr-source HEAD status", "cd /work/book-builder; git reset --hard",
                 "echo '\n\"git\" push origin main\n'", "cat <<'EOF'\n\"git\" push origin main\nEOF"):
        assert no(fine) is None, fine
    # the main tree from a worktree: by either tree git uses (girsa-architect on 46b378b), or a cd in a branch
    for bad in ("git --git-dir=/work/book/.git --work-tree=. commit -m x", "GIT_DIR=/work/book/.git git commit -m x",
                "GIT_DIR=/work/book/.git GIT_WORK_TREE=/work/book git reset --hard",
                "git --git-dir=/work/book/.git reset --hard", "git --git-dir /work/book/.git --work-tree /work/book commit -m x",
                "git --git-dir=/work/book/.git --work-tree=/work/book reset --hard",
                "git --work-tree=/work/book --git-dir=/work/book/.git checkout -- a", "git -C /work/book reset --hard",
                "git --work-tree=/work/book checkout -- a", "GIT_WORK_TREE=/work/book git checkout -- a",
                "if true; then cd /work/book; fi; git reset --hard", "\\cd /work/book && git reset --hard",
                "cd /work/book-builder; if true; then cd /work/book; fi; git commit -m x",
                "cd /work/book; ls; git reset --hard", "cd /work/book; true && git reset --hard",
                "cd /work && git -C book reset -q --hard", "cd /work/book && git -C . reset -q --hard",
                "if true; then cd /work; fi; git -C book reset --hard",
                # every cd from where the one before it left (girsa-verifier's MEDIUM 2 on 828abdc)
                "cd /work && cd book && git reset -q --hard", "cd /work; cd book; git reset -q --hard",
                "cd /work && if true; then cd book; fi; git reset -q --hard", "cd /work && cd book && bash x.sh",
                # a cd's path quoted, after its options, or by pushd (found sweeping the round's siblings)
                'cd "/work/book" && git reset -q --hard', "cd '/work/book'; git reset -q --hard",
                "cd -P /work/book && git reset -q --hard", "cd -- /work/book && git reset -q --hard",
                "pushd /work/book && git reset -q --hard", "if true; then cd -P '/work/book'; fi; git reset -q --hard",
                'X=/work/book; cd "$X" && git reset -q --hard'):
        assert no(bad, "/work/book-builder"), bad
    for fine in ("git --git-dir=.git log", "git reset --hard", "GIT_DIR=.git git reset --hard",
                 "git --work-tree=. reset --hard", "if false; then cd /work/book; fi; git status",
                 "if true; then cd /work/book-builder; git reset --hard; fi", "cd /work && git -C book-builder reset --hard",
                 "cd /work/book && git -C /work/book-builder reset --hard", "cd /work && cd book-builder && git reset --hard",
                 "cd /work/book && cd /work/book-builder && git reset --hard",
                 'cd "/work/book-builder" && git reset --hard', "cd -P /work/book-builder && git reset --hard"):
        assert no(fine, "/work/book-builder") is None, fine
    # from the main tree: a cd in a branch that may not run does not move the git after it out of the main tree
    for bad in ("if false; then cd /work/book-builder; fi; git reset --hard",
                "until true; do cd /work/book-builder; done; git checkout -- a",
                "while false; do cd /work/book-builder; done; git commit -m x", "git --attr-source HEAD reset --hard"):
        assert no(bad), bad
    # a shell, a prefix word, or land.py written quoted or escaped (girsa-verifier's MEDIUM 2 on 2324302)
    for bad in ("\"bash\" -c 'git commit -m x'", "\\bash -c 'git commit -m x'", "'sh' -c \"git commit -m x\"",
                '"bash" scratch/c.sh', "\\sh scratch/c.sh", '"env" git commit -m x', "'sudo' git commit -m x",
                '"/usr/bin/git" commit -m x', "\"bash\" <<'EOF'\ngit commit -m x\nEOF",
                "cat <<'EOF' | \"bash\"\ngit commit -m x\nEOF", "\"bash\" <<< 'git commit -m x'"):
        assert no(bad), bad
    for cmd, refused in (('python3 ".claude/land.py" commit ex-operator notes -F m a.md', True),
                         ("python3 '.claude/land.py' commit ex-operator notes -F m a.md", True),
                         ('python3 ".claude/land.py" commit ex-builder notes -F m a.md', False),
                         ('grep -n "land.py commit ex-operator" notes.md', False)):
        assert bool(no(cmd, "/work/book-builder")) is refused, cmd
    # every check built on BOUNDARY reads a command after a keyword: git and cd (above), a script, cp, the tmux kill,
    # pkill and a script with a tmux kill
    assert no("if true; then bash x.sh; fi")
    wt = lambda path: path.rstrip("/").endswith("book-builder")
    assert rg.copy_refusal("if true; then cp -r /work/book-builder /tmp/c; fi", "/work", is_worktree=wt)
    assert rg.copy_refusal('"cp" -r /work/book-builder /tmp/c', "/work", is_worktree=wt)
    for bad in ("if true; then tmux kill-server; fi", "{ tmux kill-server; }", "! tmux kill-server",
                "while true; do tmux kill-server; done", "\\tmux kill-server", '"tmux" kill-server', "then pkill tmux",
                "'pkill' tmux", "if true; then bash k.sh; fi"):
        assert rg.tmux_refusal(bad, "/work/book", read=scripts.get), bad
    for fine in ("tmux ls", "then tmux ls", 'echo "tmux" kill-server', "echo \\tmux kill-server",
                 "grep -n 'tmux kill-server' f"):
        assert rg.tmux_refusal(fine, "/work/book", read=scripts.get) is None, fine


def test_an_escaped_quote_inside_a_string_does_not_turn_the_guard_off():
    """girsa-verifier, 2026-11-10, HIGH (first seen by mishmeret-builder the same day: one line of agents.sh with a
    quote escaped inside a quote, and the guard no longer saw the script's `tmux kill-session`): role_guard.mask closed
    a quote at the first quote character, escaped or not, so the string's real closing quote OPENED one and the rest
    of the command - or of a script - was masked. `echo "a \\" b"; git push origin main` was let through, for every
    role; the same in $'...'. Now a backslash and the character after it are words inside "..." and $'...', and a
    backslash is itself inside '...'. Each refusal here: alone, then after each string in the same command, on the
    next line, and in a script; and the other way - what such a string holds is still words. Placeholder paths."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("role_guard", os.path.join(PKG, "role_guard.py"))
    rg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rg)
    main = lambda p: os.path.normpath(p).startswith("/work/book") and "/work/book-" not in os.path.normpath(p)
    scripts = {}
    no = lambda role, cmd, cwd="/work/book": rg.refusal(role, cmd, cwd, main_tree=main, read=scripts.get)
    strings = ('echo "a \\" b"',            # one escaped quote
               'echo "a \\"b\\" c"',        # two: the count never mattered
               "echo $'it\\'s'",            # the same fault in $'...'
               'echo "it\'s \\" fine"',     # an apostrophe beside it
               'echo "a\\\\"',              # an escaped backslash, then the real closing quote
               "echo 'a\\'",                # '...' has no escape: it closes at the quote after the backslash
               'echo "$(echo ")")"',
               # girsa-verifier's round on 0cff45c: the `$` that opens $'...' is a lone one, and not an escaped one
               "echo $$'a\\'",              # `$$`, then a plain '...' (its MEDIUM 1: refused before the fix, lost by it)
               "echo \\$'a\\'",             # an escaped `$`, then a plain '...' (its LOW 1: held by no test)
               "echo $$$'it\\'s'",          # `$$`, then $'...'
               "echo \\$$'it\\'s'")         # an escaped `$`, then $'...'
    for cmd, role, said in (("git push origin main", "ex-builder", "operator's"),
                            ("git push --force origin main", "ex-operator", "never pushes"),
                            ("git commit -m x", "ex-builder", "main tree")):
        assert said in no(role, cmd), cmd
        for s in strings:
            scripts["/work/book/x.sh"] = f"{s}\n{cmd}\n"
            for hidden in (f"{s}; {cmd}", f"{s}\n{cmd}", f"{s} && {cmd}", "bash x.sh"):
                why = no(role, hidden)
                assert why and said in why, (s, hidden)
    # a quoted argument that is a command, with escaped quotes of its own
    assert "operator's" in no("ex-builder", 'bash -c "echo \\"x\\"; git push origin main"')
    # THE OTHER WAY: what a string with an escaped quote holds is words, and so is a comment after it
    for words in ('echo "git push origin main \\" still words"', "echo $'git push origin main \\' still words'",
                  'echo "a \\" b" # git push origin main', 'grep -n "say \\"git commit -m x\\"" notes.md',
                  'echo "a \\" b"; echo \'git push origin main\'', 'git log --grep "a \\"quoted\\" word" --oneline'):
        assert no("ex-builder", words) is None, words
    # the tmux check reads a script through the same mask: an escaped quote above its kill-session hid it
    script = 'tell() { osascript -e "display notification \\"$1\\" with title \\"ex\\""; }\ntmux kill-session -t ex\n'
    why = rg.tmux_refusal("bash roles.sh", "/work/elsewhere", lambda p: script if p.endswith("roles.sh") else None)
    assert why and "LIVE tmux server" in why
    # the mask keeps every position: a span found in it reads the same span of the original
    for text in strings + (script, "a \\", '"open \\', 'echo "a line continued \\\nin its string"\ngit status'):
        assert len(rg.mask(text)) == len(text) and rg.mask(text).count("\n") == text.count("\n"), text


def test_the_role_guard_lets_a_role_land_through_land_py_only_as_itself():
    """The reviewer, 2026-10-26, Board #86 A (girsa-verifier's MEDIUM 1 on the landing script's plan): tools/land.py runs
    git add, commit and merge as Python subprocesses the guard never sees, and takes the role as its second word. So
    the guard refuses (1) a `land.py commit` or `land.py land` naming a role other than the session's, (2) a command
    that sets CLAUDE_CODE_AGENT, the variable land.py reads for the role, and (3) `land.py commit` in the main tree for
    any session but the operator's. land.py's other subcommands, and the words in quotes or a heredoc, are not
    commands. Placeholder paths; the main tree is a fake predicate."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("role_guard", os.path.join(PKG, "role_guard.py"))
    rg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rg)
    main = lambda p: os.path.normpath(p).startswith("/work/book") and "/work/book-" not in os.path.normpath(p)
    scripts = {"/work/book-builder/l.sh": "python3 tools/land.py land ex-operator code\n"}
    no = lambda role, cmd, cwd="/work/book-builder": rg.refusal(role, cmd, cwd, main_tree=main, read=scripts.get)
    # (1) as itself, from its worktree: runs; under another role's name, in any form: refused
    for fine in ("python3 tools/land.py land ex-builder code", "./venv/bin/python tools/land.py commit ex-builder "
                 "code -F m.txt a.py", "R=ex-builder; python3 tools/land.py land $R notes",
                 "cd /work/book-builder && tools/land.py land ex-builder code"):
        assert no("ex-builder", fine) is None, fine
    for other in ("python3 tools/land.py land ex-operator code", "python3 tools/land.py commit ex-verifier notes "
                  "-F m.txt a.md", "R=ex-operator; python3 tools/land.py land $R code", "tools/land.py land",
                  "true && /work/book/tools/land.py commit ex-ui-steward code -F m a.py", "bash l.sh",
                  'bash -c "python3 tools/land.py land ex-operator code"'):
        why = no("ex-builder", other)
        assert why and "only as itself" in why, other
    assert "only as itself" in no(rg.NO_ROLE, "python3 tools/land.py land ex-builder code")
    # (2) setting the variable land.py reads, in any form
    for sets in ("CLAUDE_CODE_AGENT=ex-operator python3 tools/land.py land ex-operator code",
                 "export CLAUDE_CODE_AGENT=ex-operator", "env CLAUDE_CODE_AGENT=ex-operator python3 x.py"):
        assert "CLAUDE_CODE_AGENT" in no("ex-builder", sets), sets
        assert "CLAUDE_CODE_AGENT" in no("ex-operator", sets), sets
    # (3) a commit through land.py in the main tree: the operator's alone
    assert "operator's alone" in no("ex-builder", "python3 tools/land.py commit ex-builder code -F m a.py",
                                    cwd="/work/book")
    assert no("ex-operator", "python3 tools/land.py commit ex-operator code -F m a.py", cwd="/work/book") is None
    assert no("ex-builder", "python3 tools/land.py land ex-builder code", cwd="/work/book") is None   # a landing
    # what is not a land.py commit or land is not refused
    for fine in ("python3 tools/land.py gate --set landing", "python3 tools/land.py check-conflict a.py",
                 'grep -n "land.py commit ex-operator" x.md', "cat tools/land.py",
                 "git commit -q -F - <<'M'\nland.py land ex-operator code; CLAUDE_CODE_AGENT=x\nM\n",
                 "echo $CLAUDE_CODE_AGENT"):
        assert no("ex-builder", fine) is None, fine


def test_the_role_guard_sends_every_commit_and_landing_in_this_repository_through_land_py():
    """The reviewer, 2026-10-26: "add the extra guard" (the landing plan's section 6). In this repository - its main
    clone or a linked worktree, never a copy or a corpus root - `git commit` is refused for every role, the operator
    too, and `git merge` in the main tree (a landing), but `--abort`: tools/land.py does both, with the lane check, the
    gate and the hold. A worktree's own merge (bringing main in) runs; a session with no role keeps its commits in a
    worktree. And the operator's other ways to a commit on main (Board #87 A). Placeholder paths; fake predicates."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("role_guard", os.path.join(PKG, "role_guard.py"))
    rg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rg)
    main = lambda p: os.path.normpath(p) in ("/work/book", "/work/root")
    project = lambda p: os.path.normpath(p).startswith("/work/book")       # the main clone and its worktrees
    scripts = {"/work/book-builder/c.sh": "git commit -q -m x\n"}
    no = lambda role, cmd, cwd: rg.refusal(role, cmd, cwd, main_tree=main, read=scripts.get, project_tree=project)
    for role in ("ex-operator", "ex-builder"):
        for cmd, cwd in (("git commit -m x", "/work/book-builder"), ("git commit --amend --no-edit", "/work/book-builder"),
                         ("git -C /work/book-builder commit -m x", "/tmp"), ("bash c.sh", "/work/book-builder"),
                         ("git -C /work/book merge --ff-only builder", "/work/book-builder")):
            why = no(role, cmd, cwd)
            assert why and "`land.py " in why, (role, cmd)
    assert "`land.py commit ROLE" in no("ex-operator", "git commit -m x", "/work/book")
    assert "`land.py land ROLE" in no(rg.NO_ROLE, "git -C /work/book merge --ff-only x", "/work/book-x")
    for fine, cwd in (("git commit -m x", "/work/copy"), ("git -C /work/root commit -m x", "/work/book"),
                      ("git merge --ff-only main", "/work/book-builder"), ("git merge --abort", "/work/book"),
                      ("git commit-tree t -m x", "/work/book-builder"), ('echo "git commit -m x"', "/work/book")):
        assert no("ex-operator", fine, cwd) is None, fine
    assert no(rg.NO_ROLE, "git commit -m x", "/work/book-x") is None      # a one-off session, in its worktree
    # Board #87 A (girsa-verifier's LOW): the other commands that make a commit on main are refused to the operator in
    # the main tree too, each one's --abort apart; in a worktree, a copy or a corpus root they run
    for verb in ("revert --no-edit HEAD", "cherry-pick abc", "am p.mbox", "rebase main", "commit-tree t -m x",
                 "update-ref refs/heads/b HEAD"):
        assert "no gate saw" in no("ex-operator", "git " + verb, "/work/book"), verb
        for cwd in ("/work/book-operator", "/work/copy", "/work/root"):
            assert no("ex-operator", "git " + verb, cwd) is None, (verb, cwd)
    for fine in ("git rebase --abort", "git cherry-pick --abort", "git am --abort", "git revert --abort"):
        assert no("ex-operator", fine, "/work/book") is None, fine


def test_the_role_guard_refuses_a_check_whose_failure_cannot_stop_the_commit_after_it():
    """The reviewer, 2026-10-13: "this issue keeps biting us" - a check piped through tail before a commit or merge
    (621d4699 committed over a FAIL; on 2026-10-13 a FAIL went on to `git merge`). Refused for every role: a check whose
    failure cannot stop a commit, merge, push or tag later in the same command; allowed where its own status is used.
    And `bash -c` inside a heredoc body is words (the guard refused its own probe). Placeholder commands."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("role_guard", os.path.join(PKG, "role_guard.py"))
    rg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rg)
    no = lambda cmd: rg.check_status_refusal(cmd, "/work/elsewhere", read=lambda p: None)
    for refused in ("python3 tools/check_lane.py r --doc-only | tail -1\ngit merge --ff-only b",     # the incident
                    "./venv/bin/python tools/check_lane.py r --doc-only; git commit -m x",
                    "venv/bin/python -m pytest tests -q | tail -3 && git commit -m x",
                    "set -e\npytest -q && echo PASS\ngit merge --ff-only b",
                    "pytest -q || true; git push origin x:refs/heads/y",
                    "if venv/bin/python tools/check_lane.py r | tail -1; then git commit -m x; fi",
                    "bash -c 'pytest -q | tail -1; git commit -m x'", "set -e\nset +e\npytest -q\ngit commit -m x",
                    "pytest -q | tail -1; rc=$?; [ $rc = 0 ] || exit 1\ngit commit -m x"):
        why = no(refused)
        assert why and "cannot stop" in why, refused
    assert "(in the script land.sh)" in rg.check_status_refusal(
        "bash land.sh", "/work/elsewhere", read=lambda p: "pytest -q | tail -1\ngit merge --ff-only b\n")
    for fine in ("set -e\n./venv/bin/python tools/check_lane.py r --doc-only\ngit commit -q -F - <<'MSG'\nx | tail\nMSG\n",
                 "if ! ./venv/bin/python tools/check_lane.py r; then echo failed; git reset -q; exit 1; fi\ngit commit -m x",
                 './venv/bin/python tools/check_lane.py r || { echo "failed"; git reset -q; exit 1; }\ngit commit -m x',
                 "pytest -q && git commit -m x", "set -o pipefail; set -e; pytest -q | tail -3; git commit -m x",
                 "pytest -q | tail -3", "git log | grep pytest; git commit -m x", "echo 'pytest | tail; git commit'",
                 "pytest -q > o 2>&1; rc=$?; [ $rc -eq 0 ] || exit 1\ngit commit -m x",
                 'pytest -q 2>&1 | tail -1\n[ "${PIPESTATUS[0]}" = 0 ] || exit 4\ngit commit -m x',
                 "venv/bin/python - <<'EOF'\nx = \"bash -c 'pytest | tail -1; git commit -m x'\"\nEOF\n"):
        assert no(fine) is None, fine
    # the same heredoc is words for the push check too
    assert rg.refusal("ex-builder", "venv/bin/python - <<'EOF'\nx = \"bash -c 'git push origin b'\"\nEOF\n",
                      "/work/elsewhere", main_tree=lambda p: False, read=lambda p: None) is None
    src = open(os.path.join(PKG, "role_guard.py"), encoding="utf-8").read()
    assert "or check_status_refusal(command, cwd)" in src, "main() asks the check of every role"


def test_the_role_guard_refuses_a_check_or_script_piped_into_another_command():
    """Board #66 A (2026-10-20; the reviewer: "i keep seeing agents messing up by picking up tail's exit status. how do
    we fix that properly for all?"): a check or a shell script anywhere but last in a pipe is refused for every role -
    the status a session sees is the last command's - unless pipefail is on or PIPESTATUS is read next. Any other pipe
    is untouched. Placeholder commands."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("role_guard", os.path.join(PKG, "role_guard.py"))
    rg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rg)
    no = lambda cmd: rg.piped_check_refusal(cmd, "/work/elsewhere", read=lambda p: None)
    for refused in ("pytest -q | tail -1", "bash commit.sh | tail -6", "./land.sh 2>&1 | tee log",
                    "venv/bin/python -m pytest tests -q 2>&1 | grep passed", "python3 tools/check_draft.py d.txt | head",
                    "bash -c 'pytest -q | tail -1'", "set -o pipefail\nset +o pipefail\npytest -q | tail -1",
                    # girsa-verifier's LOW on 8ac9341b: a python by a variable, a group, a bash -c argument piped
                    "PY=venv/bin/python; $PY -m pytest x | tail -1", '"$PY" -m pytest x | tail -1',
                    "{ pytest x; } | tail -1", 'bash -c "pytest x" | tail -1'):
        why = no(refused)
        assert why and "reads as a pass" in why, refused
    assert "(in the script land.sh)" in rg.piped_check_refusal("bash land.sh", "/work/elsewhere",
                                                                read=lambda p: "pytest -q | tail -1\n")
    for fine in ("git log | head", "pytest -q > o 2>&1; echo rc=$?; tail o", "set -o pipefail; pytest -q | tail -1",
                 "pytest -q | tail -1; echo ${PIPESTATUS[0]}", "grep pytest f | head", "cat x.sh | head",
                 "echo 'pytest | tail'", "ls *.sh | head", "venv/bin/python - <<'EOF'\nx = 'pytest | tail'\nEOF\n",
                 "{ git log; } | head", 'bash -c "git log" | head', '"$PY" script.py | tail', '"$EDITOR" f | head',
                 'bash -c "pytest x" || exit 1'):
        assert no(fine) is None, fine
    src = open(os.path.join(PKG, "role_guard.py"), encoding="utf-8").read()
    assert "or piped_check_refusal(command, cwd)" in src, "main() asks it of every role"


def test_the_role_guard_refuses_a_time_typed_ahead_of_the_clock():
    """The reviewer, 2026-10-13, Q&A #8, "go 1 and 2": times typed ahead of the clock kept putting an effect before its
    cause ("we're wasting time on this class of mistake"). Refused for every role: today's date followed by a time later
    than the clock (a minute's grace), any time of a range after it, or a minute left as x - in a document a file tool
    writes, a Board post (its --answer-file / --body-file too) or a commit message. Allowed: a past time, another day, a
    plan's time without the date, an ISO stamp with its offset read as that instant. Placeholder dates and texts."""
    import importlib.util
    from datetime import datetime, timedelta, timezone
    spec = importlib.util.spec_from_file_location("role_guard", os.path.join(PKG, "role_guard.py"))
    rg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rg)
    now = datetime(2030, 1, 2, 15, 34, 20, tzinfo=timezone(timedelta(hours=3)))
    for refused in ("updated 2030-01-02 15:36", "[2030-01-02 14:43-15:40, x]", "2030-01-02, 16:00",
                    "2030-01-02 15:3x", "2030-01-02 07:40 to 15:50", "2030-01-02T13:00:00+00:00"):
        assert rg.future_time_refusal(refused, now), refused
    for fine in ("updated 2030-01-02 15:35", "[2030-01-02 14:43-15:01]", "2030-01-01 23:59", "from 18:00",
                 "2030-01-02T12:26:16+00:00", "2030-01-02", ""):
        assert rg.future_time_refusal(fine, now) is None, fine
    # an x minute with no date is refused too (Board #51 A, 2026-10-18: "19:1x" in a Board corner got through)
    for refused in ("my corner at 19:1x", "read 14:xx by the clock", "(9:0X)"):
        assert rg.future_time_refusal(refused, now), refused
    for fine in ("s[1:x]", "0x1F", "a 2:1 ratio", "1:xy"):
        assert rg.future_time_refusal(fine, now) is None, fine
    # only the lines a file tool adds: an old line kept by an edit, or by a file written whole, is not judged again
    old, slip = "[08:2" + "x, an old entry]\n", "at 19:1" + "x\n"
    assert rg.time_refusal("Edit", {"file_path": "x/N.md", "old_string": old, "new_string": old + "new line\n"}, "/w") is None
    assert rg.time_refusal("Write", {"file_path": "x/N.md", "content": old + "new line\n"}, "/w", read=lambda p: old) is None
    assert rg.time_refusal("Write", {"file_path": "x/N.md", "content": old + slip}, "/w", read=lambda p: old)
    # which calls are read: documents, Board posts and their files, commit messages - not code, not other commands
    today = datetime.now().astimezone()
    ahead = (today + timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M") if today.hour < 23 else None
    if ahead:      # the real clock: 30 minutes ahead stays today unless the test runs in the day's last half hour
        assert rg.time_refusal("Edit", {"file_path": "x/NOTES.md", "new_string": f"done {ahead}"}, "/w")
        assert rg.time_refusal("Write", {"file_path": "x/draft.txt", "content": f"sent {ahead}"}, "/w")
        assert rg.time_refusal("Edit", {"file_path": "x/code.py", "new_string": f"# {ahead}"}, "/w") is None
        assert rg.time_refusal("Bash", {"command": f"git commit -m 'landed {ahead}'"}, "/w")
        assert rg.time_refusal("Bash", {"command": "python3 .claude/board/board.py qa --answer-file $S/a.md",
                                        }, "/w", read=lambda p: f"updated {ahead}")
        assert rg.time_refusal("Bash", {"command": f"echo {ahead}"}, "/w") is None
        # a command that writes a document (girsa-verifier's LOW on 19170cc1); reading one, or writing data, runs
        for writes in (f"cat >> design-study/NOTES.md <<'EOF'\nentry {ahead}\nEOF", f"sed -i '' 's/a/{ahead}/' NOTES.md",
                       f"python3 -c \"open('NOTES.md','a').write('{ahead}')\"", f"echo {ahead} | tee -a x.txt"):
            assert rg.time_refusal("Bash", {"command": writes}, "/w"), writes
        for reads in (f"grep '{ahead}' NOTES.md", f"echo {ahead} > out.json"):
            assert rg.time_refusal("Bash", {"command": reads}, "/w") is None, reads
    src = open(os.path.join(PKG, "role_guard.py"), encoding="utf-8").read()
    assert 'why = time_refusal(tool, event.get("tool_input") or {}' in src, "main() asks it of every role and tool"


def test_the_commit_check_refuses_a_time_typed_ahead_in_any_commit(tmp_path):
    """The reviewer, 2026-10-13, Board #33: "A". git's pre-commit hook (.claude/hooks/time_precommit.py --install)
    refuses a commit whose added lines in a .md or .txt file carry today's date with a time later than the clock -
    however the text was written (a script, a moved scratch file: girsa-verifier's probe of the role guard). A past
    time, a .json file and a line only removed pass. A tree without the script lets the commit run. Placeholder repo."""
    import shutil
    import subprocess
    from datetime import datetime, timedelta
    now = datetime.now().astimezone()
    if now.hour == 23 and now.minute >= 29:
        return                      # 30 minutes ahead would be tomorrow: the case cannot be built in the day's last half hour
    ahead, past = (now + timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M"), now.strftime("%Y-%m-%d") + " 00:00"
    repo = tmp_path / "repo"
    (repo / ".claude" / "hooks").mkdir(parents=True)
    # the project's path to the check (the placeholder config's `guard.precommit`), a stand-in for its shim
    (repo / ".claude" / "hooks" / "time_check.py").write_text(
        f"import runpy, sys\nsys.path.insert(0, {PKG!r})\n"
        f"runpy.run_path({os.path.join(PKG, 'time_precommit.py')!r}, run_name='__main__')\n", encoding="utf-8")
    git = lambda *a: subprocess.run(["git", "-c", "user.name=placeholder", "-c", "user.email=placeholder@example.org", *a], cwd=repo,
                                    capture_output=True, text=True)
    git("init", "-q")
    assert subprocess.run([sys.executable, os.path.join(PKG, "time_precommit.py"), "--install"], cwd=repo,
                          capture_output=True, text=True).returncode == 0
    hook = (repo / ".git" / "hooks" / "pre-commit").read_text(encoding="utf-8")
    assert '/.claude/hooks/time_check.py"' in hook and "# Example's time check (" in hook, hook
    def commit(path, text):
        (repo / path).write_text(text, encoding="utf-8")
        git("add", path)
        return git("commit", "-q", "-m", "placeholder")
    assert commit("NOTES.md", f"entry {past}\n").returncode == 0
    bad = commit("NOTES.md", f"entry {past}\nentry {ahead}\n")
    assert bad.returncode != 0 and "commit refused by the time check" in bad.stderr and "NOTES.md" in bad.stderr
    git("reset", "-q")
    assert commit("draft.txt", f"[{past}-{ahead[-5:]}]\n").returncode != 0, "a range's later end"
    git("reset", "-q")
    assert commit("data.json", f'"{ahead}"\n').returncode == 0, "only .md and .txt"
    assert commit("NOTES.md", "entry\n").returncode == 0, "a line removed is not read"
    shutil.rmtree(repo / ".claude")
    assert commit("OTHER.md", f"{ahead}\n").returncode == 0, "a tree without the script commits"


def test_the_role_guard_keeps_every_role_off_the_live_tmux_server():
    """The reviewer, 2026-10-11, the Board #14: "A - Add the guard". Every role runs in a pane of the roles' tmux
    server, where $TMUX is set and tmux follows it ahead of TMUX_TMPDIR: a test's `TMUX_TMPDIR=<folder> tmux
    kill-server` stopped the live server and all five roles. Refused for every role, the operator too: kill-server, and
    kill-session / kill-window on the roles' session (no target, or one the guard cannot read, counts) - unless the
    command reaches a server of its own (-S, -L other than default, or $TMUX cleared AND TMUX_TMPDIR set), also one
    level into a script, which inherits the command's environment. And a heredoc with a QUOTED tag is words: its body
    was read as commands before (the old mask looked for the tag where the quotes had already become spaces).
    Placeholder paths and script."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("role_guard", os.path.join(PKG, "role_guard.py"))
    rg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rg)
    # a comment's apostrophe opens no quote (it had hidden the line below it from the reader)
    script = "# the role's script\nS=\"ex\"\nif true; then\n  tmux kill-session -t \"$S\"\nfi\n"
    read = lambda p: script if p.endswith("roles.sh") else None
    no = lambda cmd: rg.tmux_refusal(cmd, "/work/elsewhere", read)
    for refused in ("tmux kill-server", "TMUX_TMPDIR=/tmp/x/sock tmux kill-server; echo done",     # the incident
                    "tmux kill-session -t ex", "tmux kill-session", "tmux kill-window -t ex:0",
                    "tmux kill-session -t =ex", "env -u TMUX tmux kill-server", "tmux -L default kill-server",
                    "bash roles.sh --restart", "TMUX_TMPDIR=/tmp/x bash ./roles.sh", "bash -c 'tmux kill-server'",
                    "cd /tmp && /usr/bin/tmux kill-server", 'TMUX_TMPDIR=/tmp/x tmux -2 kill-session -t "$T"'):
        why = no(refused)
        assert why and "LIVE tmux server" in why, refused
    for fine in ("env -u TMUX TMUX_TMPDIR=/tmp/x tmux kill-server", "tmux -S /tmp/x/sock kill-server",
                 "tmux -L testsock kill-server", "env -u TMUX TMUX_TMPDIR=/tmp/x bash roles.sh --restart",
                 "unset TMUX; export TMUX_TMPDIR=/tmp/x; tmux kill-server", 'TMUX= TMUX_TMPDIR="$T/s" tmux kill-server',
                 "tmux kill-session -t scratch-test", "tmux list-sessions", "echo 'tmux kill-server'",
                 "grep -n 'kill-server' x.py", 'git commit -m "never tmux kill-server"',
                 "cat <<'EOF'\ntmux kill-server\nEOF\n", 'cat <<"EOF"\ntmux kill-server\nEOF\n',
                 "bash -n roles.sh", "echo x  # then tmux kill-server"):
        assert no(fine) is None, fine
    # the repository's own agents.sh, read from disk: run against the live server it is refused (its --restart kills
    # the roles' session); in a test server's environment, or only syntax-checked, it runs
    assert "in the script agents.sh" in rg.tmux_refusal("bash agents.sh --resume", PKG)
    assert rg.tmux_refusal("env -u TMUX TMUX_TMPDIR=/tmp/x bash agents.sh --resume", PKG) is None
    assert rg.tmux_refusal("bash -n agents.sh", PKG) is None
    # the forms tmux itself takes (girsa-verifier's LOW on bba1587e): aliases, unique prefixes, a pane, pkill/killall,
    # a target that points into the reached server; and a shell reading a heredoc or a here-string runs its body
    for refused in ("tmux killw -t ex:1", "tmux kill-serv", "tmux kill-sess -t ex", "tmux kill-pane",
                    "tmux killp -t ex:0.1", "tmux kill-pane -t %3", "tmux kill-window -t :1", "pkill tmux",
                    "killall tmux", "pkill -f tmux", "bash <<< 'tmux kill-server'", "bash <<'EOF'\ntmux kill-server\nEOF\n",
                    "zsh <<'EOF'\ntmux kill-server\nEOF\n", "sh -s <<EOF\ntmux kill-server\nEOF\n",
                    "cat <<'EOF' | bash\ntmux kill-server\nEOF\n", ". /dev/stdin <<'EOF'\ntmux kill-server\nEOF\n",
                    "echo a\\ #b; tmux kill-server"):
        why = no(refused)
        assert why and "LIVE tmux server" in why, refused
    for fine in ("tmux kill-pane -t scratch:0.1", "pkill -f review_server.py", "env -u TMUX TMUX_TMPDIR=/tmp/x tmux killw",
                 "./venv/bin/python - <<'EOF'\ntmux kill-server\nEOF\n"):
        assert no(fine) is None, fine
    for refused in ("bash <<'EOF'\ngit push origin b\nEOF\n", "sh -s <<'EOF'\ngit push origin b\nEOF\n",
                    "bash <<EOF\ngit push origin b\nEOF\n", "bash <<< 'git push origin b'", "echo a\\ #b; git push origin b"):
        assert rg.refusal("ex-builder", refused, "/work/book-builder", main_tree=lambda p: False,
                          read=lambda p: None), refused
    # the operator is not exempt: main() asks both checks of every role
    assert rg.refusal("ex-operator", "tmux kill-server", "/tmp") is None and no("tmux kill-server")
    # the quoted-tag heredoc, for the git checks too: a body line that would be a push is words
    main = lambda p: False
    body = "git commit -q -F - <<'MSG'\ngit push origin b\nMSG\n"
    assert rg.refusal("ex-builder", body, "/work/book-builder", main_tree=main, read=lambda p: None) is None
    assert rg.refusal("ex-builder", "git push origin b", "/work/book-builder", main_tree=main, read=lambda p: None)


def _placeholder_clone_and_worktree(tmp_path, monkeypatch, gate_rc=0, hold_rc=0):
    """A placeholder main clone (branch `main`) and a worktree of it on `feature`, with the tools land.py calls replaced:
    the lane check passes, the Board answers `hold_rc` to a hold and records each call, the gate answers `gate_rc` and
    records the tree it ran in; the time check is the role guard's own, at a fixed clock (2030-01-02 12:00), so a time
    two hours on is the same day's at any hour the gate runs (ex-verifier, 2026-10-26: red from 22:00 to midnight on
    the real clock). Placeholder names; the session is ex-builder."""
    import datetime
    import subprocess
    land = _land()
    for k, v in (("GIT_AUTHOR_NAME", "placeholder"), ("GIT_AUTHOR_EMAIL", "placeholder@example.org"),
                 ("GIT_COMMITTER_NAME", "placeholder"), ("GIT_COMMITTER_EMAIL", "placeholder@example.org")):
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("CLAUDE_CODE_AGENT", "ex-builder")
    main, tree = tmp_path / "main", tmp_path / "worktree"
    main.mkdir()
    git = lambda cwd, *a: subprocess.run(["git", "-C", str(cwd), *a], check=True, capture_output=True, text=True).stdout
    git(main, "init", "-q", "-b", "main")
    (main / "placeholder.py").write_text("def kept():\n    return 1\n", encoding="utf-8")
    (main / "rulings.jsonl").write_text('{"placeholder": "a pending ruling"}\n', encoding="utf-8")
    (main / "plan.md").write_text("# A placeholder plan\n", encoding="utf-8")       # the plan a code landing names
    git(main, "add", ".")
    git(main, "commit", "-q", "-m", "placeholder")
    git(main, "worktree", "add", "-q", "-b", "feature", str(tree))
    calls = {"board": [], "gate": []}

    def board(repo, *args):
        calls["board"].append(args[0])
        return (hold_rc if args[0] == "hold" else 0), f"placeholder {args[0]}"
    monkeypatch.setattr(land, "lane_check", lambda repo, role, **kw: (0, "PASS"))
    monkeypatch.setattr(land, "board", board)
    monkeypatch.setattr(land, "run_gate", lambda tree, name: calls["gate"].append(tree) or gate_rc)
    noon = datetime.datetime(2030, 1, 2, 12, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=2)))
    monkeypatch.setattr(land, "time_refusal", lambda text, real=land.time_refusal: real(text, noon))
    return land, main, tree, git, calls


def test_land_commit_stages_what_it_names_and_refuses_the_rest(tmp_path, monkeypatch):
    """tools/land.py commit (STEP-LANDING-SCRIPT-PLAN.md section 5): refused with something already staged, a name that
    stages nothing, a message with a time later than the clock, a role not the session's (girsa-verifier's MEDIUM 1);
    committed otherwise - and after every refusal nothing is left staged. Placeholder repository."""
    land, main, tree, git, calls = _placeholder_clone_and_worktree(tmp_path, monkeypatch)
    message = tmp_path / "message.txt"
    message.write_text("Placeholder change\n", encoding="utf-8")
    (tree / "placeholder.py").write_text("def kept():\n    return 2\n", encoding="utf-8")
    (tree / "other.txt").write_text("placeholder\n", encoding="utf-8")
    git(tree, "add", "other.txt")
    with pytest.raises(land.Refused, match="the index already holds other.txt"):
        land.commit("ex-builder", "code", str(message), ["placeholder.py"], cwd=str(tree))
    git(tree, "reset", "-q")
    with pytest.raises(land.Refused, match="no such file.py"):
        land.commit("ex-builder", "code", str(message), ["placeholder.py", "no such file.py"], cwd=str(tree))
    (tree / ".gitignore").write_text("ignored.txt\n", encoding="utf-8")
    (tree / "ignored.txt").write_text("placeholder\n", encoding="utf-8")
    with pytest.raises(land.Refused):                        # an ignored file: git refuses it, or it stages nothing
        land.commit("ex-builder", "code", str(message), ["placeholder.py", "ignored.txt"], cwd=str(tree))
    (tree / ".gitignore").unlink()
    (tree / "ignored.txt").unlink()
    (tree / "unchanged.txt").write_text("placeholder\n", encoding="utf-8")
    git(tree, "add", "unchanged.txt")
    git(tree, "commit", "-q", "-m", "placeholder")
    with pytest.raises(land.Refused, match=r"staged \['placeholder.py'\], named"):     # a name that stages nothing
        land.commit("ex-builder", "code", str(message), ["placeholder.py", "unchanged.txt"], cwd=str(tree))
    assert git(tree, "diff", "--cached", "--name-only") == ""
    assert git(tree, "diff", "--cached", "--name-only") == ""
    message.write_text("Placeholder change, done 2030-01-02 14:00\n", encoding="utf-8")     # two hours past the fixed clock
    with pytest.raises(land.Refused, match="later than the clock"):
        land.commit("ex-builder", "code", str(message), ["placeholder.py"], cwd=str(tree))
    message.write_text("Placeholder change\n", encoding="utf-8")
    with pytest.raises(land.Refused, match="this session is ex-builder, not ex-verifier"):
        land.commit("ex-verifier", "code", str(message), ["placeholder.py"], cwd=str(tree))
    with pytest.raises(land.Refused, match="the main tree is ex-operator's alone"):
        land.commit("ex-builder", "code", str(message), ["placeholder.py"], cwd=str(main))
    monkeypatch.delenv("CLAUDE_CODE_AGENT")
    with pytest.raises(land.Refused, match="no role's session"):
        land.commit("ex-builder", "code", str(message), ["placeholder.py"], cwd=str(tree))
    monkeypatch.setenv("CLAUDE_CODE_AGENT", "ex-builder")
    assert git(tree, "diff", "--cached", "--name-only") == ""
    with pytest.raises(land.Refused, match="collected no test"):        # pytest's exit 5 (the plan's rehearsal)
        land.commit("ex-builder", "code", str(message), ["placeholder.py"], tests="-k no_such_test", cwd=str(tree))
    land.commit("ex-builder", "code", str(message), ["placeholder.py"], cwd=str(tree))
    assert git(tree, "log", "-1", "--format=%s").strip() == "Placeholder change"
    assert git(tree, "status", "--porcelain", "--untracked-files=no") == ""
    # ex-operator in the main tree: the landing gate under the Board's hold, released after
    monkeypatch.setenv("CLAUDE_CODE_AGENT", "ex-operator")
    (main / "placeholder.py").write_text("def kept():\n    return 3\n", encoding="utf-8")
    land.commit("ex-operator", "code", str(message), ["placeholder.py"], cwd=str(main))
    assert calls["board"] == ["hold", "release"] and calls["gate"] == [str(main)]


# A driver for a stopped land.py: the placeholder fixture, land.main (so its own signal handler), the Board's calls
# written to a file as they happen, and a step that waits ("waiting") - the frozen gate of a landing, whose copy's
# removal then takes 3 s, or a commit's lane check
_STOP_DRIVER = r'''
import os, pathlib, sys, time
import pytest
tests, tmp, log, what = sys.argv[1], pathlib.Path(sys.argv[2]), sys.argv[3], sys.argv[4]
sys.path.insert(0, tests)
import test_guard
tmp.mkdir(parents=True)
mp = pytest.MonkeyPatch()
land, main, tree, git, calls = test_guard._placeholder_clone_and_worktree(tmp, mp)


def note(word):
    with open(log, "a") as fh:
        fh.write(word + "\n")


def wait(*args, **kwargs):
    note("waiting")
    time.sleep(30)
    return 0


def board(repo, *args):
    if args[0] == "release":
        time.sleep(0.5)                                         # where a second signal lands
    note(args[0])
    return 0, "placeholder"


mp.setattr(land, "board", board)
(tree / "placeholder.py").write_text("def kept():\n    return 1\n\n\ndef added():\n    return 2\n", encoding="utf-8")
os.chdir(tree)
if what == "land":
    git(tree, "commit", "-q", "-am", "placeholder: a function added")
    mp.setattr(land, "run_gate", lambda t, name: wait() if "-land-" in str(t) else 0)
    removal = land.shutil.rmtree

    def slow(path, **kwargs):
        note("removing")
        time.sleep(3)
        removal(path, **kwargs)
    mp.setattr(land.shutil, "rmtree", slow)
    land.main(["land", "ex-builder", "code", "--plan", "plan.md"])
else:
    (tmp / "message.txt").write_text("Placeholder change\n", encoding="utf-8")
    mp.setattr(land, "lane_check", lambda *a, **kw: (wait(), (0, "PASS"))[1])
    land.main(["commit", "ex-builder", "code", "-F", str(tmp / "message.txt"), "placeholder.py"])
'''


def _stopped(tmp_path, what, sig, kill_after, again=False):
    """Run the driver; once it waits, `sig` to each of its processes (`again`: once more 0.2 s later, in the release),
    then (`kill_after` s later) SIGKILL - what Claude Code's stop does (measured: SIGTERM to the command's group,
    SIGKILL ~1.5 s after). (exit, the Board's calls)."""
    import signal
    import subprocess
    import time
    driver, log = tmp_path / "driver.py", tmp_path / "board.log"
    tmp_path.mkdir()
    driver.write_text(_STOP_DRIVER, encoding="utf-8")
    p = subprocess.Popen([sys.executable, "-B", str(driver), os.path.dirname(__file__), str(tmp_path / "t"), str(log),
                          what], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    deadline = time.time() + 60
    while not (log.exists() and "waiting" in log.read_text()):
        assert p.poll() is None and time.time() < deadline, p.communicate()[0][-2000:]
        time.sleep(0.05)

    def tree_of(pid):
        kids = subprocess.run(["pgrep", "-P", str(pid)], capture_output=True, text=True).stdout.split()
        return [pid] + [k for kid in kids for k in tree_of(int(kid))]
    group = tree_of(p.pid)
    for sent, then in [(sig, 0.2)] * again + [(sig, kill_after - 0.2 * again)] + [(signal.SIGKILL, 0)] * bool(kill_after):
        for pid in group:
            try:
                os.kill(pid, sent)
            except ProcessLookupError:
                pass
        time.sleep(then)
    p.communicate(timeout=30)
    return p.returncode, log.read_text().split()


def test_land_py_stopped_releases_the_hold_and_leaves_nothing_staged(tmp_path):
    """M07 item 6 (notes/PLAN-LAND-SIGNAL.md): a stop's SIGTERM, or SIGHUP, had ended land.py with no `finally` run - a
    stopped `land.py commit` in the main tree had left the Board's hold and its staged names (girsa-verifier's sweep,
    2026-11-09). Now: a landing stopped in its frozen gate releases the hold before the copy's slow removal, which
    SIGKILL then cuts short (girsa-verifier's MEDIUM 1 on the plan); the same under SIGHUP; a commit stopped in its
    lane check leaves nothing staged. Placeholder repositories, real signals."""
    import signal
    import subprocess
    rc, calls = _stopped(tmp_path / "term", "land", signal.SIGTERM, 1.47, again=True)    # a second one in the release
    assert "release" in calls and calls.index("release") < calls.index("removing"), (rc, calls)
    rc, calls = _stopped(tmp_path / "hup", "land", signal.SIGHUP, 0)
    assert rc == 128 + signal.SIGHUP and "release" in calls, (rc, calls)
    rc, calls = _stopped(tmp_path / "commit", "commit", signal.SIGTERM, 1.47)
    staged = subprocess.run(["git", "-C", str(tmp_path / "commit" / "t" / "worktree"), "diff", "--cached", "--name-only"],
                            capture_output=True, text=True, check=True).stdout
    assert rc == 128 + signal.SIGTERM and staged == "", (rc, staged)


def test_land_lands_on_main_and_releases_the_hold_on_every_exit(tmp_path, monkeypatch, capsys):
    """tools/land.py land: a refused hold merges nothing; a red gate merges nothing and releases the hold; a stopped
    rebase releases the hold; a replayed commit continued with a wrong resolution is refused, after main moves too; taken
    back, checked at its stop and continued, it lands - main fast-forwarded and gated again on a frozen copy holding the
    live rulings file, the hold released. Placeholder repository."""
    land, main, tree, git, calls = _placeholder_clone_and_worktree(tmp_path, monkeypatch, hold_rc=1)
    (tree / "placeholder.py").write_text("def kept():\n    return 1\n\n\ndef added():\n    return 2\n", encoding="utf-8")
    git(tree, "commit", "-q", "-am", "placeholder: a function added")
    tip = git(main, "rev-parse", "main").strip()
    with pytest.raises(land.Refused, match="refused the hold"):
        land.land("ex-builder", "code", cwd=str(tree), plan="plan.md")
    assert git(main, "rev-parse", "main").strip() == tip and calls["board"] == ["hold"]     # nothing held, nothing released
    monkeypatch.setattr(land, "board", lambda repo, *a: calls["board"].append(a[0]) or (0, "placeholder"))
    monkeypatch.setattr(land, "run_gate", lambda t, name: calls["gate"].append(t) or 1)
    calls["board"].clear()
    with pytest.raises(land.Red):
        land.land("ex-builder", "code", cwd=str(tree), plan="plan.md")
    assert git(main, "rev-parse", "main").strip() == tip and calls["board"] == ["hold", "release"]
    # main moves with a change to the same function: the rebase stops, the file stamped, the hold released
    (main / "placeholder.py").write_text("def kept():\n    return 9\n", encoding="utf-8")
    git(main, "commit", "-q", "-am", "placeholder: main's change")
    monkeypatch.setattr(land, "run_gate", lambda t, name: calls["gate"].append(t) or 0)
    calls["board"].clear()
    with pytest.raises(land.Refused, match="the rebase stopped on a conflict in placeholder.py"):
        land.land("ex-builder", "code", cwd=str(tree), plan="plan.md")
    assert calls["board"] == ["hold", "release"]
    with pytest.raises(land.Refused, match="a rebase is still in progress"):     # mid-rebase HEAD names no branch
        land.land("ex-builder", "code", cwd=str(tree), plan="plan.md")
    # CONTINUED WITH A WRONG RESOLUTION AND NO CHECK (girsa-verifier's MEDIUM 1 (a) on the build): the branch's function
    # lost - here its whole change, so git drops the emptied commit; the landing finds the commit left out and refuses,
    # and still does after main moves on (a resolution that keeps a part: the second-stop test below)
    import json
    import subprocess
    (tree / "placeholder.py").write_text("def kept():\n    return 9\n", encoding="utf-8")
    git(tree, "add", "placeholder.py")
    subprocess.run(["git", "-C", str(tree), "-c", "core.editor=true", "rebase", "--continue"], check=True,
                   capture_output=True)
    with pytest.raises(land.Refused, match="left out by the rebase: the branch does not hold its change"):
        land.land("ex-builder", "code", cwd=str(tree), plan="plan.md")
    (main / "elsewhere.txt").write_text("placeholder\n", encoding="utf-8")
    git(main, "add", "elsewhere.txt")
    git(main, "commit", "-q", "-m", "placeholder: another landing meanwhile")
    with pytest.raises(land.Refused, match="left out by the rebase: the branch does not hold its change"):
        land.land("ex-builder", "code", cwd=str(tree), plan="plan.md")
    # taken back to before its rebase, as the refusal says: it stops again, is checked at the stop, and lands
    git_dir = git(tree, "rev-parse", "--absolute-git-dir").strip()
    with open(os.path.join(git_dir, land.STAMP), encoding="utf-8") as fh:
        before = json.load(fh)["before"]
    git(tree, "reset", "-q", "--hard", before)
    with pytest.raises(land.Refused, match="the rebase stopped on a conflict"):
        land.land("ex-builder", "code", cwd=str(tree), plan="plan.md")
    (tree / "placeholder.py").write_text("def kept():\n    return 9\n", encoding="utf-8")     # the branch's side lost
    with pytest.raises(land.Red):
        land.check_conflict(["placeholder.py"], cwd=str(tree))
    (tree / "placeholder.py").write_text("def kept():\n    return 9\n\n\ndef added():\n    return 2\n", encoding="utf-8")
    land.check_conflict(["placeholder.py"], cwd=str(tree))
    git(tree, "add", "placeholder.py")
    subprocess.run(["git", "-C", str(tree), "-c", "core.editor=true", "rebase", "--continue"], check=True,
                   capture_output=True)
    # A PAGE FILE IN THE LANDING says the servers restart (girsa-verifier's LOW on step 4: `land.server.page` pinned by
    # no test)
    (tree / "page").mkdir()
    (tree / "page" / "look.js").write_text("// placeholder\n", encoding="utf-8")
    git(tree, "add", "page/look.js")
    git(tree, "commit", "-q", "-m", "placeholder: a page file")
    # THE FROZEN COPY IS GATED WITH THE LIVE RULINGS FILE (girsa-verifier's LOW 1): main's has a ruling git does not
    (main / "rulings.jsonl").write_text('{"placeholder": "a pending ruling"}\n{"placeholder": "a Save"}\n',
                                                 encoding="utf-8")
    seen = []
    monkeypatch.setattr(land, "run_gate", lambda t, name: calls["gate"].append(t) or seen.append(
        open(os.path.join(t, "rulings.jsonl"), encoding="utf-8").read() if "example-land-" in t else None) or 0)
    calls["gate"].clear()
    head = land.land("ex-builder", "code", cwd=str(tree), plan="plan.md")
    assert git(main, "rev-parse", "main").strip() == head
    assert "  the servers load: restart - page/look.js\n" in capsys.readouterr().out
    assert calls["board"][-2:] == ["hold", "release"] and len(calls["gate"]) == 2      # the worktree, then main's copy
    assert calls["gate"][0] == str(tree.resolve()) and "example-land-" in calls["gate"][1]
    assert seen[-1] == (main / "rulings.jsonl").read_text(encoding="utf-8")
    assert not os.path.exists(os.path.join(git_dir, land.STAMP))


def test_land_refuses_a_stop_resolved_against_main_after_main_moves_on(tmp_path, monkeypatch):
    """girsa-verifier's MEDIUM 1 (a) on the landing script's build, as its stamp_probe.py built it: the rebase stops on a
    file, which is resolved by dropping main's change, with no check-conflict, and continued; another commit lands on
    main; the landing refuses all the same (it landed before, losing main's change). Placeholder repository."""
    import subprocess
    land, main, tree, git, calls = _placeholder_clone_and_worktree(tmp_path, monkeypatch)
    (tree / "placeholder.py").write_text("def kept():\n    return 1\n\n\ndef added():\n    return 2\n", encoding="utf-8")
    git(tree, "commit", "-q", "-am", "placeholder: a function added")
    (main / "placeholder.py").write_text("def kept():\n    return 9\n", encoding="utf-8")
    git(main, "commit", "-q", "-am", "placeholder: main's change")
    with pytest.raises(land.Refused, match="conflict in placeholder.py"):
        land.land("ex-builder", "code", cwd=str(tree), plan="plan.md")
    (tree / "placeholder.py").write_text("def kept():\n    return 1\n\n\ndef added():\n    return 2\n", encoding="utf-8")
    git(tree, "add", "placeholder.py")
    subprocess.run(["git", "-C", str(tree), "-c", "core.editor=true", "rebase", "--continue"], check=True,
                   capture_output=True)
    (main / "elsewhere.txt").write_text("placeholder\n", encoding="utf-8")
    git(main, "add", "elsewhere.txt")
    git(main, "commit", "-q", "-m", "placeholder: another landing meanwhile")
    tip = git(main, "rev-parse", "main").strip()
    with pytest.raises(land.Refused, match="placeholder.py: kept: differs from the side that changed it"):
        land.land("ex-builder", "code", cwd=str(tree), plan="plan.md")
    assert git(main, "rev-parse", "main").strip() == tip


def test_land_refuses_a_replay_reworded_at_its_stop_and_takes_a_commit_dropped_on_purpose(tmp_path, monkeypatch):
    """girsa-verifier's LOWs on the landing script's round (its replay_edges_probe.py). Case B: a stop resolved by
    dropping main's change and committed with another subject before the rebase goes on - the replay matches no
    original, and its original is left out - refused. Case A: a stop resolved to main's side on purpose (git drops the
    emptied commit) - refused, and the refusal names `--accept dropped:COMMIT`, with which it lands. Placeholder
    repository."""
    import json
    import subprocess
    land, main, tree, git, calls = _placeholder_clone_and_worktree(tmp_path, monkeypatch)
    cont = lambda: subprocess.run(["git", "-C", str(tree), "-c", "core.editor=true", "rebase", "--continue"],
                                  capture_output=True)
    (tree / "placeholder.py").write_text("def kept():\n    return 1\n\n\ndef added():\n    return 2\n", encoding="utf-8")
    git(tree, "commit", "-q", "-am", "placeholder: a function added")
    (main / "placeholder.py").write_text("def kept():\n    return 9\n", encoding="utf-8")
    git(main, "commit", "-q", "-am", "placeholder: main's change")
    with pytest.raises(land.Refused, match="conflict in placeholder.py"):
        land.land("ex-builder", "code", cwd=str(tree), plan="plan.md")
    git_dir = git(tree, "rev-parse", "--absolute-git-dir").strip()
    with open(os.path.join(git_dir, land.STAMP), encoding="utf-8") as fh:
        before = json.load(fh)["before"]
    (tree / "placeholder.py").write_text("def kept():\n    return 1\n\n\ndef added():\n    return 2\n", encoding="utf-8")
    git(tree, "add", "placeholder.py")
    git(tree, "commit", "-q", "-m", "placeholder: another subject at the stop")
    assert cont().returncode == 0
    tip = git(main, "rev-parse", "main").strip()
    with pytest.raises(land.Refused, match="matches no original while one was left out"):
        land.land("ex-builder", "code", cwd=str(tree), plan="plan.md")
    assert git(main, "rev-parse", "main").strip() == tip
    # case A: taken back, the stop resolved to main's side on purpose
    git(tree, "reset", "-q", "--hard", before)
    with pytest.raises(land.Refused, match="conflict in placeholder.py"):
        land.land("ex-builder", "code", cwd=str(tree), plan="plan.md")
    (tree / "placeholder.py").write_text("def kept():\n    return 9\n", encoding="utf-8")
    git(tree, "add", "placeholder.py")
    assert cont().returncode == 0
    with pytest.raises(land.Refused, match="--accept dropped:COMMIT") as refused:
        land.land("ex-builder", "code", cwd=str(tree), plan="plan.md")
    assert f"{before[:8]} (the commit): left out by the rebase" in str(refused.value)
    # the id names one original, 7 characters at least: a shorter prefix, none or another commit's is refused
    # (girsa-verifier's LOW on this round: `dropped:1` landed it)
    for named in (before[:6], "", git(main, "rev-parse", "main").strip()[:8]):
        with pytest.raises(land.Refused, match=f"dropped:{named}: names"):
            land.land("ex-builder", "code", cwd=str(tree), plan="plan.md", accept=[f"dropped:{named}"])
    land.land("ex-builder", "code", cwd=str(tree), plan="plan.md", accept=[f"dropped:{before[:7]}"])
    assert git(main, "rev-parse", "main").strip() == tip                    # nothing of the branch's: main as it was


def test_land_checks_a_second_stop_and_a_file_that_is_not_python(tmp_path, monkeypatch):
    """girsa-verifier's MEDIUM 1 (b) on the landing script's build: a branch of two commits stops twice; the second stop,
    met by a bare `git rebase --continue`, resolved with main's change dropped - refused, naming that file. A conflicted
    file that is not Python lands only with --accept (its LOW 1). Placeholder repository."""
    import subprocess
    land, main, tree, git, calls = _placeholder_clone_and_worktree(tmp_path, monkeypatch)
    cont = lambda: subprocess.run(["git", "-C", str(tree), "-c", "core.editor=true", "rebase", "--continue"],
                                  capture_output=True)
    (tree / "placeholder.py").write_text("def kept():\n    return 2\n", encoding="utf-8")
    git(tree, "commit", "-q", "-am", "placeholder: first")
    (tree / "second.py").write_text("def other():\n    return 2\n", encoding="utf-8")
    (tree / "notes.txt").write_text("the branch's line\n", encoding="utf-8")
    git(tree, "add", "second.py", "notes.txt")
    git(tree, "commit", "-q", "-m", "placeholder: second")
    (main / "placeholder.py").write_text("def kept():\n    return 3\n", encoding="utf-8")
    (main / "second.py").write_text("def other():\n    return 3\n", encoding="utf-8")
    (main / "notes.txt").write_text("main's line\n", encoding="utf-8")
    git(main, "add", "placeholder.py", "second.py", "notes.txt")
    git(main, "commit", "-q", "-m", "placeholder: main's changes")
    with pytest.raises(land.Refused, match="conflict in placeholder.py"):
        land.land("ex-builder", "code", cwd=str(tree), plan="plan.md")
    (tree / "placeholder.py").write_text("def kept():\n    return 2\n", encoding="utf-8")    # both changed: the branch's
    with pytest.raises(land.Red):
        land.check_conflict(["placeholder.py"], cwd=str(tree))                    # named until accepted
    land.check_conflict(["placeholder.py"], accept=["kept"], cwd=str(tree))
    git(tree, "add", "placeholder.py")
    assert cont().returncode != 0                                                  # the second stop, met by git alone
    (tree / "second.py").write_text("def other():\n    return 3\n", encoding="utf-8")       # the branch's change dropped
    (tree / "notes.txt").write_text("main's line\nthe branch's line\n", encoding="utf-8")
    git(tree, "add", "second.py", "notes.txt")
    assert cont().returncode == 0
    with pytest.raises(land.Refused) as refused:
        land.land("ex-builder", "code", cwd=str(tree), plan="plan.md")
    assert "second.py: other: changed on both sides" in str(refused.value)
    assert "notes.txt: (the file): not Python" in str(refused.value)
    assert "placeholder.py" not in str(refused.value)                               # accepted at its stop
    head = land.land("ex-builder", "code", cwd=str(tree), plan="plan.md", accept=["second.py::other", "notes.txt"])
    assert git(main, "rev-parse", "main").strip() == head


def test_land_refuses_a_builder_code_landing_that_names_no_plan_and_lets_the_other_roles_through(tmp_path, monkeypatch):
    """tools/land.py land (Board Q&A #62, gate 1; #99 B; design-study/STEP-LAND-NAMES-A-PLAN-PLAN.md): girsa-builder's
    code landing that names no plan, or one not committed at the branch's HEAD, is refused before the hold, main
    unmoved; the plan named goes to the range's lane check, whose refusal (check_lane.py --plan on the case) merges
    nothing and releases the hold; named by a full path, it is read in the worktree; a notes landing names none; the
    other roles that land code - ex-ui-steward, ex-demo-operator, ex-verifier - land it with none. Placeholder
    repository."""
    land, main, tree, git, calls = _placeholder_clone_and_worktree(tmp_path, monkeypatch)
    (tree / "placeholder.py").write_text("def kept():\n    return 2\n", encoding="utf-8")
    git(tree, "commit", "-q", "-am", "placeholder: a change")
    tip = git(main, "rev-parse", "main").strip()
    with pytest.raises(land.Refused, match="a code landing of ex-builder names its plan"):
        land.land("ex-builder", "code", cwd=str(tree))
    (tree / "uncommitted.md").write_text("# A placeholder plan, not committed\n", encoding="utf-8")
    for plan in ("uncommitted.md", "no-such-plan.md", str(main / "plan.md")):        # the last outside the worktree
        with pytest.raises(land.Refused, match="no plan at"):
            land.land("ex-builder", "code", cwd=str(tree), plan=plan)
    (tree / "uncommitted.md").unlink()
    assert git(main, "rev-parse", "main").strip() == tip and calls["board"] == [] and calls["gate"] == []
    asked = []
    monkeypatch.setattr(land, "lane_check", lambda repo, role, **kw: asked.append(kw) or (1, "FAIL placeholder"))
    with pytest.raises(land.Refused, match="the lane check refused the range"):
        land.land("ex-builder", "code", cwd=str(tree), plan="plan.md")
    assert asked[-1]["plan"] == "plan.md" and asked[-1]["rng"] == f"{tip}..HEAD"
    assert git(main, "rev-parse", "main").strip() == tip and calls["board"] == ["hold", "release"]
    monkeypatch.setattr(land, "lane_check", lambda repo, role, **kw: asked.append(kw) or (0, "PASS"))
    whys = []
    monkeypatch.setattr(land, "board", lambda repo, *a: whys.append(a) or (0, "placeholder"))
    head = land.land("ex-builder", "code", cwd=str(tree), plan=str(tree / "plan.md"))
    assert git(main, "rev-parse", "main").strip() == head and asked[-1]["plan"] == "plan.md"
    assert whys[0][0] == "hold" and "feature (plan plan.md): placeholder: a change" in whys[0]      # the Board's record
    (tree / "notes.md").write_text("placeholder notes\n", encoding="utf-8")
    git(tree, "add", "notes.md")
    git(tree, "commit", "-q", "-m", "placeholder: notes")
    head = land.land("ex-builder", "notes", cwd=str(tree))
    assert git(main, "rev-parse", "main").strip() == head and asked[-1]["plan"] is None and asked[-1]["doc_only"]
    for n, role in enumerate(("ex-ui-steward", "ex-demo-operator", "ex-verifier")):
        monkeypatch.setenv("CLAUDE_CODE_AGENT", role)
        (tree / "placeholder.py").write_text(f"def kept():\n    return {3 + n}\n", encoding="utf-8")
        git(tree, "commit", "-q", "-am", f"placeholder: {role}'s change")
        head = land.land(role, "code", cwd=str(tree))
        assert git(main, "rev-parse", "main").strip() == head and asked[-1]["plan"] is None, role


def test_land_hands_the_plan_to_check_lane(monkeypatch):
    """tools/land.py's lane check: the plan a landing names reaches check_lane.py as `--plan` (Board Q&A #62, gate 1);
    none named, no `--plan`. The command as built, nothing run."""
    import subprocess
    import types
    land = _land()
    ran = []
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: ran.append(cmd) or types.SimpleNamespace(
        returncode=0, stdout="", stderr=""))
    land.lane_check("placeholder", "ex-builder", rng="a..b", plan="design-study/PLAN.md")
    land.lane_check("placeholder", "ex-builder", rng="a..b")
    assert ran[0][-5:] == ["ex-builder", "--range", "a..b", "--plan", "design-study/PLAN.md"]
    assert ran[1][-3:] == ["ex-builder", "--range", "a..b"]


def test_land_because_covers_only_the_commits_made_under_the_reviewers_words(monkeypatch):
    """tools/land.py land --because (the Mishmeret move's step 2, Board #114 A): the words reach the range's lane check
    only when every commit of the range that goes outside the lane on its own carries them, as `commit --because`
    writes them - a commit in the lane needs none, one outside without them is named. Placeholder commits."""
    land = _land()
    bodies = {"aaaa1111": "x\n\nThe reviewer's words: Board #1 A", "bbbb2222": "in the lane",
              "cccc3333": "outside, no words", "dddd4444": "x\n\nThe reviewer's words: Board #2 B"}
    monkeypatch.setattr(land, "said", lambda top, *a: " ".join(bodies) if a[0] == "rev-list" else bodies[a[-1]])
    monkeypatch.setattr(land, "lane_check", lambda top, role, rng=None, **k: (0 if rng == "bbbb2222^..bbbb2222" else 1,
                                                                          ""))
    assert land.unworded("placeholder", "ex-builder", "a..b", "Board #1 A") == ["cccc3333", "dddd4444"]
    # the line compared whole (girsa-verifier's LOW 2 on 0e730ccf): words that begin a commit's words do not cover it
    assert land.unworded("placeholder", "ex-builder", "a..b", "Board #1") == ["aaaa1111", "cccc3333", "dddd4444"]
    bodies.pop("cccc3333"), bodies.pop("dddd4444")
    assert land.unworded("placeholder", "ex-builder", "a..b", "Board #1 A") == []


def test_land_because_refuses_an_unworded_commit_first_and_passes_the_words_to_the_range_check(tmp_path, monkeypatch):
    """girsa-verifier's LOW 1 on 0e730ccf (its mutations U4, U5 stayed green): `land --because` is driven end to end.
    A range with a commit outside the lane that does not carry the words is refused before the range's lane check,
    the gate and the merge - main unmoved, the hold released; once every such commit carries them, the words reach the
    range's lane check and the branch lands. Placeholder repository; every commit is outside the lane here."""
    land, main, tree, git, calls = _placeholder_clone_and_worktree(tmp_path, monkeypatch)
    tip = git(main, "rev-parse", "main").strip()
    asked = []
    monkeypatch.setattr(land, "lane_check", lambda repo, role, rng=None, **kw: (
        1, "FAIL placeholder") if rng and "^.." in rng else (asked.append(dict(kw, rng=rng)) or (0, "PASS")))
    (tree / "placeholder.py").write_text("def kept():\n    return 2\n", encoding="utf-8")
    git(tree, "commit", "-q", "-am", "placeholder: worded\n\nThe reviewer's words: Board #1 A")
    (tree / "placeholder.py").write_text("def kept():\n    return 3\n", encoding="utf-8")
    git(tree, "commit", "-q", "-am", "placeholder: not worded")
    bare = git(tree, "rev-parse", "HEAD").strip()[:8]
    with pytest.raises(land.Refused, match=f"outside the lane without them: {bare}$"):
        land.land("ex-builder", "code", cwd=str(tree), plan="plan.md", because="Board #1 A")
    assert asked == [] and calls["gate"] == [] and calls["board"] == ["hold", "release"]
    assert git(main, "rev-parse", "main").strip() == tip
    git(tree, "commit", "-q", "--amend", "-m", "placeholder: worded too\n\nThe reviewer's words: Board #1 A")
    head = land.land("ex-builder", "code", cwd=str(tree), plan="plan.md", because="Board #1 A")
    assert git(main, "rev-parse", "main").strip() == head
    assert asked[-1]["because"] == "Board #1 A" and asked[-1]["rng"] == f"{tip}..HEAD", asked


def test_the_role_guard_guards_this_repository_and_the_named_corpus_roots_not_a_copy(tmp_path):
    """The reviewer, 2026-10-02: "guard - (a)". girsa-verifier's finding: the first `is_main_tree` took every tree
    whose git dir is its common dir for the main tree - every repository that is not a linked worktree - so a role was
    refused `git checkout` in its own rehearsal copy. Now only this repository's main clone (the hook's own) and the
    corpus roots in CORPUS_ROOTS are guarded: not a linked worktree of either, not a copy (`cp -c -R` carries its own
    .git), not another repository. Placeholder repositories in a temporary folder."""
    import importlib.util
    import shutil
    import subprocess
    spec = importlib.util.spec_from_file_location("role_guard", os.path.join(PKG, "role_guard.py"))
    rg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rg)

    def git(cwd, *args):
        subprocess.run(["git", "-c", "user.name=placeholder", "-c", "user.email=placeholder", *args],
                       cwd=cwd, check=True, capture_output=True)
    book, corpus, other = tmp_path / "book", tmp_path / "corpus", tmp_path / "other"
    for repo in (book, corpus, other):
        repo.mkdir()
        git(repo, "init", "-q")
        git(repo, "commit", "-q", "--allow-empty", "-m", "placeholder")
    (book / "scratch").mkdir()
    git(book, "worktree", "add", "-q", str(tmp_path / "book-builder"))
    shutil.copytree(book, tmp_path / "book-copy", symlinks=True)
    shutil.copytree(corpus, tmp_path / "corpus-copy", symlinks=True)
    guarded = {rg._git_dirs(str(book))[1], rg._git_dirs(str(corpus))[1]}
    is_main = lambda p: rg.is_main_tree(str(p), guarded=guarded)
    assert is_main(book) is True and is_main(book / "scratch") is True and is_main(corpus) is True
    for free in ("book-builder", "book-copy", "corpus-copy", "other"):
        assert is_main(tmp_path / free) is False, free
    assert is_main(tmp_path / "missing") is None
    # the input that must make the old rule fail: it took the copy for the main tree
    assert (lambda d: d[0] == d[1])(rg._git_dirs(str(tmp_path / "book-copy")))
    # through the refusal: a role may reset its copy, not the main tree; the operator may do both
    main_tree = lambda p: rg.is_main_tree(p, guarded=guarded)
    no = lambda role, cwd: rg.refusal(role, "git checkout -q -- part1.json", str(cwd), main_tree=main_tree)
    assert no("ex-verifier", tmp_path / "book-copy") is None
    assert "main tree" in no("ex-verifier", book) and "main tree" in no("ex-verifier", corpus)
    assert no("ex-operator", book) is None
    # by default: the repository the hook belongs to - this one - and the corpus roots that exist
    import config
    assert os.path.realpath(rg.HOOK_REPO) == os.path.realpath(config.root())


def test_the_role_guard_keeps_the_file_tools_out_of_the_main_tree(tmp_path):
    """The reviewer, 2026-10-09: "A" (girsa-verifier's finding: the role guard ran on Bash only, so a role's Edit, Write and
    NotebookEdit changed the main tree's files unguarded). The hook now runs on the file tools too (.claude/settings.json's
    matcher) and refuses every role but the operator a file in a guarded tree - judged by the nearest existing folder,
    so a new file in a new folder is caught - and lets a worktree, a copy and anything outside a repository through."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("role_guard", os.path.join(PKG, "role_guard.py"))
    rg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rg)
    guarded = tmp_path / "main"
    (guarded / "docs").mkdir(parents=True)
    other = tmp_path / "worktree"
    other.mkdir()
    main_tree = lambda here: os.path.realpath(here).startswith(os.path.realpath(guarded))
    assert rg.edit_refusal("ex-verifier", str(guarded / "docs" / "brief.md"), main_tree)
    assert rg.edit_refusal("ex-verifier", str(guarded / "new" / "deeper" / "x.md"), main_tree)    # folders not there yet
    assert rg.edit_refusal(rg.NO_ROLE, str(guarded / "docs" / "brief.md"), main_tree)
    assert rg.edit_refusal("ex-operator", str(guarded / "docs" / "brief.md"), main_tree) is None
    assert rg.edit_refusal("ex-verifier", str(other / "brief.md"), main_tree) is None
    assert rg.edit_refusal("ex-verifier", "", main_tree) is None
    # (the project's settings that run the guard on the file tools are the project's to test: Girsa's stayed there)
    assert rg.FILE_TOOLS == {"Edit": "file_path", "Write": "file_path", "NotebookEdit": "notebook_path"}


def test_the_role_guards_corpus_roots_are_the_books_homes_list(tmp_path):
    """STEP5-TEST-COPY-NOTICE-PLAN.md revision 2 item 6 (Lesson 60): the role guard reads its corpus roots from the one
    list of homes, pipeline/book_homes.json - a root added there is guarded with no second edit. A missing, unreadable
    or misshapen list leaves the fallback guarded, never nothing; a home with no root adds the fallback beside the good
    roots (girsa-verifier's LOW on 71175b1d). Placeholder roots."""
    import importlib.util
    listed = os.path.join(REPO, "homes.json")       # the placeholder project's `guard.homes`, read at import
    with open(listed, "w", encoding="utf-8") as fh:
        json.dump({"homes": [{"title": "Book Z", "root": "~/placeholder-z", "url": "u"}]}, fh)
    try:
        spec = importlib.util.spec_from_file_location("role_guard_roots", os.path.join(PKG, "role_guard.py"))
        guard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guard)
    finally:
        os.unlink(listed)
    assert guard.CORPUS_ROOTS == ("~/placeholder-z",), guard.CORPUS_ROOTS
    homes = tmp_path / "book_homes.json"
    homes.write_text(json.dumps({"homes": [{"title": "Book A", "root": "~/placeholder-a", "url": "u"},
                                           {"title": "Book B", "root": "~/placeholder-b", "url": "u"}]}), encoding="utf-8")
    assert guard.corpus_roots(str(homes)) == ("~/placeholder-a", "~/placeholder-b")
    for broken in ("{not json", json.dumps({"homes": [{"title": "no root"}]}), json.dumps({"homes": []}), json.dumps([])):
        homes.write_text(broken, encoding="utf-8")
        assert guard.corpus_roots(str(homes)) == guard.FALLBACK_CORPUS_ROOTS, broken
    assert guard.corpus_roots(str(tmp_path / "missing.json")) == guard.FALLBACK_CORPUS_ROOTS
    homes.write_text(json.dumps({"homes": [{"title": "Book A", "root": "~/placeholder-a", "url": "u"}, {"title": "no root"}]}),
                     encoding="utf-8")
    assert guard.corpus_roots(str(homes)) == ("~/placeholder-a",) + guard.FALLBACK_CORPUS_ROOTS, "a good root kept"


def test_the_role_guard_refuses_a_stash_and_a_copy_of_a_worktree_in_every_tree_of_this_repository():
    """The reviewer, 2026-10-27: "sweep the rules for missing gates - widen rules exactly as much as needed, no more".
    Two LANES.md rules broken on record with a gap in the guard: `git stash` was refused only in the main tree and only
    to the other roles, but the stash list is shared by every worktree (2026-10-20: the demo operator popped the
    builder's, in their worktrees) - now refused to every role in the main clone and every worktree, `list` and `show`
    still free, a copy (its own .git) or another repository untouched; and a rehearsal copy of a worktree shares its
    index and HEAD (2026-10-02) - a recursive `cp` of a linked worktree's top folder is refused. Placeholder paths."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("role_guard", os.path.join(PKG, "role_guard.py"))
    rg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rg)
    main = lambda p: os.path.normpath(p) == "/work/book"
    ours = lambda p: os.path.normpath(p) in ("/work/book", "/work/book-builder")     # the main clone and a worktree
    no = lambda role, cmd, cwd: rg.refusal(role, cmd, cwd, main_tree=main, read=lambda p: None, project_tree=ours)
    for role in ("ex-operator", "ex-builder", rg.NO_ROLE):
        for cwd in ("/work/book", "/work/book-builder"):
            for stash in ("git stash", "git stash push -m x", "git stash pop", "git -C . stash apply"):
                assert "stash list is shared" in (no(role, stash, cwd) or ""), (role, cwd, stash)
            for fine in ("git stash list", "git stash show -p"):
                assert no(role, fine, cwd) is None, (role, cwd, fine)
        assert no(role, "git stash", "/tmp/copy") is None, role                         # a copy: its own stash
    worktrees = {"/work/book-builder"}
    cp = lambda cmd, cwd="/tmp": rg.copy_refusal(cmd, cwd, is_worktree=lambda p: os.path.normpath(p) in worktrees)
    for bad in ("cp -c -R /work/book-builder /tmp/c", "cp -cR /work/book-builder/ /tmp/c", "cd /work && cp -R "
                "book-builder /tmp/c", "S=/work/book-builder; cp -r $S /tmp/c", "cp --recursive /work/book-builder x"):
        assert "linked worktree" in (cp(bad) or ""), bad
    for fine in ("cp -c -R /work/book /tmp/c", "cp /work/book-builder/a.txt /tmp/", "cp -R /work/book-builder/docs x",
                 "echo 'cp -R /work/book-builder x'"):
        assert cp(fine) is None, fine


def test_land_stages_a_renamed_file_under_both_its_names(tmp_path):
    """land.py's commit compares what it staged with the names it was given (`_staged`): a file moved to a new name is
    two names - the old one removed, the new one added - and git's rename detection reported the new one alone, so a
    commit naming both was refused as "a name that is ignored, unchanged or misspelt" (C8's build, 2026-10-27: known
    session cases renamed fixed-). Placeholder files."""
    import subprocess
    import land
    git = lambda *a: subprocess.run(["git", "-C", str(tmp_path), *a], check=True, capture_output=True)
    git("init", "-q")
    (tmp_path / "one.txt").write_text("placeholder\n", encoding="utf-8")
    git("add", "one.txt")
    git("-c", "user.name=placeholder", "-c", "user.email=placeholder", "commit", "-q", "-m", "start")
    (tmp_path / "one.txt").rename(tmp_path / "renamed.txt")
    git("add", "--", "one.txt", "renamed.txt")
    assert land._staged(str(tmp_path)) == ["one.txt", "renamed.txt"]



def test_nothing_is_written_into_a_pin_by_any_role_and_the_checkouts_main_tree_is_the_operators(tmp_path, monkeypatch):
    """design-study/STEP-MISHMERET-MOVE-PLAN.md in Girsa, section 1, THE PIN: a pin (`<tree>/.pins/<sha>` of a tree in
    `guard.trees`) is the code every hook runs, so a file tool's write into it, or a git command there that changes a
    tree, is refused to every role, the operator too; a read passes, and so does a `.pins` folder of a tree not named.
    The checkout's own main tree is guarded like the project's: the operator's alone, its linked worktrees anyone's.
    Placeholder repositories in the placeholder project's checkout path."""
    import importlib.util
    import subprocess
    checkout = os.path.join(REPO, "checkout")              # the placeholder config's `guard.trees`
    git = lambda cwd, *a: subprocess.run(["git", "-C", str(cwd), "-c", "user.name=placeholder", "-c",
                                          "user.email=placeholder@example.org", *a], check=True, capture_output=True)
    os.makedirs(checkout)
    try:
        git(checkout, "init", "-q", "-b", "main")
        git(checkout, "commit", "-q", "--allow-empty", "-m", "placeholder")
        sha = subprocess.run(["git", "-C", checkout, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        pin = os.path.join(checkout, ".pins", sha)
        git(checkout, "worktree", "add", "-q", "--detach", pin, sha)
        git(checkout, "worktree", "add", "-q", "-b", "feature", os.path.join(checkout, "..", "checkout-feature"))
        spec = importlib.util.spec_from_file_location("role_guard", os.path.join(PKG, "role_guard.py"))
        rg = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rg)
        assert rg.pin_of(os.path.join(pin, "mishmeret", "role_guard.py")) == os.path.realpath(pin)
        assert rg.pin_of(os.path.join(checkout, ".pins")) is None and rg.pin_of(os.path.join(checkout, "x.py")) is None
        assert rg.pin_of(str(tmp_path / ".pins" / sha / "x.py")) is None, "a .pins folder of a tree not named"
        file_event = lambda role, path: {"tool_name": "Write", "agent_type": role,
                                         "tool_input": {"file_path": path, "content": "x"}}
        bash = lambda role, command, cwd: {"tool_name": "Bash", "agent_type": role, "cwd": cwd,
                                           "tool_input": {"command": command}}
        for role in ("ex-operator", "ex-builder", rg.NO_ROLE):
            assert rg.check(file_event(role, os.path.join(pin, "mishmeret", "board.py")), [""]) == 2, role
            for command, cwd in (("git checkout -q main", pin), (f"git -C {pin} reset --hard", REPO),
                                 (f"cd {pin} && git merge --ff-only main", REPO), ("git stash", pin)):
                assert rg.check(bash(role, command, cwd), [""]) == 2, (role, command)
            for command, cwd in (("git log -1", pin), ("git stash list", pin), (f"git -C {pin} status", REPO),
                                 (f"git -C {checkout} worktree add --detach .pins/{'1' * 40} main", REPO)):
                assert rg.check(bash(role, command, cwd), [""]) == 0, (role, command)
        # the checkout's main tree: the operator's alone; a linked worktree of it is anyone's
        assert rg.check(bash("ex-builder", "git checkout -q -b x", checkout), [""]) == 2
        assert rg.check(bash("ex-operator", "git merge --ff-only feature", checkout), [""]) == 0
        assert rg.check(bash("ex-builder", "git checkout -q -b x", os.path.join(checkout, "..", "checkout-feature")),
                        [""]) == 0
        assert rg.check(file_event("ex-builder", os.path.join(checkout, "README.md")), [""]) == 2
        assert rg.check(file_event("ex-operator", os.path.join(checkout, "README.md")), [""]) == 0
    finally:
        import shutil
        shutil.rmtree(checkout, ignore_errors=True)
        shutil.rmtree(os.path.join(REPO, "checkout-feature"), ignore_errors=True)


def test_no_role_changes_a_foreign_repository_in_its_main_clone_or_any_worktree(tmp_path):
    """Board #153 B: a repository in `guard.foreign` (a Mishmeret session wrote into Girsa: d87aa497, through land.py)
    is refused to every role, the operator too, in its main clone AND every linked worktree - a file tool's write, a
    git command that changes a tree (merge --ff-only too), and land.py commit or land. A read passes; so does a copy with
    its own .git, and the same commands in a worktree of a repository not named. The placeholder config names none
    (the field is optional: absent, FOREIGN is empty); the test names its own. Placeholder repositories in tmp_path."""
    import importlib.util
    import subprocess
    foreign, other = str(tmp_path / "foreign"), str(tmp_path / "other")
    git = lambda cwd, *a: subprocess.run(["git", "-C", str(cwd), "-c", "user.name=placeholder", "-c",
                                          "user.email=placeholder@example.org", *a], check=True, capture_output=True)
    for repo in (foreign, other):
        os.makedirs(repo)
        git(repo, "init", "-q", "-b", "main")
        git(repo, "commit", "-q", "--allow-empty", "-m", "placeholder")
        git(repo, "worktree", "add", "-q", "-b", "feature", repo + "-wt")
    subprocess.run(["cp", "-R", foreign, str(tmp_path / "copy")], check=True)
    spec = importlib.util.spec_from_file_location("role_guard", os.path.join(PKG, "role_guard.py"))
    rg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rg)
    assert rg.FOREIGN == ()
    rg.FOREIGN = (foreign,)
    file_event = lambda role, path: {"tool_name": "Write", "agent_type": role,
                                     "tool_input": {"file_path": path, "content": "x"}}
    bash = lambda role, command, cwd: {"tool_name": "Bash", "agent_type": role, "cwd": cwd,
                                       "tool_input": {"command": command}}
    for role in ("ex-operator", "ex-builder", rg.NO_ROLE):
        for tree in (foreign, foreign + "-wt"):
            assert rg.check(file_event(role, os.path.join(tree, "new", "x.md")), [""]) == 2, (role, tree)
            for command, cwd in (("git checkout -q -b x", tree), (f"git -C {tree} merge --ff-only main", REPO),
                                 (f"cd {tree} && ./venv/bin/python tools/land.py commit {role} code -F m x.py", REPO)):
                assert rg.check(bash(role, command, cwd), [""]) == 2, (role, command)
            for command, cwd in (("git log -1", tree), (f"git -C {tree} status", REPO), ("git stash list", tree)):
                assert rg.check(bash(role, command, cwd), [""]) == 0, (role, command)
        assert rg.check(file_event(role, str(tmp_path / "copy" / "x.md")), [""]) == 0, "a copy is not the repository"
    assert rg.check(file_event("ex-builder", os.path.join(other + "-wt", "x.md")), [""]) == 0
    assert rg.check(bash("ex-builder", "git checkout -q -b y", other + "-wt"), [""]) == 0
    assert rg.foreign_tree(foreign + "-wt") == foreign and rg.foreign_tree(other) is None


def test_a_clean_rebase_leaves_its_stamp_so_a_rebase_by_hand_before_the_next_call_is_checked(tmp_path, monkeypatch):
    """girsa-verifier's LOW 2 on step 3: the stamp, dropped after a rebase that finished in the call, left a rebase run
    by hand in the worktree before the next call unchecked. Now it is kept marked clean: at the next call it is dropped
    while the branch still sits on what it was rebased onto (an amend after a red gate lands, step 3's case), and the
    hand rebase's replays are checked when main has moved under it - a wrong resolution refused. Placeholder repos."""
    import subprocess
    for case in ("amended", "by hand"):
        (tmp_path / case.replace(" ", "-")).mkdir()
        land, main, tree, git, calls = _placeholder_clone_and_worktree(tmp_path / case.replace(" ", "-"), monkeypatch)
        (tree / "placeholder.py").write_text("def kept():\n    return 1\n\n\ndef added():\n    return 2\n",
                                             encoding="utf-8")
        git(tree, "commit", "-q", "-am", "placeholder: a function added")
        monkeypatch.setattr(land, "run_gate", lambda t, name: 1)
        with pytest.raises(land.Red):                                   # rebased cleanly, then the gate is red
            land.land("ex-builder", "code", cwd=str(tree), plan="plan.md")
        monkeypatch.setattr(land, "run_gate", lambda t, name: 0)
        if case == "amended":
            git(tree, "commit", "-q", "--amend", "-m", "placeholder: a function added, the message amended")
            head = land.land("ex-builder", "code", cwd=str(tree), plan="plan.md")
            assert git(main, "rev-parse", "main").strip() == head
            continue
        (main / "placeholder.py").write_text("def kept():\n    return 9\n", encoding="utf-8")
        git(main, "commit", "-q", "-am", "placeholder: main's change")
        assert subprocess.run(["git", "-C", str(tree), "rebase", "main"], capture_output=True).returncode != 0
        (tree / "placeholder.py").write_text("def kept():\n    return 9\n", encoding="utf-8")     # the branch's side lost
        git(tree, "add", "placeholder.py")
        subprocess.run(["git", "-C", str(tree), "-c", "core.editor=true", "rebase", "--continue"], check=True,
                       capture_output=True)
        with pytest.raises(land.Refused, match="left out by the rebase: the branch does not hold its change"):
            land.land("ex-builder", "code", cwd=str(tree), plan="plan.md")


def test_check_conflict_compares_three_versions_statement_by_statement():
    """land.merged_statement_faults (girsa-verifier's MEDIUM 2 on the landing plan): each top-level statement against the
    base and both sides. The keep-both merge that lost a test's last line (7d892135) is red; a function main deleted and
    the branch left alone is green when absent and red when kept; a module constant lost is red; a function both sides
    changed is named until accepted. Placeholder source."""
    land = _land()
    base = "LIMIT = 1\n\ndef shared():\n    return 1\n\ndef gone():\n    return 0\n"
    ours = "LIMIT = 1\n\ndef shared():\n    return 1\n\ndef test_a():\n    assert 1\n    assert 2\n"   # gone deleted
    theirs = base + "\ndef test_b():\n    assert 3\n"
    good = "LIMIT = 1\n\ndef shared():\n    return 1\n\ndef test_a():\n    assert 1\n    assert 2\n\ndef test_b():\n" \
           "    assert 3\n"
    assert land.merged_statement_faults(base, ours, theirs, good) == []
    lost_line = good.replace("    assert 2\n", "")
    assert land.merged_statement_faults(base, ours, theirs, lost_line) == [
        ("test_a", "differs from the side that changed it")]
    kept = good + "\ndef gone():\n    return 0\n"
    assert land.merged_statement_faults(base, ours, theirs, kept) == [
        ("gone", "present, where one side deleted it and the other left it")]
    assert land.merged_statement_faults(base, ours, theirs, good.replace("LIMIT = 1\n\n", "")) == [
        ("= LIMIT", "absent, where the merge keeps it")]
    both = theirs.replace("return 1", "return 2")
    ours_both = ours.replace("return 1", "return 3")
    resolved = good.replace("return 1", "return 3")
    assert [k for k, _w in land.merged_statement_faults(base, ours_both, both, resolved)] == ["shared"]
    assert land.merged_statement_faults(base, ours_both, both, resolved, accept=("shared",)) == []


def test_no_refusal_cites_one_projects_documents_board_items_or_dated_incidents():
    """Mishmeret is general-purpose (the reviewer in Girsa, 2026-11-01: "the next project will have different roles"):
    a refusal keeps its reason and its remedy, and cites no project's document, Board item, status id or dated incident
    (girsa-verifier's LOW on step 4; the words girsa-operator's). Every string a return or raise in the guard, the
    landing tool and the commit check builds; comments and docstrings are history and not read."""
    import ast
    cited = re.compile(r"Board #|LANES|START_HERE|WRITING\.md|\b0[A-Z]{2}\b|skill `|tools/land\.py|corpus root|"
                       r"rulings file|20\d\d-\d\d-\d\d")
    found = []
    for name in ("role_guard.py", "land.py", "time_precommit.py"):
        tree = ast.parse(open(os.path.join(PKG, name), encoding="utf-8").read())
        for node in ast.walk(tree):
            if isinstance(node, (ast.Return, ast.Raise)):
                for c in ast.walk(node):
                    if isinstance(c, ast.Constant) and isinstance(c.value, str) and cited.search(c.value):
                        found.append(f"{name}:{c.lineno}: {c.value}")
    assert not found, "\n".join(found)
