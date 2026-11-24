"""Every distinct (command, cwd, role) a session ran in a shell, from the transcripts under the folders given: Claude
Code's (`~/.claude/projects/<folder>`, its Bash tool_use; the role its transcript's agentSetting or agentName, a
subagent's its parent session's) and pi's (`~/.pi/agent/sessions/<folder>`, its bash toolCall, the cwd from the session's header; no
role). Written as JSON lines {"command", "cwd", "folder", "role"} to OUT - the role null where none is on the record,
for decide.py's `each` (notes/PLAN-PROTECTED-REFS.md: rule 45 by the role that ran each command).

    python3 -I extract.py OUT FOLDER...

Prints the transcripts read and the pairs written. The transcripts are private: OUT stays in a scratch folder, and only
counts and placeholder forms of what it holds go into this repository."""
import json
import os
import sys


def commands(path):
    """(command, cwd) for each shell command in one transcript file."""
    cwd = ""
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if '"Bash"' not in line and '"bash"' not in line and '"session"' not in line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if rec.get("type") == "session":                # pi: the session's header holds its cwd
                cwd = rec.get("cwd") or ""
            content = (rec.get("message") or {}).get("content")
            for part in content if isinstance(content, list) else ():
                if not isinstance(part, dict):
                    continue
                if part.get("type") == "tool_use" and part.get("name") == "Bash":                # Claude Code
                    cmd, where = (part.get("input") or {}).get("command"), rec.get("cwd") or ""
                elif part.get("type") == "toolCall" and part.get("name") == "bash":               # pi
                    cmd, where = (part.get("arguments") or {}).get("command"), cwd
                else:
                    continue
                if isinstance(cmd, str) and cmd:
                    yield cmd, where


def role_of(path):
    """The role a Claude Code transcript's session ran as: its agentSetting, else its agentName (the first project's
    October and November transcripts hold only the name, 180 of them), or None."""
    found = {}
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if '"agent-setting"' in line or '"agent-name"' in line:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                found.setdefault(rec.get("type"), rec.get("agentSetting") or rec.get("agentName"))
    return found.get("agent-setting") or found.get("agent-name")


def main(out, folders):
    seen, files = set(), 0
    with open(out, "w", encoding="utf-8") as fh:
        for folder in folders:
            sessions = {n[:-len(".jsonl")]: role_of(os.path.join(folder, n)) for n in os.listdir(folder)
                        if n.endswith(".jsonl")}
            for dp, _, names in os.walk(folder):
                for name in sorted(names):
                    if not name.endswith(".jsonl"):
                        continue
                    files += 1
                    # a subagent's transcript, under <session>/, runs as its parent session's role
                    role = sessions.get(name[:-len(".jsonl")] if dp == folder else
                                        os.path.relpath(dp, folder).split(os.sep)[0])
                    for cmd, cwd in commands(os.path.join(dp, name)):
                        if (cmd, cwd, role) not in seen:
                            seen.add((cmd, cwd, role))
                            fh.write(json.dumps({"command": cmd, "cwd": cwd, "folder": os.path.basename(folder),
                                                 "role": role}) + "\n")
    print(f"transcripts: {files}, distinct command-cwd-role triples: {len(seen)}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2:])
