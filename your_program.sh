#!/usr/bin/env bash
#
# This script is a wrapper for your program.
# It activates the virtual environment and runs app/main.py

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment if it exists
if [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
else
    echo "Error: Virtual environment not found. Run: python3 -m venv .venv && source .venv/bin/activate && pip install anthropic"
    exit 1
fi

# Run the main Python script with all arguments
python "$SCRIPT_DIR/app/main.py" "$@"
