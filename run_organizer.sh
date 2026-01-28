#!/bin/bash
# Desktop Organizer - Unix/macOS Launcher
# Run this script to organize your desktop

echo "========================================"
echo "Desktop Organizer AI Agent"
echo "========================================"
echo

# Check if ANTHROPIC_API_KEY is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "ERROR: ANTHROPIC_API_KEY environment variable not set."
    echo
    echo "Set it with: export ANTHROPIC_API_KEY='your-key-here'"
    echo "Or add it to your ~/.bashrc or ~/.zshrc for persistence."
    echo
    exit 1
fi

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Please install Python 3.8+"
    exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to script directory
cd "$SCRIPT_DIR"

# Run the organizer
if [[ "$1" == "--dry-run" ]] || [[ "$1" == "-n" ]]; then
    echo "Running in DRY RUN mode - no changes will be made"
    echo
    python3 desktop_organizer.py --dry-run
else
    echo "Running for REAL - files will be organized"
    echo
    python3 desktop_organizer.py "$@"
fi

echo
echo "========================================"
