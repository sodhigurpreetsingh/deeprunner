#!/bin/bash
# Start the backend server for Sales AI
# Usage: ./start_backend.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "../.venv" ]; then
    source ../.venv/bin/activate
else
    echo "Error: No .venv found in backend/ or project root."
    echo "Create one with: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Install/update dependencies
pip install -r requirements.txt --quiet

# Start the server
echo "Starting Sales AI backend on http://0.0.0.0:8000"
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
