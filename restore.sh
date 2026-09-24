#!/usr/bin/env bash
set -euo pipefail

# Restore dark-glass desktop environment from portable configs.
# Run from the linux_desktop_customization/ directory.
# Usage: ./restore.sh [--dry-run]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIGS="$SCRIPT_DIR/configs"
DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

run() {
    if $DRY_RUN; then
        echo "[dry-run] $*"
    else
        "$@"
    fi
}

echo "=== Dark-Glass Desktop Restore ==="
echo "Source: $CONFIGS"
echo ""

# 0a. System dependencies
echo "[0a/12] System dependencies..."
REQUIRED_PKGS=(gnome-terminal nemo wmctrl xdotool x11-utils)
MISSING_PKGS=()
for pkg in "${REQUIRED_PKGS[@]}"; do
    if ! dpkg -s "$pkg" &>/dev/null; then
        MISSING_PKGS+=("$pkg")
    fi
done
if [[ ${#MISSING_PKGS[@]} -gt 0 ]]; then
    echo "       Missing: ${MISSING_PKGS[*]}"
    echo "       Installing (requires sudo)..."
    run sudo apt-get install -y "${MISSING_PKGS[@]}"
else
    echo "       All dependencies installed"
fi

# 0b. GNOME Shell extensions
echo "[0b/12] GNOME Shell extensions..."
EXT_PKGS=(gnome-shell-extension-desktop-icons-ng gnome-shell-extension-appindicator gnome-shell-extension-ubuntu-dock)
MISSING_EXTS=()
for pkg in "${EXT_PKGS[@]}"; do
    if ! dpkg -s "$pkg" &>/dev/null; then
        MISSING_EXTS+=("$pkg")
    fi
done
if [[ ${#MISSING_EXTS[@]} -gt 0 ]]; then
    echo "       Missing: ${MISSING_EXTS[*]}"
    run sudo apt-get install -y "${MISSING_EXTS[@]}"
else
    echo "       All extensions installed"
fi
for ext in ding@rastersoft.com tiling-assistant@ubuntu.com ubuntu-appindicators@ubuntu.com ubuntu-dock@ubuntu.com; do
    run gnome-extensions enable "$ext" 2>/dev/null || true
done

# 0c. Coding fonts
echo "[0c/12] Coding fonts..."
FONT_PKGS=(fonts-jetbrains-mono fonts-firacode fonts-cascadia-code fonts-hack)
MISSING_FONTS=()
for pkg in "${FONT_PKGS[@]}"; do
    if ! dpkg -s "$pkg" &>/dev/null; then
        MISSING_FONTS+=("$pkg")
    fi
done
if [[ ${#MISSING_FONTS[@]} -gt 0 ]]; then
    echo "       Missing: ${MISSING_FONTS[*]}"
    run sudo apt-get install -y "${MISSING_FONTS[@]}"
else
    echo "       All coding fonts installed"
fi

# 1. GTK3 CSS (Nemo dark-glass + DING fix)
echo "[1/12] GTK3 CSS..."
run mkdir -p ~/.config/gtk-3.0
run cp "$CONFIGS/gtk-3.0-gtk.css" ~/.config/gtk-3.0/gtk.css

# 2. VS Code
echo "[2/12] VS Code settings..."
run mkdir -p ~/.config/Code/User
run cp "$CONFIGS/vscode-settings.json" ~/.config/Code/User/settings.json
if command -v code &>/dev/null; then
    echo "       Installing extensions..."
    while IFS= read -r ext; do
        run code --install-extension "$ext" --force 2>/dev/null || true
    done < "$CONFIGS/vscode-extensions.txt"
else
    echo "       VS Code not found — skipping extensions"
fi

# 3. Nemo-glass wrapper
echo "[3/12] nemo-glass wrapper..."
run mkdir -p ~/.local/bin
run cp "$CONFIGS/nemo-glass" ~/.local/bin/nemo-glass
run chmod +x ~/.local/bin/nemo-glass

# 4. Workspace wallpaper daemon
echo "[4/12] Workspace wallpaper daemon..."
run mkdir -p ~/Documents/desktops
run cp "$CONFIGS/workspace-wallpapers-fast.sh" ~/Documents/desktops/workspace-wallpapers-fast.sh
run chmod +x ~/Documents/desktops/workspace-wallpapers-fast.sh

# 5. Autostart entry
echo "[5/12] Autostart entry..."
run mkdir -p ~/.config/autostart
run cp "$CONFIGS/workspace-wallpapers.desktop" ~/.config/autostart/workspace-wallpapers.desktop

# 6. Shortcut plumbing: gsettings fix for conda, Super+T tiler script
#    (the shortcuts themselves are loaded with the dconf settings in step 7)
echo "[6/12] Shortcut prerequisites..."
# Conda's GLib has no dconf module; without this, any `gsettings set` run from a
# conda shell writes to ~/.config/glib-2.0/settings/keyfile and GNOME never sees it
GIO_LINE='export GIO_EXTRA_MODULES=/usr/lib/x86_64-linux-gnu/gio/modules'
for rc in ~/.bashrc ~/.profile; do
    if [ -f "$rc" ] && ! grep -qs 'GIO_EXTRA_MODULES' "$rc"; then
        if $DRY_RUN; then echo "[dry-run] append GIO_EXTRA_MODULES to $rc"; else printf '\n%s\n' "$GIO_LINE" >> "$rc"; fi
        echo "       Added GIO_EXTRA_MODULES to $rc"
    fi
done
# Ctrl+Space is a GNOME shortcut now; an old xbindkeys binding would fight it
if grep -qsiE 'control *\+ *space' ~/.xbindkeysrc; then
    run pkill -x xbindkeys || true
    run mv ~/.xbindkeysrc ~/.xbindkeysrc.bak
    echo "       Retired xbindkeys Ctrl+Space binding (~/.xbindkeysrc.bak)"
fi
run mkdir -p ~/.local/bin
run cp "$CONFIGS/gnome-window-tiler" ~/.local/bin/gnome-window-tiler
run chmod +x ~/.local/bin/gnome-window-tiler

# 7. dconf settings
echo "[7/12] dconf settings..."
if ! $DRY_RUN; then
    dconf load /org/gnome/terminal/ < "$CONFIGS/gnome-terminal.dconf"
    dconf load /org/gnome/desktop/interface/ < "$CONFIGS/gnome-desktop-interface.dconf"
    dconf load /org/gnome/desktop/background/ < "$CONFIGS/gnome-desktop-background.dconf"
    dconf load /org/nemo/ < "$CONFIGS/nemo.dconf"
    dconf load /org/gnome/shell/extensions/ < "$CONFIGS/gnome-extensions.dconf"
    dconf load /org/gnome/desktop/wm/preferences/ < "$CONFIGS/gnome-wm.dconf"
    # Workspace/window/screenshot shortcuts and fixed workspaces (needed for Ctrl+5..0)
    sed "s#@HOME@#$HOME#g" "$CONFIGS/gnome-keybindings.dconf" | dconf load /
else
    echo "[dry-run] dconf load (7 databases)"
fi

# 8. Wallpaper images
echo "[8/12] Wallpaper images..."
WALLPAPER_SRC="$SCRIPT_DIR/wallpapers"
WALLPAPER_DST="$HOME/Documents/desktops/MJ7-Topaz/light-processed-dark20"
if [[ -d "$WALLPAPER_SRC" ]]; then
    run mkdir -p "$WALLPAPER_DST"
    run cp "$WALLPAPER_SRC"/*.png "$WALLPAPER_DST/"
    echo "       Copied $(ls "$WALLPAPER_SRC"/*.png 2>/dev/null | wc -l) images"
else
    echo "       wallpapers/ directory not found — skipping"
fi

# 9. System-level overrides (requires sudo)
echo "[9/12] System dconf overrides (no-suspend)..."
if [[ -w /etc/dconf/db/local.d/ ]]; then
    run cp "$CONFIGS/00-no-suspend" /etc/dconf/db/local.d/00-no-suspend
    run dconf update
else
    echo "       Needs sudo. Run manually:"
    echo "       sudo cp $CONFIGS/00-no-suspend /etc/dconf/db/local.d/"
    echo "       sudo dconf update"
fi

# 10. Custom dark-glass icons
echo "[10/12] Dark-glass icons..."
ICON_SCRIPT="$SCRIPT_DIR/icons/install-icons.sh"
if [[ -x "$ICON_SCRIPT" ]]; then
    run "$ICON_SCRIPT"
else
    echo "       icons/install-icons.sh not found — skipping"
fi

# 11. Wallpaper processing tools
echo "[11/12] Wallpaper processing tools..."
TOOLS_SRC="$SCRIPT_DIR/wallpaper-tools"
TOOLS_DST="$HOME/Documents/desktops"
if [[ -d "$TOOLS_SRC" ]]; then
    run mkdir -p "$TOOLS_DST"
    for f in "$TOOLS_SRC"/*.py "$TOOLS_SRC"/*.sh; do
        [[ -f "$f" ]] || continue
        run cp "$f" "$TOOLS_DST/"
        run chmod +x "$TOOLS_DST/$(basename "$f")"
    done
    echo "       Copied wallpaper pipeline scripts to $TOOLS_DST"
else
    echo "       wallpaper-tools/ directory not found — skipping"
fi

# 12. Verify shortcuts
echo "[12/12] Checking shortcuts..."
if ! $DRY_RUN; then
    GIO_EXTRA_MODULES=/usr/lib/x86_64-linux-gnu/gio/modules "$SCRIPT_DIR/check-hotkeys.sh" || true
fi

echo ""
echo "=== Done ==="
echo ""
echo "Remaining manual steps:"
echo "  1. Log out and back in (or run: killall -HUP gnome-shell)"
echo "  2. Verify: switch workspaces to confirm wallpaper rotation"
echo "  3. If using VS Code: allow vibrancy CSS injection when prompted, then restart"
