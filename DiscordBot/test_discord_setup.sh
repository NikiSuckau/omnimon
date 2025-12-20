#!/bin/bash
# Test script for Discord online battles
# Run this before testing on R36S to verify everything works

echo "=== Omnimon Discord Battle Test ==="
echo ""

# Check if bot is running
echo "Step 1: Testing Discord Bot..."
echo "Open Discord and type: !help"
echo "Press Enter when bot responds..."
read

# Check Python dependencies
echo ""
echo "Step 2: Checking Python dependencies..."
python3 -c "import requests; print('✅ requests installed')" 2>/dev/null || echo "❌ requests NOT installed. Run: pip3 install requests"
python3 -c "import json; print('✅ json (built-in)')"

# Test Discord client
echo ""
echo "Step 3: Testing Discord client..."
echo "Edit game/network/discord_client.py and set:"
echo "  - WEBHOOK_URL"
echo "  - BOT_TOKEN"
echo "  - CHANNEL_ID"
echo ""
echo "Then run: python3 game/network/discord_client.py"
echo ""
echo "Press Enter to continue..."
read

# Create config file
echo ""
echo "Step 4: Creating config file..."
if [ ! -f "game/network/discord_config.json" ]; then
    cp game/network/discord_config.json.template game/network/discord_config.json
    echo "✅ Created discord_config.json"
    echo "⚠️  Edit game/network/discord_config.json with your values"
else
    echo "✅ discord_config.json already exists"
fi

echo ""
echo "=== Next Steps ==="
echo "1. Configure discord_config.json with your Discord credentials"
echo "2. Run bot: python3 discord_relay_bot.py"
echo "3. Test in Discord: !host 123456"
echo "4. Integrate into game (scene_connect.py)"
echo ""
echo "Done!"
