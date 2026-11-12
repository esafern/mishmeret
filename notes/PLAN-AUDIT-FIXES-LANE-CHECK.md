# The lane check's half of item 2 (notes/PLAN-AUDIT-FIXES.md): girsa-operator's own commit

`.claude/` is the operator's (`.claude/lanes.txt`), and this edit is the check itself, which judges the commit that
brings it (girsa-verifier's review, the first project's 3a321c10). So it is written and tested here and committed
by girsa-operator: `.claude/lane_check.py` reads the commit message's file that land.py names in
`MISHMERET_COMMIT_MESSAGE`, and `tests/test_own_project.py` gains its test. Either commit may come first: with the
variable unset, nothing more is read.

Applied from the repository's top:

    sed -n '/^```diff$/,/^```$/{/^```/d;p;}' notes/PLAN-AUDIT-FIXES-LANE-CHECK.md | git apply

Measured on a scratch copy of builder-audit-fixes: applied, `tests/test_own_project.py` 4 passed and the whole suite
147 passed; the new test alone over today's lane check: 1 failed (its rule out).

```diff
diff -ru a/.claude/lane_check.py b/.claude/lane_check.py
--- a/.claude/lane_check.py
+++ b/.claude/lane_check.py
@@ -6,7 +6,9 @@
 Fails (exit 1) on a staged path outside ROLE's lane in `.claude/lanes.txt` - reported, not failed, under `--because`,
 the reviewer's words the commit message then carries; on a path not a `.md` under `--doc-only`; and, on every commit,
 whatever its paths (this repository is PUBLIC), on an added line holding a personal address, a name or address from
-the local roster, or this machine's home folder - counted by file, the text never shown. The roster is
+the local roster, or this machine's home folder - counted by file, the text never shown - and on a line of the commit's
+message so holding one, the file land.py names in MISHMERET_COMMIT_MESSAGE (notes/PLAN-AUDIT-FIXES.md, item 2; unset,
+no message is read). The roster is
 `.claude/roster.local.json` in the MAIN clone, untracked ({"reviewers": {id: {"display", "email"}}}, a Girsa roster's
 shape); without it the names go unchecked and the report says so. `--range` and `--plan` are refused (exit 2): no one
 runs `land.py land` here; the operator merges."""
@@ -69,17 +71,25 @@
             out.append(f"  NOT A DOCUMENT (--doc-only): {p}")
             failed = True
     pattern, why = forbidden()
+    carries = lambda line: [a for a in PERSONAL_ADDRESS.findall(line) if not NOT_PERSONAL.search(a)] or pattern.search(line)
     added, path = {}, None
     for line in git("diff", "--cached", "-U0", "--no-color", "--no-renames").splitlines():
         if line.startswith("+++ "):
             path = line[6:]
         elif line.startswith("+") and path:
-            if [a for a in PERSONAL_ADDRESS.findall(line) if not NOT_PERSONAL.search(a)] or pattern.search(line):
+            if carries(line):
                 added[path] = added.get(path, 0) + 1
     for p, n in sorted(added.items()):
         out.append(f"  {p}: {n} added line{' carries' if n == 1 else 's carry'} a personal address, a roster name or "
                    "this machine's home folder (the text is not shown here)")
         failed = True
+    if os.environ.get("MISHMERET_COMMIT_MESSAGE"):
+        with open(os.environ["MISHMERET_COMMIT_MESSAGE"], encoding="utf-8") as fh:
+            n = sum(1 for line in fh if carries(line))
+        if n:
+            out.append(f"  the commit message: {n} line{' carries' if n == 1 else 's carry'} a personal address, a roster "
+                       "name or this machine's home folder (the text is not shown here)")
+            failed = True
     out += [f"  {why}"] if why else []
     print("\n".join(out + ["FAIL" if failed else "PASS"]))
     return 1 if failed else 0
diff -ru a/tests/test_own_project.py b/tests/test_own_project.py
--- a/tests/test_own_project.py
+++ b/tests/test_own_project.py
@@ -80,3 +80,24 @@
     stage("notes/named.md", "as placeholder.person said\n")
     rc, out = check("mishmeret-builder")
     assert rc == 1 and "notes/named.md: 1 added line" in out and "no name was checked" not in out, out
+
+
+def test_the_commit_message_is_scanned_as_the_added_lines_are(staged, monkeypatch, tmp_path_factory):
+    """notes/PLAN-AUDIT-FIXES.md, item 2: land.py hands the lane check the commit's message (MISHMERET_COMMIT_MESSAGE),
+    which it scans as it scans the added lines - a line holding this machine's home folder fails, the text not shown;
+    a clean message passes; unset, no message is read."""
+    stage, check, _ = staged
+    stage("notes/ok.md")
+    folder = tmp_path_factory.mktemp("message")
+    bad, good = folder / "bad.txt", folder / "good.txt"
+    bad.write_text("Placeholder change\n\nran in " + os.path.expanduser("~") + "/x\n", encoding="utf-8")
+    good.write_text("Placeholder change\n", encoding="utf-8")
+    monkeypatch.setenv("MISHMERET_COMMIT_MESSAGE", str(bad))
+    rc, out = check("mishmeret-builder")
+    assert rc == 1 and "the commit message: 1 line carries" in out and os.path.expanduser("~") not in out, out
+    monkeypatch.setenv("MISHMERET_COMMIT_MESSAGE", str(good))
+    rc, out = check("mishmeret-builder")
+    assert rc == 0 and "the commit message" not in out, out
+    monkeypatch.delenv("MISHMERET_COMMIT_MESSAGE")
+    rc, out = check("mishmeret-builder")
+    assert rc == 0 and "the commit message" not in out, out
```
