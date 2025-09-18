#!/usr/bin/env python3
r"""
Play Hebrew Prayer Audio Files

This script plays tefillos (prayer services) for specified dates and types.
If the tefilla doesn't exist, it will be built automatically (including all necessary chunks).

Usage:
    python play_tefilla.py                           # Play current tefilla
    python play_tefilla.py --date 2025-09-23         # Play tefilla for specific date
    python play_tefilla.py --date 2025-09-23 --tefilla shacharis  # Play specific tefilla type
    python play_tefilla.py --date 2025-09-23 --tefilla shacharis --player "C:\Program Files\VLC\vlc.exe"  # Use specific player
"""

import argparse
import subprocess
import sys
import os
from datetime import date, datetime
from pathlib import Path

# Import our modules
# Add paths for imports
project_root = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "scripts"))

from tefilla_builder import TefillaBuilder
from chunk_processor import ChunkProcessor
from tts_generate import get_current_tefilla_type


def find_audio_player():
    """Find the default audio player on the system."""
    # Common audio players on Windows
    windows_players = [
        r"C:\Program Files\Windows Media Player\wmplayer.exe",
        r"C:\Program Files (x86)\Windows Media Player\wmplayer.exe",
        r"C:\Program Files\VLC\vlc.exe",
        r"C:\Program Files (x86)\VLC\vlc.exe",
        r"C:\Program Files\VideoLAN\VLC\vlc.exe",
        r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
    ]
    
    # Check if any of the common players exist
    for player in windows_players:
        if os.path.exists(player):
            return player
    
    # Try to use the default system player
    try:
        # On Windows, we can try to use the default program for .mp3 files
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"\.mp3")
        default_program = winreg.QueryValue(key, "")
        winreg.CloseKey(key)
        
        # Get the command for the default program
        key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, f"{default_program}\\shell\\open\\command")
        command = winreg.QueryValue(key, "")
        winreg.CloseKey(key)
        
        # Extract the executable path
        player_path = command.split('"')[1] if '"' in command else command.split()[0]
        if os.path.exists(player_path):
            return player_path
    except:
        pass
    
    # Fallback: try to use the system default
    return "start"  # Windows command to open with default program


def play_audio_file(file_path, player=None):
    """Play an audio file using the specified player or default player."""
    if not os.path.exists(file_path):
        print(f"❌ Error: Audio file not found: {file_path}")
        return False
    
    if player is None:
        player = find_audio_player()
    
    try:
        # Try multiple methods to play the file
        success = False
        
        # Method 1: Use Windows 'start' command with /wait to ensure it opens
        try:
            subprocess.Popen(f'start /wait "" "{file_path}"', shell=True)
            print(f"🎵 Playing: {file_path}")
            success = True
        except:
            pass
        
        # Method 2: Try using Windows Media Player directly
        if not success:
            try:
                wmplayer_path = r"C:\Program Files\Windows Media Player\wmplayer.exe"
                if os.path.exists(wmplayer_path):
                    subprocess.Popen([wmplayer_path, str(file_path)])
                    print(f"🎵 Playing with Windows Media Player: {file_path}")
                    success = True
            except:
                pass
        
        # Method 3: Try using the default program directly
        if not success:
            try:
                subprocess.Popen(f'"{file_path}"', shell=True)
                print(f"🎵 Playing with default program: {file_path}")
                success = True
            except:
                pass
        
        if not success:
            print(f"❌ Error: Could not launch audio player")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Error playing audio file: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Play Hebrew prayer audio files")
    parser.add_argument("--date", type=str, help="Date in YYYY-MM-DD format (default: today)")
    parser.add_argument("--tefilla", type=str, choices=["shacharis", "mincha", "maariv"], 
                       help="Tefilla type (default: current time appropriate)")
    parser.add_argument("--player", type=str, help="Path to audio player executable")
    parser.add_argument("--list", action="store_true", help="List available tefillos for the date")
    
    args = parser.parse_args()
    
    # Determine target date
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print(f"❌ Error: Invalid date format. Use YYYY-MM-DD")
            sys.exit(1)
    else:
        target_date = date.today()
    
    # Determine tefilla type
    if args.tefilla:
        tefilla_type = args.tefilla
    else:
        tefilla_type = get_current_tefilla_type()
    
    print(f"🎵 Hebrew Prayer Audio Player")
    print(f"📅 Target date: {target_date}")
    print(f"🕌 Tefilla type: {tefilla_type}")
    print()
    
    # Initialize chunk processor and tefilla builder
    chunk_processor = ChunkProcessor()
    builder = TefillaBuilder(chunk_processor)
    
    if args.list:
        # List available tefillos for the date
        print(f"📋 Available tefillos for {target_date}:")
        for t_type in ["shacharis", "mincha", "maariv"]:
            try:
                # Try to build/get the tefilla file
                t_file = builder.build_tefilla(t_type, target_date)
                if t_file and t_file.exists():
                    print(f"  ✅ {t_type}: {t_file.name}")
                else:
                    print(f"  ❌ {t_type}: Not found")
            except Exception as e:
                print(f"  ❌ {t_type}: Error - {e}")
        return
    
    # Build the tefilla (it will reuse existing if available)
    print(f"🔨 Building/getting tefilla...")
    try:
        tefilla_file = builder.build_tefilla(tefilla_type, target_date)
        print(f"✅ Tefilla ready: {tefilla_file.name}")
    except Exception as e:
        print(f"❌ Error building tefilla: {e}")
        sys.exit(1)
    
    # Get the final tefilla file path
    final_tefilla_file = tefilla_file
    
    if not final_tefilla_file or not final_tefilla_file.exists():
        print(f"❌ Error: Tefilla file not found after building")
        sys.exit(1)
    
    # Play the audio file
    print(f"🎵 Starting playback...")
    success = play_audio_file(final_tefilla_file, args.player)
    
    if success:
        print(f"✅ Playback started successfully")
    else:
        print(f"❌ Failed to start playback")
        sys.exit(1)


if __name__ == "__main__":
    main()
