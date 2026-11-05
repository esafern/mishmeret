"""HOW THIS PROJECT RUNS MISHMERET: every hook and command in `.claude/` is a few lines that call `stand_in` here. It runs
the same-named module of the ONE Mishmeret commit `.claude/mishmeret.json` names (`mishmeret_commit`), from that commit's
own worktree, `<checkout>/.pins/<sha>` - so the code every hook runs and the config it reads change in one commit. The
checkout is `~/work/mishmeret`, or MISHMERET_DIR. A command (never a hook, whose environment is Claude Code's) may name
another tree in MISHMERET_TREE - a branch being built. The README's "How a project uses it"; this file is the project's
own, the one bootstrap copy (the first project's, Girsa's `.claude/mishmeret_shim.py`, less its retired variable names).

    stand_in(__name__, ".claude/board/board.py", "board", "command")

Run as a script, the moved module runs as `__main__` with the same arguments and its exit status; imported, the moved
module is put in `sys.modules` under the old name, so the importer gets it.

WHAT A FAULT DOES IS THE PATH'S OWN: a missing checkout or pin, an unreadable config, a fault in the import or the run -
each prints its sentence and exits 2 where the path `refuses` (it guards: a 1 would let the action through), 1 where it
`reports` or is a command."""
import json
import os
import runpy
import sys
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, ".claude", "mishmeret.json")
KINDS = {"refuses": 2, "reports": 1, "command": 1}


class Missing(Exception):
    pass


def tree(kind):
    """The Mishmeret tree to run: MISHMERET_TREE for a command, else the pinned commit's worktree. Raises Missing with
    the sentence to print."""
    if kind == "command" and os.environ.get("MISHMERET_TREE"):
        return os.environ["MISHMERET_TREE"]
    with open(CONFIG, encoding="utf-8") as fh:
        cfg = json.load(fh)
    checkout = os.path.expanduser(os.environ.get("MISHMERET_DIR") or "~/work/mishmeret")
    if not os.path.isdir(checkout):
        raise Missing(f"Mishmeret is not at {checkout}: in your own terminal, clone {cfg['repository']} there, or set "
                      f"MISHMERET_DIR to its checkout.")
    sha = cfg["mishmeret_commit"]
    pin = os.path.join(checkout, ".pins", sha)
    if not os.path.isdir(os.path.join(pin, "mishmeret")):
        raise Missing(f"Mishmeret's pinned commit {sha} has no worktree at {pin}: in your own terminal, run\n"
                      f"git -C {checkout} fetch\nthen\ngit -C {checkout} worktree add --detach {pin} {sha}")
    return pin


def _prepare(old, kind):
    pkg = os.path.join(tree(kind), "mishmeret")
    # A CONFIG A SHIM SET IS ITS OWN TREE'S, NEVER ANOTHER'S: a value a shim set (marked in MISHMERET_CONFIG_BY_SHIM)
    # gives way to this shim's own; one set by hand - a test's placeholder project - is kept.
    if os.environ.get("MISHMERET_CONFIG") in (None, os.environ.get("MISHMERET_CONFIG_BY_SHIM")):
        os.environ["MISHMERET_CONFIG"] = os.environ["MISHMERET_CONFIG_BY_SHIM"] = CONFIG
    os.environ["MISHMERET_AS"] = old
    # FIRST on the path, every time: a shim's folder put in front of it later would make the moved name find the shim
    # again, which imports itself until Python's recursion limit
    while pkg in sys.path:
        sys.path.remove(pkg)
    sys.path.insert(0, pkg)
    return pkg


def _fail(old, kind, said):
    print(f"{said} ({old} did not run.)", file=sys.stderr)
    sys.exit(KINDS[kind])


def stand_in(name, old, module, kind):
    """Run (`name` is "__main__") or stand in for (imported) the moved `module`; `old` is this path, from the root."""
    if kind not in KINDS:
        raise ValueError(f"kind {kind!r}: one of {', '.join(KINDS)}")
    if name != "__main__":
        _prepare(old, "command" if kind == "command" else kind)
        sys.modules.pop(module, None)
        moved = __import__(module)
        sys.modules[name] = moved
        return moved
    try:
        pkg = _prepare(old, kind)
    except Missing as e:
        _fail(old, kind, str(e))
    except Exception:
        _fail(old, kind, "Mishmeret could not be found: " + traceback.format_exc().strip())
    path = os.path.join(pkg, module + ".py")
    sys.argv[0] = path
    try:
        runpy.run_path(path, run_name="__main__")
    except SystemExit:
        raise
    except Exception:
        _fail(old, kind, traceback.format_exc().strip())
    sys.exit(0)
