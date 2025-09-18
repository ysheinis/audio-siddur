#!/usr/bin/env python3
r"""
Scheduled Tefilla Player

This script is designed to be run by Windows Task Scheduler multiple times per day.
It checks if today is Shabbat or Yom Tov, and if so, plays the appropriate tefilla.
If not, it silently exits.

Usage for Windows Task Scheduler:
- Schedule to run 3 times daily (e.g., 7:00 AM, 1:00 PM, 7:00 PM)
- The script will automatically determine if it should play and which tefilla type

The script will:
- Check if today is Shabbat or Yom Tov
- If yes: play the appropriate tefilla for the current time
- If no: silently exit (no output, no error)
"""

import sys
import os
import argparse
from datetime import date, datetime
from pathlib import Path

# Add paths for imports
import subprocess
import os
from pathlib import Path
# Calculate project root - go up one level from scripts directory
# Use os.path.abspath to get the absolute path of the current file
script_path = os.path.abspath(__file__)
project_root = Path(script_path).parent.parent.resolve()
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "scripts"))


def log_message(message: str):
    """Log a message to the scheduled_tefilla.log file."""
    try:
        # Log to the logs directory in the project root
        # Use os.path.abspath to get the absolute path of the current file
        script_path = os.path.abspath(__file__)
        project_root = Path(script_path).parent.parent.resolve()
        logs_dir = project_root / "logs"
        logs_dir.mkdir(exist_ok=True)
        log_file = logs_dir / "scheduled_tefilla.log"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"Logging failed: {e}")  # Print error for debugging


from tefilla_rules import HebrewCalendar
from tefilla_builder import TefillaBuilder
from chunk_processor import ChunkProcessor
from tts_generate import get_current_tefilla_type

# Import play_tefilla functions locally to avoid circular import
def find_audio_player():
    """Find the default audio player on the system."""
    # Common audio players on Windows
    players = [
        r"C:\Program Files\Windows Media Player\wmplayer.exe",
        r"C:\Program Files (x86)\Windows Media Player\wmplayer.exe",
        "wmplayer.exe",  # If in PATH
        "vlc.exe",       # VLC if installed
    ]
    
    for player in players:
        if os.path.exists(player) or player.endswith('.exe'):
            log_message(f"Found audio player: {player}")
            return player
    
    log_message("No audio player found, using default: wmplayer.exe")
    return "wmplayer.exe"  # Default fallback

def play_audio_file(audio_file_path: Path, player_path: str = None):
    """Play an audio file using the specified player."""
    if not audio_file_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
    
    if player_path is None:
        player_path = find_audio_player()
    
    try:
        # Use subprocess to play the audio file
        log_message(f"Attempting to play {audio_file_path} with {player_path}")
        
        # Try using Windows 'start' command for better compatibility
        try:
            # Use Windows 'start' command to open the file with default player
            process = subprocess.Popen(["start", "", str(audio_file_path)], shell=True)
            log_message("Used Windows 'start' command to play audio")
        except:
            # Fallback to direct player call
            if "wmplayer" in player_path.lower():
                # For Windows Media Player, try to make it visible
                process = subprocess.Popen([player_path, "/play", "/close", str(audio_file_path)])
            else:
                # For other players
                process = subprocess.Popen([player_path, str(audio_file_path)])
        
        log_message(f"Player process started with PID: {process.pid}")
        
        # Wait a moment to see if the process starts successfully
        import time
        time.sleep(1)
        
        # Check if process is still running
        if process.poll() is None:
            log_message("Player process is running successfully")
            return True
        else:
            log_message(f"Player process exited with code: {process.returncode}")
            return False
            
    except Exception as e:
        log_message(f"Error playing audio: {e}")
        return False


def is_shabbat_or_yom_tov(target_date: date) -> bool:
    """Check if the given date is Shabbat or Yom Tov."""
    calendar = HebrewCalendar()
    conditions = calendar.get_date_conditions(target_date, 'shacharis')
    
    # Check if it's Shabbat
    if conditions.day_of_week == 'shabbat':
        return True
    
    # Check if it's a major holiday
    major_holidays = [
        'rosh_hashana', 'yom_kippur', 'sukkot', 'shmini_atzeret', 
        'pesach', 'shavuot'
    ]
    
    if conditions.holiday in major_holidays:
        return True
    
    return False


def get_tefilla_type_for_time() -> str:
    """Get the appropriate tefilla type based on current time."""
    return get_current_tefilla_type()


def main():
    """Main function for scheduled tefilla playback."""
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Scheduled Tefilla Player')
        parser.add_argument('--date', type=str, help='Date to use (YYYY-MM-DD format). Default: today')
        args = parser.parse_args()
        
        # Get date (today or specified)
        if args.date:
            try:
                today = date.fromisoformat(args.date)
                log_message(f"Script started for specified date: {today}")
            except ValueError:
                log_message(f"Invalid date format: {args.date}. Using today instead.")
                today = date.today()
        else:
            today = date.today()
            log_message(f"Script started for date: {today}")
        
        # Check if today is Shabbat or Yom Tov
        if not is_shabbat_or_yom_tov(today):
            # Not Shabbat or Yom Tov - silently exit
            log_message("Not Shabbat or Yom Tov - exiting")
            sys.exit(0)
        
        log_message("Today is Shabbat or Yom Tov - proceeding with tefilla")
        
        # It's Shabbat or Yom Tov - determine tefilla type
        tefilla_type = get_tefilla_type_for_time()
        log_message(f"Current tefilla type: {tefilla_type}")
        
        # Initialize components
        credentials_file = str(project_root / "config" / "google_api_key.json")
        log_message(f"Using credentials file: {credentials_file}")
        chunk_processor = ChunkProcessor(credentials_file=credentials_file)
        builder = TefillaBuilder(chunk_processor)
        
        # Build/get the tefilla
        log_message("Building/getting tefilla...")
        tefilla_file = builder.build_tefilla(tefilla_type, today)
        
        if not tefilla_file or not tefilla_file.exists():
            # If we can't build the tefilla, silently exit
            log_message("Failed to build tefilla - exiting")
            sys.exit(0)
        
        log_message(f"Tefilla ready: {tefilla_file.name}")
        
        # Play the audio file
        print("Starting audio playback...")
        log_message("Starting audio playback...")
        player = find_audio_player()
        print(f"Using audio player: {player}")
        log_message(f"Using audio player: {player}")
        print(f"Playing file: {tefilla_file}")
        log_message(f"Playing file: {tefilla_file}")
        
        success = play_audio_file(tefilla_file, player)
        
        if not success:
            # If playback fails, silently exit
            print("Audio playback failed - exiting")
            log_message("Audio playback failed - exiting")
            sys.exit(0)
        
        # Success - log and wait a moment to ensure player starts
        print("Audio playback started successfully")
        log_message("Audio playback started successfully")
        import time
        time.sleep(2)  # Give the player time to start
        print("Script completed - player should be running")
        log_message("Script completed - player should be running")
        sys.exit(0)
        
    except Exception as e:
        # Any error - log it and silently exit
        log_message(f"Error occurred: {str(e)}")
        sys.exit(0)


if __name__ == "__main__":
    main()
