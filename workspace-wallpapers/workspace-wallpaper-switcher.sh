#!/bin/bash

# Workspace Wallpaper Switcher for GNOME
# This script monitors workspace changes and updates wallpaper accordingly

# Define wallpaper paths for each workspace
# Modify these paths to your desired wallpapers
declare -A WALLPAPERS
WALLPAPERS[0]="/usr/share/backgrounds/warty-final-ubuntu.png"
WALLPAPERS[1]="/usr/share/backgrounds/Jammy-Jellyfish_WP_1920x1080.png"
WALLPAPERS[2]="/usr/share/backgrounds/ubuntu-wallpaper-d.png"
WALLPAPERS[3]="/usr/share/backgrounds/Focal-Fossa_WP_1920x1080.png"

# Function to get current workspace
get_current_workspace() {
    gdbus call --session \
        --dest org.gnome.Shell \
        --object-path /org/gnome/Shell \
        --method org.gnome.Shell.Eval "global.workspace_manager.get_active_workspace_index()" | \
        cut -d "'" -f 2
}

# Function to set wallpaper
set_wallpaper() {
    local wallpaper="$1"
    if [ -f "$wallpaper" ]; then
        gsettings set org.gnome.desktop.background picture-uri "file://$wallpaper"
        gsettings set org.gnome.desktop.background picture-uri-dark "file://$wallpaper"
        echo "Wallpaper set to: $wallpaper"
    else
        echo "Wallpaper not found: $wallpaper"
    fi
}

# Main monitoring loop
echo "Workspace Wallpaper Switcher started..."
echo "Press Ctrl+C to stop"

LAST_WORKSPACE=-1

while true; do
    CURRENT_WORKSPACE=$(get_current_workspace)
    
    if [ "$CURRENT_WORKSPACE" != "$LAST_WORKSPACE" ]; then
        echo "Switched to workspace $CURRENT_WORKSPACE"
        
        if [ -n "${WALLPAPERS[$CURRENT_WORKSPACE]}" ]; then
            set_wallpaper "${WALLPAPERS[$CURRENT_WORKSPACE]}"
        else
            echo "No wallpaper defined for workspace $CURRENT_WORKSPACE"
        fi
        
        LAST_WORKSPACE=$CURRENT_WORKSPACE
    fi
    
    sleep 0.5
done