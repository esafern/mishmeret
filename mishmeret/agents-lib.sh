# agents-lib.sh - what agents.sh and agents-morning.sh share (the duplication audit's E26; the reviewer, Board #82 A,
# 2026-10-26): the clone they work in, the roles they start, where a session's transcript is, and which tmux pane a
# role's session runs in. Each script kept its own copy; with GIRSA_DIR set, the night run read one clone and its Go
# started the roles, through agents.sh, in another. Sourced by both, never run alone.

DIR="${GIRSA_DIR:-$HOME/work/sefer-digitization-pipeline}"
export GIRSA_DIR="$DIR"      # a script one of them starts (agents.sh, from the night run's Go) works in the same clone
PY="$DIR/venv/bin/python"
ROLES="girsa-operator girsa-builder girsa-verifier girsa-ui-steward girsa-architect"
PROJECTS="${GIRSA_CLAUDE_PROJECTS:-$HOME/.claude/projects}"

transcript_of() {   # sessionId -> its transcript's path, or nothing
  ls "$PROJECTS"/*/"$1".jsonl 2>/dev/null | head -1
}

role_info() {   # role -> "status sessionId pid", or "absent - -" when it is not running
  claude agents --json 2>/dev/null | "$PY" -c '
import sys, json
try:
    rows = json.load(sys.stdin)
except Exception:
    rows = []
a = next((x for x in rows if isinstance(x, dict) and x.get("name") == sys.argv[1]), None)
print(*(("absent", "-", "-") if a is None else (a.get("status"), a.get("sessionId") or "-", a.get("pid") or "-")))' "$1"
}

role_state() {   # role -> its status from `claude agents` (idle, busy, ..., or absent), with a busy role whose turn has
                 # ended counted idle: `claude agents` says busy while a background task of its own runs (a watcher
                 # loop, a `board.py wait`) - role_usage.turn_ended, as the Board and keepalive_due.py read it
  local info st sid
  info=$(role_info "$1"); st=${info%% *}; sid=$(echo "$info" | cut -d' ' -f2)
  if [ "$st" = "busy" ] && "$PY" -c 'import sys; sys.path.insert(0, sys.argv[1]); import role_usage
sys.exit(0 if role_usage.turn_ended(sys.argv[2]) else 1)' "$DIR/.claude/board" "$sid" 2>/dev/null; then st=idle; fi
  echo "$st"
}

pane_of_pid() {   # a role's claude pid -> its tmux pane in the "girsa" session (the process is a child of the pane's shell)
  local ppid; ppid=$(ps -o ppid= -p "$1" 2>/dev/null | tr -d ' ')
  [ -n "$ppid" ] || return 0
  tmux list-panes -s -t girsa -F '#{pane_pid} #{pane_id}' 2>/dev/null | awk -v p="$ppid" '$1 == p {print $2}'
}

pane_of() {   # role -> its tmux pane id, or nothing
  local pid; pid=$(role_info "$1" | cut -d' ' -f3)
  [ "$pid" = "-" ] || pane_of_pid "$pid"
}
