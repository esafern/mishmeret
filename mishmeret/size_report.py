#!/usr/bin/env python3
"""Which start-up documents are near their size limit - a report, not a hook; the operator runs it at every start and
tells the reviewer (the reviewer, 2026-10-06: "i've seen a session rewriting some wording to squeeze a few kb out of
text to make it just barely fit - that is not a good process").

    venv/bin/python .claude/hooks/size_report.py            every file and status item read at a role's start
    venv/bin/python .claude/hooks/size_report.py --check    exit 1 when one is over its limit

WHY A WARNING BAND. A session that meets a limit in the middle of its own task trims a few words to get past it. A
file flagged at WARN of its limit, at the start of a session, gets a whole block moved to its home as planned work.
The remedy is always the same: move a WHOLE block, word for word, to the home named below - never reword to fit, and
never raise a limit without the reviewer.
"""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
WARN = 0.80
READ = 100_000      # about 25,000 tokens - what one Read loads
HISTORY = "PROJECT-STATUS-HISTORY.md under a dated heading"

# path: (limit in bytes, where a whole block goes)
FILES = {
    "START_HERE.md": (30_000, "START_HERE-HISTORY.md (reasoning, incidents) or a role's own file (a role's procedure)"),
    "LESSONS.md": (30_000, "START_HERE-HISTORY.md (each lesson's long form, by number)"),
    "WRITING.md": (30_000, "START_HERE-HISTORY.md (reasoning, incidents)"),
    "PROJECT-STATUS.md": (60_000, "tools/split_project_status.py (settled items), " + HISTORY + " (old TL;DR lines)"),
    ".claude/agents/LANES.md": (30_000, "design-study/SESSION-ROLES-PLAN.md (the plan behind the lanes)"),
    "design-study/OPERATOR-NOTEBOOK.md": (READ, HISTORY),
    "design-study/VERIFIER-NOTEBOOK.md": (READ, HISTORY),
    "design-study/ARCHITECT-NOTEBOOK.md": (READ, HISTORY),
    "design-study/STEP5-HANDOVER.md": (READ, "the step's status item"),
}
ITEM_LIMIT = READ   # a role's open status item: rotate it (a new item; the old one archived by the split tool)
# a role's current state, read at every start (Board #63 A): what is open, waiting and next - a few KB, never history
STATE_GLOB, STATE_LIMIT = "design-study/STATE-girsa-*.md", 6_000
STATE_HOME = "the role's log (its status item), the block's settled lines"


def open_items(path):
    """[(id, bytes)] of the items in PROJECT-STATUS-OPEN.md's first "## Open items" section."""
    text = open(path, encoding="utf-8").read()
    first = text.split("\n## ", 1)[0]      # the file opens with "## Open items"; the next "## " ends it
    out, cur, size = [], None, 0
    for line in first.split("\n"):
        m = re.match(r"^(0[A-Z0-9]{2})\. ", line)
        if m:
            if cur:
                out.append((cur, size))
            cur, size = m.group(1), 0
        if cur:
            size += len(line.encode("utf-8")) + 1
    if cur:
        out.append((cur, size))
    return out


def report(repo=REPO):
    """(lines, over): one line per file or item at WARN of its limit or above; the names over the limit."""
    lines, over = [], []
    rows = [(p, os.path.getsize(os.path.join(repo, p)), lim, home) for p, (lim, home) in FILES.items()
            if os.path.exists(os.path.join(repo, p))]
    rows += [(os.path.relpath(p, repo), os.path.getsize(p), STATE_LIMIT, STATE_HOME)
             for p in sorted(glob.glob(os.path.join(repo, STATE_GLOB)))]
    status_open = os.path.join(repo, "PROJECT-STATUS-OPEN.md")
    if os.path.exists(status_open):
        rows += [(f"status item {i}", n, ITEM_LIMIT, "a new item for the role; the old one archived by the split tool")
                 for i, n in open_items(status_open)]
    for name, size, limit, home in rows:
        share = size / limit
        if share >= WARN:
            word = "OVER" if share > 1 else "near"
            lines.append(f"{word:4} {name}: {size:,} of {limit:,} bytes ({share:.0%}) - move a whole block to {home}")
            if share > 1:
                over.append(name)
    if not lines:
        lines.append(f"every start-up document is under {WARN:.0%} of its limit")
    return lines, over


def main(argv):
    lines, over = report()
    print("\n".join(lines))
    return 1 if ("--check" in argv and over) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
