# term.sh - the session scripts' one terminal (notes/PLAN-TERMINAL-ADAPTER.md; the reviewer, 2026-11-25: "small
# terminal adapter", then "wezterm"). Every step agents.sh, agents-morning.sh and agents-lib.sh take in a terminal is
# a function here, each in tmux's form and in WezTerm's; the scripts name no terminal themselves (a test holds them
# to it). Sourced by agents-lib.sh, never run alone. Which one: the config's `terminal` (MM_TERMINAL), tmux when absent,
# read at each call - agents-lib.sh sources this before it reads the config. It sets SESSION and MM_STATE_DIR.
#
# WEZTERM'S FORMS, as probed and measured (the plan's head; WezTerm 20240203): a session is a workspace; a pane's tags
# (tmux's own options, @role and @colour) are lines of a file, <state_dir>/panes-<session>.tsv, begun afresh by
# term_new - pane ids repeat across servers (girsa-architect's Q2, measured), so a file a server left behind would
# give a new pane another's role; a pane's command is its tty's foreground process; a capture joins a line whose text
# fills its pane to the next, as tmux's -J does (a line wrapped at a space stays two: WezTerm pads a line with spaces,
# as Claude Code's screen does, so a full one alone is read as wrapped - the measure). None: the pane border's label
# (the tab's title instead), the tiled layout, a settings file. agents.sh runs only inside a WezTerm window, whose
# server its panes are spawned into (Q4).
#
# THE KILL IS WRITTEN OUT, never behind a variable or a shell function: the role guard reads a script with what it
# sources (role_guard.py, _sourced) and refuses either terminal's kill on its live panes.

term_tags_file() { echo "$MM_STATE_DIR/panes-$1.tsv"; }   # session -> WezTerm's tags file

term_wez_panes() {   # session -> "pane_id cols tty_name" for each of its panes (WezTerm)
  wezterm cli --no-auto-start list --format json 2>/dev/null | python3 -c '
import json, sys
for p in json.load(sys.stdin):
    if p.get("workspace") == sys.argv[1]:
        print(p["pane_id"], p["size"]["cols"], p.get("tty_name") or "-")' "$1"
}

term_panes() {   # session -> its pane ids, one a line
  if [ "${MM_TERMINAL:-}" = wezterm ]; then term_wez_panes "$1" | cut -d' ' -f1
  else tmux list-panes -s -t "$1" -F '#{pane_id}' 2>/dev/null; fi
}

term_has() {   # session -> success while it is running
  if [ "${MM_TERMINAL:-}" = wezterm ]; then [ -n "$(term_panes "$1")" ]
  else tmux has-session -t "$1" 2>/dev/null; fi
}

term_kill() {   # session -> every pane of it closed (and WezTerm's tags file with them)
  if [ "${MM_TERMINAL:-}" = wezterm ]; then
    local p
    for p in $(term_panes "$1"); do wezterm cli --no-auto-start kill-pane --pane-id "$p"; done
    rm -f "$(term_tags_file "$1")"
  else
    tmux kill-session -t "$1"
  fi
}

term_new() {   # session dir -> its first pane, made in dir; its id
  if [ "${MM_TERMINAL:-}" = wezterm ]; then
    [ -n "${WEZTERM_UNIX_SOCKET:-}" ] || { echo "$(basename "$0"): the config's terminal is wezterm - run this from a WezTerm window, whose server the roles' panes are made in (none is started by a script)" >&2; exit 1; }
    mkdir -p "$MM_STATE_DIR" && : > "$(term_tags_file "$1")"
    wezterm cli --no-auto-start spawn --new-window --workspace "$1" --cwd "$2"
  else
    tmux new-session -d -s "$1" -x "$(tput cols)" -y "$(tput lines)" -c "$2" -P -F '#{pane_id}'
  fi
}

term_split() {   # pane across|down dir -> a new pane beside it (across) or below it, made in dir; its id
  if [ "${MM_TERMINAL:-}" = wezterm ]; then
    local side=--bottom; [ "$2" = across ] && side=--right
    wezterm cli --no-auto-start split-pane --pane-id "$1" "$side" --cwd "$3"
  else
    local side=-v; [ "$2" = across ] && side=-h
    tmux split-window "$side" -t "$1" -c "$3" -P -F '#{pane_id}'
  fi
}

term_send() {   # pane text -> the text typed into the pane, then Enter
  if [ "${MM_TERMINAL:-}" = wezterm ]; then wezterm cli --no-auto-start send-text --pane-id "$1" --no-paste "$2"$'\r'
  else tmux send-keys -t "$1" "$2" Enter; fi
}

term_capture() {   # pane -e|lines -> its screen with its colours (-e), or its last LINES lines, each wrapped line joined
  if [ "${MM_TERMINAL:-}" = wezterm ]; then
    if [ "$2" = -e ]; then wezterm cli --no-auto-start get-text --pane-id "$1" --escapes; return; fi
    local cols; cols=$(term_wez_panes "$SESSION" | awk -v p="$1" '$1 == p {print $2}')
    wezterm cli --no-auto-start get-text --pane-id "$1" --start-line "-$2" | python3 -c '
import sys
width, held = int(sys.argv[1]) if sys.argv[1] else -1, ""     # its width unknown: nothing joined
for line in sys.stdin.read().split("\n"):
    held += line
    if len(line.rstrip(" ")) != width:      # a screen pads its lines with spaces: only a full one was wrapped
        print(held)
        held = ""
if held:
    print(held)' "$cols"
  elif [ "$2" = -e ]; then tmux capture-pane -e -p -t "$1" 2>/dev/null
  else tmux capture-pane -p -J -S "-$2" -t "$1" 2>/dev/null; fi
}

term_cmd() {   # pane -> the command in its foreground: the shell's own name while it is at its prompt
  if [ "${MM_TERMINAL:-}" = wezterm ]; then
    local tty; tty=$(term_wez_panes "$SESSION" | awk -v p="$1" '$1 == p {print $3}')
    [ -n "$tty" ] && [ "$tty" != - ] || return 0
    ps -o stat=,comm= -t "${tty#/dev/}" 2>/dev/null | awk '$1 ~ /\+/ {n = split($2, a, "/"); print a[n]; exit}'
  else
    tmux display-message -p -t "$1" '#{pane_current_command}' 2>/dev/null
  fi
}

term_pane_of_pid() {   # session pid -> the pane whose shell is the process's parent (a role's session, started there)
  local ppid; ppid=$(ps -o ppid= -p "$2" 2>/dev/null | tr -d ' ')
  [ -n "$ppid" ] || return 0
  if [ "${MM_TERMINAL:-}" = wezterm ]; then
    local tty; tty=$(ps -o tty= -p "$ppid" 2>/dev/null | tr -d ' ')
    [ -n "$tty" ] && term_wez_panes "$1" | awk -v t="/dev/$tty" '$3 == t {print $1}'
  else
    tmux list-panes -s -t "$1" -F '#{pane_pid} #{pane_id}' 2>/dev/null | awk -v p="$ppid" '$1 == p {print $2}'
  fi
}

term_tag() {   # pane key value -> the pane tagged (tmux: its own option @key; WezTerm: a line of the session's tags file)
  if [ "${MM_TERMINAL:-}" = wezterm ]; then printf '%s\t%s\t%s\n' "$1" "$2" "$3" >> "$(term_tags_file "$SESSION")"
  else tmux set-option -p -t "$1" "@$2" "$3"; fi
}

term_tag_of() {   # pane key -> its tag, the latest given; nothing when it has none
  if [ "${MM_TERMINAL:-}" = wezterm ]; then
    awk -F'\t' -v p="$1" -v k="$2" '$1 == p && $2 == k {v = $3} END {print v}' "$(term_tags_file "$SESSION")" 2>/dev/null
  else
    tmux show-options -pv -t "$1" "@$2" 2>/dev/null
  fi
}

term_list() {   # session -> "pane role command" for each of its panes
  if [ "${MM_TERMINAL:-}" = wezterm ]; then
    local p; for p in $(term_panes "$1"); do echo "$p $(term_tag_of "$p" role) $(term_cmd "$p")"; done
  else
    tmux list-panes -s -t "$1" -F '#{pane_id} #{@role} #{pane_current_command}'
  fi
}

term_label() {   # session -> each pane labelled with its role in its colour (tmux's border); WezTerm: the tab's title
  if [ "${MM_TERMINAL:-}" = wezterm ]; then
    wezterm cli --no-auto-start set-tab-title --pane-id "$(term_panes "$1" | head -1)" "$1" 2>/dev/null
  else
    tmux set-option -w -t "$1" pane-border-status top
    tmux set-option -w -t "$1" pane-border-format ' #[fg=#{@colour},bold]#{@role}#[default] '
  fi
}

term_layout() {   # session -> its panes tiled (tmux); WezTerm keeps the splits as made
  [ "${MM_TERMINAL:-}" = wezterm ] || tmux select-layout -t "$1" tiled
}

term_focus() {   # pane -> the pane selected
  if [ "${MM_TERMINAL:-}" = wezterm ]; then wezterm cli --no-auto-start activate-pane --pane-id "$1"
  else tmux select-pane -t "$1"; fi
}

term_conf() {   # file -> the terminal's settings loaded from it, when it is there (tmux's; WezTerm reads its own)
  [ "${MM_TERMINAL:-}" = wezterm ] || { [ -f "$1" ] && tmux source-file "$1"; }
  return 0
}

term_attach() {   # session -> this terminal shows it: tmux attaches; the WezTerm window already holds its panes
  if [ "${MM_TERMINAL:-}" = wezterm ]; then exit 0; fi
  exec tmux attach-session -t "$1"
}
