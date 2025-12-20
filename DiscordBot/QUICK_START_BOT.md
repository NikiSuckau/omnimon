# Quick Start Guide - Discord Bot

## Fastest Way to Start Bot (Windows)

### Option 1: Use Batch File (EASIEST)

Just double-click:
```
start_bot.bat
```

This will:
1. Set the token automatically
2. Start the bot
3. Keep window open

---

### Option 2: PowerShell One-Liner

```powershell
$env:DISCORD_BOT_TOKEN="YOUR_BOT_TOKEN_HERE"; python discord_relay_bot.py
```

---

### Option 3: Edit discord_relay_bot.py Directly (For Testing Only)

Open `discord_relay_bot.py` and replace line 263:

```python
# Change this line:
TOKEN = os.getenv('DISCORD_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# To this:
TOKEN = 'YOUR_BOT_TOKEN_HERE'
```

⚠️ **Warning**: Don't commit this file to Git!

---

## Verify Bot is Running

You should see:
```
[Bot] Starting Discord Relay Bot...
[Bot] Logged in as Omnimon Battle Relay
[Bot] Bot ID: 1446967235066466405
[Bot] Ready to relay battles!
```

---

## Test Bot in Discord

Type in your Discord channel:
```
!battlehelp
```

Bot should respond with command list.

---

## Next Steps

Once bot is running:
1. Run `python tests/test_1_discord_bot.py` (manual tests)
2. Run `python tests/test_2_discord_client.py` (automated tests)
3. Run `python tests/test_3_ui_components.py` (UI tests)
