#!/usr/bin/env python3
"""mishmeret/land.py, run from the commit .claude/mishmeret.json pins (.claude/mishmeret_shim.py), with the same
arguments, or stood in for when imported. A missing checkout or pin is said, and the command exits 1."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "."))
import mishmeret_shim  # noqa: E402

mishmeret_shim.stand_in(__name__, ".claude/land.py", "land", "command")
