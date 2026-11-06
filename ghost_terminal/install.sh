#!/usr/bin/env bash
# ============================================================
#  GHOST TERMINAL INSTALLER
#  Transparent black terminals + sci-fi wallpapers + tiling
#  Targets: Ubuntu GNOME (Wayland or X11), ultrawide displays
# ============================================================
set -euo pipefail

PACK_DIR="$(cd "$(dirname "$0")" && pwd)"
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RESET='\033[0m'

banner() {
    echo -e "${GREEN}"
    echo "  ╔══════════════════════════════════════╗"
    echo "  ║       G H O S T   T E R M I N A L    ║"
    echo "  ║   transparent terminals + sci-fi wp   ║"
    echo "  ╚══════════════════════════════════════╝"
    echo -e "${RESET}"
}

step() { echo -e "\n${CYAN}[*] $1${RESET}"; }

banner

# -----------------------------------------------------------
# 1. Install GNOME Terminal transparent-black profile
# -----------------------------------------------------------
step "Installing GNOME Terminal profile (black bg, 42% transparency, green text)..."
if command -v dconf &>/dev/null; then
    dconf load /org/gnome/terminal/legacy/profiles:/ < "$PACK_DIR/profiles/gnome-terminal.dconf"
    echo "    Done. Open a new GNOME Terminal tab to see the profile."
else
    echo "    SKIP: dconf not found. Install gnome-terminal for this feature."
fi

# -----------------------------------------------------------
# 2. Set dark GTK theme
# -----------------------------------------------------------
step "Setting GNOME to prefer-dark color scheme..."
gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark' 2>/dev/null || true
gsettings set org.gnome.desktop.interface gtk-theme 'Yaru-dark' 2>/dev/null || true
echo "    Dark theme enabled."

# -----------------------------------------------------------
# 3. Copy wallpapers into user backgrounds
# -----------------------------------------------------------
step "Copying wallpapers to ~/.local/share/backgrounds/ghost-terminal/..."
DEST="$HOME/.local/share/backgrounds/ghost-terminal"
mkdir -p "$DEST"
cp -ru "$PACK_DIR"/wallpapers/ultrawide/* "$DEST/" 2>/dev/null || true
cp -ru "$PACK_DIR"/wallpapers/cyberpunk-cities/* "$DEST/" 2>/dev/null || true
cp -ru "$PACK_DIR"/wallpapers/dark-scraped/* "$DEST/" 2>/dev/null || true
cp -ru "$PACK_DIR"/wallpapers/dark-variants/* "$DEST/" 2>/dev/null || true
COUNT=$(find "$DEST" -type f | wc -l)
echo "    $COUNT wallpapers installed."

# -----------------------------------------------------------
# 4. Set the first dark wallpaper as default
# -----------------------------------------------------------
step "Setting a default dark wallpaper..."
FIRST_WP=$(find "$DEST" -type f \( -name '*.jpg' -o -name '*.png' \) | sort | head -1)
if [ -n "$FIRST_WP" ]; then
    gsettings set org.gnome.desktop.background picture-uri "file://$FIRST_WP"
    gsettings set org.gnome.desktop.background picture-uri-dark "file://$FIRST_WP"
    gsettings set org.gnome.desktop.background picture-options 'spanned'
    echo "    Set: $(basename "$FIRST_WP")"
fi

# -----------------------------------------------------------
# 5. Install workspace wallpaper daemon
# -----------------------------------------------------------
step "Installing workspace wallpaper switcher daemon..."
chmod +x "$PACK_DIR"/daemon/*.sh 2>/dev/null || true

AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"
if [ -f "$PACK_DIR/autostart/workspace-wallpapers.desktop" ]; then
    # Update the Exec path to point at the pack's daemon
    sed "s|Exec=.*|Exec=$PACK_DIR/daemon/workspace-wallpapers-fast.sh|" \
        "$PACK_DIR/autostart/workspace-wallpapers.desktop" \
        > "$AUTOSTART_DIR/workspace-wallpapers.desktop"
    echo "    Daemon will auto-start on login."
else
    echo "    SKIP: No autostart .desktop file found."
fi

# -----------------------------------------------------------
# 6. Install window-tiling shortcuts
# -----------------------------------------------------------
step "Setting up window tiling shortcuts..."
chmod +x "$PACK_DIR"/scripts/*.sh 2>/dev/null || true
chmod +x "$PACK_DIR"/scripts/*.py 2>/dev/null || true

# Native GNOME tiling keys
gsettings set org.gnome.mutter.keybindings toggle-tiled-left "['<Super>Left']" 2>/dev/null || true
gsettings set org.gnome.mutter.keybindings toggle-tiled-right "['<Super>Right']" 2>/dev/null || true
echo "    Super+Left/Right tiling enabled."

# -----------------------------------------------------------
# 7. Enable 11 dynamic workspaces (hacker multi-desk)
# -----------------------------------------------------------
step "Configuring workspaces..."
gsettings set org.gnome.desktop.wm.preferences num-workspaces 11 2>/dev/null || true
gsettings set org.gnome.mutter dynamic-workspaces false 2>/dev/null || true
echo "    11 static workspaces configured."

# -----------------------------------------------------------
# Done
# -----------------------------------------------------------
echo ""
echo -e "${GREEN}============================================${RESET}"
echo -e "${GREEN}  Ghost Terminal installed successfully.${RESET}"
echo -e "${GREEN}============================================${RESET}"
echo ""
echo "  Next steps:"
echo "    1. Open a new GNOME Terminal to see transparent black + green text"
echo "    2. Log out and back in to activate the wallpaper daemon"
echo "    3. Use Super+Left / Super+Right to tile windows"
echo "    4. Browse wallpapers in: $DEST"
echo ""
echo "  Tools included in $PACK_DIR/tools/:"
echo "    - wallpaper_scraper.py   : Download more dark wallpapers"
echo "    - darken_wallpapers.py   : Darken bright wallpapers"
echo "    - analyze_wallpapers.py  : Score wallpapers by darkness"
echo "    - targeted_scraper.py    : Scrape cyberpunk/sci-fi walls"
echo ""
