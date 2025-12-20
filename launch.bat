@echo off
REM Launch script for Omnipet Virtual Pet Game on Windows
REM Edit config.json to change fullscreen, screen size, and other settings

echo Starting Omnipet Virtual Pet Game...
echo Note: You can edit config.json to change display settings

REM Set environment variables for better compatibility
set SDL_VIDEO_CENTERED=1

REM Check if fullscreen was requested
if "%1"=="--fullscreen" set OMNIPET_FULLSCREEN=1
if "%1"=="-f" set OMNIPET_FULLSCREEN=1

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found
    echo Please install Python 3 from https://python.org
    pause
    exit /b 1
)

REM Check for pygame
python -c "import pygame" >nul 2>&1
if errorlevel 1 (
    echo Error: pygame not installed
    echo Install with: pip install pygame
    pause
    exit /b 1
)

REM Run the game
python main.py %*

REM Keep window open if there was an error
if errorlevel 1 pause
