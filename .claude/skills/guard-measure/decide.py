"""Rule 45's one side: the guard in GUARD_DIR (a folder holding role_guard.py and config.py - a `git archive` extract
of the old commit, or a copy of the new `mishmeret/`, never the tree being edited) judges every command in CMDS
(extract.py's output) at its cwd, as ROLE, under the project config CONFIG, with the Bash rules the hook runs (the time
rule aside: the same code on both sides). Writes one JSON line per command to OUT: {"i", "why"} (the refusal or null)
or {"i", "fault"}. Git's tree lookups and the scripts it reads are memoized; each side runs in its own process.

    python3 -I decide.py GUARD_DIR CONFIG CMDS ROLE OUT"""
import functools
import json
import os
import sys


def main(folder, cfg, cmds, role, out):
    os.environ["MISHMERET_CONFIG"] = cfg
    for k in ("CLAUDE_PROJECT_DIR", "MISHMERET_AS", "MISHMERET_TREE"):
        os.environ.pop(k, None)
    sys.path.insert(0, folder)
    import role_guard as rg
    rg._git_dirs = functools.lru_cache(maxsize=None)(rg._git_dirs)
    rg.guarded_git_dirs = functools.lru_cache(maxsize=None)(rg.guarded_git_dirs)
    read = functools.lru_cache(maxsize=None)(rg._read)
    with open(cmds, encoding="utf-8") as fh, open(out, "w", encoding="utf-8") as w:
        for i, line in enumerate(fh):
            r = json.loads(line)
            c, cwd = r["command"], r["cwd"] or os.path.expanduser("~")
            try:
                why = (rg.refusal(role, c, cwd, read=read) or rg.tmux_refusal(c, cwd, read=read)
                       or rg.copy_refusal(c, cwd) or rg.check_status_refusal(c, cwd, read=read)
                       or rg.piped_check_refusal(c, cwd, read=read))
                w.write(json.dumps({"i": i, "why": why}) + "\n")
            except Exception as e:
                w.write(json.dumps({"i": i, "fault": f"{type(e).__name__}: {e}"}) + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 6:
        sys.exit(__doc__)
    main(*sys.argv[1:])
