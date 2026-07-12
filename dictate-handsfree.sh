#!/bin/bash
# Hands-free voice dictation
# Automatically detects speech - no keyboard needed
#
# Usage:
#   ./dictate-handsfree.sh                    # Use base model with default mic
#   ./dictate-handsfree.sh -m small           # Use small model (more accurate)
#   ./dictate-handsfree.sh -d "Blue Yeti"     # Specify microphone by name
#   ./dictate-handsfree.sh -c                 # Output to clipboard only
#   ./dictate-handsfree.sh --list-devices     # Show available microphones
#   ./dictate-handsfree.sh --test-vad         # Test voice detection only

set -euo pipefail
cd "$(dirname "$0")"

device_args=()
if [[ -n "${SOTTO_AUDIO_DEVICE:-}" ]]; then
    device_args=(--device "$SOTTO_AUDIO_DEVICE")
fi

exec python3 hands_free.py "${device_args[@]}" "$@"
