#!/usr/bin/env bash
# Read-only triage for a frozen GNOME Shell on X11. Changes nothing. Safe to run over SSH:
#   ssh drn2@<ip> 'bash -s' < gnome-shell-hang-triage.sh
# Background and reasoning: see incident-report_2026-10-30.md in this directory.

export XDG_RUNTIME_DIR=/run/user/$(id -u)
export DBUS_SESSION_BUS_ADDRESS=unix:path=$XDG_RUNTIME_DIR/bus

GS=$(pgrep -x gnome-shell | head -1)
[ -n "$GS" ] || { echo "No gnome-shell process found."; exit 2; }
echo "gnome-shell pid $GS, running $(ps -o etime= -p "$GS" | tr -d ' ')"

# 1. Does the main loop answer a request that needs it? (Peer.Ping is NOT a valid test: it answers while hung.)
OUT=$(timeout 6 gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell \
  --method org.freedesktop.DBus.Properties.Get org.gnome.Shell ShellVersion 2>&1)
RC=$?
echo
echo "== 1. main-loop request (6 s limit) =="
echo "exit code $RC   (124 = timed out)   reply: ${OUT:-<none>}"

# 2. Is the main thread making progress?
vol() { awk '$1=="voluntary_ctxt_switches:"{print $2}' "/proc/$GS/task/$GS/status" 2>/dev/null; }
V1=$(vol); sleep 3; V2=$(vol)
echo
echo "== 2. main thread (TID $GS) =="
echo "voluntary context switches: $V1 -> $V2 over 3 s   wait channel: $(cat /proc/$GS/task/$GS/wchan 2>/dev/null)"
echo "(healthy idle shell: counter rises, waits in ep_poll/poll;  hung: counter frozen, futex_do_wait)"

# 3. Every thread's CPU, unfiltered (a spinning helper such as 'dconf worker' shows up here)
echo
echo "== 3. busiest threads (2nd sample, all threads) =="
SPIN=""
top -H -b -n2 -d1 -p "$GS" | awk '/^top -/{n++} n==2 && /^ *[0-9]+ /' | head -5 | while read -r tid _ _ _ _ _ _ _ cpu _; do
  printf "TID %-8s %-16s %s%% CPU\n" "$tid" "$(cat /proc/$GS/task/$tid/comm 2>/dev/null)" "$cpu"
done
SPIN=$(top -H -b -n2 -d1 -p "$GS" | awk '/^top -/{n++} n==2 && /^ *[0-9]+ /{ if ($9+0 >= 90 && $1 != '"$GS"') print $1 }' | head -1)
[ -n "$SPIN" ] && echo ">> non-main thread $SPIN ($(cat /proc/$GS/task/$SPIN/comm 2>/dev/null)) is pegged at >=90% CPU"

# 4. Is the X server itself alive?
echo
echo "== 4. X server =="
XN=$(ls /tmp/.X11-unix/ 2>/dev/null | sed -n 's/^X//p' | head -1)
if [ -n "$XN" ]; then
  echo "display :$XN -> $(DISPLAY=:$XN XAUTHORITY=$XDG_RUNTIME_DIR/gdm/Xauthority timeout 5 xrandr --query 2>&1 | head -1)"
else
  echo "no X socket found in /tmp/.X11-unix"
fi

# 5. Session-failed screen state
echo
echo "== 5. session state =="
echo "org.gnome.Shell@x11.service: $(systemctl --user is-active org.gnome.Shell@x11.service 2>&1)"
echo "gnome-session-failed.service: $(systemctl --user is-active gnome-session-failed.service 2>&1)   (active = the Oh-no screen is up; do NOT stop it)"

# Verdict
echo
echo "== VERDICT =="
if [ "$RC" = 124 ] && [ "$V1" = "$V2" ]; then
  echo "HUNG: gnome-shell's main loop is not responding."
  [ -n "$SPIN" ] && echo "      A helper thread is spinning (matches the 2026-10-30 incident)."
  echo "      Next: run unfreeze-shell (saves evidence, restarts without the Oh-no screen); see incident-report_2026-10-30.md, 'Runbook'."
elif [ "$RC" = 0 ] && [ "$V1" != "$V2" ]; then
  echo "OK: the main loop is answering and making progress."
else
  echo "UNCLEAR: mixed signals (request rc=$RC, counters $V1 -> $V2). Run again in a few seconds."
fi
