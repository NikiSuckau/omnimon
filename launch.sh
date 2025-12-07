#!/bin/bash
# Launch script for Omnipet Virtual Pet Game
# Works on Ubuntu, Batocera, other Linux distributions, and macOS
# Edit config.json to change fullscreen, screen size, and other settings

# Set environment variables for better compatibility
export SDL_VIDEO_CENTERED=1

# Detect the environment
if [ -f "/usr/bin/batocera-info" ]; then
    echo "Detected Batocera system"
    export Omnipet_FULLSCREEN=1
    export SDL_VIDEODRIVER=kmsdrm
elif [ -n "$WAYLAND_DISPLAY" ]; then
    echo "Detected Wayland environment"
    export SDL_VIDEODRIVER=wayland
elif [ -n "$DISPLAY" ]; then
    echo "Detected X11 environment"
    export SDL_VIDEODRIVER=x11
elif [ -d "/Library/Apple" ]; then
    echo "Detected macOS environment"
    export SDL_VIDEODRIVER=cocoa
else
    echo "No display server detected, trying framebuffer"
    export SDL_VIDEODRIVER=fbcon
fi

# Check if fullscreen was requested
if [ "$1" = "--fullscreen" ] || [ "$1" = "-f" ]; then
    export Omnipet_FULLSCREEN=1
fi

# Check for Python 3
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "Error: Python not found"
    exit 1
fi

# Check for required Python packages
$PYTHON_CMD -c "import pygame" 2>/dev/null || {
    echo "Error: pygame not installed"
    echo "Install with: pip install pygame"
    exit 1
}

# Change to the directory where the script is located
cd "$(dirname "$0")"

# Run the game
echo "Starting Omnipet Virtual Pet Game..."
echo "Note: You can edit config.json to change display settings"
$PYTHON_CMD main.py "$@"
