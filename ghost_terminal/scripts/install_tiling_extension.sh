#!/bin/bash
# Script to set up window tiling keybinding for GNOME on Wayland

echo "Setting up window tiling for GNOME on Wayland..."

# Create the keybinding script location
SCRIPT_PATH="$HOME/.local/bin/gnome-window-tiler"
mkdir -p "$HOME/.local/bin"

# Copy the Python script
cp "$HOME/Desktop/wayland_window_tiler.py" "$SCRIPT_PATH"
chmod +x "$SCRIPT_PATH"

# Add custom keybinding to GNOME
echo "Adding custom keyboard shortcut..."

# Get the current custom keybindings
CURRENT_BINDINGS=$(gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings)

# Add our new binding if not already present
if [[ ! "$CURRENT_BINDINGS" == *"'/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom-window-tiler/'"* ]]; then
    # Handle empty array with type annotation
    if [[ "$CURRENT_BINDINGS" == "@as []" ]] || [[ "$CURRENT_BINDINGS" == "[]" ]]; then
        gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings "['/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom-window-tiler/']"
    else
        # Reset the keybindings properly
        gsettings reset org.gnome.settings-daemon.plugins.media-keys custom-keybindings
        gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings "['/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom-window-tiler/']"
    fi
fi

# Configure the custom keybinding
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom-window-tiler/ name 'Window Tiler'
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom-window-tiler/ command "$SCRIPT_PATH"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom-window-tiler/ binding '<Super>t'

echo "✓ Window tiling script installed!"
echo "✓ Keyboard shortcut set to: Super+T"
echo ""
echo "Usage:"
echo "  Press Super+T to cycle through window positions:"
echo "  1. Full screen → 2. Left half → 3. Right half → 4. Quarter positions"
echo ""
echo "To change the keyboard shortcut, go to:"
echo "  Settings → Keyboard → View and Customize Shortcuts → Custom Shortcuts"