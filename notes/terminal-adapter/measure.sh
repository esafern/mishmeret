#!/bin/bash
# The terminal adapter's measure (notes/PLAN-TERMINAL-ADAPTER.md, "THE BUILD"): agents.sh's sequence of terminal steps,
# run through a term.sh on a PRIVATE server - never the live one. 22 checks; one line each, ok or FAULT, then the
# counts; exit 0 when every check is ok. Kept here for the Windows run (girsa-verifier's NOTE 3 on the build: a pane's
# command under WezTerm is pinned by this alone - the tests' stubs have no process on a tty).
#
#   tmux:    D=$(mktemp -d); env -u TMUX TMUX_TMPDIR=$D WEZTERM_UNIX_SOCKET=$D/none MM_TERMINAL=tmux \
#              TERM=xterm-256color bash measure.sh <mishmeret>/term.sh
#   WezTerm: a socket's path must be short on macOS (SUN_LEN): S=$(mktemp -d "${TMPDIR%/}/mmwez.XXXX"); a config
#              holding `return { unix_domains = { { name = 'mm', socket_path = '<S>/s' } },
#              default_prog = { '/bin/bash', '--norc', '-i' } }`; `wezterm-mux-server --config-file <it> --daemonize`;
#              then env -u TMUX TMUX_TMPDIR=$S/notmux WEZTERM_UNIX_SOCKET=$S/s MM_TERMINAL=wezterm \
#              TERM=xterm-256color bash measure.sh <mishmeret>/term.sh
#            and stop that server by its pid (`pgrep -f "wezterm-mux-server --pid-file-fd 3 --config-file <it>"`, then
#            kill): the guard refuses pkill of wezterm.
# Both sockets are named because term.sh holds both terminals' kills, and the role guard reads them both.
set -u
. "$1"
SESSION=mm-measure
MM_STATE_DIR="$(mktemp -d "${TMPDIR%/}/mmstate.XXXX")"
ok=0; bad=0
check() { if eval "$2"; then ok=$((ok + 1)); echo "ok    $1"; else bad=$((bad + 1)); echo "FAULT $1"; fi; }
wait_for() { local i; for i in $(seq 1 40); do eval "$1" && return 0; /bin/sleep 0.25; done; return 1; }
at_shell() { case "$(term_cmd "$1")" in zsh|-zsh|bash|-bash|sh|-sh) return 0 ;; esac; return 1; }

check "no session at start" '! term_has $SESSION'
p1=$(term_new $SESSION "$PWD"); check "a first pane, its id ($p1)" '[ -n "$p1" ]'
p2=$(term_split "$p1" across "$PWD"); p3=$(term_split "$p2" down "$PWD"); p4=$(term_split "$p3" across "$PWD")
check "three splits, each its own id ($p2 $p3 $p4)" '[ "$(printf "%s\n" $p1 $p2 $p3 $p4 | sort -u | wc -l | tr -d " ")" = 4 ]'
check "the session lists its four panes" '[ "$(term_panes $SESSION | sort | tr "\n" " ")" = "$(printf "%s\n" $p1 $p2 $p3 $p4 | sort | tr "\n" " ")" ]'
check "the session is running" 'term_has $SESSION'
i=0; for p in $p1 $p2 $p3 $p4; do i=$((i + 1)); term_tag "$p" role "r$i"; term_tag "$p" colour "#00000$i"; done
check "each pane's role read back" '[ "$(term_tag_of $p1 role) $(term_tag_of $p2 role) $(term_tag_of $p3 role) $(term_tag_of $p4 role)" = "r1 r2 r3 r4" ]'
check "each pane's colour read back" '[ "$(term_tag_of $p3 colour)" = "#000003" ]'
check "an untagged key is empty" '[ -z "$(term_tag_of $p1 nothing)" ]'
for p in $p1 $p2 $p3 $p4; do wait_for "at_shell $p"; done
check "each pane at its shell" 'at_shell $p1 && at_shell $p2 && at_shell $p3 && at_shell $p4'
for p in $p1 $p2 $p3 $p4; do term_send "$p" "echo MARK-$p-DONE"; done
for p in $p1 $p2 $p3 $p4; do wait_for "term_capture $p 50 | grep -q 'MARK-$p-DONE'"; done
check "each pane ran a typed line, captured" '( for p in $p1 $p2 $p3 $p4; do term_capture $p 50 | grep -q "^MARK-$p-DONE" || exit 1; done )'
term_send "$p1" "printf '\\033[31mRED%s\\033[0m\\n' LINE"
wait_for "term_capture $p1 50 | grep -q REDLINE"
ESC=$'\033'
check "a capture with escapes holds the colour" 'term_capture $p1 -e | grep -qF "${ESC}[31mREDLINE"'
check "one without holds none" 'term_capture $p1 50 | grep REDLINE | grep -vqF "$ESC"'
long=$(printf 'W%.0s' $(seq 1 75))
term_send "$p2" "echo $long"
wait_for "term_capture $p2 50 | grep -q '^$long\$'"
check "a line wider than its pane read back whole" 'term_capture $p2 50 | grep -q "^$long\$"'
term_send "$p2" "/bin/sleep 30 &"
/bin/sleep 1
check "a pane with a job in the background at its shell" 'at_shell $p2'
term_send "$p3" "/bin/sleep 31"
wait_for '[ "$(term_cmd $p3)" = sleep ]'
check "a foreground sleep the pane's command" '[ "$(term_cmd $p3)" = sleep ]'
term_send "$p4" "/bin/sleep 32"
wait_for 'pgrep -f "^/bin/sleep 32" >/dev/null'
pid=$(pgrep -f "^/bin/sleep 32" | head -1)
check "a process's pane from its parent shell ($pid)" '[ "$(term_pane_of_pid $SESSION $pid)" = "$p4" ]'
check "the list's pane, role and command" 'term_list $SESSION | grep -qx "$p3 r3 sleep"'
check "the label" 'term_label $SESSION'
check "the layout" 'term_layout $SESSION'
check "the focus" 'term_focus $p4'
term_kill $SESSION
wait_for '! term_has $SESSION'
check "the session killed" '! term_has $SESSION'
check "its tags gone with it, or never a file (tmux)" '[ ! -s "$(term_tags_file $SESSION)" ]'
left=$(pgrep -f "^/bin/sleep 3[012]"); [ -n "$left" ] && kill $left 2>/dev/null
rm -rf "$MM_STATE_DIR"
echo "checks: $((ok + bad)), ok $ok, faults $bad"
[ "$bad" = 0 ]
