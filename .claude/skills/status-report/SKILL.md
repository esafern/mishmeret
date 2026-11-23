---
name: status-report
description: The big picture of Mishmeret for the reviewer - each piece in flight and what is left to land it, what is next and its size, what each project that pins Mishmeret runs, the loose ends and technical debt, who waits on whom, and what waits on the reviewer - from the records and read-only counts; any role, when the reviewer asks.
---

The reviewer, 2026-11-23, in mishmeret-builder's pane: "grab the status-report skill from girsa and add it to
mishmeret", then "do s-r first and give me one". Taken from the first project's skill of that name, which the reviewer
had sent back once for listing what each role did instead of answering "how much is left". Any role runs it when the
reviewer asks for the big picture or types `/status-report`. It reads records and runs read-only counts; it changes
nothing and proposes nothing new.

**Read, in the same turn as the report:**
1. Every role's state file (`sizes.state_files` in `.claude/mishmeret.json`): its Built, Now, Next and Open lines.
2. What is LEFT, where it is written: the plan of each piece in flight (`notes/PLAN-*.md` named in a state's Now), its
   `## The case`, its items and the review recorded at its head; the latest item of `notes/LOG.md` for what was found
   and not fixed.
3. Mishmeret's Board: `python3 .claude/board/board.py list --open`, and each role's corner, its last `status` record:
   ```
   python3 -c '
   import json, os
   d = os.environ.get("MISHMERET_BOARD_DIR") or os.path.expanduser(json.load(open(".claude/mishmeret.json", encoding="utf-8"))["board_dir"])
   last = {}
   for line in open(os.path.join(d, "board.jsonl"), encoding="utf-8"):
       r = json.loads(line)
       if r.get("type") == "status": last[r["role"]] = r
   for role, r in last.items(): print(role, r["ts"][:16], r.get("state"), "waits for", r.get("waiting_for"), "|", r.get("now", ""))
   '
   ```
4. EACH PROJECT THAT PINS MISHMERET - each repository in the config's `guard.foreign`, read only: the commit its
   `.claude/mishmeret.json` names (`mishmeret_commit`) against Mishmeret's main, and the open items on its Board (its
   config's `board_dir`) that ask about Mishmeret - the reviewer answers those there, not here:
   ```
   python3 -c '
   import json, os, sys
   cfg = json.load(open(os.path.join(os.path.expanduser(sys.argv[1]), ".claude", "mishmeret.json"), encoding="utf-8"))
   print("pins", cfg["mishmeret_commit"][:7])
   rows, closed = {}, set()
   for line in open(os.path.join(os.path.expanduser(cfg["board_dir"]), "board.jsonl"), encoding="utf-8"):
       r = json.loads(line)
       if r.get("type") == "item": rows[r["id"]] = r
       elif r.get("type") in ("answer", "withdraw"): closed.add(r.get("id"))
   for i, r in sorted(rows.items()):
       if i not in closed and "mishmeret" in (r.get("title", "") + r.get("body", "")).lower():
           print("#%s" % i, r["ts"][:16], r["role"], "|", r["title"])
   ' <the project's tree>
   ```
5. The counts, run then: `git log --oneline -1 main`; `git rev-list --count origin/main..main` (said "not fetched"
   unless fetched in that turn); `git branch --no-merged main` and the merged `builder-*` branches; each worktree
   (`git worktree list`) and whether a session runs in it (`ListAgents`); the pins (`ls .pins`) against the projects'
   `mishmeret_commit`; the suite's size from `pytest --collect-only -q`, never from a grep (DEFINED IS NOT COLLECTED);
   main's commits per day (`git log --since=<14 days ago> --format=%ad --date=short main | uniq -c`) - the pace.

**The report, in this order - the reviewer's questions first:**
1. **Each piece in flight: how much is left to land it.** Its stages, each with its commit or its message: plan,
   review, build, check, merge, push, and each pinning project's pin. What it is waiting for, and on whom.
2. **What is next, and its size.** Each state's Next, in order. An estimate of each, labeled as the role's, with the
   pace it rests on and what would make it wrong (an item that grew while its plan was measured).
3. **The projects that pin Mishmeret.** Each one's pin against main: the pieces it does not run yet, by commit. Its
   Board's open items about Mishmeret, each by #N.
4. **Loose ends and technical debt.** The states' Open lines; review LOWs left for a later touch, counted; tests red,
   skipped or held; findings logged and not fixed; housekeeping (commits not pushed, branches merged and not deleted,
   worktrees with no session, untracked files in a tree).
5. **Now:** each role's piece now and next, and who waits on whom - a role waiting on an idle role, or a corner older
   than its role's last commit, named first.
6. **What waits on the reviewer** - each item with what it is, why it is theirs, what happens on their answer, and its
   Board #N (on which project's Board) or full path.

**The rules:**
- Every count is copied with its source named, or run in that turn with its command named - never from memory or an
  earlier reply (SAY WHICH ONE YOU CHECKED); a sentence of absence likewise (A SENTENCE OF ABSENCE IS A CLAIM).
- An estimate is a number with its basis, labeled as the role's; never a date no record holds. A list of what each
  role is doing is not an answer to "how much is left".
- "Merged", "pushed", "pinned" and a Board item's state are read in that turn, from git and the Board's record (STATE,
  NOT PRINTOUT).
- Every entry named carries its Board #N or commit, every file its full path; roles, never people's names; paths with
  `~` (this repository is public). Plain words, no arrows.
- It ends by naming what it rests on - the files read, the counts run - and what it did not check.
- The full report goes on Mishmeret's Board, `board.py qa --role <you> --question "<the reviewer's words>"
  --answer-file F`; the pane gets the answers in short, a few lines a question, and the Board's link.
- A fault seen while reading goes the usual way - logged in the role's log, to its owner - not into the report as new
  work.
