# Compositor freeze on the Legion — 2026-10-30

> Published copy: the hostname, LAN address and details of unrelated hardware were removed.

> Author: Claude Code running on the Mac, diagnosing the Legion over SSH.
>
> Companion notes from the Claude session on the Legion, which found the likely trigger after this was first written:
> `cause-and-fixes_20261030_180155.md` (log history, trigger, likely mechanism, fixes), `unfreeze-shell_20261030_192908.sh`
> (one-command recovery) and, one folder up, `message_mac-claude_freeze-followup_20261030_202610.txt`.
> Where the two reports differ, the cause-and-fixes note is the newer one. This file was updated later the same evening to reflect it.

Written the same day, from the debugging session. Times are UTC+4 (the machine's local time).
**Root cause is NOT confirmed by a backtrace.** A likely trigger was found afterwards (see TL;DR). Where something is an inference or an untested idea, it says so.

## TL;DR

- **Symptom:** switching workspaces (left/right) while the machine was busy with compute froze the desktop.
  The mouse cursor still moved, but nothing repainted and no keyboard input worked. The machine itself was fine
  (other jobs kept running).
- **What was actually hung:** `gnome-shell`'s main thread. One of its own helper threads, `dconf worker`,
  was spinning at 100% CPU while the main thread sat blocked on a futex.
- **Fix that worked:** `kill -KILL` on the gnome-shell process (systemd respawned it in ~1 s).
- **Side effects of that fix:** GNOME put up its fullscreen "Oh no! Something has gone wrong" screen over every
  workspace, and **Brave crashed** 15 s later. mpv, the `claude` sessions and the python jobs all survived.
- **Likely trigger (found later by the Legion-side Claude):** the per-workspace wallpaper daemon, which writes a new wallpaper into dconf
  on every workspace switch. Both freezes since its Sep 24 fix (Oct 11 13:03, Oct 30 17:04) came right after a burst of switches.
  The daemon was stopped at 19:26 and its autostart disabled, so per-workspace wallpapers are currently off.
- **Not done:** no backtrace of the hung process was taken before it was killed, so the mechanism (a lock-order deadlock between GJS
  garbage collection and GSettings, per the other note) is still a hypothesis.

## The machine

| | |
|---|---|
| Model | Lenovo Legion Pro 7 16IRX9H (83DE), hostname `<hostname>` |
| OS | Ubuntu 24.04.5 LTS, kernel 7.0.0-38-generic, GNOME Shell 46.0 |
| Session | **X11** (Xorg + gnome-shell/mutter), display is **`:1`**, not `:0` |
| X auth | `XAUTHORITY=/run/user/1001/gdm/Xauthority` |
| GPUs | Intel Raptor Lake-S UHD + NVIDIA RTX 4080 Laptop, proprietary driver 580.178.04 |
| Display | Samsung LC49G95T on HDMI-0, running 3840x1080 |
| RAM | 31 GiB + 8 GiB swap file |
| LAN | dynamic address (reserve it in the router if you want it stable) |

## Timeline (2026-10-30)

| Time | Event |
|---|---|
| ~17:04 | Freeze begins. The wallpaper daemon's log shows five workspace switches at 17:04:05.9–17:04:10.5, each followed by a wallpaper write; the last write was at 17:04:10.572. (My earlier estimate from the `dconf worker` thread's CPU time, ~19.5 min at ~17:23, agreed.) |
| ~17:16 | Legion found on the LAN from the Mac (ARP cache + ping sweep of the LAN; the only Ubuntu SSH banner), key installed with `ssh-copy-id`. |
| 17:16–17:23 | Read-only diagnosis (below). |
| 17:25:30 | `kill -KILL 5476` (gnome-shell). Respawned as pid 1995847 in ~1 s. systemd then started `gnome-session-failed.service`. |
| 17:25:45 | Brave exited (crash). Scope `app-org.chromium.Chromium-11403` ended. |
| shortly after | Fail screen hidden (see "Getting rid of the Oh-no screen"). Workspace switching worked again. |

## How it was diagnosed

1. **X server was alive.** Xorg's main loop was in `ep_poll` with its context-switch counter advancing, and
   `xrandr --query` on `:1` answered. The cursor is drawn by the X server/GPU, which is why it still moved.
2. **gnome-shell's main loop was dead.**
   - A D-Bus *property read* (`org.freedesktop.DBus.Properties.Get org.gnome.Shell ShellVersion`) timed out
     after 6 s, while the same kind of call to the bus daemon returned instantly.
   - The main thread (TID = PID) was state `S`, wait channel `futex_do_wait`, and its voluntary
     context-switch counter did not change over several seconds. A healthy idle shell waits in `ep_poll`/`poll`.
3. **One thread was spinning.** `dconf worker` (a thread inside gnome-shell) held 99.9% CPU continuously;
   every other thread was at 0%. The `dconf-service` daemon itself was idle.
4. **Things that looked guilty but weren't** (see "Retracted leads").

Likely cause (not proven by a backtrace): a lock-order deadlock between GJS garbage collection on the main thread and GSettings change
dispatch on the `dconf worker` thread, set off by the wallpaper daemon's per-switch dconf writes. That fits what was seen live. The
source-code reading behind it is in `cause-and-fixes_20261030_180155.md`; I have not verified it independently.

## Retracted leads (so nobody chases them again)

- **"gnome-shell is spinning on CPU."** The first `top` snapshot showed 100%, but that was the `dconf worker` thread, not the main loop.
  An earlier per-thread view filtered by thread *name* and hid that thread. Don't filter thread names.
- **NVIDIA/GPU hang.** No Xid, GPU reset or hung-task messages this boot; GPU idle (P8). (One `Xid 31` on Oct 24 in the previous boot came from mpv's `vo` thread; no known link.)
- **Disk I/O stalls.** The 6.7 h "full" figure in `/proc/pressure/io` is a cumulative counter that counts any moment all
  active tasks wait on I/O, even a single reader on a slow disk. It is not evidence of a stall and was dropped.
- **Memory pressure.** 24 GB was available at the time. (Separate issue: a runaway `python` hit the OOM killer at 25–29 GB on Oct 7 x3, Oct 14 x2, Oct 26 and Oct 28.)
- **Heavy compute load as the cause.** The Legion-side note's sysstat 10-minute averages show the CPUs about 87–89% idle during the hang. Short bursts would not show at that resolution, so load is neither confirmed nor ruled out.
- **`org.freedesktop.DBus.Peer.Ping` as a health check.** It still answers while the main loop is hung (it appears to be served from GDBus's worker thread). Use the property read instead.

## What went wrong with the fix

Claude (the assistant) said apps would survive a gnome-shell restart on X11. Most did; **Brave did not**.

- `kill -KILL` on the shell makes `org.gnome.Shell@x11.service` fail, and its `OnFailure` hook starts
  `gnome-session-failed.service` — a fullscreen "Oh no! Something has gone wrong" lockdown with a Log Out button, shown on every workspace.
- That service is a trap: it has `ExecStopPost=gnome-session-ctl --shutdown` and `OnFailure=gnome-session-shutdown.target`
  (job mode `replace-irreversibly`). **If the fail-screen process is stopped, closed, or exits uncleanly, the whole session shuts down**
  and every GUI app dies. Do **not** click Log Out and do not `systemctl stop` it.
- Brave crashed ~15 s after the kill: `exit_type` is `Crashed`, apport wrote `/var/crash/_opt_brave.com_brave_brave.1001.crash`
  (163 MB, contains browser memory — don't upload it). Cause not confirmed; the timing points at losing the window manager.
  Its session files on disk were intact (last write 17:13), so relaunching and clicking Restore recovers the tabs.

### Getting rid of the Oh-no screen (what worked)

Hide its X windows; leave the process running so nothing triggers the shutdown:

```bash
export DISPLAY=:1 XAUTHORITY=/run/user/$(id -u)/gdm/Xauthority
PID=$(pgrep -f '^/usr/libexec/gnome-session-failed')
xdotool search --pid "$PID"            # expect 2 windows (one tiny, one screen-sized)
xdotool windowunmap <each window id>   # hides them
# to undo:  xdotool windowmap <each window id>
```

The session is still flagged "failed" internally; a normal log out/reboot clears it.

### Temporary systemd override still in place — remove at next logout/reboot

Two drop-ins were added while trying to defuse the trap. `ExecStopPost=` was cleared successfully. The `OnFailure=` lines do nothing, by design:
systemd.unit(5) says dependencies cannot be reset to an empty list, only added to in drop-ins. **So the trap is still armed**: if the hidden
fail-screen process fails, `OnFailure=gnome-session-shutdown.target` ends the session. Leave it running; a normal log out clears it.
Afterwards remove the drop-ins:

```bash
rm -f ~/.config/systemd/user/gnome-session-failed.service.d/zz-temp-no-shutdown.conf \
      ~/.config/systemd/user/gnome-session-failed.target.d/zz-temp-no-shutdown.conf
rmdir ~/.config/systemd/user/gnome-session-failed.service.d ~/.config/systemd/user/gnome-session-failed.target.d
systemctl --user daemon-reload
```

## Runbook for next time

1. **Don't reboot, don't log out, don't hard-reset.** If compute jobs are still running, they are fine.
2. **Run `unfreeze-shell`** (written by the Legion-side Claude; `~/.local/bin/unfreeze-shell` links to
   `unfreeze-shell_20261030_192908.sh` in this folder). Either:
   - at the laptop: `Ctrl+Alt+F3`, log in, run `unfreeze-shell`. It switches back to the desktop by itself (otherwise `Ctrl+Alt+F2`); or
   - from the Mac: `ssh -t <user>@<hostname>.local .local/bin/unfreeze-shell`. That name resolved from the Mac on 2026-10-30 and offered the same host key as the IP; the first connection by name needs the key accepted once.
     Otherwise use the IP (router DHCP list, or `arp -a` plus a ping-sweep of the LAN).
   If someone is at a text console while you run it over SSH, ask them to press `Ctrl+Alt+F2` afterwards.
3. What it does: checks that the main loop really is hung (a D-Bus property read gets no answer, twice), saves thread states and
   journals to `~/gnome-shell-hangs/<time>/`, offers a core dump with `sudo gcore` (your sudo password; `Ctrl+C` skips it; the screen
   stays frozen 10–60 s meanwhile), restarts the shell with **SIGINT** instead of SIGKILL, and hides the "Oh no" screen if it still comes up.
   - `unfreeze-shell --check` only reports. Don't run it on a healthy shell without `--check` or `--dry-run`: it restarts the shell.
   - **Untested on the real shell.** I checked its premises on 2026-10-30: the unit has `Restart=always` and `SuccessExitStatus=1`,
     and the running shell neither catches nor ignores SIGINT or SIGHUP. Its tests were on dummy units.
   - **Brave may still crash.** Losing the window manager is the likely cause and SIGINT doesn't avoid that.
4. Optional read-only look first: `ssh drn2@<ip> 'bash -s' < gnome-shell-hang-triage.sh` (prints a HUNG/OK verdict).
5. *(Untested idea)* Quit Brave cleanly first (SIGTERM to the main browser process) so its session saves with a normal exit.
6. Last resort if `unfreeze-shell` fails: take a backtrace, then `kill -KILL <gnome-shell pid>` (expect the Oh-no screen; hide it as above).
   The backtrace needs your sudo password (ptrace is restricted: `ptrace_scope=1`):
   ```bash
   ssh -t drn2@<ip> "sudo gdb -p <gnome-shell pid> -batch -iex 'set debuginfod enabled off' \
     -ex 'thread apply all bt 25' 2>&1 | tee ~/gnome-shell-hang-bt.txt | tail -40"
   ```
7. Relaunch Brave → Restore.

## Prevention ideas

- **Wallpaper daemon off (done 19:26 by the Legion-side Claude; per-workspace wallpapers are currently off).** This is also the test: if the
  shell freezes again with it off, the lock-order theory is wrong. To get the wallpapers back with less risk: `DEBOUNCE=2` in the daemon
  (fewer writes, same risk per write), or do it inside the shell with an extension that swaps images without writing settings (not started).
- **Get a backtrace next time** (`unfreeze-shell` offers a core dump). If it matches the theory, report it upstream to GJS. The Legion-side
  note found no matching bug report in one web search and says GJS master still has the same busy-wait lock; I haven't checked either.
- **Package updates:** per the Legion-side note, the pending `libglib2.0-0t64` and `gnome-shell` updates fix different hangs, and
  `libgjs0g`, `mutter` and `dconf` have none available. I haven't verified that.
- **Compute load (low confidence).** The CPUs were mostly idle on average during the hang, so load isn't shown to matter. If you still want to
  protect the desktop: `nice -n 10` or `systemd-run --user --scope -p CPUWeight=50 ...` for heavy jobs.
- **Keep long jobs independent of the GUI.** The python/mpv/claude processes survived because they aren't tied to the shell.
  GUI apps (Brave) are the exposed ones.
- **Reserve this machine's address** in the router so it is easy to find while the screen is frozen (the `.local` name also works).

## Unrelated things noticed (not tied to this freeze)

- Python OOM kills (dates above), launched from GNOME Terminal.
- USB disconnects on Oct 29 at 20:48 (`1-9.1`), 22:06 (`1-9.1`), 22:29 (`1-12`), and hundreds of EIO warnings reading one directory block (`inode 209649735`) on `sda1`, seen via `mpv` and `ls`. Worth a SMART check and a look at power/cable/hub for the USB drives.
- Six monitor re-probe bursts today for the Samsung ultrawide (HDMI-0), plus an "Unable to read EDID" at boot.
- `gsd-media-keys` logged failures grabbing shortcuts right after the shell restart (17:25:31); none since.
