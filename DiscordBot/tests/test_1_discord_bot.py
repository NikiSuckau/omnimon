#!/usr/bin/env python3
"""
Test 1: Discord Bot Functionality
Tests the Discord bot without the R36S game.

Run this on your PC to verify bot is working correctly.
"""

import sys
import time

def test_bot_responsive():
    """Test if bot responds to commands."""
    print("=" * 60)
    print("TEST 1: Discord Bot Responsiveness")
    print("=" * 60)
    print()
    print("Instructions:")
    print("1. Make sure discord_relay_bot.py is running")
    print("2. Open your Discord channel")
    print("3. Type: !battlehelp")
    print()
    input("Press Enter when you see the bot's help message...")
    print("✅ Bot is responsive!\n")

def test_host_room():
    """Test creating a host room."""
    print("=" * 60)
    print("TEST 2: Create Host Room")
    print("=" * 60)
    print()
    print("In Discord, type: !host 123456")
    print()
    input("Press Enter when bot confirms room creation...")
    print("✅ Room creation works!\n")
    return "123456"

def test_join_room(room_code):
    """Test joining a room."""
    print("=" * 60)
    print("TEST 3: Join Room")
    print("=" * 60)
    print()
    print(f"In Discord, type: !join {room_code}")
    print()
    input("Press Enter when bot confirms you joined...")
    print("✅ Room joining works!\n")

def test_send_data(room_code):
    """Test sending battle data."""
    print("=" * 60)
    print("TEST 4: Send Battle Data")
    print("=" * 60)
    print()
    test_data = '{"pets":["Agumon","Gabumon"],"modules":["D-3"]}'
    print(f"In Discord, type: !data {room_code} {test_data}")
    print()
    input("Press Enter when bot confirms data received...")
    print("✅ Data sending works!\n")

def test_get_data(room_code):
    """Test retrieving opponent data."""
    print("=" * 60)
    print("TEST 5: Get Opponent Data")
    print("=" * 60)
    print()
    print(f"In Discord, type: !getdata {room_code}")
    print()
    print("Expected: Bot should DM you the opponent's data")
    print()
    input("Press Enter when you receive the DM...")
    print("✅ Data retrieval works!\n")

def test_status():
    """Test status command."""
    print("=" * 60)
    print("TEST 6: Check Room Status")
    print("=" * 60)
    print()
    print("In Discord, type: !status")
    print()
    input("Press Enter when you see active rooms list...")
    print("✅ Status check works!\n")

def test_close_room(room_code):
    """Test closing a room."""
    print("=" * 60)
    print("TEST 7: Close Room")
    print("=" * 60)
    print()
    print(f"In Discord, type: !close {room_code}")
    print()
    input("Press Enter when bot confirms room closed...")
    print("✅ Room closing works!\n")

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("DISCORD BOT TEST SUITE")
    print("=" * 60)
    print()
    print("This test validates the Discord bot is working correctly.")
    print("You'll need to manually type commands in Discord.")
    print()
    input("Press Enter to start tests...")
    print()
    
    try:
        # Test 1: Bot responsive
        test_bot_responsive()
        
        # Test 2: Create room
        room_code = test_host_room()
        
        # Test 3: Join room
        test_join_room(room_code)
        
        # Test 4: Send data
        test_send_data(room_code)
        
        # Test 5: Get data
        test_get_data(room_code)
        
        # Test 6: Status
        test_status()
        
        # Test 7: Close room
        test_close_room(room_code)
        
        # Summary
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("Discord bot is working correctly.")
        print("Next: Test the Python client (test_2_discord_client.py)")
        print()
        
    except KeyboardInterrupt:
        print("\n\n❌ Tests cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
