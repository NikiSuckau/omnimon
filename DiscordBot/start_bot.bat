@echo off

cd /d "%~dp0"

REM This sets the token temporarily for the current session

set DISCORD_BOT_TOKEN=YOUR_BOT_TOKEN_HERE

echo Discord Bot Token set for this session
echo Starting bot...
echo.

python discord_relay_bot.py

pause
