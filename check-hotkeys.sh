#!/usr/bin/env bash
set -uo pipefail

# Compare live GNOME shortcuts with configs/gnome-keybindings.dconf and detect
# the conda gsettings trap. Run after any system update or when a shortcut
# "disappears".
# Usage: ./check-hotkeys.sh [--fix]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SAVED="$SCRIPT_DIR/configs/gnome-keybindings.dconf"
FIX=false
[[ "${1:-}" == "--fix" ]] && FIX=true
problems=0

warn() { echo "  ✗ $*"; problems=$((problems + 1)); }
ok()   { echo "  ✓ $*"; }

echo "[1/3] gsettings backend"
# gsettings from a conda env lacks the dconf module unless GIO_EXTRA_MODULES
# points at the system modules; its writes then land in a keyfile GNOME ignores.
gs=$(command -v gsettings)
live=$(dconf read /org/gnome/mutter/dynamic-workspaces)
seen=$(gsettings get org.gnome.mutter dynamic-workspaces 2>/dev/null)
if [ "${live:-true}" = "$seen" ]; then
    ok "$gs reads the real settings database"
else
    warn "$gs does not see real settings (dconf=$live, gsettings=$seen)"
    echo "    Fix: export GIO_EXTRA_MODULES=/usr/lib/x86_64-linux-gnu/gio/modules (see README)"
fi
if [ -f ~/.config/glib-2.0/settings/keyfile ]; then
    warn "~/.config/glib-2.0/settings/keyfile exists: settings were written to the wrong store"
    echo "    Review it, apply what you want with dconf write, then move it aside"
fi

echo "[2/3] Shortcuts vs $SAVED"
drift=$(sed "s#@HOME@#$HOME#g" "$SAVED" | python3 -c '
import configparser, subprocess, sys
c = configparser.RawConfigParser(interpolation=None); c.optionxform = str
c.read_string(sys.stdin.read())
norm = lambda v: v.replace("@as ", "").replace("uint32 ", "")
for s in c.sections():
    for k, v in c.items(s):
        real = subprocess.run(["dconf", "read", f"/{s}/{k}"], capture_output=True, text=True).stdout.strip() or "(default)"
        if norm(real) != norm(v):
            print(f"{s}/{k}: saved {v}, live {real}")
') || { warn "could not compare shortcuts (python3 error above)"; drift="error"; }
if [ "$drift" = "error" ]; then
    :
elif [ -z "$drift" ]; then
    ok "all saved shortcuts are live"
else
    while IFS= read -r line; do warn "$line"; done <<< "$drift"
    if $FIX; then
        sed "s#@HOME@#$HOME#g" "$SAVED" | dconf load /
        echo "    Reloaded saved shortcuts"
    else
        echo "    Run with --fix to reload the saved shortcuts"
    fi
fi

echo "[3/3] Helpers"
tiler=$(dconf read /org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom-window-tiler/command | tr -d "'")
if [ -n "$tiler" ] && [ ! -x "$tiler" ]; then
    warn "Super+T command missing: $tiler"
else
    ok "Super+T tiler installed"
fi
if pgrep -x xbindkeys >/dev/null && grep -qsiE 'control *\+ *space' ~/.xbindkeysrc; then
    warn "xbindkeys also grabs Ctrl+Space; it will fight the GNOME shortcut"
fi

echo
if [ "$problems" -eq 0 ]; then echo "All good."; else echo "$problems problem(s) found."; fi
exit $(( problems > 0 ))
