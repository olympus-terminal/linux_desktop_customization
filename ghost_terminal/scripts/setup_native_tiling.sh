#!/bin/bash
# Setup native GNOME tiling shortcuts

echo "Setting up native GNOME window tiling shortcuts..."

# Enable edge tiling
gsettings set org.gnome.mutter edge-tiling true

# Set up tiling keyboard shortcuts
echo "Setting keyboard shortcuts:"

# Half-screen tiling
echo "  • Super+Left  = Tile window to left half"
echo "  • Super+Right = Tile window to right half"

# These are usually already set by default, but let's ensure they're enabled
gsettings set org.gnome.desktop.wm.keybindings maximize "['<Super>Up']"
gsettings set org.gnome.desktop.wm.keybindings unmaximize "['<Super>Down', '<Alt>F5']"

# For quarter tiling, we'll use a different approach
echo ""
echo "For quarter-screen tiling, you can:"
echo "1. Install the 'gTile' GNOME extension from: https://extensions.gnome.org/extension/28/gtile/"
echo "   - Open Firefox/Chrome and go to the URL above"
echo "   - Click 'Install' to add the extension"
echo "   - It provides Super+Enter for a tiling grid"
echo ""
echo "2. Or install 'Tiling Assistant' extension for more options:"
echo "   sudo apt install gnome-shell-extension-manager"
echo "   Then search for 'Tiling Assistant' in the Extension Manager"
echo ""
echo "Current tiling shortcuts active:"
echo "  • Super+Left   = Left half"
echo "  • Super+Right  = Right half"  
echo "  • Super+Up     = Maximize"
echo "  • Super+Down   = Restore"