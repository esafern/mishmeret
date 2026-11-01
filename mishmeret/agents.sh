#!/bin/bash
# agents.sh - start Girsa's five role sessions in one tmux window, one pane each, each pane labelled in its role's colour.
#
#   bash agents.sh             start them; if the "girsa" tmux session is already running, start again each role whose
#                              pane is back at its shell, then attach to it
#   bash agents.sh --restart   stop the running "girsa" tmux session first, then start them again. This ends every role
#                              session in it, whatever it is doing - let each finish its work and land first.
#   bash agents.sh --resume    as with no option, but each role is started by RESUMING its last session, with its
#                              context (`claude --resume <id>`) - for when the roles stopped without landing (2026-10-11
#                              17:51: their tmux server ended under them). A role whose last session is still running
#                              is not started again; one with no session starts fresh. Not after a night run's landing:
#                              those sessions were closed on purpose, and start fresh.
#
# Each role starts as START_HERE says: from the main clone, `claude --agent girsa-<role> --name girsa-<role>`.
# The session recap is turned on for every role by .claude/settings.json (CLAUDE_CODE_ENABLE_AWAY_SUMMARY), not here:
# Claude Code turns it off for a session started with --agent unless that is set.
# The label on each pane's top border is tmux's own, so it keeps its colour whatever Claude Code does to the pane's title.
# The colours are the roles' (.claude/agents/girsa-<role>.md), as the hex values Claude Code draws them with.

set -u
SESSION="girsa"
# the clone (GIRSA_DIR, else the main clone) and the roles: agents-lib.sh, shared with agents-morning.sh
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/agents-lib.sh"
MODE="${1:-}"

effort_of() {   # role -> the effort its agent file names; passed as --effort, since Claude Code does not apply an agent
                # file's effort itself - the user settings' would win (the reviewer, 2026-10-06: "go agents.sh")
  sed -n 's/^effort: *//p' "$DIR/.claude/agents/$1.md" | head -1
}

# THE AGENTS' TMUX SETTINGS, LOADED EVERY TIME (the reviewer, 2026-10-11: "control-a z doesn't work today for zooming"):
# ~/.tmux-agents.conf holds the Ctrl-A prefix, Alt+z zoom and mouse; nothing loaded it, so the tmux server agents.sh
# started on 2026-10-09 ran on tmux's defaults. Loaded into the server whenever this script starts or attaches.
TMUX_CONF="${GIRSA_TMUX_CONF:-$HOME/.tmux-agents.conf}"
load_tmux_conf() { [ -f "$TMUX_CONF" ] && tmux source-file "$TMUX_CONF"; return 0; }

# RESUME (the reviewer, 2026-10-11: "build the agents.sh resume option"): each role's last session in this clone, from
# tools/role_sessions.py - "ROLE<tab>ID<tab>WHEN", "ROLE<tab>live<tab>ID" or "ROLE<tab>none".
# A ROLE WHOSE SESSION IS RUNNING ELSEWHERE IS NEVER STARTED AGAIN, in any mode (the reviewer, 2026-10-25: "confirm it will
# not restart this sessions or other low-consumption sessions currently running" - an operator running outside tmux, its
# pane back at the shell, would have got a second operator)
SESSIONS=$("$DIR/venv/bin/python" "$DIR/tools/role_sessions.py" --clone "$DIR" $ROLES) || SESSIONS=""
if [ "$MODE" = "--resume" ]; then
  echo "Resuming each role's last session:"; printf '%s\n' "$SESSIONS" | sed 's/^/  /'
fi
session_of() { printf '%s\n' "$SESSIONS" | awk -F'\t' -v r="$1" '$1 == r { print $2; exit }'; }

start_role() {   # pane-id role colour; fails when the role is left alone (its last session is running elsewhere)
  tmux set-option -p -t "$1" @role "$2"
  tmux set-option -p -t "$1" @colour "$3"
  local sid; sid=$(session_of "$2")
  if [ "$sid" = "live" ]; then
    tmux send-keys -t "$1" "echo '$2: its last session is still running elsewhere - not started again here'" Enter
    return 1
  fi
  if [ "$MODE" = "--resume" ]; then
    case "$sid" in
      ""|none) ;;                                       # no earlier session: started fresh, below
      *) tmux send-keys -t "$1" "cd '$DIR' && claude --resume $sid --agent $2 --name $2 --effort $(effort_of "$2") 'agents.sh --resume: this session stopped without landing (its tmux pane closed) and is resumed here with its context. A command that was running when it stopped did not finish - check the state of what you were doing before you go on.'" Enter
         return ;;
    esac
  fi
  # NO OPENING PROMPT HERE: the agent file's `initialPrompt` sends the brief's line itself, so typing it too sent it twice
  # (the reviewer, 2026-10-25: "each command line includes the start prompt as a parameter which is duplicative")
  tmux send-keys -t "$1" "cd '$DIR' && claude --agent $2 --name $2 --effort $(effort_of "$2")" Enter
}

if tmux has-session -t "$SESSION" 2>/dev/null; then
  if [ "${1:-}" = "--restart" ]; then
    tmux kill-session -t "$SESSION"
  else
    # A ROLE WHOSE PANE IS BACK AT ITS SHELL IS STARTED AGAIN IN IT (the reviewer, 2026-10-10: "it opened all the panes but
    # i had to manually start each agent" - the night run had closed the roles and left the session and its panes)
    started=""
    while read -r pane role cmd; do
      [ -n "$role" ] || continue
      case "$cmd" in
        zsh|-zsh|bash|-bash|sh|-sh) start_role "$pane" "$role" "$(tmux show-options -pv -t "$pane" @colour)" && started="$started $role" ;;
      esac
    done < <(tmux list-panes -s -t "$SESSION" -F '#{pane_id} #{@role} #{pane_current_command}')
    if [ -n "$started" ]; then echo "The tmux session '$SESSION' is already running - started again:$started. Attaching."
    else echo "The tmux session '$SESSION' is already running, every role in it - attaching. To stop it and start again: bash agents.sh --restart"; fi
    load_tmux_conf
    exec tmux attach-session -t "$SESSION"
  fi
fi

# Each pane is addressed by the id tmux returns when it is made, so a later split never moves a role to another pane.
# THE ORDER IS THE LAYOUT: "tiled" fills its grid in pane order, two to a row, the fifth alone and full width - so the
# steward and the architect on top, the operator and the verifier in the middle, the builder at the bottom (the
# reviewer, 2026-10-06: "oper and ver should be the middle two with ui and arch on the top"). Each split puts its new
# pane right after the one it splits, so splitting the newest pane each time keeps this order.
steward=$(tmux new-session -d -s "$SESSION" -x "$(tput cols)" -y "$(tput lines)" -c "$DIR" -P -F '#{pane_id}')
load_tmux_conf
architect=$(tmux split-window -h -t "$steward" -c "$DIR" -P -F '#{pane_id}')
operator=$(tmux split-window -v -t "$architect" -c "$DIR" -P -F '#{pane_id}')
verifier=$(tmux split-window -h -t "$operator" -c "$DIR" -P -F '#{pane_id}')
builder=$(tmux split-window -v -t "$verifier" -c "$DIR" -P -F '#{pane_id}')

start_role "$operator"  girsa-operator   "#ca8a04"   # yellow
start_role "$builder"   girsa-builder    "#0891b2"   # cyan
start_role "$verifier"  girsa-verifier   "#16a34a"   # green
start_role "$steward"   girsa-ui-steward "#c46686"   # pink
start_role "$architect" girsa-architect  "#6a9bcc"   # blue

tmux set-option -w -t "$SESSION" pane-border-status top
tmux set-option -w -t "$SESSION" pane-border-format ' #[fg=#{@colour},bold]#{@role}#[default] '
tmux select-layout -t "$SESSION" tiled
tmux select-pane -t "$operator"
exec tmux attach-session -t "$SESSION"
