"""
Omnimon Discord Relay Bot
Handles online battles between R36S devices via Discord relay.
"""

import discord
from discord.ext import commands
import json
import asyncio
from datetime import datetime, timedelta
import os
import re
import string
from aiohttp import web
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord_bot')

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Active battle rooms
rooms = {}

# Linked users database (code -> user_data)
# Format: {"code": {"user_id": str, "username": str, "tamer_name": str, "linked_at": str}}
linked_users = {}
USERS_DB_FILE = "linked_users.json"

def load_linked_users():
    """Load linked users from JSON file."""
    global linked_users
    try:
        if os.path.exists(USERS_DB_FILE):
            with open(USERS_DB_FILE, 'r') as f:
                linked_users = json.load(f)
            print(f"[Bot] Loaded {len(linked_users)} linked users")
        else:
            linked_users = {}
            print("[Bot] No existing user database, starting fresh")
    except Exception as e:
        print(f"[Bot] Error loading users: {e}")
        linked_users = {}

def save_linked_users():
    """Save linked users to JSON file."""
    try:
        with open(USERS_DB_FILE, 'w') as f:
            json.dump(linked_users, f, indent=2)
        print(f"[Bot] Saved {len(linked_users)} linked users")
    except Exception as e:
        print(f"[Bot] Error saving users: {e}")

# Cleanup old rooms
async def cleanup_old_rooms():
    while True:
        await asyncio.sleep(300)  # Every 5 minutes
        current_time = datetime.now()
        expired = [code for code, room in rooms.items() 
                   if current_time - room['created_at'] > timedelta(minutes=30)]
        for code in expired:
            del rooms[code]
            print(f"[Cleanup] Removed room {code}")

# Auto-update battle results
async def auto_update_battle_result(room_code: str, simulation_result: dict):
    try:
        print(f"[Auto-Result] Waiting 45s for animation in room {room_code}...")
        await asyncio.sleep(45)
        
        if room_code not in rooms:
            return
        
        room = rooms[room_code]
        winner_team = simulation_result.get('winner', 0)
        
        if winner_team == 1:
            winner_name = room.get('host_name', 'Host')
            result_emoji = "🏆"
            result_text = f"HOST WINS! ({winner_name})"
            color = 0x00FF00
        elif winner_team == 2:
            winner_name = room.get('guest_name', 'Guest')
            result_emoji = "🏆"
            result_text = f"GUEST WINS! ({winner_name})"
            color = 0x00FF00
        else:
            result_emoji = "🤝"
            result_text = "DRAW!"
            color = 0xFFFF00
        
        channel = bot.get_channel(room['channel_id'])
        if not channel:
            return
        
        # Find and update battle embed
        async for message in channel.history(limit=50):
            if message.embeds and f"Battle Data: {room_code}" in message.content:
                new_embed = discord.Embed(
                    title=f"{result_emoji} Battle Complete!",
                    description=f"**{result_text}**",
                    color=color
                )
                new_embed.set_footer(text=f"Room {room_code} • Omnimon R36S")
                await message.edit(embed=new_embed)
                await channel.send(f"{result_emoji} Battle finished! {result_text}")
                print(f"[Auto-Result] Updated room {room_code}")
                break
    except Exception as e:
        print(f"[Auto-Result] Error: {e}")

@bot.event
async def on_ready():
    print(f'[Bot] Logged in as {bot.user.name}')
    print(f'[Bot] Bot ID: {bot.user.id}')
    print('[Bot] Ready!')
    load_linked_users()
    bot.loop.create_task(cleanup_old_rooms())

@bot.event
async def on_message(message):
    """Process embeds with battle data AND monitor for auto-result updates."""
    # Debug: log ALL messages
    print(f"[DEBUG] Message received from: {message.author.name}, webhook: {message.webhook_id}, bot: {message.author.bot}")
    print(f"[DEBUG] Content: {message.content[:100] if message.content else 'None'}")
    print(f"[DEBUG] Has embeds: {len(message.embeds) if message.embeds else 0}")
    
    # Process commands first
    await bot.process_commands(message)
    
    # Only process webhook/bot messages with embeds
    if not message.embeds:
        print(f"[DEBUG] Skipping - no embeds")
        return
    
    print(f"[DEBUG] Has embeds, checking webhook/bot...")
    if not (message.webhook_id or message.author.bot):
        print(f"[DEBUG] Skipping - not from webhook or bot")
        return
    
    print(f"[DEBUG] Is webhook/bot, checking for 'Battle Data:'...")
    # Check if it's a battle data message
    if "Battle Data:" not in message.content:
        print(f"[DEBUG] Skipping - no 'Battle Data:' in content")
        return
    
    print(f"[DEBUG] Has 'Battle Data:', extracting room code...")
    match = re.search(r'Battle Data: (\d{6})', message.content)
    if not match:
        print(f"[DEBUG] Skipping - room code not found")
        return
    
    room_code = match.group(1)
    print(f"[DEBUG] Found room code: {room_code}")
    
    for embed in message.embeds:
        print(f"[DEBUG] Processing embed...")
        
        if not embed.description:
            print(f"[DEBUG] Skipping - no description")
            continue
        
        print(f"[DEBUG] Embed has description, length: {len(embed.description)}")
        
        if '```json' not in embed.description:
            print(f"[DEBUG] Skipping - no ```json marker")
            continue
        
        print(f"[DEBUG] Found ```json marker, extracting...")
        
        try:
            # Robust JSON extraction: Find first { and last }
            # This avoids issues with markdown markers, spoilers, or whitespace
            json_start = embed.description.find('{')
            json_end = embed.description.rfind('}')
            
            if json_start == -1 or json_end == -1 or json_start > json_end:
                 print(f"[DEBUG] Skipping - could not find JSON braces {{ }}")
                 continue
            
            json_str = embed.description[json_start:json_end+1]
            
            print(f"[DEBUG] Extracted JSON length: {len(json_str)}")
            print(f"[DEBUG] First 100 chars: {json_str[:100]}")
            
            # Remove spoiler tags just in case (though braces logic usually avoids them)
            json_str = json_str.replace('||', '')
            
            print(f"[DEBUG] Parsing JSON...")
            battle_data = json.loads(json_str)
            
            print(f"[DEBUG] JSON parsed successfully!")
            
            # Must have type field
            data_type = battle_data.get('type')
            print(f"[DEBUG] Data type: {data_type}")
            
            if not data_type:
                print(f"[DEBUG] Skipping - no type field")
                continue
            
            # Ensure room exists
            if room_code not in rooms:
                rooms[room_code] = {
                    'host': 0,
                    'host_name': 'Host',
                    'host_data': None,
                    'guest': 0,
                    'guest_name': 'Guest',
                    'guest_data': None,
                    'created_at': datetime.now(),
                    'channel_id': message.channel.id
                }
            
            room = rooms[room_code]
            
            # Store data based on type
            if data_type == 'host_data':
                room['host_data'] = battle_data
                print(f"[Embed] Host data received for room {room_code}")
            elif data_type == 'guest_data':
                room['guest_data'] = battle_data
                print(f"[Embed] Guest data received for room {room_code}")
            else:
                continue
            
            # Check if both players ready
            if room['host_data'] and room['guest_data']:
                print(f"[Embed] Room {room_code} READY! Sending opponent data...")
                
                # Send battle ready message
                await message.channel.send(f"🎊 **Battle Ready for room `{room_code}`!**")
                
                # AUTO-SEND opponent data so game can read it
                # IMPORTANT: Must include room code text so client filters pick it up!
                
                guest_json = json.dumps(room['guest_data'])
                guest_embed = discord.Embed(
                    title="Guest Data",
                    description=f"||```json\n{guest_json}\n```||",
                    color=0x3498db
                )
                await message.channel.send(f"**Room {room_code} Guest Data:**", embed=guest_embed)
                
                host_json = json.dumps(room['host_data'])
                host_embed = discord.Embed(
                    title="Host Data",
                    description=f"||```json\n{host_json}\n```||",
                    color=0x3498db
                )
                await message.channel.send(f"**Room {room_code} Host Data:**", embed=host_embed)
                
                print(f"[Embed] Sent opponent data for room {room_code}")
                
                # Schedule result update if simulation present
                if 'simulation_result' in battle_data:
                    print(f"[Embed] Scheduling result update for room {room_code}")
                    bot.loop.create_task(
                        auto_update_battle_result(room_code, battle_data['simulation_result'])
                    )
            
        except json.JSONDecodeError as e:
            # Print JSON errors for debugging
            print(f"[DEBUG] JSON parsing error: {e}")
        except Exception as e:
            print(f"[Embed] Unexpected error: {e}")

# Commands for game communication

@bot.command(name='host')
async def host_battle(ctx, code: str = None, username: str = "Tamer"):
    """Create battle room."""
    if not code or len(code) != 6 or not code.isdigit():
        await ctx.send("❌ Invalid code. Use 6 digits.")
        return
    
    if code in rooms:
        await ctx.send(f"⚠️ Room `{code}` already exists")
        return
    
    rooms[code] = {
        'host': ctx.author.id,
        'host_name': username,
        'host_data': None,
        'guest': None,
        'guest_name': None,
        'guest_data': None,
        'created_at': datetime.now(),
        'channel_id': ctx.channel.id
    }
    
    await ctx.send(f"✅ Room `{code}` created!\nHost: **{username}**")
    print(f"[Host] Room {code} created by {username}")

@bot.command(name='join')
async def join_battle(ctx, code: str = None, username: str = "Tamer"):
    """Join battle room."""
    if not code or len(code) != 6 or not code.isdigit():
        await ctx.send("❌ Invalid code")
        return
    
    if code not in rooms:
        await ctx.send(f"❌ Room `{code}` not found")
        return
    
    if rooms[code]['guest']:
        await ctx.send(f"❌ Room `{code}` is full")
        return
    
    rooms[code]['guest'] = ctx.author.id
    rooms[code]['guest_name'] = username
    
    await ctx.send(f"✅ Joined room `{code}`!\nGuest: **{username}**")
    await ctx.send(f"🎮 **{username}** joined room `{code}`!")
    print(f"[Join] {username} joined room {code}")

@bot.command(name='data')
async def send_battle_data(ctx, code: str, *, data: str):
    """Receive battle data."""
    if code not in rooms:
        await ctx.send(f"❌ Room `{code}` not found")
        return
    
    try:
        battle_data = json.loads(data)
    except:
        await ctx.send("❌ Invalid JSON")
        return
    
    room = rooms[code]
    data_type = battle_data.get('type')
    
    if data_type == 'host_data':
        room['host_data'] = battle_data
        await ctx.send(f"✅ Host data received for room `{code}`")
    elif data_type == 'guest_data':
        room['guest_data'] = battle_data
        await ctx.send(f"✅ Guest data received for room `{code}`")
    else:
        return
    
    # Check if both ready
    if room['host_data'] and room['guest_data']:
        await ctx.send(f"🎊 **Battle Ready for room `{code}`!**")
        
        # AUTO-SEND opponent data so game can read it
        # Send guest data wrapped in JSON code block
        guest_json = json.dumps(room['guest_data'])
        guest_embed = discord.Embed(
            title="Guest Data",
            description=f"||```json\n{guest_json}\n```||",
            color=0x3498db
        )
        await ctx.send(f"**Room {code} Guest Data:**", embed=guest_embed)
        
        # Send host data wrapped in JSON code block
        host_json = json.dumps(room['host_data'])
        host_embed = discord.Embed(
            title="Host Data",
            description=f"||```json\n{host_json}\n```||",
            color=0x3498db
        )
        await ctx.send(f"**Room {code} Host Data:**", embed=host_embed)
        
        print(f"[Data] Room {code} ready! Auto-sent opponent data")
        
        # Schedule result update if simulation present
        if 'simulation_result' in battle_data:
            bot.loop.create_task(auto_update_battle_result(code, battle_data['simulation_result']))

@bot.command(name='getdata')
async def get_opponent_data(ctx, code: str):
    """Get opponent's battle data."""
    if code not in rooms:
        return
    
    room = rooms[code]
    user_id = ctx.author.id
    
    if user_id == room['host'] and room['guest_data']:
        data_json = json.dumps(room['guest_data'])
        await ctx.send(f"```json\n{data_json}\n```")
        print(f"[GetData] Sent guest data to host for room {code}")
    elif user_id == room['guest'] and room['host_data']:
        data_json = json.dumps(room['host_data'])
        await ctx.send(f"```json\n{data_json}\n```")
        print(f"[GetData] Sent host data to guest for room {code}")

@bot.command(name='status')
async def check_status(ctx):
    """Check active rooms."""
    if not rooms:
        await ctx.send("No active rooms")
        return
    
    msg = "**Active Rooms:**\n"
    for code, room in rooms.items():
        host = room['host_name']
        guest = room.get('guest_name', 'Waiting...')
        msg += f"• Room `{code}`: {host} vs {guest}\n"
    
    await ctx.send(msg)

@bot.command(name='link')
async def link_account(ctx, *, tamer_name: str = None):
    """
    Link Discord account with Omnimon game.
    Usage: !link [TamerName]
    """
    # Use Discord username if tamer_name not provided
    if not tamer_name:
        tamer_name = ctx.author.name
    
    # Generate random 4-char alphanumeric code
    import random
    chars = string.ascii_uppercase + string.digits
    code = ''.join(random.choices(chars, k=4))
    
    # Ensure uniqueness (simple check)
    while code in linked_users:
        code = ''.join(random.choices(chars, k=4))
    
    # Store user link
    user_data = {
        "user_id": str(ctx.author.id),
        "username": ctx.author.name,
        "tamer_name": tamer_name,
        "linked_at": datetime.now().isoformat()
    }
    
    linked_users[code] = user_data
    save_linked_users()
    
    # Send response in format expected by R36S client via DM for security
    # Format: [PAIR] code:XXXX user:Name id:123
    response = f"**Your Pairing Code:** `{code}`\nEnter this code in your Omnimon game."
    
    try:
        # Send pairing info privately via DM
        await ctx.author.send(response)
        # Confirm in channel that DM was sent
        await ctx.send(f"✅ Code sent to your DMs! Check messages from {bot.user.name}.")
    except discord.Forbidden:
        # User has DMs disabled, send to channel with warning
        await ctx.send(f"⚠️ Could not send DM. Please enable DMs.\nYour code is: ||`{code}`||")
    
    print(f"[Link] {ctx.author.name} linked as '{tamer_name}' with code {code}")


@bot.command(name='unlink')
async def unlink_account(ctx):
    """Unlink Discord account from Omnimon game."""
    # Find user's link
    user_code = None
    for code, data in linked_users.items():
        if data['user_id'] == str(ctx.author.id):
            user_code = code
            break
    
    if user_code:
        tamer_name = linked_users[user_code]['tamer_name']
        del linked_users[user_code]
        save_linked_users()
        await ctx.send(f"✅ Unlinked account **{tamer_name}**")
        print(f"[Unlink] {ctx.author.name} unlinked code {user_code}")
    else:
        await ctx.send("❌ No linked account found")

@bot.command(name='whoami')
async def whoami(ctx):
    """Check your linked account status."""
    # Find user's link
    for code, data in linked_users.items():
        if data['user_id'] == str(ctx.author.id):
            linked_at = datetime.fromisoformat(data['linked_at'])
            await ctx.send(
                f"**Your Linked Account:**\n"
                f"🎮 Tamer: **{data['tamer_name']}**\n"
                f"🔗 Code: `{code}`\n"
                f"📅 Linked: {linked_at.strftime('%Y-%m-%d %H:%M')}" 
            )
            return
    
    await ctx.send("❌ No linked account found\nUse `!link CODE TamerName` to link")

@bot.command(name='users')
async def list_users(ctx):
    """List all linked users (Admin feature for future Storage/Trading)."""
    if not linked_users:
        await ctx.send("No linked users yet")
        return
    
    msg = "**Linked Users:**\n"
    for code, data in sorted(linked_users.items()):
        msg += f"• `{code}`: **{data['tamer_name']}** (@{data['username']})\n"
    
    await ctx.send(msg)

# ==========================================
# HTTP API Server for Game Client
# ==========================================

async def api_link(request):
    """Handle link request from game client."""
    try:
        data = await request.json()
        code = data.get('code')
        
        if not code:
            return web.json_response({'error': 'Missing code'}, status=400)
            
        code = code.upper()
        
        if code in linked_users:
            user_data = linked_users[code]
            return web.json_response({
                'status': 'success',
                'username': user_data['username'],
                'tamer_name': user_data['tamer_name'],
                'user_id': user_data['user_id']
            })
        else:
            return web.json_response({'error': 'Invalid code or not linked yet'}, status=404)
            
    except Exception as e:
        logger.error(f"API Error: {e}")
        return web.json_response({'error': str(e)}, status=500)

async def api_rooms(request):
    """List available battle rooms."""
    active_rooms = []
    current_time = datetime.now()
    
    for code, room in rooms.items():
        # Filter out stale rooms (> 5 mins inactivity)
        if current_time - room.get('last_active', room['created_at']) < timedelta(minutes=5):
            active_rooms.append({
                'id': code,
                'name': room.get('name', 'Battle Room'),
                'host': room['host_name'],
                'status': room['status'],
                'created': room['created_at'].isoformat(),
                'players': room.get('guests', []) + [room['host_name']]
            })
            
    return web.json_response(active_rooms)

async def api_create_room(request):
    """Create a new battle room."""
    try:
        data = await request.json()
        host_name = data.get('host')
        room_name = data.get('name', 'Battle')
        
        if not host_name:
             return web.json_response({'error': 'Missing host name'}, status=400)
        
        # Room ID: 6 digit random code for easier typing if needed, or UUID
        import random
        room_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        rooms[room_id] = {
            'id': room_id,
            'name': room_name,
            'host_name': host_name,
            'host_id': data.get('user_id'),
            'status': 'waiting',
            'created_at': datetime.now(),
            'last_active': datetime.now(),
            'guests': [],
            'data_queue': [] # Queue for battle messages
        }
        
        return web.json_response({
            'success': True,
            'room_id': room_id,
            'room_code': room_id
        })
        
    except Exception as e:
        logger.error(f"Create Room Error: {e}")
        return web.json_response({'error': str(e)}, status=500)

async def api_join_room(request):
    """Join an existing room."""
    room_id = request.match_info.get('room_id')
    try:
        data = await request.json()
        player_name = data.get('player')
        
        if room_id not in rooms:
            return web.json_response({'error': 'Room not found'}, status=404)
            
        room = rooms[room_id]
        if room['status'] != 'waiting':
             return web.json_response({'error': 'Room already in battle'}, status=400)
             
        if any(g['name'] == player_name for g in room['guests']):
             return web.json_response({'error': 'Name taken'}, status=409)
             
        # Add guest
        room['guests'].append({
            'name': player_name,
            'id': data.get('user_id')
        })
        room['last_active'] = datetime.now()
        
        # If full, start battle
        if len(room['guests']) >= 1: # 1 host + 1 guest = 2
            room['status'] = 'ready'
            
        return web.json_response({'success': True, 'status': room['status']})
        
    except Exception as e:
         return web.json_response({'error': str(e)}, status=500)

async def api_room_status(request):
    """Get status of a room."""
    room_id = request.match_info.get('room_id')
    if room_id not in rooms:
        return web.json_response({'error': 'Room not found'}, status=404)
    
    room = rooms[room_id]
    room['last_active'] = datetime.now() # Keep alive
    
    queue = room.get('data_queue', [])
    # DEBUG LOG
    # print(f"Room {room_id} status polled. Queue len: {len(queue)}")
    
    return web.json_response({
        'id': room['id'],
        'status': room['status'],
        'host': room['host_name'],
        'guests': [g['name'] for g in room['guests']],
        'data_queue': queue[-50:] # Increased from 10 to 50
    })

async def api_room_data(request):
    """Send battle data to a room."""
    room_id = request.match_info.get('room_id')
    if room_id not in rooms:
        return web.json_response({'error': 'Room not found'}, status=404)
        
    try:
        data = await request.json()
        print(f"Received DATA for room {room_id}: {data.get('type')}")
        room = rooms[room_id]
        
        # Append to message queue (simple relay for now)
        if 'data_queue' not in room:
            room['data_queue'] = []
            
        # Add timestamp and sender
        msg = {
            'ts': datetime.now().isoformat(),
            'data': data
        }
        room['data_queue'].append(msg)
        # Keep queue small
        if len(room['data_queue']) > 50:
            room['data_queue'].pop(0)
            
        room['last_active'] = datetime.now()
        return web.json_response({'success': True})
        
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)

async def start_web_server():
    """Start the aiohttp web server."""
    app = web.Application()
    app.router.add_get('/health', lambda r: web.json_response({'status': 'ok'}))
    app.router.add_post('/link', api_link)
    app.router.add_get('/rooms', api_rooms)
    app.router.add_post('/room', api_create_room)
    app.router.add_post('/room/{room_id}/join', api_join_room)
    app.router.add_get('/room/{room_id}/status', api_room_status)
    app.router.add_post('/room/{room_id}/data', api_room_data)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 5000)
    
    print("=========================================")
    print("🌍 HTTP API Server running on port 5000")
    print("=========================================")
    await site.start()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    load_linked_users()
    
    # Start background tasks
    bot.loop.create_task(cleanup_old_rooms())
    
    # Start Web Server
    await start_web_server()


if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    if not TOKEN:
        print("Error: Set DISCORD_BOT_TOKEN environment variable")
    else:
        bot.run(TOKEN)
