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

import config  # noqa: E402  (the project's config: mishmeret/config.py)

REPO = config.root()
_SIZES = config.load()["sizes"]   # every limit and home is the project's (its `sizes` field)
WARN = _SIZES["warn_percent"] / 100

# path: (limit in bytes, where a whole block goes)
FILES = {path: tuple(row) for path, row in _SIZES["files"].items()}
ITEM_LIMIT = _SIZES["item_limit"]   # a role's open status item: rotate it (a new item; the old one archived)
ITEM_HOME = _SIZES["item_home"]
STATUS_FILE = _SIZES["status_file"]
ITEM = re.compile(_SIZES["item_pattern"])
# a role's current state, read at every start: what is open, waiting and next - a few KB, never history
STATE_GLOB, STATE_LIMIT = _SIZES["state_files"], _SIZES["state_limit"]
STATE_HOME = _SIZES["state_home"]


def open_items(path):
    """[(id, bytes)] of the items in the open status file's first section (it opens with "## Open items"); an item
    starts at a line ITEM matches, its id the first group."""
    text = open(path, encoding="utf-8").read()
    first = text.split("\n## ", 1)[0]      # the file opens with "## Open items"; the next "## " ends it
    out, cur, size = [], None, 0
    for line in first.split("\n"):
        m = ITEM.match(line)
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
    status_open = os.path.join(repo, STATUS_FILE)
    if os.path.exists(status_open):
        rows += [(f"status item {i}", n, ITEM_LIMIT, ITEM_HOME) for i, n in open_items(status_open)]
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
