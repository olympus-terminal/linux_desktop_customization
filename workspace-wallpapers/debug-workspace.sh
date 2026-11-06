#!/bin/bash

echo "Debug: Starting workspace monitor..."

# Test workspace detection
get_workspace() {
    wmctrl -d 2>/dev/null | grep '\*' | cut -d' ' -f1
}

LAST_WS=$(get_workspace)
echo "Starting from workspace: $LAST_WS"

# Monitor for 30 seconds
END=$(($(date +%s) + 30))
while [ $(date +%s) -lt $END ]; do
    CURRENT_WS=$(get_workspace)

    if [ "$CURRENT_WS" != "$LAST_WS" ]; then
        echo "[$(date +%T)] Workspace changed: $LAST_WS -> $CURRENT_WS"
        LAST_WS=$CURRENT_WS
    else
        # Show we're still monitoring
        printf "."
    fi

    sleep 0.05
done

echo ""
echo "Debug: Monitoring complete"