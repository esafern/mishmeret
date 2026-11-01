import sys, json, glob, os
# usage.py TRANSCRIPT START END [MARK]: tokens of every API call in [START, END) UTC, subagents included, deduped by message id
f, start, end = sys.argv[1], sys.argv[2], sys.argv[3]
mark = sys.argv[4] if len(sys.argv) > 4 else None
files = [f] + glob.glob(os.path.join(f[:-6], "subagents", "*.jsonl"))
seen, tot, marks = set(), dict(inp=0, cw=0, cr=0, out=0, calls=0), []
for fn in files:
    for line in open(fn, encoding="utf-8"):
        try: r = json.loads(line)
        except Exception: continue
        ts = r.get("timestamp", "")
        if not (start <= ts < end): continue
        m = r.get("message") or {}
        if mark and r.get("type") == "user" and isinstance(m.get("content"), str) and mark in m["content"]:
            marks.append(ts[:19])
        u = m.get("usage") if r.get("type") == "assistant" else None
        if not u or m.get("id") in seen: continue
        seen.add(m.get("id")); tot["calls"] += 1
        tot["inp"] += u.get("input_tokens", 0); tot["cw"] += u.get("cache_creation_input_tokens", 0)
        tot["cr"] += u.get("cache_read_input_tokens", 0); tot["out"] += u.get("output_tokens", 0)
print(f"calls {tot['calls']}  input {tot['inp']:,}  cache-write {tot['cw']:,}  cache-read {tot['cr']:,}  output {tot['out']:,}  subagent files {len(files)-1}")
if marks: print("marks:", marks[:3], "...", marks[-2:])
