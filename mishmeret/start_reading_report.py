#!/usr/bin/env python3
"""What each role reads at start, in bytes - a report, not a hook (Board #63 A, 2026-10-20: the architect's plan,
design-study/START-READING-ARCHITECT.md, section 6: "the operator's measurement kept as a tool and run after each
step").

    venv/bin/python .claude/hooks/start_reading_report.py            one line per role
    venv/bin/python .claude/hooks/start_reading_report.py --check    exit 1 on a faulty START READS line

Each role's brief (the config's `start_reads.briefs`, a glob; in Girsa .claude/roles/girsa-*.md) names what it reads
at every start on ONE line:

    START READS: START_HERE.md, LESSONS.md, WRITING.md, design-study/STATE-girsa-<role>.md

paths from the repository's root; a `*` names the newest file it matches (a builder's handover). Added to each role:
what Claude Code loads into every session by itself (the two CLAUDE.md files and the memory index). A log is never on
the line - a status file is read on demand, by item id, never at start (the plan's step 1). A brief without the line
has not moved yet and is reported so.
"""
import glob
import os
import re
import subprocess
import sys

import config  # noqa: E402  (the project's config: mishmeret/config.py)

REPO = config.root()
TOKEN_BYTES = 3.6   # a rough rate for English prose; other alphabets run higher
BRIEFS = config.load()["start_reads"]["briefs"]           # the project's briefs, a glob from the root
LOGS = tuple(config.load()["start_reads"]["logs"])        # the project's logs, by file name: never on the line
LINE = re.compile(r"^START READS:\s*(.+)$", re.M)


def main_clone(repo):
    """The main clone's folder - the parent of git's common dir - since every role starts there, a worktree's report
    included (girsa-verifier's LOW on 9ccbdf2b: from a worktree the memory index was left out); `repo` when not git."""
    out = subprocess.run(["git", "-C", repo, "rev-parse", "--path-format=absolute", "--git-common-dir"],
                         capture_output=True, text=True)
    return os.path.dirname(out.stdout.strip()) if out.returncode == 0 else repo


def auto_loaded(repo, home=os.path.expanduser("~")):
    """[(name, path)] - what Claude Code puts into every session in this repository before its first message."""
    folder = main_clone(repo).replace("/", "-").replace(".", "-")
    memory = os.path.join(home, ".claude", "projects", folder, "memory", "MEMORY.md")
    return [("CLAUDE.md", os.path.join(repo, "CLAUDE.md")), ("~/.claude/CLAUDE.md", os.path.join(home, ".claude",
            "CLAUDE.md")), ("the memory index", memory)]


def resolve(repo, name):
    """The file a START READS entry names (a `*` the newest match), or None."""
    if "*" in name:
        found = sorted(glob.glob(os.path.join(repo, name)), key=os.path.getmtime)
        return found[-1] if found else None
    path = os.path.join(repo, name)
    return path if os.path.isfile(path) else None


def report(repo=REPO, home=os.path.expanduser("~")):
    """(lines, faults): one line per role; each fault a sentence naming the brief and the entry."""
    lines, faults = [], []
    auto = sum(os.path.getsize(p) for _, p in auto_loaded(repo, home) if os.path.isfile(p))
    lines += [f"(not counted - {name} not found at {p})" for name, p in auto_loaded(repo, home) if not os.path.isfile(p)]
    for brief in sorted(glob.glob(os.path.join(repo, BRIEFS))):
        role = os.path.basename(brief)[:-3]
        found = LINE.findall(open(brief, encoding="utf-8").read())
        if not found:
            lines.append(f"{role:20} not moved yet (no START READS line in its brief)")
            continue
        if len(found) > 1:
            faults.append(f"{role}: {len(found)} START READS lines - one only")
        total, parts = auto + os.path.getsize(brief), []
        for name in (n.strip() for n in found[0].split(",") if n.strip()):
            if os.path.basename(name) in LOGS:
                faults.append(f"{role}: {name} is a log - read it on demand, by item id, never at start")
            path = resolve(repo, name)
            if path is None:
                faults.append(f"{role}: {name} names no file")
                continue
            size = os.path.getsize(path)
            total += size
            parts.append(f"{name} {size / 1000:.1f}")
        lines.append(f"{role:20} {total / 1000:5.0f} KB (~{total / TOKEN_BYTES / 1000:.0f}k tokens): automatic "
                     f"{auto / 1000:.1f}, brief {os.path.getsize(brief) / 1000:.1f}, " + ", ".join(parts))
    return lines, faults


def main(argv):
    lines, faults = report()
    print("\n".join(lines + ["FAULT " + f for f in faults]))
    return 1 if ("--check" in argv and faults) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
