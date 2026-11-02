#!/bin/bash
# agents-morning.sh - the morning restart of the project's role sessions, run by the reviewer when they decide (the
# reviewer, 2026-10-06: "option (b) but tell me to do it and give me the script that makes it easy and waits for
# everyone to idle if my morning connection kicked agents into action"; then "I don't care if the script types /land
# in the agent's windows as long as I decide when to run it").
#
#   bash agents-morning.sh
#
# Run it from a terminal window OUTSIDE the roles' tmux session (the last step ends that session). It
#   1. waits until all the roles are idle - a role reconnecting in the morning may be busy for a while; when none of
#      them is running (after a restart of the Mac), it starts them with `bash agents.sh` and goes no further;
#   2. on your "yes", types /land into every pane but the operator's, runs `claude update` while they land, waits until all are
#      idle, then types /land into the operator's;
#   3. asks you whether every pane said it is ready to clear, and only on "yes" runs `bash agents.sh --restart`,
#      which ends the tmux session and starts the roles fresh - on the updated Claude Code - each given its first
#      message by agents.sh.
# Ctrl-C at any point stops it; nothing is typed or restarted without your "yes".
#
#   bash agents-morning.sh --install-reminder   an alert at 06:00, Sunday to Thursday, saying to run this; it stays
#                                               on screen until OK is clicked (the reviewer: "it should wait for a dismissal")
#   bash agents-morning.sh --remove-reminder    removes it (the reviewer, 2026-10-06: "can you schedule the morning
#                                               macos job to remind me"). The reminder only notifies; it runs nothing.
#
# THE NIGHT RUN, in place of the morning /land (the reviewer, 2026-10-08: "for night schedule - check every 1/2 hour
# after 6 PM - if i am idle, check the agents that have been idle for 15 minutes, and land;clear;exit them. cont until
# all are closed. then update claude and wait for a 'go' input from me in the morning to start them all up"; a /land
# in the morning had cost about 2 million input tokens on caches gone cold overnight):
#
#   bash agents-morning.sh --install-night      launchd starts the night run at 18:00 every day; removes the 06:00
#                                               reminder, which the night run's "Go" replaces
#   bash agents-morning.sh --remove-night       removes it
#   bash agents-morning.sh --night              the night run itself, now (launchd's command)
#   MISHMERET_NIGHT_DRY_RUN=1 bash agents-morning.sh --night   says what it would type, types nothing, ends after one check
#   bash agents-morning.sh --skip-tonight       tonight's run does nothing; the job stays loaded (the reviewer, 2026-10-21:
#                                               "a clean way to tell it not to run w/o turning it off")
#   bash agents-morning.sh --skip               every run does nothing until --resume
#   bash agents-morning.sh --resume             removes both
#
# Every half hour: when you have touched neither keyboard nor mouse for 15 minutes, each role that is idle, whose
# last turn was 15 minutes ago or more AND WHOSE CONTEXT IS OVER 200,000 TOKENS (the config's night.context_limit; the Board #11,
# D4, and #31) is sent /land - one under it is sent /land too and then kept running, never cleared; once it is idle again and its pane says it is "ready to clear",
# /clear and /exit. A role that lands without saying so is asked once to report back; one that still does not, or that
# stops to ask you something, is left open and named in a notification - nothing is cleared that did not say it was ready. While roles are landing it looks every minute.
# When every role is closed, kept running or left open: if any was closed, `claude update`, then an alert that waits for
# you - "Go" starts the closed ones again with `bash agents.sh` in a new iTerm2 window (never --restart, which would end
# the roles kept running); if none was closed, nothing more. The Mac is kept awake until then (caffeinate), not while the
# alert waits. Its log: <the config's state_dir>/night/<date>/log.txt.
# Since the Board #12 (2026-10-11): started by hand from a terminal, it does not wait for you to be idle; a role whose
# last message says it is ready to clear, quiet two minutes, is cleared and closed at once (busy or idle, any context);
# and a role whose only running task is a Board wait (`board.py wait`) counts as idle.
# A ROLE WAITING FOR ANOTHER ROLE'S WORK IS NOT IDLE (the reviewer, 2026-10-11: "night run should not have told the ver to
# land when it had work to do. it should not have been idle."): a role whose Board corner says it is waiting for a role
# still running - not kept, left open or closed by this run - is not sent /land; it is looked at again next pass.

set -u
# the clone, the roles, the transcripts and the pane lookup (the project's config): agents-lib.sh, shared with
# agents.sh - which this run's Go and step 3 start, in the same clone (MISHMERET_CONFIG is exported there)
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/agents-lib.sh"
LABEL="$MM_LAUNCHD_PREFIX.agents-morning-reminder"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

if [ "${1:-}" = "--install-reminder" ]; then
  mkdir -p "$HOME/Library/LaunchAgents"
  days=""; for d in 0 1 2 3 4; do   # launchd's weekdays: 0 Sunday ... 4 Thursday
    days="$days<dict><key>Weekday</key><integer>$d</integer><key>Hour</key><integer>6</integer><key>Minute</key><integer>0</integer></dict>"
  done
  cat > "$PLIST" <<PLIST_END
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key><array>
    <string>/usr/bin/osascript</string><string>-e</string>
    <string>beep</string><string>-e</string>
    <string>display alert "$MM_PROJECT: the agents' morning restart" message "Run, from a window outside tmux:  bash ${DIR/#$HOME/~}/agents-morning.sh" buttons {"OK"} default button "OK"</string>
  </array>
  <key>StartCalendarInterval</key><array>$days</array>
  <key>StandardErrorPath</key><string>$MM_STATE_DIR/morning-reminder.err</string>
</dict>
</plist>
PLIST_END
  launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null
  launchctl bootstrap "gui/$(id -u)" "$PLIST" && echo "Reminder installed: 06:00, Sunday to Thursday ($PLIST)."
  exit $?
fi
if [ "${1:-}" = "--remove-reminder" ]; then
  launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null; rm -f "$PLIST"; echo "Reminder removed."; exit 0
fi

# ---- THE NIGHT RUN (described at the top) ----
NIGHT_LABEL="$MM_LAUNCHD_PREFIX.agents-night"
NIGHT_PLIST="$HOME/Library/LaunchAgents/$NIGHT_LABEL.plist"
CHECK_EVERY=$MM_NIGHT_CHECK_EVERY    # seconds between looks
YOU_IDLE=$MM_NIGHT_YOU_IDLE           # you: no keyboard or mouse for this long
ROLE_IDLE=$MM_NIGHT_ROLE_IDLE         # a role: idle, its last turn this long ago
LANDED_QUIET=$MM_NIGHT_LANDED_QUIET   # after /land: idle this long before its pane is read
ASK_READY="Has this session finished every step of /land? If it has, end with the closing sentence the land command asks for. If it has not, finish landing first."   # never the phrase itself: the pane is read for it
POLL=$MM_NIGHT_POLL                    # while a role lands
# A ROLE IS CLOSED ONLY WHEN ITS CONTEXT DEGRADES, NOT EVERY NIGHT (the reviewer, the Board #11, 2026-10-10: "A - All five",
# D4: "a role restarts only when its context degrades"): measured as the context its last turn carried, from its
# transcript. Over this many tokens it lands and is closed; UNDER IT, IT LANDS BUT IS NOT CLEARED (the reviewer, the
# Board #31, 2026-10-13: "c lower the limit to 200k so most times roles will be closed. if less than that - just land
# but not clear" - at 500,000 the operator was kept at 486,593 tokens, unlanded). A context that cannot be read is
# landed and kept too (Lesson 59: never closed on a guess).
CONTEXT_LIMIT=$MM_NIGHT_CONTEXT_LIMIT
GAP=$MM_NIGHT_GAP                       # between /clear and /exit
DRY="${MISHMERET_NIGHT_DRY_RUN:-}"

if [ "${1:-}" = "--install-night" ]; then
  mkdir -p "$HOME/Library/LaunchAgents" "$MM_STATE_DIR/night"
  cat > "$NIGHT_PLIST" <<PLIST_END
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$NIGHT_LABEL</string>
  <key>ProgramArguments</key><array>
    <string>/bin/bash</string><string>$DIR/agents-morning.sh</string><string>--night</string>
  </array>
  <key>EnvironmentVariables</key><dict>
    <key>PATH</key><string>$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
  </dict>
  <key>StartCalendarInterval</key><dict><key>Hour</key><integer>18</integer><key>Minute</key><integer>0</integer></dict>
  <key>StandardOutPath</key><string>$MM_STATE_DIR/night/launchd.out</string>
  <key>StandardErrorPath</key><string>$MM_STATE_DIR/night/launchd.err</string>
</dict>
</plist>
PLIST_END
  launchctl bootout "gui/$(id -u)/$NIGHT_LABEL" 2>/dev/null
  launchctl bootstrap "gui/$(id -u)" "$NIGHT_PLIST" || exit 1
  echo "Night run installed: 18:00 every day ($NIGHT_PLIST)."
  if [ -e "$PLIST" ]; then
    launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null; rm -f "$PLIST"
    echo "The 06:00 reminder removed: the night run's Go replaces it."
  fi
  exit 0
fi
if [ "${1:-}" = "--remove-night" ]; then
  launchctl bootout "gui/$(id -u)/$NIGHT_LABEL" 2>/dev/null; rm -f "$NIGHT_PLIST"; echo "Night run removed."; exit 0
fi

SKIP_DIR="$MM_STATE_DIR/night"
# the file that holds the run started on date $1, if any; read at the start and at every look (girsa-verifier's LOW on
# 7ba22ad8: a run going since 18:00 kept landing and clearing after --skip-tonight said it would do nothing)
skip_file() { local f; for f in "$SKIP_DIR/skip" "$SKIP_DIR/skip-$1"; do [ -e "$f" ] && { echo "$f"; return 0; }; done; return 1; }
if [ "${1:-}" = "--skip-tonight" ]; then
  mkdir -p "$SKIP_DIR" && touch "$SKIP_DIR/skip-$(date +%F)" || exit 1
  # A RUN GOING SINCE AN EARLIER EVENING (typed after midnight; girsa-verifier): its own date's file holds it too
  for going in "$SKIP_DIR"/????-??-??/.running; do
    [ -d "$going" ] || continue; d=$(basename "$(dirname "$going")"); touch "$SKIP_DIR/skip-$d"
    [ "$d" = "$(date +%F)" ] || echo "The night run going since $d 18:00 stops at its next look."
  done
  echo "The night run of $(date +%F) will do nothing - one already going stops at its next look; the job stays loaded."
  echo "Undo: bash agents-morning.sh --resume"; exit 0
fi
if [ "${1:-}" = "--skip" ]; then
  mkdir -p "$SKIP_DIR" && touch "$SKIP_DIR/skip" || exit 1
  echo "Every night run will do nothing - one already going stops at its next look; the job stays loaded."
  echo "Undo: bash agents-morning.sh --resume"; exit 0
fi
if [ "${1:-}" = "--resume" ]; then
  rm -f "$SKIP_DIR/skip" "$SKIP_DIR"/skip-????-??-??; echo "The night run runs again from tonight."; exit 0
fi

if [ "${1:-}" = "--night" ]; then
  # A RUN HELD BY --skip OR --skip-tonight ends before it looks at anything; one already going, at its next look
  RUN_DATE=$(date +%F)
  if f=$(skip_file "$RUN_DATE"); then
    mkdir -p "$SKIP_DIR"; echo "$(date '+%F %H:%M:%S') skipped: $f" >> "$SKIP_DIR/skipped.log"
    [ -z "$DRY" ] || echo "skipped: $f"
    exit 0
  fi
  if [ -n "$DRY" ]; then NIGHT="$MM_STATE_DIR/night/dry-$(date +%F-%H%M%S)"; else NIGHT="$MM_STATE_DIR/night/$(date +%F)"; fi
  mkdir -p "$NIGHT"
  say() { echo "$(date '+%F %H:%M:%S') $*" >> "$NIGHT/log.txt"; [ -z "$DRY" ] || echo "$*"; }
  notify() {
    say "told you: $*"
    [ -n "$DRY" ] || osascript -e "display notification \"$*\" with title \"$MM_PROJECT: the night run\"" >/dev/null 2>&1
  }
  type_in() {   # pane text
    if [ -n "$DRY" ]; then say "(dry run) would type $2 into $1"; else tmux send-keys -t "$1" "$2" Enter; fi
  }
  you_idle() { ioreg -c IOHIDSystem | awk '/HIDIdleTime/ {print int($NF / 1000000000); exit}'; }
  quiet_for() {   # sessionId -> seconds since its transcript last changed (its last turn); 0 when not found
    local f; f=$(transcript_of "$1")
    if [ -n "$f" ]; then echo $(( $(date +%s) - $(stat -f %m "$f") )); else echo 0; fi
  }
  context_of() {   # sessionId -> the tokens its last turn carried (input, cache read, cache written); 0 when not read
    local f; f=$(transcript_of "$1")
    [ -n "$f" ] || { echo 0; return; }
    "$PY" "$HERE/role_usage.py" context "$f" 2>/dev/null || echo 0   # a notice's zeros passed over (role_usage.last_call)
  }
  # A BOARD WAIT IS NOT WORK (the reviewer, 2026-10-11, Board #12: the steward's background `board.py wait` on its open
  # Board questions kept it "busy" all night - a running background task makes `claude agents` say busy - so the run
  # never found it idle). A role's pid -> success when each Bash shell it runs is a Board wait and nothing else, and
  # there is at least one; its own helpers (caffeinate) are not tasks. Combined below with ROLE_IDLE's quiet transcript.
  only_board_waits() {
    local c g n=0
    for c in $(pgrep -P "$1" 2>/dev/null); do
      case "$(ps -o comm= -p "$c" 2>/dev/null)" in *bash) ;; *) continue ;; esac
      g=$(pgrep -P "$c" 2>/dev/null); [ -n "$g" ] || return 1
      for c in $g; do ps -ww -o command= -p "$c" 2>/dev/null | grep -qE 'board\.py wait [0-9]+$' || return 1; done
      n=$((n + 1))
    done
    [ "$n" -gt 0 ]
  }
  # LANDED UNDER THE LIMIT (the Board #31): its landing is done, so it is kept running - not cleared - and stays kept
  # (`landed-kept`) until someone works with it again
  keep_landed() {
    say "$1: landed, context under ${CONTEXT_LIMIT} - kept running, not cleared"
    rm -f "$NIGHT/$1.land-sent" "$NIGHT/$1.land-only" "$NIGHT/$1.asked"; touch "$NIGHT/$1.kept" "$NIGHT/$1.landed-kept"
  }
  # ITS LAST MESSAGE SAYS IT IS READY TO CLEAR (the reviewer, 2026-10-11, Board #12: "If the last thing in an agent's
  # transcript is landed or ready to clear, don't wait for it to be idle"): sessionId -> success when the last thing in
  # its transcript - after any prompt put to it - is its own message saying so.
  said_ready() {
    local f; f=$(transcript_of "$1")
    [ -n "$f" ] || return 1
    "$PY" - "$f" <<'READY_END'
import json, os, re, sys
path = sys.argv[1]
with open(path, "rb") as fh:
    fh.seek(max(0, os.path.getsize(path) - 4 * 1024 * 1024))
    lines = fh.read().decode("utf-8", "replace").splitlines()
for line in reversed(lines):
    try:
        r = json.loads(line)
    except ValueError:
        continue
    if r.get("type") not in ("user", "assistant") or r.get("isMeta"):
        continue
    c = (r.get("message") or {}).get("content")
    blocks = [{"type": "text", "text": c}] if isinstance(c, str) else (c if isinstance(c, list) else [])
    text = " ".join(b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text")
    if r["type"] == "user":
        if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in blocks) or not text.strip():
            continue        # a tool's answer, not a prompt
        sys.exit(1)         # a prompt came after its last words
    if text.strip():
        # THE CLOSING SENTENCE ITSELF, as the last line of its last message - never the phrase anywhere (girsa-verifier,
        # 2026-10-11, on f4f82233: "I am not ready to clear yet ...", or a LANDED message quoting the rule, matched it)
        last = [l for l in text.splitlines() if l.strip()][-1]
        sys.exit(0 if re.sub(r"[*_`]", "", last).strip() == "The session is ready to clear." else 1)
sys.exit(1)
READY_END
  }
  # THE CLOSING SENTENCE ON A LINE OF ITS OWN in the pane (land.md, step 8), the reply's bullet or emphasis allowed -
  # never the phrase inside a line (girsa-verifier, 2026-10-11: "not ready to clear yet" matched the loose pattern)
  READY_LINE='^[[:space:]]*(⏺|●)?[[:space:]]*[*_`]*The session is ready to clear\.[*_`]*[[:space:]]*$'
  # STARTED BY HAND, IT DOES NOT WAIT FOR YOU TO BE IDLE (the reviewer, 2026-10-11, Board #12: "If I start any of the
  # agents scripts, don't wait for me to be idle"): launchd gives the run no terminal; one means you started it.
  BY_HAND=""
  if [ -t 0 ] || [ -t 1 ]; then BY_HAND=1; YOU_IDLE=0; fi
  if ! mkdir "$NIGHT/.running" 2>/dev/null; then say "another night run is going - this one stops"; exit 0; fi
  trap 'rmdir "$NIGHT/.running" 2>/dev/null' EXIT
  cafe=""
  if [ -z "$DRY" ]; then caffeinate -i -w $$ & cafe=$!; fi
  say "night run started${BY_HAND:+ by hand - not waiting for you to be idle}"
  while :; do
    # held: no more /land or clearing, but the night's end still runs - the roles closed so far get their Go (girsa-verifier)
    if f=$(skip_file "$RUN_DATE"); then say "held by $f - no more roles sent /land or cleared; a role already sent /land finishes it"; break; fi
    open=0; landing=0; pending=0; you=$(you_idle)
    for r in $ROLES; do
      info=$(role_info "$r"); st=${info%% *}; rest=${info#* }; sid=${rest%% *}; pid=${rest#* }
      if [ "$st" = "absent" ]; then
        # WHO CLOSED IT, AND EACH ROLE COUNTED ONCE (2026-10-11: three roles kept running, then closed outside the run,
        # were counted both ways - "5 closed, 3 kept running" for five roles - and "closed" read as the run's own doing;
        # girsa-verifier the same morning: a role left open for you and then closed kept its `left` mark the same way)
        if [ ! -e "$NIGHT/$r.closed" ]; then
          if [ -e "$NIGHT/$r.cleared" ]; then say "$r: not running - closed by this run (it had said it was ready to clear)"
          elif [ -e "$NIGHT/$r.land-sent" ]; then say "$r: not running - closed after its /land"
          else say "$r: not running - closed outside this run"; touch "$NIGHT/$r.outside"; fi
          rm -f "$NIGHT/$r.kept" "$NIGHT/$r.left" "$NIGHT/$r.nopane"; touch "$NIGHT/$r.closed"
        fi
        continue
      fi
      open=$((open + 1))
      if [ -e "$NIGHT/$r.closed" ]; then   # closed by this run and started again: its landing starts over
        # (2026-10-10: a run held open over a day kept the markers of three roles it had closed; started again, each would
        # have been read as landing and named "left open" - or cleared - on its first idle two minutes)
        rm -f "$NIGHT/$r.closed" "$NIGHT/$r.outside" "$NIGHT/$r.land-sent" "$NIGHT/$r.land-only" "$NIGHT/$r.landed-kept" "$NIGHT/$r.left" "$NIGHT/$r.asked" "$NIGHT/$r.kept" "$NIGHT/$r.nopane" "$NIGHT/$r.cleared"; say "$r: running again after it was closed - its landing starts over"
        pending=$((pending + 1)); continue
      fi
      pane=$(pane_of_pid "$pid")
      bw=""   # a Board wait only is not work (only_board_waits, above)
      if [ "$st" = "busy" ] && only_board_waits "$pid"; then st=idle; bw=" (only a Board wait running)"; fi
      if [ -e "$NIGHT/$r.cleared" ]; then   # cleared and sent /exit: waiting for it to close, five minutes at most
        if [ -n "$(find "$NIGHT/$r.cleared" -mmin +5 2>/dev/null)" ]; then
          notify "$r: cleared but still running five minutes after /exit - left open for you"
          rm -f "$NIGHT/$r.cleared"; touch "$NIGHT/$r.left"
        else pending=$((pending + 1)); landing=$((landing + 1)); fi
        continue
      fi
      # LANDED AND SAID SO: cleared and closed now - not waiting for it to be idle, nor for you, whatever its context
      if [ -n "$pane" ] && [ ! -e "$NIGHT/$r.landed-kept" ] && [ "$(quiet_for "$sid")" -ge "$LANDED_QUIET" ] \
          && said_ready "$sid"; then
        if [ -e "$NIGHT/$r.land-only" ]; then keep_landed "$r"; continue; fi
        say "$r: its last message says it is ready to clear$bw - /clear, /exit"
        type_in "$pane" "/clear"; sleep "$GAP"; type_in "$pane" "/exit"; sleep "$GAP"
        rm -f "$NIGHT/$r.kept" "$NIGHT/$r.left"; touch "$NIGHT/$r.cleared"
        pending=$((pending + 1)); landing=$((landing + 1)); continue
      fi
      if [ "$st" = "busy" ] && [ -e "$NIGHT/$r.left" ]; then   # someone is working with it again: start over
        rm -f "$NIGHT/$r.left" "$NIGHT/$r.land-sent" "$NIGHT/$r.asked"; say "$r: busy again after it was left open - its landing starts over"
        pending=$((pending + 1)); continue
      fi
      if [ -e "$NIGHT/$r.kept" ]; then   # kept running tonight; worked with again, it is looked at again when idle
        [ "$st" = "busy" ] && { rm -f "$NIGHT/$r.kept" "$NIGHT/$r.landed-kept"; say "$r: busy again after it was kept - looked at again when idle"; pending=$((pending + 1)); }
        continue
      fi
      [ -e "$NIGHT/$r.left" ] || pending=$((pending + 1))     # a role left open for you holds the run no longer
      if [ -e "$NIGHT/$r.land-sent" ]; then
        [ -e "$NIGHT/$r.left" ] && continue
        landing=$((landing + 1))
        q=$(quiet_for "$sid")
        # /LAND NOT LANDED (2026-10-30 and 10-31: every role after /land was asked to report back or said to be asking
        # you something, then left open): answered by a notice Claude Code wrote itself, its weekly limit - or, where
        # it left no record, its transcript unchanged since /land was typed. Named for what it is, idle or waiting.
        if { [ "$st" = "idle" ] && [ "$q" -ge "$LANDED_QUIET" ]; } || [ "$st" = "waiting" ]; then
          sent=$(stat -f %m "$NIGHT/$r.land-sent")
          if [ $(( $(date +%s) - q )) -lt "$sent" ]; then
            notify "$r: its transcript has not changed since /land was typed - /land did not reach it; left open for you"
            touch "$NIGHT/$r.left"; continue
          fi
          n=$("$PY" "$HERE/role_usage.py" synthetic-after "$(transcript_of "$sid")" "$sent" 2>/dev/null)
          if [ -n "$n" ]; then
            notify "$r: /land was answered by a notice, not a landing - $n - left open for you"
            touch "$NIGHT/$r.left"; continue
          fi
        fi
        if [ "$st" = "idle" ] && [ "$q" -ge "$LANDED_QUIET" ]; then
          # THE PANE'S RECENT HISTORY, ITS WRAPPED LINES JOINED (2026-10-09, the night of 10-08: the builder and the verifier
          # said "ready to clear" and were left open - the phrase had scrolled above the visible pane, or a narrow pane
          # broke it across two lines; the steward wrote "can be cleared")
          if [ -n "$pane" ] && tmux capture-pane -p -J -S -200 -t "$pane" 2>/dev/null \
              | grep -qE "$READY_LINE"; then
            if [ -e "$NIGHT/$r.land-only" ]; then keep_landed "$r"; continue; fi
            say "$r: landed and says it is ready to clear - /clear, /exit"
            type_in "$pane" "/clear"; sleep "$GAP"; type_in "$pane" "/exit"; sleep "$GAP"
          elif [ ! -e "$NIGHT/$r.asked" ]; then
            # ASKED ONCE TO REPORT BACK before it is left open (the reviewer, 2026-10-10: "when each agent is idle, tell it
            # to land and report back that it is ready to clear" - the operator's landing of 10-09 left out the sentence
            # and held the run open a day)
            say "$r: landed without saying it is ready to clear - asked to report back"
            type_in "$pane" "$ASK_READY"; touch "$NIGHT/$r.asked"
          else
            notify "$r: asked, and still did not say it is ready to clear - left open for you"; touch "$NIGHT/$r.left"
          fi
        elif [ "$st" = "waiting" ]; then
          notify "$r: stopped to ask you something while landing - left open for you"; touch "$NIGHT/$r.left"
        fi
        continue
      fi
      [ "$you" -ge "$YOU_IDLE" ] || continue
      q=$(quiet_for "$sid")
      { [ "$st" = "idle" ] && [ "$q" -ge "$ROLE_IDLE" ]; } || continue
      if [ -z "$pane" ]; then
        [ -e "$NIGHT/$r.nopane" ] || { notify "$r: its tmux pane was not found - not landed"; touch "$NIGHT/$r.nopane"; }
        pending=$((pending - 1)); continue      # nothing more this run can do for it
      fi
      # A PLAN WINDOW AT ITS LIMIT: no /land, which a session at the limit answers with a notice and lands nothing
      # (2026-10-30; the Board's #118, A). Named once; the first night run after the reset lands it.
      lim=$("$PY" "$HERE/board.py" at-limit 2>/dev/null)
      if [ -n "$lim" ]; then
        [ -e "$NIGHT/$r.limit" ] || { notify "$r: not landed - limit, $lim; the next night run tries again"; touch "$NIGHT/$r.limit"; }
        pending=$((pending - 1)); continue
      fi
      # WAITING FOR ANOTHER ROLE'S WORK (the comment at the top): that role still running, and not kept, left open or
      # closed by this run - so work may still come; tonight 2026-10-11 the builder's HANDOFF reached the verifier 37 s
      # after its /land
      w=$("$PY" "$HERE/board.py" waiting-for "$r" 2>/dev/null)
      if [ -n "$w" ] && [ "$(role_info "$w" | cut -d' ' -f1)" != "absent" ] \
          && [ ! -e "$NIGHT/$w.kept" ] && [ ! -e "$NIGHT/$w.left" ] && [ ! -e "$NIGHT/$w.closed" ]; then
        [ -e "$NIGHT/$r.waits" ] || { say "$r: its corner says it is waiting for $w, still running - not idle, looked at again next pass"; touch "$NIGHT/$r.waits"; }
        continue
      fi
      rm -f "$NIGHT/$r.waits"
      ctx=$(context_of "$sid")
      if [ "${ctx:-0}" -lt "$CONTEXT_LIMIT" ]; then   # landed, then kept running - never cleared (land-only)
        if [ "${ctx:-0}" -gt 0 ]; then say "$r: context ${ctx} tokens, under ${CONTEXT_LIMIT} - /land, then kept running"
        else say "$r: its context could not be read - /land, then kept running"; fi
        type_in "$pane" "/land"; touch "$NIGHT/$r.land-sent" "$NIGHT/$r.land-only"; landing=$((landing + 1)); continue
      fi
      say "$r: idle${bw}, last turn ${q}s ago; you idle ${you}s; context ${ctx} tokens - /land"
      type_in "$pane" "/land"; touch "$NIGHT/$r.land-sent"; landing=$((landing + 1))
    done
    [ "$pending" -gt 0 ] || break       # every role closed, kept running, or left open for you
    if [ -n "$DRY" ]; then say "(dry run) one look: $open running, $pending to look at, $landing landing; you idle ${you}s"; exit 0; fi
    if [ "$landing" -gt 0 ]; then sleep "$POLL"; else sleep "$CHECK_EVERY"; fi
  done
  closed=$(ls "$NIGHT"/*.closed 2>/dev/null | wc -l | tr -d ' ')
  say "the night's work is done: $closed closed ($(ls "$NIGHT"/*.outside 2>/dev/null | wc -l | tr -d ' ') of them outside this run), $(ls "$NIGHT"/*.kept 2>/dev/null | wc -l | tr -d ' ') kept running, $(ls "$NIGHT"/*.left 2>/dev/null | wc -l | tr -d ' ') left open for you, $(ls "$NIGHT"/*.nopane 2>/dev/null | wc -l | tr -d ' ') whose pane was not found, $(ls "$NIGHT"/*.limit 2>/dev/null | wc -l | tr -d ' ') not landed for the plan's limit"
  if [ "$closed" -eq 0 ]; then say "no role was closed - no update, no Go"; exit 0; fi
  if [ -n "$DRY" ]; then say "(dry run) would run claude update, then wait for your Go"; exit 0; fi
  claude update >> "$NIGHT/log.txt" 2>&1
  v=$(claude --version 2>/dev/null)
  say "Claude Code is now $v"
  [ -z "$cafe" ] || kill "$cafe" 2>/dev/null   # the Mac may sleep while the alert waits
  ans=$(osascript -e "display alert \"$MM_PROJECT: $closed of the roles landed and closed\" message \"Claude Code is now $v. Go starts the closed roles again; the others keep running.\" buttons {\"Not today\", \"Go\"} default button \"Go\"" 2>>"$NIGHT/log.txt")
  case "$ans" in
    *:Go)
      say "Go - starting the closed roles again"
      # in iTerm2, the reviewer's terminal (2026-10-10: "friday it started up the sessions in a terminal window instead of
      # iterm2")
      osascript -e 'tell application "iTerm"' -e 'activate' -e 'set w to (create window with default profile)' \
        -e "tell current session of w to write text \"MISHMERET_CONFIG='$MISHMERET_CONFIG' bash '$DIR/agents.sh'\"" -e 'end tell' >/dev/null ;;   # never --restart: it would end the roles kept running; MISHMERET_CONFIG: a new window does not inherit this run's
    # "Not today" OR NO ANSWER: never started unattended (the reviewer, 2026-10-27: "no to restarting roles at night -
    # they will then start working w/o superv. [without supervision] and burn thru tokens")
    *) say "not started (${ans:-no answer}) - start them with: bash agents.sh" ;;
  esac
  exit 0
fi

if [ -n "${TMUX:-}" ] && [ "$(tmux display-message -p '#S' 2>/dev/null)" = "$SESSION" ]; then
  echo "This window is inside the '$SESSION' tmux session, which the last step ends. Run it from another terminal window."
  exit 1
fi

states() {   # one line per role: "name status" (status "absent" when no session of that name is listed; a busy role
             # whose turn has ended is idle - 0NA, 2026-10-26: the operator's keep-alive loop kept it busy to this wait)
  local r; for r in $ROLES; do echo "$r $(role_state "$r")"; done
}
# A ROLE THAT IS NOT RUNNING IS NOT WAITED FOR (the reviewer, 2026-10-08: "The start script spins on missing agents" -
# an absent role counted as busy, so the wait never ended). It is named once, and the restart starts it.
busy_ones() { states | awk '$2 != "idle" && $2 != "absent" {printf "%s (%s) ", $1, $2}'; }
absent_ones() { states | awk '$2 == "absent" {printf "%s ", $1}'; }

wait_all_idle() {   # $1 = seconds every running role must stay idle in a row; $2 = "start" at step 1 only
  local quiet=0 b a
  a=$(absent_ones)
  # NONE RUNNING AT STEP 1, NOTHING TO LAND: start them (the reviewer, 2026-10-27: "agents_morning should just call
  # agents when appr. [appropriate] rather than tell me to do it" - after a restart of the Mac it said "Start them with:
  # bash agents.sh"); plain agents.sh, never --restart, ends nothing. Gone during step 2's landing, they stopped without
  # landing: a stop that names --resume, never fresh sessions over them (girsa-verifier's LOW on c524fb2e)
  if [ "$(echo $a | wc -w)" -eq "$(echo $ROLES | wc -w)" ]; then
    if [ "${2:-}" = "start" ]; then
      echo "  No role session is running (claude agents lists none of the roles) - starting them: bash agents.sh"
      exec bash "$DIR/agents.sh"
    fi
    echo
    echo "  No role session is running any more (claude agents lists none of the roles): they stopped during the landing."
    echo "  Resume each with its context: bash agents.sh --resume"
    exit 1
  fi
  [ -z "$a" ] || echo "  Not running, so not waited for: $a"
  while [ "$quiet" -lt "$1" ]; do
    b=$(busy_ones)
    if [ -n "$b" ]; then quiet=0; printf '\r  waiting for: %-100s' "$b"; else quiet=$((quiet + 10)); printf '\r  all idle for %ss%-90s' "$quiet" ""; fi
    sleep 10
  done
  echo
}

echo "Step 1 - waiting until all the roles are idle."
wait_all_idle 30 start
echo
echo "Step 2 - /land in each role's pane. Each lands its session and ends by saying it is ready to clear;"
echo "         answer any question one asks you in its pane."
read -r -p "         Type yes to send /land - to the others first, the operator last (anything else: you type it): " answer
send_land() {   # roles...
  local r pane
  for r in "$@"; do
    pane=$(pane_of "$r")
    if [ -n "$pane" ]; then tmux send-keys -t "$pane" "/land" Enter; echo "         sent to $r ($pane)"
    else echo "         $r: its pane was not found - type /land in it yourself"; fi
  done
}
update_claude() {   # while the sessions land: a running session keeps the version it started with, and the fresh
                    # sessions of step 3 start on the new one (the reviewer, 2026-10-06: "do claude update right after
                    # telling the sessions to land and before starting new sessions")
  echo "         Updating Claude Code (claude update):"
  claude update 2>&1 | sed 's/^/           /'
  echo "         Claude Code is now $(claude --version 2>/dev/null)."
}
wait_landed() {
  sleep 30
  echo "         Waiting until all have been idle for two minutes running."
  wait_all_idle 120
}
if [ "$answer" = "yes" ]; then
  # the operator last: the others land into the main tree, and the operator's own landing checks what they landed
  send_land $(for r in $ROLES; do [ "$r" = "$MM_OPERATOR_ROLE" ] || printf '%s ' "$r"; done)
  update_claude
  wait_landed
  send_land "$MM_OPERATOR_ROLE"
  wait_landed
else
  read -r -p "         Press Enter once you have typed /land in every role's pane (the operator last). " _
  update_claude
  wait_all_idle 120
fi
echo
echo "Step 3 - did every pane say it is ready to clear?"
read -r -p "         Type yes to restart all the roles (bash agents.sh --restart), anything else to stop here: " answer
if [ "$answer" != "yes" ]; then
  echo "Stopped. Nothing restarted. Finish the landing in the pane that is not ready, then run this again."
  exit 0
fi
echo
exec bash "$DIR/agents.sh" --restart
