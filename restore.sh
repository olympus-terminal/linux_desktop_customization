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

# 1. GTK3 CSS (Nemo dark-glass + DING fix)
echo "[1/8] GTK3 CSS..."
run mkdir -p ~/.config/gtk-3.0
run cp "$CONFIGS/gtk-3.0-gtk.css" ~/.config/gtk-3.0/gtk.css

# 2. VS Code
echo "[2/8] VS Code settings..."
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
echo "[3/8] nemo-glass wrapper..."
run mkdir -p ~/.local/bin
run cp "$CONFIGS/nemo-glass" ~/.local/bin/nemo-glass
run chmod +x ~/.local/bin/nemo-glass

# 4. Workspace wallpaper daemon
echo "[4/8] Workspace wallpaper daemon..."
run mkdir -p ~/Documents/desktops
run cp "$CONFIGS/workspace-wallpapers-fast.sh" ~/Documents/desktops/workspace-wallpapers-fast.sh
run chmod +x ~/Documents/desktops/workspace-wallpapers-fast.sh

# 5. Autostart entry
echo "[5/8] Autostart entry..."
run mkdir -p ~/.config/autostart
run cp "$CONFIGS/workspace-wallpapers.desktop" ~/.config/autostart/workspace-wallpapers.desktop

# 6. Keybinding (Ctrl+Space -> gnome-terminal)
echo "[6/8] xbindkeys config..."
run cp "$CONFIGS/xbindkeysrc" ~/.xbindkeysrc

# 7. dconf settings
echo "[7/8] dconf settings..."
if ! $DRY_RUN; then
    dconf load /org/gnome/terminal/ < "$CONFIGS/gnome-terminal.dconf"
    dconf load /org/gnome/desktop/interface/ < "$CONFIGS/gnome-desktop-interface.dconf"
    dconf load /org/gnome/desktop/background/ < "$CONFIGS/gnome-desktop-background.dconf"
    dconf load /org/nemo/ < "$CONFIGS/nemo.dconf"
    dconf load /org/gnome/shell/extensions/ < "$CONFIGS/gnome-extensions.dconf"
    dconf load /org/gnome/desktop/wm/preferences/ < "$CONFIGS/gnome-wm.dconf"
else
    echo "[dry-run] dconf load (6 databases)"
fi

# 8. Wallpaper images
echo "[8/9] Wallpaper images..."
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
echo "[9/9] System dconf overrides (no-suspend)..."
if [[ -w /etc/dconf/db/local.d/ ]]; then
    run cp "$CONFIGS/00-no-suspend" /etc/dconf/db/local.d/00-no-suspend
    run dconf update
else
    echo "       Needs sudo. Run manually:"
    echo "       sudo cp $CONFIGS/00-no-suspend /etc/dconf/db/local.d/"
    echo "       sudo dconf update"
fi

echo ""
echo "=== Done ==="
echo ""
echo "Remaining manual steps:"
echo "  1. Install GNOME extensions: ding, tiling-assistant, ubuntu-appindicators, ubuntu-dock"
echo "  2. Log out and back in (or run: killall -HUP gnome-shell)"
echo "  3. Verify: switch workspaces to confirm wallpaper rotation"
