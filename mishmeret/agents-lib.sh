# agents-lib.sh - what agents.sh and agents-morning.sh share (the duplication audit's E26; the reviewer, Board #82 A,
# 2026-10-26): the clone they work in, the roles they start, where a session's transcript is, and which tmux pane a
# role's session runs in. Each script kept its own copy; with the clone set, the night run read one clone and its Go
# started the roles, through agents.sh, in another. Sourced by both, never run alone.
#
# All of it is the project's, from its config (mishmeret/config.py --shell): the clone is the config's root, so a
# script one of them starts (agents.sh, from the night run's Go) works in the same clone through MISHMERET_CONFIG.

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# NO PROJECT NAMED, NO RUN (two runs of 2026-11-05, each this checkout's script run directly): one, in Mishmeret's own
# folder, was refused without saying where to run it from; the other, in the project's folder, ran this checkout - not
# the commit the project pins - and exported the config it read to every role with no shim's mark, so the project's
# shim in a role's worktree kept the main clone's config. A start script runs through the project's own copy (its shim
# names the config and the pinned commit, and marks what it sets) or with MISHMERET_CONFIG set by hand.
[ -n "${MISHMERET_CONFIG:-}" ] || { echo "$(basename "$0"): no project named - run the project's own $(basename "$0") from its folder (bash $(basename "$0") there): it names the project's config and the Mishmeret commit the project pins. Or set MISHMERET_CONFIG to the project's .claude/mishmeret.json." >&2; exit 1; }
MM_CFG=$(python3 "$HERE/config.py" --shell) || { echo "$(basename "$0"): the Mishmeret config $MISHMERET_CONFIG cannot be read" >&2; exit 1; }
eval "$MM_CFG"
DIR="$MM_ROOT"
PY="$MM_PYTHON"
ROLES="$MM_ROLES"
PROJECTS="$MM_PROJECTS"
SESSION="$MM_SESSION"

colour_of() {   # role -> its colour (MM_COLOURS, "name=colour" words)
  local w; for w in $MM_COLOURS; do [ "${w%%=*}" = "$1" ] && { echo "${w#*=}"; return; }; done
}

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
sys.exit(0 if role_usage.turn_ended(sys.argv[2]) else 1)' "$HERE" "$sid" 2>/dev/null; then st=idle; fi
  echo "$st"
}

pane_of_pid() {   # a role's claude pid -> its tmux pane in the roles' session (the process is a child of the pane's shell)
  local ppid; ppid=$(ps -o ppid= -p "$1" 2>/dev/null | tr -d ' ')
  [ -n "$ppid" ] || return 0
  tmux list-panes -s -t "$SESSION" -F '#{pane_pid} #{pane_id}' 2>/dev/null | awk -v p="$ppid" '$1 == p {print $2}'
}

pane_of() {   # role -> its tmux pane id, or nothing
  local pid; pid=$(role_info "$1" | cut -d' ' -f3)
  [ "$pid" = "-" ] || pane_of_pid "$pid"
}

run_going() {   # a night run's lock folder -> success unless the run that wrote its process id there is gone (a lock
                # with no id counts as going, as every lock did before the id was kept)
  local p; p=$(cat "$1/pid" 2>/dev/null) || return 0
  kill -0 "$p" 2>/dev/null
}

alert() {   # text title -> a notification on the Mac: both as osascript's arguments, never spliced into its script; and
            # no quote escaped inside a quote, for the role guard reads these scripts (agents.sh's tell and the night
            # run's notify, two copies merged: notes/PLAN-AUDIT-FIXES.md, item 4)
  osascript -e 'on run a' -e 'display notification (item 1 of a) with title (item 2 of a)' -e 'end run' "$1" "$2" >/dev/null 2>&1
}

going_run() {   # -> the lock of a night run that is going (<state_dir>/night/<its date>/.running), or nothing
  local l
  for l in "$MM_STATE_DIR"/night/*/.running; do
    if [ -d "$l" ] && run_going "$l"; then echo "$l"; return; fi
  done
}
