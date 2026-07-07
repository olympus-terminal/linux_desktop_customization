#!/bin/bash

echo "Testing workspace detection..."

# Method 1: wmctrl
echo "Method 1 (wmctrl):"
WORKSPACE=$(wmctrl -d 2>/dev/null | grep '\*' | cut -d' ' -f1)
echo "Current workspace: $WORKSPACE"

# Method 2: Using xprop
echo ""
echo "Method 2 (xprop):"
if command -v xprop &> /dev/null; then
    WORKSPACE2=$(xprop -root _NET_CURRENT_DESKTOP 2>/dev/null | cut -d' ' -f3)
    echo "Current workspace: $WORKSPACE2"
else
    echo "xprop not available"
fi

# Method 3: Using gdbus
echo ""
echo "Method 3 (gdbus):"
if command -v gdbus &> /dev/null; then
    WORKSPACE3=$(gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell --method org.gnome.Shell.Eval 'global.workspace_manager.get_active_workspace_index()' 2>/dev/null | sed 's/.*"\([0-9]*\)".*/\1/')
    echo "Current workspace: $WORKSPACE3"
else
    echo "gdbus not available"
fi

echo ""
echo "Now monitoring for 10 seconds. Switch workspaces to test detection..."
LAST_WS=$(wmctrl -d 2>/dev/null | grep '\*' | cut -d' ' -f1)
echo "Starting from workspace: $LAST_WS"

for i in {1..100}; do
    CURRENT_WS=$(wmctrl -d 2>/dev/null | grep '\*' | cut -d' ' -f1)
    if [ "$CURRENT_WS" != "$LAST_WS" ]; then
        echo "Workspace changed: $LAST_WS -> $CURRENT_WS"
        LAST_WS=$CURRENT_WS
    fi
    sleep 0.1
done

echo "Monitoring complete."