#!/usr/bin/env bash
set -euo pipefail

# Install dark-glass custom icons from source PNGs.
# Expects 1024x1024 source PNGs in icons/src/.
# Resizes to all standard hicolor sizes and places them in ~/.local/share/icons/hicolor/.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_DIR="$SCRIPT_DIR/src"
ICON_BASE="$HOME/.local/share/icons/hicolor"
SIZES=(16 22 24 32 48 64 128 256 512)

if ! command -v convert &>/dev/null; then
    echo "Error: ImageMagick (convert) is required. Install with: sudo apt install imagemagick"
    exit 1
fi

install_icon() {
    local src="$1"
    local name="$2"
    local category="$3"  # apps, places, devices, status

    if [[ ! -f "$src" ]]; then
        echo "  SKIP $name — source not found: $src"
        return
    fi

    echo "  Installing $name ($category)..."
    for size in "${SIZES[@]}"; do
        local dir="$ICON_BASE/${size}x${size}/$category"
        mkdir -p "$dir"
        convert "$src" -resize "${size}x${size}" "$dir/${name}.png"
    done
}

echo "=== Installing Dark-Glass Icons ==="
echo "Source: $SRC_DIR"
echo ""

# App icons (override via .desktop files)
install_icon "$SRC_DIR/terminal-glass.png"   "terminal-glass"   "apps"
install_icon "$SRC_DIR/nemo-glass.png"       "nemo-glass"       "apps"
install_icon "$SRC_DIR/settings-glass.png"   "settings-glass"   "apps"
install_icon "$SRC_DIR/rhythmbox-glass.png"  "rhythmbox-glass"  "apps"

# Theme icons (override by matching standard icon names)
install_icon "$SRC_DIR/drive-removable-media.png"  "drive-removable-media"      "devices"
install_icon "$SRC_DIR/drive-removable-media.png"  "drive-removable-media-usb"  "devices"
install_icon "$SRC_DIR/user-trash.png"             "user-trash"                 "places"
install_icon "$SRC_DIR/user-trash-full.png"        "user-trash-full"            "status"

# Update icon cache
echo ""
echo "Updating icon cache..."
gtk-update-icon-cache -f -t "$ICON_BASE" 2>/dev/null || true

# Install .desktop overrides
echo "Installing .desktop overrides..."
APPS_DIR="$HOME/.local/share/applications"
CONFIGS_DIR="$SCRIPT_DIR/../configs"
mkdir -p "$APPS_DIR"

for desktop_file in \
    org.gnome.Terminal.desktop \
    nemo.desktop \
    org.gnome.Settings.desktop \
    org.gnome.Rhythmbox3.desktop; do
    if [[ -f "$CONFIGS_DIR/$desktop_file" ]]; then
        cp "$CONFIGS_DIR/$desktop_file" "$APPS_DIR/"
        echo "  $desktop_file"
    fi
done

echo ""
echo "=== Done ==="
echo "Log out and back in (or run: gtk-update-icon-cache -f -t $ICON_BASE)"
