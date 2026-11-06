# GNOME Shell (X11) freezes on workspace switch: main thread blocked, `dconf worker` thread spinning

A write-up of one hang, its likely trigger, a recovery that worked, and a better one that is still untested.
Written with the help of an AI assistant. **The mechanism in section 3 is a hypothesis from reading source code; no backtrace has confirmed it.**

## 1. Summary

- **Symptom:** after a burst of workspace switches (left/right), the desktop froze. The mouse cursor still moved, but nothing repainted
  and no keyboard input worked. The rest of the machine was fine: SSH worked and other processes kept running.
- **What was hung:** `gnome-shell`'s main thread, blocked on a futex. A helper thread inside gnome-shell named **`dconf worker`** was
  spinning at ~100% CPU. The `dconf-service` daemon was idle, the X server was healthy, and the GPU was idle.
- **Likely trigger:** a user script that wrote the wallpaper setting through dconf on **every** workspace switch. Both freezes seen in
  about a month came right after a burst of switches, with the script's last log line being one of those writes.
- **Fix that worked:** `kill -KILL` on the gnome-shell process (systemd respawned it in about a second). It has side effects (section 4).
- **Prevention:** stop writing settings on every workspace switch. If freezes continue with that removed, the hypothesis below is wrong.

## 2. Environment

- Ubuntu 24.04, **X11** session (this does not apply to Wayland, where the shell is the display server)
- GNOME Shell 46.0, GJS 1.80.2, GLib 2.80.0, dconf 0.40.0, systemd 255
- Laptop with hybrid Intel + NVIDIA graphics (proprietary driver 580.x); no GPU errors were logged around the hang
- Roughly 6,700 per-switch settings writes were logged since the script's last change, and 2 freezes occurred in that time (about 1 per 3,000
  writes), so this is a rare race, not a failure on every switch. Of those writes, about 60% came less than 2 s after the previous switch.

## 3. Diagnosis

### 3.1 Checks that worked (all read-only, over SSH or a text console)

```bash
GS=$(pgrep -x gnome-shell)

# 1. Does the shell's MAIN LOOP answer? A property read needs it. (Use a timeout.)
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus
timeout 6 gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell \
  --method org.freedesktop.DBus.Properties.Get org.gnome.Shell ShellVersion; echo "rc=$?"   # 124 = hung

# 2. Is the main thread making progress? (hung: counter frozen, wchan = futex_do_wait; healthy idle: poll/epoll)
for i in 1 2 3; do awk '$1=="voluntary_ctxt_switches:"{print $2}' /proc/$GS/task/$GS/status; cat /proc/$GS/task/$GS/wchan; echo; sleep 2; done

# 3. Per-thread CPU, UNFILTERED. A spinning helper thread shows here.
top -H -b -n2 -d1 -p $GS | awk '/^top -/{n++} n==2' | head -12

# 4. Is the X server itself alive?  (find the display first: ls /tmp/.X11-unix/)
DISPLAY=:N XAUTHORITY=/run/user/$(id -u)/gdm/Xauthority timeout 5 xrandr --query | head -1
```

### 3.2 Pitfalls

- **`org.freedesktop.DBus.Peer.Ping` is not a health check.** It still answers while the main loop is hung (GDBus appears to serve it from its
  own worker thread). Use a property read that the main loop has to service.
- **Do not filter `top -H` output by thread name.** An early attempt filtered on names I expected, which hid the `dconf worker` thread
  that was the one spinning.
- A process-level `top` showing gnome-shell at 100% CPU was misleading: it was one helper thread, not the main loop.
- The cursor still moving does not mean the shell is alive: the cursor is drawn by the X server/GPU.

### 3.3 Ruled out

- **GPU/driver hang:** no Xid, reset or hung-task messages; GPU idle.
- **Memory pressure:** plenty of RAM available at the time.
- **Disk I/O:** the shell's main thread was in an interruptible futex wait, not disk wait. (The kernel's cumulative I/O pressure counter looked large,
  but it counts any time all active tasks wait on I/O, even one reader on a slow disk. It is not evidence of a stall.)
- **High CPU load as a cause:** averaged CPU usage was about 87-89% idle during the hang. Short bursts would not show in 10-minute averages, so load is
  neither confirmed nor ruled out.

## 4. The hypothesis (unverified): a lock-order deadlock

From reading the installed source versions (not from a backtrace), two threads can take the same two locks in opposite order:

```
gnome-shell MAIN THREAD (GJS garbage collection)       "dconf worker" THREAD (a dconf change notification arrives)
----------------------------------------------         -------------------------------------------------------
1. holds GJS's toggle-queue lock (a busy-wait           1. holds the GSettings backend mutex while it walks
   spin lock) for the whole GC sweep                       every GSettings object in the process
2. frees a dead Gio.Settings, whose cleanup needs       2. takes a temporary ref on a JS-owned GSettings
   the GSettings backend mutex                             -> GJS toggle notification -> needs the toggle-queue lock
   ==> blocks in futex, forever                            ==> spins at 100% CPU, forever
```

This matches the observations: main thread in `futex_do_wait` making no progress, `dconf worker` at ~100% CPU, `dconf-service` idle.

Places to look in the source (function and file names only; line numbers are deliberately omitted because the reading is unverified):

- GJS `gi/toggle.cpp`: `ToggleQueue::lock()` is a busy-wait compare-exchange loop (no sleep or yield).
- GJS `gi/object.cpp`: `update_heap_wrapper_weak_pointers()` holds the toggle-queue lock during the GC sweep; `wrapped_gobj_toggle_notify()` takes it from any thread.
- GLib `gio/gsettingsbackend.c`: `g_settings_backend_dispatch_signal()` holds the backend lock while taking weak refs on every GSettings.
- GNOME Shell `js/ui/background.js`: each `Background` creates its own `Gio.Settings`, so each wallpaper change leaves one more for the GC to free.

Why a per-switch wallpaper write would set it off (inference): each write sends a change notification to the worker thread, and the switch
animation allocates many JS objects, so GC runs around switches. In a burst, the next write can land while the previous wallpaper's objects are being collected.

**What would confirm it:** a backtrace (or core dump) of the next hang. Expected: `dconf worker` in `ToggleQueue::lock` / `wrapped_gobj_toggle_notify`
under `g_weak_ref_get` and `g_settings_backend_keys_changed`; the main thread in `g_mutex_lock` under `g_settings_backend_watch_weak_notify`
under `g_object_unref` / `release_native_object` under GC frames. `ptrace_scope=1` means you need `sudo`; use debuginfod so frames have names:

```bash
sudo gdb -p $GS -batch -iex 'set debuginfod enabled off' -ex 'thread apply all bt 25'   # quick; names may show as ??
# better: sudo gcore -o ~/hang $GS   then, as yourself:
gdb -batch -iex 'set debuginfod enabled on' -ex 'thread apply all bt' /usr/bin/gnome-shell ~/hang.<pid>
```

Upstream: the busy-wait lock was still present in GJS master when checked, and one web search found no matching bug report.
A backtrace would be the thing to attach if reporting it.

## 5. Recovery

### 5.1 What worked: SIGKILL, with side effects

`kill -KILL <gnome-shell pid>` ends it, and systemd respawns it within about a second (`Restart=always`). On Ubuntu 24.04 the unit is
`org.gnome.Shell@x11.service`, with `OnFailure=org.gnome.Shell-disable-extensions.service gnome-session-failed.target`. Death by SIGKILL counts as a failure, which causes:

1. **A fullscreen "Oh no! Something has gone wrong" lockdown screen** on every workspace, with a Log Out button.
   It is a trap: `gnome-session-failed.service` has `ExecStopPost=gnome-session-ctl --shutdown` and `OnFailure=gnome-session-shutdown.target`
   (`OnFailureJobMode=replace-irreversibly`). **If that process is stopped, closed or fails, the whole session shuts down**, ending every GUI app.
   Do not click Log Out and do not `systemctl stop` it.
2. **One Chromium-based browser crashed about 15 seconds after the kill.** Cause not confirmed; losing the window manager is the likely reason.
   Its session files were intact, so reopening and clicking Restore recovered the tabs. All other apps survived.

**Getting rid of the lockdown screen without ending the session:** hide its X windows and leave the process running.

```bash
export DISPLAY=:N XAUTHORITY=/run/user/$(id -u)/gdm/Xauthority
xdotool search --pid "$(pgrep -f '^/usr/libexec/gnome-session-failed')"   # two windows: one tiny, one screen-sized
xdotool windowunmap <each id>            # undo with: xdotool windowmap <each id>
```

A systemd drop-in that empties `ExecStopPost=` works, but one that tries to empty `OnFailure=` does nothing: systemd.unit(5) says dependencies
cannot be reset to an empty list in a drop-in. The session stays flagged as failed until the next logout.

### 5.2 Better, but still untested on a real shell: SIGINT instead of SIGKILL

- gnome-shell neither catches nor ignores SIGINT or SIGHUP (check `SigCgt` / `SigIgn` in `/proc/<pid>/status`; the running shell caught
  SIGILL, SIGTRAP, SIGABRT, SIGBUS, SIGFPE, SIGSEGV, SIGTERM and signal 33, and ignored SIGPIPE and SIGXFSZ). The kernel therefore ends the process on
  SIGINT even if its main thread is deadlocked, just as with SIGKILL.
- systemd.service(5), `SuccessExitStatus=`: besides exit status 0, the signals SIGHUP, SIGINT, SIGTERM and SIGPIPE count as a clean exit for non-oneshot
  units. With `Restart=always` the shell restarts, and `OnFailure=` should not fire, so the lockdown screen should not appear.
- SIGTERM is caught by the shell, so a hung shell is unlikely to act on it.
- Tested only on throwaway units with the same restart settings (SIGINT and SIGHUP restarted them with no failure logged; SIGKILL logged
  `Failed with result 'signal'` and triggered `OnFailure=`). **Not yet tried on the real shell**, and it will not prevent the browser crash if that
  is caused by the window manager disappearing.

Whichever signal is used: save evidence first (thread states, journal, ideally a core dump with `sudo gcore`), because the restart destroys it.
A text console (`Ctrl+Alt+F3`) or SSH is enough to do all of this; no reboot or logout is needed.

## 6. Prevention / workarounds

- **Stop changing settings on every workspace switch.** This is both the fix and the test: if freezes continue, the hypothesis is wrong.
- If per-workspace wallpapers are wanted: debounce harder (e.g. 2 s) to merge bursts (fewer writes, same risk per write), or implement it inside the
  shell as an extension that swaps the displayed image without writing settings (an extension bug can also crash the shell).
- Keep a recovery path that does not need the desktop: SSH, or a text console, and a script that checks the main loop with a property read.
- Keep long-running jobs independent of the GUI session (tmux, user services). In this incident the non-GUI jobs all survived the shell restart.
- Package updates available at the time (GLib, gnome-shell) fixed other hangs, not this one; GJS, mutter and dconf had no update.

## 7. Caveats

- Two freezes only; one was observed live, the other reconstructed from logs.
- The deadlock mechanism is from source reading by an AI assistant and has not been independently checked or caught in a backtrace.
- X11 / Ubuntu 24.04 specifics (unit names, signal handling) may differ on other distributions or versions.
- The SIGINT recovery is untested on a real shell.
