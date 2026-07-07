#\!/bin/bash

echo "Debug workspace detection - switch workspaces to test"
echo "Press Ctrl+C to stop"
echo ""

LAST_WORKSPACE=""

while true; do
    CURRENT=$(wmctrl -d | grep '*' | cut -d' ' -f1)

    if [ "$CURRENT" \!= "$LAST_WORKSPACE" ]; then
        echo "$(date '+%H:%M:%S') - Workspace changed to $((CURRENT + 1)) (index: $CURRENT)"
        LAST_WORKSPACE=$CURRENT
    fi

    sleep 0.1
done
