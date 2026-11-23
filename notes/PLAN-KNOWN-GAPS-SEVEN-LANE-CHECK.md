# The lane check's half of item 9 (notes/PLAN-KNOWN-GAPS-SEVEN.md): girsa-operator's own commit

`.claude/` is the operator's (`.claude/lanes.txt`), and this edit is the check itself, which judges the commit that
brings it (girsa-verifier's ruling on the audit fixes, M09). So it is written and tested here and committed by
girsa-operator: in `.claude/lane_check.py` a `+++ ` line is a file's header only between `diff --git` and the file's
first `@@` - an added line that begins "++ " reads `+++ ...` in the diff, and was left unscanned, the file's next lines
filed under a path cut from it. `tests/test_own_project.py` gains its test. The same fix to
`mishmeret/time_precommit.py` is in e5a4d40. Either commit may come first.

Applied from the repository's top:

    sed -n '/^```diff$/,/^```$/{/^```/d;p;}' notes/PLAN-KNOWN-GAPS-SEVEN-LANE-CHECK.md | git apply

Measured on a copy of the main clone at e5a4d40: the diff below, extracted by that command, is byte for byte the
worktree's; applied, the whole suite 161 passed; tests/test_own_project.py over today's lane check, the new test in it: 1 failed, 3 passed (its rule out).

```diff
diff --git a/.claude/lane_check.py b/.claude/lane_check.py
index 295d26d..f7ff98f 100644
--- a/.claude/lane_check.py
+++ b/.claude/lane_check.py
@@ -72,11 +72,17 @@ def main(argv):
             failed = True
     pattern, why = forbidden()
     carries = lambda line: [a for a in PERSONAL_ADDRESS.findall(line) if not NOT_PERSONAL.search(a)] or pattern.search(line)
-    added, path = {}, None
+    added, path, hunk = {}, None, False
     for line in git("diff", "--cached", "-U0", "--no-color", "--no-renames").splitlines():
-        if line.startswith("+++ "):
+        # a "+++ " line is a header only before the file's first @@: an added line "++ x" reads "+++ x" too, and was
+        # left unscanned, the file's next lines filed under it (notes/PLAN-KNOWN-GAPS.md, item 9)
+        if line.startswith("diff --git "):
+            hunk = False
+        elif line.startswith("@@"):
+            hunk = True
+        elif not hunk and line.startswith("+++ "):
             path = line[6:]
-        elif line.startswith("+") and path:
+        elif hunk and line.startswith("+") and path:
             if carries(line):
                 added[path] = added.get(path, 0) + 1
     for p, n in sorted(added.items()):
diff --git a/tests/test_own_project.py b/tests/test_own_project.py
index 0893995..8a880c7 100644
--- a/tests/test_own_project.py
+++ b/tests/test_own_project.py
@@ -75,6 +75,13 @@ def test_every_commit_is_scanned_for_an_address_a_roster_name_and_the_home_folde
         rc, out = check("mishmeret-builder")
         assert rc == 1 and f"notes/bad{i}.md: 1 added line carries" in out and line.strip() not in out, out
         subprocess.run(["git", "-C", str(root), "rm", "-q", "--cached", f"notes/bad{i}.md"], check=True)
+    # AN ADDED LINE THAT BEGINS "++ " reads "+++ ..." in the diff, as a file's header (notes/PLAN-KNOWN-GAPS.md, item 9):
+    # it went unscanned, and the file's next line was filed under a "path" cut from it - its text in the report
+    address = "pp" + "@" + "mail.co"
+    stage("notes/plus.md", f"++ mail {address}\nmail {address}\n")
+    rc, out = check("mishmeret-builder")
+    assert rc == 1 and "notes/plus.md: 2 added lines carry" in out and address not in out, out
+    subprocess.run(["git", "-C", str(root), "rm", "-q", "--cached", "notes/plus.md"], check=True)
     (root / ".claude" / "roster.local.json").write_text(json.dumps(
         {"reviewers": {"r1": {"display": "Placeholder Person", "email": "pp" + "@" + "mail.co"}}}), encoding="utf-8")
     stage("notes/named.md", "as placeholder.person said\n")
```
