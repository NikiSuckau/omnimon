# Discord Online Battles - Setup Guide

## Overview
This prototype enables online battles between R36S devices using a Discord bot as a relay server.

## Architecture
```
R36S #1 ──┐
          ├──> Discord Bot (Relay Server) <──┐
R36S #2 ──┘                                   ├── R36S #3
                                              └── R36S #4
```

---

## Part 1: Discord Bot Setup (One-time, runs on PC)

### 1. Create Discord Bot

1. Go to https://discord.com/developers/applications
2. Click **"New Application"** → Name it "Omnimon Battle Relay"
3. Go to **"Bot"** tab → Click **"Add Bot"**
4. Under **"Token"**, click **"Reset Token"** → Copy the token
5. Enable these **Privileged Gateway Intents**:
   - ✅ Message Content Intent
   - ✅ Server Members Intent

### 2. Invite Bot to Your Server

1. Go to **"OAuth2"** → **"URL Generator"**
2. Select scopes:
   - [x] `bot`
3. Select bot permissions:
   - [x] Send Messages
   - [x] Read Message History
   - [x] Read Messages/View Channels
4. Copy the generated URL
5. Open URL in browser → Select your server → Authorize

### 3. Get Channel ID

1. In Discord, enable Developer Mode:
   - Settings → Advanced → Developer Mode (ON)
2. Right-click the channel where bot will operate
3. Click **"Copy ID"**

### 4. Create Webhook

1. In Discord channel settings → **Integrations** → **Webhooks**
2. Click **"New Webhook"**
3. Copy **Webhook URL**

### 5. Run the Bot

**On your PC/server:**

```bash
# Install dependencies
pip install discord.py

# Set bot token as environment variable
export DISCORD_BOT_TOKEN='your_bot_token_here'

# Or edit discord_relay_bot.py and replace YOUR_BOT_TOKEN_HERE

# Run bot
python discord_relay_bot.py
```

Bot should print:
```
[Bot] Logged in as Omnimon Battle Relay
[Bot] Ready to relay battles!
```

---

## Part 2: R36S Configuration

### 1. Create Config File

Create `game/network/discord_config.json`:

```json
{
  "webhook_url": "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN",
  "bot_token": "YOUR_BOT_TOKEN",
  "channel_id": "YOUR_CHANNEL_ID",
  "enabled": false
}
```

**Replace with your actual values from Part 1**

### 2. Install Dependencies on R36S

```bash
# On R36S via SSH
pip3 install requests
```

---

## Part 3: Testing the Prototype

### Test 1: Bot Commands (Discord)

In your Discord channel, type:

```
!help
```

Bot should respond with command list.

```
!host 123456
```

Bot creates room 123456.

```
!join 123456
```

Bot confirms you joined.

### Test 2: Python Client Test

**On your PC** (to test before R36S):

```bash
cd "c:/Users/esera/Desktop/Omnimon R36S/game/network"

# Edit discord_client.py and set your config at the bottom
python discord_client.py
```

This will:
1. Generate random 6-digit code
2. Send `!host` command to bot
3. Send test battle data
4. Wait for opponent (timeout after 30s)

### Test 3: Full R36S Test (2 devices)

**Device 1 (Host):**
1. Launch game
2. Navigate to Connect menu
3. Select "Online Battle" (when implemented)
4. Choose "Host"
5. Note the 6-digit code displayed

**Device 2 (Guest):**
1. Launch game
2. Navigate to Connect menu  
3. Select "Online Battle"
4. Choose "Join"
5. Enter host's 6-digit code using EmulationStation keyboard
6. Battle begins!

---

## Discord Bot Commands Reference

| Command | Description | Example |
|---------|-------------|---------|
| `!host <code>` | Create a battle room | `!host 123456` |
| `!join <code>` | Join existing room | `!join 123456` |
| `!data <code> <json>` | Send battle data | `!data 123456 {"pets":[...]}` |
| `!getdata <code>` | Get opponent's data | `!getdata 123456` |
| `!status` | View active rooms | `!status` |
| `!close <code>` | Close your room | `!close 123456` |
| `!help` | Show help | `!help` |

---

## Troubleshooting

### Bot doesn't respond
- Check bot is online in Discord (green status)
- Verify bot has permissions in channel
- Check bot token is correct

### "Invalid JSON data" error
- Ensure battle_data dict is valid JSON
- Check for syntax errors in data

### Timeout waiting for opponent
- Ensure both players use same room code
- Check internet connection
- Verify both sent `!data` commands

### R36S can't connect
- Check `discord_config.json` values
- Ensure R36S has internet access
- Verify `requests` library is installed

---

## Next Steps

To integrate this into the R36S game:

1. ✅ Bot server running (discord_relay_bot.py)
2. ✅ Client library created (discord_client.py)
3. ⏳ Modify `scene_connect.py` to add "Online" mode
4. ⏳ Add room code input UI
5. ⏳ Integrate with existing battle system

---

## Security Notes

- **Bot token** = password for bot, keep secret
- **Webhook URL** = allows posting to channel, keep private
- Data is visible in Discord channel (use private channel)
- Rooms auto-expire after 30 minutes

---

## Cost

- **Free!** Discord bots are free for reasonable use
- No server hosting costs
- No database needed
- Works anywhere with internet

---

## Support

If you encounter issues:
1. Check Discord bot logs
2. Check R36S `log.txt`
3. Verify all tokens/IDs are correct
4. Test with `python discord_client.py` first
