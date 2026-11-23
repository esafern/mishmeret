"""Rule 45's comparison: CMDS (extract.py's output), OLD and NEW (decide.py's, one side each). Prints the counts -
newly refused, newly let through, faults - then each changed decision: its cwd, the command (its first 300
characters) and the new reason, or the old one for a command now let through. Exits 1 when the three files differ in
length (the sides judged different records) or a side faulted.

    python3 -I compare.py CMDS OLD NEW"""
import json
import sys


def main(cmds_path, old_path, new_path):
    load = lambda p: [json.loads(line) for line in open(p, encoding="utf-8")]
    cmds, old, new = load(cmds_path), load(old_path), load(new_path)
    if not len(cmds) == len(old) == len(new):
        print(f"the files differ in length: {len(cmds)} commands, {len(old)} old, {len(new)} new")
        return 1
    refused, through, faults = [], [], []
    for c, o, n in zip(cmds, old, new):
        if "fault" in o or "fault" in n:
            faults.append((c, o.get("fault") or n.get("fault")))
        elif not o["why"] and n["why"]:
            refused.append((c, n["why"]))
        elif o["why"] and not n["why"]:
            through.append((c, o["why"]))
    print(f"judged {len(cmds)}: newly refused {len(refused)}, newly let through {len(through)}, faults {len(faults)}")
    for title, rows in (("NEWLY REFUSED", refused), ("NEWLY LET THROUGH (the old reason)", through), ("FAULTS", faults)):
        print(f"\n== {title}")
        for c, why in rows:
            print(f"-- cwd {c['cwd']}\n   {c['command'][:300]!r}\n   => {str(why)[:300]}")
    return 1 if faults else 0


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    sys.exit(main(*sys.argv[1:]))
