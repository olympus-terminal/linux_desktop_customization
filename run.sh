#!/bin/bash
# Launcher script for Voice Dictation
# Supports both local (faster-whisper) and API (Voxtral) transcription
#
# Usage:
#   ./run.sh --local           # Use local faster-whisper (no API needed)
#   ./run.sh --local -m small  # Use small model for better accuracy
#   ./run.sh                   # Use Voxtral API (requires MISTRAL_API_KEY)
#   ./run.sh --mock            # TEST ONLY: placeholder text, no transcription
#   ./run.sh --test-mic        # Test microphone
#   ./run.sh --help            # Show all options

set -euo pipefail
cd "$(dirname "$0")"

exec python3 dictate.py "$@"
