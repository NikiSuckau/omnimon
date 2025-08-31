# Omnimon Virtual Pet Game - Cross-Platform Compatibility

## Supported Systems

✅ **Linux Distributions:**
- Ubuntu 18.04+
- Debian 9+
- Fedora 30+
- Arch Linux
- Batocera (embedded gaming OS)
- RetroPie
- Any modern Linux with Python 3.9+

✅ **Windows:**
- Windows 10/11
- Windows 8.1
- Windows 7 (with Python 3.9+)

## Requirements

- Python 3.9 or newer
- pygame 1.9+ or pygame 2.x
- Optional: psutil (for system stats)
- Optional: gpiozero (for Raspberry Pi GPIO support)

## Installation

### Quick Install (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-pip
pip3 install pygame psutil
```

### Quick Install (Fedora)
```bash
sudo dnf install python3 python3-pip
pip3 install pygame psutil
```

### Quick Install (Windows)
1. Install Python from https://python.org
2. Run: `pip install pygame psutil`

### Batocera/RetroPie
The game should work out of the box if Python and pygame are available.

## Running the Game

### Configuration File
The easiest way to configure the game is through `config.json`:

```json
{
    "SCREEN_WIDTH": 240,
    "SCREEN_HEIGHT": 240,
    "constants": 30,
    "MAX_PETS": 4,
    "FULLSCREEN": false
}
```

Set `"FULLSCREEN": true` to run in fullscreen mode by default.

### Linux/Mac
```bash
# Make launch script executable (first time only)
chmod +x launch.sh

# Run in windowed mode
./launch.sh

# Run in fullscreen mode
./launch.sh --fullscreen
```

### Windows
```cmd
# Run in windowed mode
launch.bat

# Run in fullscreen mode
launch.bat --fullscreen
```

### Direct Python
```bash
# Run directly with Python
python3 vpet.py

# Force fullscreen mode
OMNIMON_FULLSCREEN=1 python3 vpet.py
```

## Environment Variables

Fullscreen mode is determined by this priority order:
1. Command line arguments (`--fullscreen` or `-f`)
2. Environment variable (`OMNIMON_FULLSCREEN=1`)
3. Configuration file (`"FULLSCREEN": true` in config.json)
4. Auto-detection for embedded systems

Other environment variables:
- `SDL_VIDEODRIVER` - Override SDL video driver (x11, wayland, kmsdrm, etc.)
- `SDL_VIDEO_CENTERED=1` - Center window on screen

## Troubleshooting

### No Display / Black Screen
```bash
# Try different video drivers
SDL_VIDEODRIVER=x11 python3 vpet.py
SDL_VIDEODRIVER=wayland python3 vpet.py
SDL_VIDEODRIVER=fbcon python3 vpet.py
```

### Permission Issues (Linux)
```bash
# Add user to necessary groups
sudo usermod -a -G audio,video,input $USER
# Log out and back in
```

### Missing Dependencies
```bash
# Test compatibility
python3 test_compatibility.py
```

## Performance Optimization

The game includes several performance optimizations:
- Scene caching to reduce redundant rendering
- Sprite caching to avoid repeated scaling operations
- Frame-rate independent animations
- Efficient system stats collection

## Hardware Support

- **Raspberry Pi**: Full GPIO and I2C support when available
- **Desktop Systems**: Keyboard input, system monitoring
- **Embedded Systems**: Automatic fullscreen detection

## Contributing

The codebase is designed to be portable and should work on any system with Python and pygame. Platform-specific features gracefully degrade when hardware is not available.
