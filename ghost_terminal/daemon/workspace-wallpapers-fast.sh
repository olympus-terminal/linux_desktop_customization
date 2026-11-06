#!/bin/bash

# Fast Workspace Wallpaper Manager using D-Bus signals
# Responds instantly to workspace changes without polling

################################################################################
# ⚠️  IMPORTANT - READ THIS BEFORE MAKING CHANGES ⚠️
################################################################################
# This script is DESIGNED to run as a background daemon/service.
# It runs CONTINUOUSLY in an infinite loop to monitor workspace changes.
#
# COMMON ISSUE: If wallpapers aren't switching, it's usually because:
# 1. Multiple instances are running (check with: pgrep -fa workspace-wallpapers)
# 2. The autostart file needs the script restarted after changes
# 3. The MODE variable isn't being set correctly from command-line args
#
# DO NOT "fix" the infinite loops - they are intentional!
# DO NOT make the script exit after one run - it must run continuously!
#
# To test: ./workspace-wallpapers-fast.sh --daemon
# To debug: Check if running with: pgrep -fa workspace-wallpapers-fast.sh
# To restart: pkill -f workspace-wallpapers-fast.sh && ./workspace-wallpapers-fast.sh --daemon &
################################################################################

# Configuration
declare -A WALLPAPERS

# Default base directory
DEFAULT_BASE_DIR="${HOME}/Documents/desktops"

# Function to populate wallpapers from a directory
populate_wallpapers() {
    local image_dir="$1"
    local index=0

    if [ ! -d "$image_dir" ]; then
        echo "Error: Directory '$image_dir' does not exist"
        exit 1
    fi

    # Find all image files and sort them for consistent ordering
    while IFS= read -r -d '' file; do
        if [ $index -le 10 ]; then  # Support up to 11 workspaces (0-10)
            WALLPAPERS[$index]="file://$file"
            ((index++))
        else
            break
        fi
    done < <(find "$image_dir" -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.bmp" -o -iname "*.tiff" \) -print0 | sort -z)

    if [ $index -eq 0 ]; then
        echo "Error: No image files found in '$image_dir'"
        exit 1
    fi

    echo "Found $index wallpaper(s) in '$image_dir'"
}

# Downscale wallpapers to the screen size once, cached. GNOME Shell decodes the
# wallpaper on its main thread, so a 6513x1832 PNG on every switch stalls it.
SCALED_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/workspace-wallpapers"

scale_wallpapers() {
    local screen
    screen=$(xprop -root _NET_DESKTOP_GEOMETRY 2>/dev/null | sed -n 's/.*= \([0-9]*\), \([0-9]*\)/\1x\2/p')
    [ -z "$screen" ] && return
    mkdir -p "$SCALED_DIR"

    local i src dst
    for i in "${!WALLPAPERS[@]}"; do
        src="${WALLPAPERS[$i]#file://}"
        dst="$SCALED_DIR/${screen}-$(basename "${src%.*}").jpg"
        if [ ! -f "$dst" ] || [ "$src" -nt "$dst" ]; then
            python3 - "$src" "$dst" "$screen" <<'PY' || continue
import sys
from PIL import Image
src, dst, screen = sys.argv[1:]
w, h = map(int, screen.split("x"))
im = Image.open(src).convert("RGB")
scale = max(w / im.width, h / im.height)
if scale < 1:
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
im.save(dst, quality=95, subsampling=0)
PY
        fi
        WALLPAPERS[$i]="file://$dst"
    done
    echo "Using wallpapers scaled to $screen in $SCALED_DIR"
}

# Set both keys in one dconf transaction so the shell reloads the background once
set_wallpaper_fast() {
    local wallpaper="$1"
    printf "[org/gnome/desktop/background]\npicture-uri='%s'\npicture-uri-dark='%s'\n" \
        "$wallpaper" "$wallpaper" | dconf load /

    local filename=$(basename "$wallpaper")
    filename="${filename%.jpg}"
    filename="${filename%.png}"
    echo "✓ Set wallpaper: $filename"
}

# Get current workspace more efficiently
get_workspace_fast() {
    # Use wmctrl for reliable workspace detection
    wmctrl -d 2>/dev/null | grep '\*' | cut -d' ' -f1
}

apply_workspace() {
    local ws="$1"
    [[ "$ws" =~ ^[0-9]+$ ]] || return
    if [ -n "${WALLPAPERS[$ws]}" ]; then
        set_wallpaper_fast "${WALLPAPERS[$ws]}"
    else
        echo "ℹ No wallpaper configured for Workspace $((ws + 1))"
    fi
}

# Event-driven monitor: xprop -spy prints a line each time _NET_CURRENT_DESKTOP
# changes, so there is no polling. Rapid switches are debounced: the wallpaper
# is set only once the workspace has been stable for DEBOUNCE seconds, and never
# from a background job, so writes cannot pile up in GNOME Shell.
DEBOUNCE=0.3

monitor_workspace_changes() {
    echo "🚀 Fast Workspace Wallpaper Daemon Started"
    echo "⚡ Using X11 property events (debounced ${DEBOUNCE}s)"
    echo "   Press Ctrl+C to stop"
    echo ""

    local line ws applied=""
    while true; do
        while read -r line; do
            ws="${line##*= }"
            # Drain further switches until things settle
            while read -r -t "$DEBOUNCE" line; do
                ws="${line##*= }"
            done
            [ "$ws" = "$applied" ] && continue
            echo "→ Switched to Workspace $((ws + 1))"
            apply_workspace "$ws"
            applied="$ws"
        done < <(xprop -root -spy _NET_CURRENT_DESKTOP 2>/dev/null)

        # xprop exits if the X connection drops (e.g. shell restart); retry
        sleep 2
        applied=""
    done
}

# Parse command line arguments
IMAGE_DIR=""
MODE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --daemon|-d)
            MODE="daemon"
            shift
            ;;
        --fast-poll|-f)
            MODE="fast-poll"
            shift
            ;;
        --test|-t)
            MODE="test"
            shift
            ;;
        --set-current|-s)
            MODE="set-current"
            shift
            ;;
        --image-dir|-i)
            IMAGE_DIR="$2"
            shift 2
            ;;
        --help|-h)
            echo "Fast Workspace Wallpaper Manager"
            echo ""
            echo "Usage:"
            echo "  $0 [OPTIONS] MODE"
            echo ""
            echo "Modes:"
            echo "  --daemon      (-d)  Event-driven via X11 property changes"
            echo "  --fast-poll   (-f)  Same as --daemon (polling was removed)"
            echo "  --test        (-t)  Test workspace detection"
            echo "  --set-current (-s)  Set wallpaper for current workspace"
            echo ""
            echo "Options:"
            echo "  --image-dir   (-i)  Specify custom directory containing wallpaper images"
            echo "  --help        (-h)  Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --daemon --image-dir ~/Pictures/Wallpapers"
            echo "  $0 --test -i /path/to/wallpapers"
            echo ""
            echo "The --daemon mode is recommended for best performance."
            echo "Images are automatically assigned to workspaces in alphabetical order."
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information."
            exit 1
            ;;
    esac
done

# Set default image directory if not specified
if [ -z "$IMAGE_DIR" ]; then
    IMAGE_DIR="$DEFAULT_BASE_DIR/MJ7-Topaz/light-processed"
fi

# Populate wallpapers from the specified directory
populate_wallpapers "$IMAGE_DIR"
case "$MODE" in daemon|fast-poll|set-current) scale_wallpapers ;; esac

# Main execution
case "$MODE" in
    daemon)
        monitor_workspace_changes
        ;;
    fast-poll)
        # Kept for existing autostart entries; polling was replaced by events
        monitor_workspace_changes
        ;;
    test)
        echo "Testing workspace detection..."
        CURRENT=$(get_workspace_fast)
        echo "Current workspace: $((CURRENT + 1))"
        echo "Using image directory: $IMAGE_DIR"
        echo ""

        if [ -n "${WALLPAPERS[$CURRENT]}" ]; then
            filename=$(basename "${WALLPAPERS[$CURRENT]}")
            echo "Current wallpaper: $filename"
        else
            echo "No custom wallpaper for this workspace"
        fi

        echo ""
        echo "📋 Available wallpapers:"
        for i in "${!WALLPAPERS[@]}"; do
            filename=$(basename "${WALLPAPERS[$i]}")
            echo "  Workspace $((i + 1)): $filename"
        done | sort -V
        ;;
    set-current)
        CURRENT=$(get_workspace_fast)
        if [ -n "${WALLPAPERS[$CURRENT]}" ]; then
            echo "Setting wallpaper for Workspace $((CURRENT + 1))..."
            set_wallpaper_fast "${WALLPAPERS[$CURRENT]}"
        else
            echo "No wallpaper configured for Workspace $((CURRENT + 1))"
        fi
        ;;
    *)
        echo "Fast Workspace Wallpaper Manager"
        echo ""
        echo "Usage:"
        echo "  $0 [OPTIONS] MODE"
        echo ""
        echo "Use --help for detailed usage information."
        ;;
esac