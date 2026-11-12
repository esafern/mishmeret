#!/bin/bash
# agents.sh - start the project's role sessions in one tmux window, one pane each, each pane labelled in its role's colour.
#
#   bash agents.sh             start them; if the roles' tmux session (the config's tmux_session) is already running, start again each role whose
#                              pane is back at its shell, then attach to it
#   bash agents.sh --restart   stop the roles' running tmux session first, then start them again. This ends every role
#                              session in it, whatever it is doing - let each finish first.
#   bash agents.sh --resume    as with no option, but each role is started by RESUMING its last session, with its
#                              context (`claude --resume <id>`) - for when the roles stopped without finishing (2026-10-11
#                              17:51: their tmux server ended under them). A role whose last session is still running
#                              is not started again; one with no session starts fresh. Not after a night run:
#                              those sessions were closed on purpose, and start fresh.
#   bash agents.sh --next ROLE PANE [exit]
#                              the Stop hook's (finish_hook.py), never typed by hand: ROLE's session in PANE has said
#                              its closing sentence - /clear, /exit, and ROLE started again in that pane; with `exit`
#                              (the longer sentence, "... ready to clear and exit.") nothing is started. Below, NEXT.
#
# Each role starts as START_HERE says: from the main clone, `claude --agent <role> --name <role>`.
# The session recap is turned on for every role by .claude/settings.json (CLAUDE_CODE_ENABLE_AWAY_SUMMARY), not here:
# Claude Code turns it off for a session started with --agent unless that is set.
# The label on each pane's top border is tmux's own, so it keeps its colour whatever Claude Code does to the pane's title.
# The colours are the roles' (the config's, as their agent files name them), as the hex values Claude Code draws them with.

set -u
# the clone, the roles and the session (the project's config): agents-lib.sh, shared with agents-morning.sh
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/agents-lib.sh"
MODE="${1:-}"

effort_of() {   # role -> the effort its agent file names; passed as --effort, since Claude Code does not apply an agent
                # file's effort itself - the user settings' would win (the reviewer, 2026-10-06: "go agents.sh")
  sed -n 's/^effort: *//p' "$DIR/${MM_AGENT_FILES//\{role\}/$1}" | head -1
}

# THE AGENTS' TMUX SETTINGS, LOADED EVERY TIME (the reviewer, 2026-10-11: "control-a z doesn't work today for zooming"):
# the config's tmux_conf (here ~/.tmux-agents.conf) holds the Ctrl-A prefix, Alt+z zoom and mouse; nothing loaded it, so the tmux server agents.sh
# started on 2026-10-09 ran on tmux's defaults. Loaded into the server whenever this script starts or attaches.
TMUX_CONF="$MM_TMUX_CONF"
load_tmux_conf() { [ -f "$TMUX_CONF" ] && tmux source-file "$TMUX_CONF"; return 0; }

# RESUME (the reviewer, 2026-10-11: "build the agents.sh resume option"): each role's last session in this clone, from
# role_sessions.py - "ROLE<tab>ID<tab>WHEN", "ROLE<tab>live<tab>ID" or "ROLE<tab>none".
# A ROLE WHOSE SESSION IS RUNNING ELSEWHERE IS NEVER STARTED AGAIN, in any mode (the reviewer, 2026-10-25: "confirm it will
# not restart this sessions or other low-consumption sessions currently running" - an operator running outside tmux, its
# pane back at the shell, would have got a second operator)
SESSIONS=$("$PY" "$HERE/role_sessions.py" $ROLES) || SESSIONS=""
if [ "$MODE" = "--resume" ]; then
  echo "Resuming each role's last session:"; printf '%s\n' "$SESSIONS" | sed 's/^/  /'
fi
session_of() { printf '%s\n' "$SESSIONS" | awk -F'\t' -v r="$1" '$1 == r { print $2; exit }'; }

# A ROLE STARTS WITH NO PROJECT CONFIG INHERITED (girsa-architect's answer 2 on notes/PLAN-START-SCRIPTS.md): its
# config is its own tree's, set by its own shim; a pane's shell holds the tmux server's environment, which is nobody's
# hand - an unmarked config there was kept by the shim in every role's worktree (the first project's 2026-11-05)
CLEAN="env -u MISHMERET_CONFIG -u MISHMERET_CONFIG_BY_SHIM"
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
      *) tmux send-keys -t "$1" "cd '$DIR' && $CLEAN claude --resume $sid --agent $2 --name $2 --effort $(effort_of "$2") 'agents.sh --resume: this session stopped without finishing (its tmux pane closed) and is resumed here with its context. A command that was running when it stopped did not finish - check the state of what you were doing before you go on.'" Enter
         return ;;
    esac
  fi
  # NO OPENING PROMPT HERE: the agent file's `initialPrompt` sends the brief's line itself, so typing it too sent it twice
  # (the reviewer, 2026-10-25: "each command line includes the start prompt as a parameter which is duplicative")
  tmux send-keys -t "$1" "cd '$DIR' && $CLEAN claude --agent $2 --name $2 --effort $(effort_of "$2")" Enter
}

# NEXT - A FINISHED SESSION IS CLEARED, EXITED AND STARTED AGAIN IN ITS PANE (the reviewer, 2026-11-10, the first
# project's Board #183: "during the day I want to clear a session after landing, then exit and start a new one. in the
# even [evening] after I'm idle I want the night run to exit and not restart"; and "add finish-and-exit": after that
# command's sentence nothing is started, whoever typed it). Started detached by the Stop hook; what it does is said to
# <state_dir>/next.log, and to you when it stops short.
# - ONLY IN THE PANE agents.sh GAVE THAT ROLE (its @role): nothing is typed into another's pane.
# - A NIGHT RUN GOING, IT STANDS DOWN (girsa-architect, 2026-11-10: one actor on a pane, and the rule's one home is
#   here, not the hook): the run reads the sentence itself, clears and exits, starts nothing. Looked for before
#   /clear and again before the start - a run begun in between finds the pane cleared and exited, not started.
#   A lock whose run is gone is no lock (agents-lib.sh, run_going). Said to you when the run had not asked that role.
# - NOTHING IS TYPED OVER WORDS STANDING IN THE PROMPT (girsa-verifier's MEDIUM 1 on the plan: by day you are at the
#   keyboard - on record, typing in a pane 135 s after its closing sentence; a /clear typed then would send your
#   half-typed words with it as a message). The prompt is read before /clear and before /exit: its line is the last
#   holding "❯" and a no-break space (a message already sent has a plain space), and its dim text is Claude Code's
#   own suggestion, not yours (measured, 2.1.322). Words there, or no prompt found: it stands down and says so.
# - NOT STARTED TWICE IN TEN MINUTES (its MEDIUM 2: nothing else bounds a role that finishes, is started, and finishes
#   again, with nobody watching): the second time it is cleared and exited, and you are told.
if [ "$MODE" = "--next" ]; then
  role="${2:-}"; pane="${3:-}"; how="${4:-}"
  mkdir -p "$MM_STATE_DIR"
  say() { echo "$(date '+%F %H:%M:%S') $role: $*" >> "$MM_STATE_DIR/next.log"; }
  tell() { say "told you: $*"; alert "$role: $*" "$MM_PROJECT: a finished session"; }   # agents-lib.sh
  at_shell() { case "$(tmux display-message -p -t "$pane" '#{pane_current_command}' 2>/dev/null)" in zsh|-zsh|bash|-bash|sh|-sh) return 0 ;; esac; return 1; }
  [ -n "$role" ] && [ -n "$pane" ] && [ "$(tmux show-options -pv -t "$pane" @role 2>/dev/null)" = "$role" ] \
    || { say "pane $pane was not given to it by agents.sh - nothing typed"; exit 0; }
  lock=$(going_run)
  if [ -n "$lock" ]; then
    if [ -e "$(dirname "$lock")/$role.land-sent" ]; then say "the night run ($lock) asked it to finish - left to that run"
    else tell "finished while a night run is going ($lock) - that run closes it, and it is not started again; bash agents.sh starts it"; fi
    exit 0
  fi
  in_prompt() {   # -> what stands in the pane's prompt, typed and not sent: nothing when it is empty, "?" when no prompt is found
    tmux capture-pane -e -p -t "$pane" 2>/dev/null | python3 -c '
import re, sys
mark = chr(0x276f) + chr(0xa0)
lines = [line for line in sys.stdin.buffer.read().decode("utf-8", "replace").splitlines() if mark in line]
rest = lines[-1].split(mark, 1)[1] if lines else "?"
print("" if rest.startswith(chr(27) + "[2m") else re.sub(chr(27) + "[^m]*m", "", rest).strip())'
  }
  typed_then() {   # the line to type: typed only into an empty prompt
    local has; has=$(in_prompt)
    if [ "$has" = "?" ]; then tell "its prompt could not be read - $1 not typed; finish closing it by hand, then: bash agents.sh"; exit 0; fi
    if [ -n "$has" ]; then tell "words are standing in its prompt - $1 not typed over them; type /clear and /exit there, then: bash agents.sh"; exit 0; fi
    tmux send-keys -t "$pane" "$1" Enter
  }
  sleep 2; typed_then "/clear"; sleep "$MM_NIGHT_GAP"; typed_then "/exit"
  n=0; until at_shell; do
    n=$((n + 1)); [ "$n" -le 60 ] || { tell "cleared, but its pane is not back at its shell a minute after /exit - not started again"; exit 0; }
    sleep 1
  done
  if [ "$how" = "exit" ]; then say "cleared and exited - not started again (its sentence asked for that)"; exit 0; fi
  lock=$(going_run)
  if [ -n "$lock" ]; then tell "cleared and exited; a night run began meanwhile ($lock) - not started again; bash agents.sh starts it"; exit 0; fi
  started="$MM_STATE_DIR/$role.next-started"
  if [ -n "$(find "$started" -mmin -10 2>/dev/null)" ]; then tell "finished again within ten minutes of being started here - cleared and exited, not started a second time; bash agents.sh starts it"; exit 0; fi
  touch "$started"
  SESSIONS=""   # its last session is the one just exited, not one running elsewhere
  start_role "$pane" "$role" "$(tmux show-options -pv -t "$pane" @colour)"
  say "cleared, exited and started again in $pane"
  exit 0
fi

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
# The panes are made in the config's page_order (MM_LAYOUT), each split of the newest, across and down in turn; then
# each role started in the config's order (MM_ROLES), in its colour (MM_COLOURS).
PANES=""; prev=""; across=1
for role in $MM_LAYOUT; do
  if [ -z "$prev" ]; then
    prev=$(tmux new-session -d -s "$SESSION" -x "$(tput cols)" -y "$(tput lines)" -c "$DIR" -P -F '#{pane_id}')
    load_tmux_conf
  else
    if [ "$across" = 1 ]; then dir=-h; across=0; else dir=-v; across=1; fi
    prev=$(tmux split-window $dir -t "$prev" -c "$DIR" -P -F '#{pane_id}')
  fi
  PANES="$PANES $role=$prev"
done
pane_for() { local w; for w in $PANES; do [ "${w%%=*}" = "$1" ] && { echo "${w#*=}"; return; }; done; }
for role in $ROLES; do
  start_role "$(pane_for "$role")" "$role" "$(colour_of "$role")"
done
operator=$(pane_for "$MM_OPERATOR_ROLE")

tmux set-option -w -t "$SESSION" pane-border-status top
tmux set-option -w -t "$SESSION" pane-border-format ' #[fg=#{@colour},bold]#{@role}#[default] '
tmux select-layout -t "$SESSION" tiled
tmux select-pane -t "$operator"
exec tmux attach-session -t "$SESSION"
