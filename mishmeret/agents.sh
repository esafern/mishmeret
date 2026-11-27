#!/bin/bash
# agents.sh - start the project's role sessions in one window, one pane each, each pane labelled in its role's colour -
# tmux's, or WezTerm's (the config's `terminal`; every terminal step is term.sh's, sourced by agents-lib.sh).
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
# The label on each pane's top border is tmux's own, so it keeps its colour whatever Claude Code does to the pane's title
# (WezTerm has none: the tab's title names the session).
# The colours are the roles' (the config's, as their agent files name them), as the hex values Claude Code draws them with.

set -u
# the clone, the roles and the session (the project's config): agents-lib.sh, shared with agents-morning.sh
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/agents-lib.sh"
MODE="${1:-}"

effort_of() {   # role -> "--effort X" for the effort its agent file names, since Claude Code does not apply an agent
                # file's effort itself - the user settings' would win (the reviewer, 2026-10-06: "go agents.sh");
                # nothing when it names none: a bare --effort took the next word, at --resume the prompt (M07)
  sed -n 's/^effort: *\([^ ][^ ]*\).*/--effort \1/p' "$DIR/${MM_AGENT_FILES//\{role\}/$1}" 2>/dev/null | head -1
}

# A ROLE RUN BY PI (notes/PLAN-PI-ROLE.md; the config's `runner: pi`): pi has no --agent and runs no Claude Code hook, so
# it is started with Mishmeret's guard extension beside this script (its tree is the pin the project's shim names) and
# no other extension; its effort as pi's --thinking, its agent file appended to the system prompt, and the agent
# file's initialPrompt as its first message (Claude Code sends that itself)
is_pi() { case " $MM_PI_ROLES " in *" $1 "*) return 0 ;; esac; return 1; }
pi_line() {   # role -> the command that starts it under pi
  local agent="$DIR/${MM_AGENT_FILES//\{role\}/$1}" first
  local line="cd '$DIR' && $CLEAN pi --no-extensions --name $1 --role $1 -e '$HERE/pi_guard.ts'"
  line="$line$(sed -n 's/^effort: *\([^ ][^ ]*\).*/ --thinking \1/p' "$agent" 2>/dev/null | head -1)"
  [ -f "$agent" ] && line="$line --append-system-prompt '$agent'"
  # the skills: pi reads no .claude/skills/, and a link in its own folder only in a trusted project (measured,
  # notes/PLAN-SHIPPED-SKILLS.md) - so the shipped ones by their tree, and the project's own one by one, its
  # mishmeret-* links left out (girsa-verifier's NOTE 2 on the plan: no skill twice)
  line="$line --skill '$HERE/skills'"
  local d; for d in "$DIR"/.claude/skills/*/; do
    [ -d "$d" ] && [ ! -L "${d%/}" ] && line="$line --skill '${d%/}'"
  done
  first=$(sed -n 's/^initialPrompt: *"\{0,1\}\(.*[^"]\)"\{0,1\} *$/\1/p' "$agent" 2>/dev/null | head -1)
  [ -n "$first" ] && line="$line '${first//\'/\'\\\'\'}'"
  echo "$line"
}

# THE AGENTS' TMUX SETTINGS, LOADED EVERY TIME (the reviewer, 2026-10-11: "control-a z doesn't work today for zooming"):
# the config's tmux_conf (here ~/.tmux-agents.conf) holds the Ctrl-A prefix, Alt+z zoom and mouse; nothing loaded it, so the tmux server agents.sh
# started on 2026-10-09 ran on tmux's defaults. Loaded into the server whenever this script starts or attaches.
TMUX_CONF="$MM_TMUX_CONF"
load_tmux_conf() { term_conf "$TMUX_CONF"; }

# THE SKILLS MISHMERET SHIPS (notes/PLAN-SHIPPED-SKILLS.md): each skill of the tree this script runs from is linked into
# the project's .claude/skills/ at every start, so a pin bump moves them all at the next start. Only a link is replaced
# or removed, never a file or folder of the project's own; a mishmeret-* link to a skill this tree no longer ships is
# removed (girsa-verifier's LOW 1 on the plan: it kept loading the old procedure from the old pin). Not committed - a
# link holds this machine's path: the project's .gitignore lists .claude/skills/mishmeret-*.
link_skills() {
  local into="$DIR/.claude/skills" s t name
  mkdir -p "$into" || return 0
  for t in "$into"/mishmeret-*; do
    if [ -L "$t" ] && [ ! -f "$HERE/skills/$(basename "$t")/SKILL.md" ]; then
      rm -f "$t" && echo "skills: $(basename "$t") is no longer shipped - its link removed"
    fi
  done
  for s in "$HERE"/skills/*/; do
    [ -f "${s}SKILL.md" ] || continue
    name=$(basename "$s"); t="$into/$name"
    if [ -e "$t" ] && [ ! -L "$t" ]; then
      echo "skills: $t is the project's own - left as it is, the shipped $name not linked"
    else
      ln -sfn "${s%/}" "$t"
    fi
  done
}
link_skills

# RESUME (the reviewer, 2026-10-11: "build the agents.sh resume option"): each role's last session in this clone, from
# role_sessions.py - "ROLE<tab>ID<tab>WHEN", "ROLE<tab>live<tab>ID" or "ROLE<tab>none".
# A ROLE WHOSE SESSION IS RUNNING ELSEWHERE IS NEVER STARTED AGAIN, in any mode (the reviewer, 2026-10-25: "confirm it will
# not restart this sessions or other low-consumption sessions currently running" - an operator running outside tmux, its
# pane back at the shell, would have got a second operator)
SESSIONS=""   # --next sets none: its role's last session is the one just exited (below)
[ "$MODE" = "--next" ] || SESSIONS=$("$PY" "$HERE/role_sessions.py" $ROLES) || SESSIONS=""
if [ "$MODE" = "--resume" ]; then
  echo "Resuming each role's last session:"; printf '%s\n' "$SESSIONS" | sed 's/^/  /'
fi
session_of() { printf '%s\n' "$SESSIONS" | awk -F'\t' -v r="$1" '$1 == r { print $2; exit }'; }

# A ROLE STARTS WITH NO PROJECT CONFIG INHERITED (girsa-architect's answer 2 on notes/PLAN-START-SCRIPTS.md): its
# config is its own tree's, set by its own shim; a pane's shell holds the tmux server's environment, which is nobody's
# hand - an unmarked config there was kept by the shim in every role's worktree (the first project's 2026-11-05)
CLEAN="env -u MISHMERET_CONFIG -u MISHMERET_CONFIG_BY_SHIM"
start_role() {   # pane-id role colour; fails when the role is left alone (its last session is running elsewhere)
  term_tag "$1" role "$2"
  term_tag "$1" colour "$3"
  local sid; sid=$(session_of "$2")
  if [ "$sid" = "live" ]; then
    term_send "$1" "echo '$2: its last session is still running elsewhere - not started again here'"
    return 1
  fi
  if is_pi "$2"; then   # started fresh, never resumed: its sessions are pi's, not in Claude Code's transcripts
    if [ ! -f "$HERE/pi_guard.ts" ]; then
      term_send "$1" "echo '$2: not started - its runner is pi, and the guard extension $HERE/pi_guard.ts is missing'"
      return 1
    fi
    term_send "$1" "$(pi_line "$2")"
    return
  fi
  if [ "$MODE" = "--resume" ]; then
    case "$sid" in
      ""|none) ;;                                       # no earlier session: started fresh, below
      *) term_send "$1" "cd '$DIR' && $CLEAN claude --resume $sid --agent $2 --name $2 $(effort_of "$2") 'agents.sh --resume: this session stopped without finishing (its pane closed) and is resumed here with its context. A command that was running when it stopped did not finish - check the state of what you were doing before you go on.'"
         return ;;
    esac
  fi
  # NO OPENING PROMPT HERE: the agent file's `initialPrompt` sends the brief's line itself, so typing it too sent it twice
  # (the reviewer, 2026-10-25: "each command line includes the start prompt as a parameter which is duplicative")
  term_send "$1" "cd '$DIR' && $CLEAN claude --agent $2 --name $2 $(effort_of "$2")"
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
  at_shell() { case "$(term_cmd "$pane")" in zsh|-zsh|bash|-bash|sh|-sh) return 0 ;; esac; return 1; }
  [ -n "$role" ] && [ -n "$pane" ] && [ "$(term_tag_of "$pane" role)" = "$role" ] \
    || { say "pane $pane was not given to it by agents.sh - nothing typed"; exit 0; }
  lock=$(going_run)
  if [ -n "$lock" ]; then
    if [ -e "$(dirname "$lock")/$role.land-sent" ]; then say "the night run ($lock) asked it to finish - left to that run"
    else tell "finished while a night run is going ($lock) - that run closes it, and it is not started again; bash agents.sh starts it"; fi
    exit 0
  fi
  in_prompt() {   # -> what stands in the pane's prompt, typed and not sent: nothing when it is empty, "?" when no prompt is found
    term_capture "$pane" -e | python3 -c '
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
    term_send "$pane" "$1"
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
  start_role "$pane" "$role" "$(term_tag_of "$pane" colour)"
  say "cleared, exited and started again in $pane"
  exit 0
fi

if term_has "$SESSION"; then
  if [ "${1:-}" = "--restart" ]; then
    term_kill "$SESSION"
  else
    # A ROLE WHOSE PANE IS BACK AT ITS SHELL IS STARTED AGAIN IN IT (the reviewer, 2026-10-10: "it opened all the panes but
    # i had to manually start each agent" - the night run had closed the roles and left the session and its panes)
    started=""
    while read -r pane role cmd; do
      [ -n "$role" ] || continue
      case "$cmd" in
        zsh|-zsh|bash|-bash|sh|-sh) start_role "$pane" "$role" "$(term_tag_of "$pane" colour)" && started="$started $role" ;;
      esac
    done < <(term_list "$SESSION")
    if [ -n "$started" ]; then echo "The roles' session '$SESSION' is already running - started again:$started. Attaching."
    else echo "The roles' session '$SESSION' is already running, every role in it - attaching. To stop it and start again: bash agents.sh --restart"; fi
    load_tmux_conf
    term_attach "$SESSION"
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
    prev=$(term_new "$SESSION" "$DIR") || exit 1
    load_tmux_conf
  else
    if [ "$across" = 1 ]; then dir=across; across=0; else dir=down; across=1; fi
    prev=$(term_split "$prev" "$dir" "$DIR")
  fi
  PANES="$PANES $role=$prev"
done
pane_for() { local w; for w in $PANES; do [ "${w%%=*}" = "$1" ] && { echo "${w#*=}"; return; }; done; }
for role in $ROLES; do
  start_role "$(pane_for "$role")" "$role" "$(colour_of "$role")"
done
operator=$(pane_for "$MM_OPERATOR_ROLE")

term_label "$SESSION"
term_layout "$SESSION"
term_focus "$operator"
term_attach "$SESSION"
