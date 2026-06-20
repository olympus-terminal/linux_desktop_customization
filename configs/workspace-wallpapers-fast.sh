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

# Fast wallpaper setter — gsettings so GNOME Shell picks up the change
set_wallpaper_fast() {
    local wallpaper="$1"
    gsettings set org.gnome.desktop.background picture-uri "$wallpaper"
    gsettings set org.gnome.desktop.background picture-uri-dark "$wallpaper"

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

# Monitor workspace changes using optimized polling
monitor_workspace_changes() {
    echo "🚀 Fast Workspace Wallpaper Daemon Started"
    echo "⚡ Using optimized polling for reliable switching"
    echo "   Press Ctrl+C to stop"
    echo ""

    LAST_WORKSPACE=$(get_workspace_fast)

    # Set initial wallpaper
    if [ -n "${WALLPAPERS[$LAST_WORKSPACE]}" ]; then
        set_wallpaper_fast "${WALLPAPERS[$LAST_WORKSPACE]}"
    fi

    while true; do
        CURRENT_WORKSPACE=$(get_workspace_fast)

        if [ "$CURRENT_WORKSPACE" != "$LAST_WORKSPACE" ]; then
            echo "→ Switched to Workspace $((CURRENT_WORKSPACE + 1))"

            if [ -n "${WALLPAPERS[$CURRENT_WORKSPACE]}" ]; then
                set_wallpaper_fast "${WALLPAPERS[$CURRENT_WORKSPACE]}"
            else
                echo "ℹ No wallpaper configured for Workspace $((CURRENT_WORKSPACE + 1))"
            fi

            LAST_WORKSPACE=$CURRENT_WORKSPACE
        else
            # Even if we haven't switched, verify the correct wallpaper is set
            # This prevents GNOME from reverting wallpapers
            if [ -n "${WALLPAPERS[$CURRENT_WORKSPACE]}" ]; then
                ACTUAL_WALLPAPER=$(gsettings get org.gnome.desktop.background picture-uri | tr -d "'")
                EXPECTED_WALLPAPER="${WALLPAPERS[$CURRENT_WORKSPACE]}"

                if [ "$ACTUAL_WALLPAPER" != "$EXPECTED_WALLPAPER" ]; then
                    echo "⚠ Correcting wallpaper for Workspace $((CURRENT_WORKSPACE + 1))"
                    set_wallpaper_fast "${WALLPAPERS[$CURRENT_WORKSPACE]}"
                fi
            fi
        fi

        sleep 0.1  # 100ms polling for responsive switching
    done
}

# Alternative: Ultra-fast polling version (if D-Bus doesn't work well)
monitor_fast_polling() {
    echo "🚀 Fast Workspace Wallpaper Daemon Started"
    echo "⚡ Using optimized polling (50ms intervals)"
    echo "   Press Ctrl+C to stop"
    echo ""
    
    LAST_WORKSPACE=$(get_workspace_fast)
    
    # Set initial wallpaper
    if [ -n "${WALLPAPERS[$LAST_WORKSPACE]}" ]; then
        set_wallpaper_fast "${WALLPAPERS[$LAST_WORKSPACE]}"
    fi
    
    while true; do
        CURRENT_WORKSPACE=$(get_workspace_fast)

        if [ "$CURRENT_WORKSPACE" != "$LAST_WORKSPACE" ]; then
            echo "→ Switched to Workspace $((CURRENT_WORKSPACE + 1))"

            if [ -n "${WALLPAPERS[$CURRENT_WORKSPACE]}" ]; then
                set_wallpaper_fast "${WALLPAPERS[$CURRENT_WORKSPACE]}" &
            fi

            LAST_WORKSPACE=$CURRENT_WORKSPACE
        else
            # Even if we haven't switched, verify the correct wallpaper is set
            # This prevents GNOME from reverting wallpapers
            if [ -n "${WALLPAPERS[$CURRENT_WORKSPACE]}" ]; then
                ACTUAL_WALLPAPER=$(gsettings get org.gnome.desktop.background picture-uri | tr -d "'")
                EXPECTED_WALLPAPER="${WALLPAPERS[$CURRENT_WORKSPACE]}"

                if [ "$ACTUAL_WALLPAPER" != "$EXPECTED_WALLPAPER" ]; then
                    echo "⚠ Correcting wallpaper for Workspace $((CURRENT_WORKSPACE + 1))"
                    set_wallpaper_fast "${WALLPAPERS[$CURRENT_WORKSPACE]}" &
                fi
            fi
        fi

        sleep 0.05  # 50ms polling for near-instant response
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
            echo "  --daemon      (-d)  Use D-Bus signals (instant response)"
            echo "  --fast-poll   (-f)  Use fast polling (50ms intervals)"
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
    IMAGE_DIR="$DEFAULT_BASE_DIR/MJ7-Topaz/light-processed-dark20"
fi

# Populate wallpapers from the specified directory
populate_wallpapers "$IMAGE_DIR"

# Main execution
case "$MODE" in
    daemon)
        monitor_workspace_changes
        ;;
    fast-poll)
        monitor_fast_polling
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