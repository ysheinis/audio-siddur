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
from datetime import date, datetime
from pathlib import Path

# Add current directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def log_message(message: str):
    """Log a message to the scheduled_tefilla.log file."""
    try:
        log_file = Path("scheduled_tefilla.log")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except:
        pass  # If logging fails, don't crash the script

from tefilla_rules import HebrewCalendar
from play_tefilla import play_audio_file, find_audio_player
from tefilla_builder import TefillaBuilder
from chunk_processor import ChunkProcessor
from tts_generate import get_current_tefilla_type


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
        # Get today's date
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
        chunk_processor = ChunkProcessor()
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
        log_message("Starting audio playback...")
        player = find_audio_player()
        success = play_audio_file(tefilla_file, player)
        
        if not success:
            # If playback fails, silently exit
            log_message("Audio playback failed - exiting")
            sys.exit(0)
        
        # Success - exit normally
        log_message("Audio playback started successfully")
        sys.exit(0)
        
    except Exception as e:
        # Any error - log it and silently exit
        log_message(f"Error occurred: {str(e)}")
        sys.exit(0)


if __name__ == "__main__":
    main()
