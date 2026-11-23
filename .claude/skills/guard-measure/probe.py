"""A probe: the guard in TREE (its `mishmeret/role_guard.py`, under the placeholder project of TREE's tests/conftest.py)
judges each case in CASES - a JSON list of [role, cwd, command] - with every Bash rule the hook runs (rules.py), on
placeholder paths: the main tree `/work/book`, its worktrees `/work/book-*` (a worktree's top folder for the copy
rule), the guarded repository both. No git and no file is read: those are judged by the paths alone, a script by an
empty read. Prints each case's decision and the reason's first words.

    python3 probe.py TREE CASES          (TREE: a copy or an extract of the commit to measure)"""
import importlib.util
import json
import os
import sys


def main(tree, cases):
    sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.path.join(tree, "tests")]
    import conftest  # noqa: F401  (the placeholder project's config, set before the guard loads it)
    from rules import judge
    spec = importlib.util.spec_from_file_location("role_guard", os.path.join(tree, "mishmeret", "role_guard.py"))
    rg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rg)
    norm = lambda p: os.path.normpath(p) + "/"
    ours = lambda p: norm(p).startswith(("/work/book/", "/work/book-"))
    fakes = {"main_tree": lambda p: norm(p).startswith("/work/book/") and "/work/book/.git" not in p,
             "project_tree": ours, "guarded": ours,
             "is_worktree": lambda p: os.path.normpath(p).startswith("/work/book-") and os.path.normpath(p).count("/") == 2}
    for role, cwd, cmd in json.load(open(cases, encoding="utf-8")):
        why = judge(rg, role, cmd, cwd, {}.get, fakes)
        print(f"{'REFUSED' if why else 'let through':11} {role:12} {cwd:20} {cmd!r}  {(why or '')[24:100]}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
