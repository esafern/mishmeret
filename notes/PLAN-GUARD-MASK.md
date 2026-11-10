# An escaped quote turned the role guard off: the plan (mishmeret-builder, 2026-11-10)

Written 13:18 (`date`). On girsa-verifier's REQUEST of 2026-11-10 (HIGH; its measure in the first project,
design-study/step5-verification/mishmeret-finish-build-2026-11-10/): the fix in `mask`, a test for each form, red on
today's code, as a piece of its own - on `builder-guard-mask`, from main, not on the finish piece's branch. The
REQUEST names the fix and its tests, so the plan and the build are one commit, for its check there.

## The case

- 2026-11-10, building `agents.sh --next` (the finish piece): one line with a quote escaped inside a quote
  (`osascript -e "display notification \"...\""`), and `tests/test_guard.py`'s own check went red - the guard no
  longer refused `bash agents.sh` against the live tmux server, its `tmux kill-session` below that line unseen.
- girsa-verifier, the same day, the guard's `refusal` called on text at 8738b21 and 51499da: `git push origin main`,
  `git push --force origin main` and `git commit -m x` in the main tree are refused alone and in a script - and each
  LET THROUGH after `echo "a \" b";` in the same command, on the next line, or in a script whose first line is that
  echo; with two escaped quotes too; and after `echo $'it\'s';`.
- The cause, `role_guard.py` `mask`: inside a quote it closed at the first quote character, escaped or not; the
  string's real closing quote then opened a quote, and everything after it was masked - for every check that reads
  the mask (git, land.py, tmux, the piped checks), in a command and one level into a script.

## The behaviour

- Inside `"..."` and inside `$'...'` a backslash and the character after it are words, masked as the rest of the
  string is (a newline after a backslash stays a newline, as every newline does). Inside `'...'` a backslash is
  itself: the quote closes at the next `'`, as the shell closes it.
- `$'` opens a kind of its own - a `'` straight after an unescaped `$` outside quotes.
- Nothing else in `mask` changes: comments, heredocs, a backslash outside quotes.
- What it costs: a command that got through only because an escaped quote above it hid it is now read. That is the
  fix. The other half of the fault goes too: words inside such a string were sometimes read as commands.

## The measure (the guard's functions called on text; no command run)

- Before, 13 forms: the push after each of five strings HIDDEN; the push inside two strings and in a comment after
  one hidden only by the misreading that hid everything after it.
- After: the push after every string SEEN; inside a string, and in a comment after one, hidden; `bash -c "echo
  \"x\"; git push origin main"` refused through the quoted-argument reader, as before.

## Tests (`test_an_escaped_quote_inside_a_string_does_not_turn_the_guard_off`)

- Three refusals (a push, a forced push for the operator, a commit in the main tree), each alone and after each of
  seven strings - joined by `;`, by a newline, by `&&`, and in a script: 84 refused.
- The other way, six commands whose refused words stand inside a string or a comment: none refused.
- The tmux check through the same mask: a script with an escaped quote above its `kill-session` is refused.
- The mask keeps its length and its newlines on each text.
- Red with each rule out, five: the escape rule (the test's first form); `$'...'` as its own kind; no escape in
  `'...'`; the escaped newline kept (not red at first - its text added, then red). The suite on this branch: 111.

## Files

- `mishmeret/role_guard.py`, `tests/test_guard.py`, `notes/PLAN-GUARD-MASK.md`
- NOT here: the state file and the log. Both are changed on `builder-finish` (51499da, in check); this piece's lines
  go into them at the first rebase after either is merged, so the two branches do not collide in notes.

## Not checked

- The guard's other readers of quotes (`SHELL_C`'s own pattern, which already takes `\.` inside `"..."`; `_unquote`)
  beyond the one form above; a `"` inside `$(...)` inside `"..."` (balanced in the one form tried, by its count).
- girsa-verifier's two unchecked sides: the piped-check refusals and the Edit and Write side.
