#!/bin/bash
# Orin Reasoning Engine - Linux/macOS Launcher
# Activates virtual environment and starts the CLI

echo "Activating Orin virtual environment..."
source env/bin/activate

echo "Starting Orin Reasoning Engine..."
python src/main.py "$@"
