"""
Hebrew Audio Siddur Generator
Main entry point for generating Hebrew prayer audio files using rule-based system.
"""

import os
import shutil
import argparse
from datetime import date, datetime
from pathlib import Path
import sys
sys.path.append("../src")
from chunk_processor import ChunkProcessor
from tefilla_builder import TefillaBuilder
from tts_map import TEXT_MAP

# --- SETUP ---

# Initialize chunk processor (handles its own cache and TTS setup)
chunk_processor = ChunkProcessor(credentials_file="../config/google_api_key.json")

# Initialize tefilla builder
tefilla_builder = TefillaBuilder(chunk_processor)

# --- MAIN PROCESSING ---

def ensure_all_chunks_processed(chunks_count: int = None):
    """Ensure chunks from TEXT_MAP are processed and cached."""
    if chunks_count is None:
        print("🔧 Processing all prayer chunks...")
        total_chunks = len(TEXT_MAP)
    else:
        print(f"🔧 Processing first {chunks_count} prayer chunks...")
        total_chunks = min(chunks_count, len(TEXT_MAP))
    
    processed_count = 0
    for key, chunk_data in TEXT_MAP.items():
        if chunks_count is not None and processed_count >= chunks_count:
            break
            
        text = chunk_data["text"]
        chunk_processor.process_chunk(key, text)
        processed_count += 1
    
    print(f"✅ {processed_count} chunks processed")

def build_tefilla_for_date(tefilla_type: str, target_date: date = None, force_rebuild: bool = False) -> Path:
    """Build a specific tefilla for a given date."""
    return tefilla_builder.build_tefilla(tefilla_type, target_date, force_rebuild)

def build_tefillos_for_date_range(start_date: date, end_date: date, tefilla_types: list, force_rebuild: bool = False):
    """Build tefillos for a range of dates and tefilla types."""
    from datetime import timedelta
    
    print(f"📅 Building tefillos from {start_date} to {end_date}")
    print(f"🕌 Tefilla types: {', '.join(tefilla_types)}")
    print("=" * 60)
    
    current_date = start_date
    total_tefillos = 0
    successful_tefillos = 0
    
    while current_date <= end_date:
        print(f"\n🗓️  Processing date: {current_date}")
        
        for tefilla_type in tefilla_types:
            total_tefillos += 1
            try:
                print(f"   🕌 Building {tefilla_type}...")
                output_file = build_tefilla_for_date(tefilla_type, current_date, force_rebuild)
                print(f"   ✅ {tefilla_type}: {output_file.name}")
                successful_tefillos += 1
            except Exception as e:
                print(f"   ❌ {tefilla_type}: Error - {e}")
        
        current_date += timedelta(days=1)
    
    print(f"\n🎉 Build complete!")
    print(f"📊 Successfully built {successful_tefillos}/{total_tefillos} tefillos")
    
    # Show final cache stats
    tefilla_builder.show_cache_stats()

def get_current_tefilla_type() -> str:
    """Determine the appropriate tefilla type for the current time."""
    current_hour = datetime.now().hour
    
    if 4 <= current_hour < 12:  # 4 AM to 12 PM
        return "shacharis"
    elif 12 <= current_hour < 18:  # 12 PM to 6 PM
        return "mincha"
    else:  # 6 PM to 4 AM
        return "maariv"

def show_hebrew_calendar_info(target_date: date, tefilla_type: str = None):
    """Show Hebrew calendar information for a date."""
    from pyluach import dates
    hebrew_date = dates.HebrewDate.from_pydate(target_date)
    print(f"📅 Hebrew date: {hebrew_date}")
    
    # Show conditions
    from tefilla_rules import HebrewCalendar
    calendar = HebrewCalendar()
    conditions = calendar.get_date_conditions(target_date, tefilla_type)
    
    print(f"🌍 Conditions:")
    print(f"   Day: {conditions.day_of_week}")
    if conditions.holiday:
        print(f"   Holiday: {conditions.holiday}")
    if conditions.rosh_chodesh:
        print(f"   Rosh Chodesh: Yes")
    if conditions.chol_hamoed:
        print(f"   Chol Hamoed: Yes")
    if conditions.fast_day:
        print(f"   Fast Day: Yes")
    if conditions.aseret_yemei_teshuvah:
        print(f"   Aseret Yemei Teshuvah: Yes")
    if conditions.sefirat_haomer > 0:
        print(f"   Sefirat HaOmer: Day {conditions.sefirat_haomer}")
    if conditions.hallel_type != "none":
        print(f"   Hallel: {conditions.hallel_type.title()}")
    
    # Show Halachic prayer variations
    print(f"🙏 Prayer Variations (Outside Israel):")
    print(f"   Mashiv HaRuach: {'Yes' if conditions.mashiv_haruach else 'No'}")
    print(f"   VeTen Tal UMattar: {'Yes' if conditions.veten_tal_umattar else 'No'}")
    if not conditions.veten_tal_umattar:
        print(f"   VeTen Brocha: Yes")
    
    # Show Hebrew date adjustment for maariv
    if tefilla_type == 'maariv':
        next_hebrew_date = hebrew_date + 1
        print(f"🌙 Maariv uses next Hebrew date: {next_hebrew_date}")

def main():
    """Main entry point with command line argument support."""
    parser = argparse.ArgumentParser(description="Hebrew Audio Siddur Generator")
    parser.add_argument("--tefilla", choices=["shacharis", "mincha", "maariv"], 
                       help="Tefilla type to generate (default: current time appropriate)")
    parser.add_argument("--date", type=str, 
                       help="Date to generate for (YYYY-MM-DD, default: today)")
    parser.add_argument("--date-range", type=str, nargs=2, metavar=('START_DATE', 'END_DATE'),
                       help="Date range to generate for (YYYY-MM-DD YYYY-MM-DD)")
    parser.add_argument("--all-tefillos", action="store_true",
                       help="Generate all tefilla types (shacharis, mincha, maariv) for each date")
    parser.add_argument("--force-rebuild", action="store_true",
                       help="Force rebuild even if cached version exists")
    parser.add_argument("--process-all", action="store_true",
                       help="Process all chunks and show cache stats")
    parser.add_argument("--process-chunks", action="store_true",
                       help="Process chunks (all chunks by default, or limited number with --chunks-count)")
    parser.add_argument("--chunks-count", type=int,
                       help="Number of chunks to process (used with --process-chunks, default: all chunks)")
    parser.add_argument("--list-tefillos", action="store_true",
                       help="List available tefilla types")
    parser.add_argument("--cache-stats", action="store_true",
                       help="Show cache statistics")
    parser.add_argument("--clear-cache", action="store_true",
                       help="Clear all cached tefillos")
    parser.add_argument("--clear-chunk-cache", action="store_true",
                       help="Clear all cached audio chunks")
    parser.add_argument("--show-calendar", action="store_true",
                       help="Show Hebrew calendar information for the target date")
    
    args = parser.parse_args()
    
    print("🎵 Hebrew Audio Siddur Generator")
    print("=" * 50)
    
    # Handle special commands
    if args.list_tefillos:
        tefillos = tefilla_builder.get_available_tefillos()
        print("📋 Available tefilla types:")
        for tefilla in tefillos:
            print(f"   • {tefilla}")
        return
    
    if args.cache_stats:
        chunk_processor.chunk_cache.show_stats()
        tefilla_builder.show_cache_stats()
        return
    
    if args.clear_cache:
        tefilla_builder.clear_cache()
        return
    
    if args.clear_chunk_cache:
        chunk_processor.chunk_cache.clear_cache()
        return
    
    # Determine target date(s)
    target_date = date.today()
    start_date = None
    end_date = None
    
    if args.date_range:
        try:
            start_date = datetime.strptime(args.date_range[0], "%Y-%m-%d").date()
            end_date = datetime.strptime(args.date_range[1], "%Y-%m-%d").date()
            if start_date > end_date:
                print(f"❌ Start date must be before or equal to end date")
                return
        except ValueError as e:
            print(f"❌ Invalid date format in range: {e}. Use YYYY-MM-DD")
            return
    elif args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print(f"❌ Invalid date format: {args.date}. Use YYYY-MM-DD")
            return
    
    if args.show_calendar:
        tefilla_type = args.tefilla or get_current_tefilla_type()
        show_hebrew_calendar_info(target_date, tefilla_type)
        return
    
    # Process chunks if requested
    if args.process_all or args.process_chunks:
        chunks_count = args.chunks_count if args.process_chunks else None
        ensure_all_chunks_processed(chunks_count)
        chunk_processor.chunk_cache.show_stats()
        if args.process_all:
            tefilla_builder.show_cache_stats()
        return

    # Determine tefilla type(s)
    if args.all_tefillos:
        tefilla_types = ["shacharis", "mincha", "maariv"]
    elif args.tefilla:
        tefilla_types = [args.tefilla]
    elif start_date and end_date:
        # For date ranges, default to all tefillos
        tefilla_types = ["shacharis", "mincha", "maariv"]
    else:
        # For single dates, default to current time appropriate tefilla
        tefilla_type = get_current_tefilla_type()
        tefilla_types = [tefilla_type]
    
    # Ensure all chunks are processed
    ensure_all_chunks_processed()
    
    # Build tefillos
    if start_date and end_date:
        # Build for date range
        build_tefillos_for_date_range(start_date, end_date, tefilla_types, args.force_rebuild)
    else:
        # Build for single date
        print(f"📅 Target date: {target_date}")
        print(f"🕌 Tefilla type: {tefilla_types[0]}")
        
        try:
            output_file = build_tefilla_for_date(tefilla_types[0], target_date, args.force_rebuild)
            print(f"\n🎉 Tefilla generated successfully!")
            print(f"📁 Output file: {output_file}")
            
            # Show cache stats
            tefilla_builder.show_cache_stats()
            
        except Exception as e:
            print(f"❌ Error generating tefilla: {e}")
            return

if __name__ == "__main__":
    main()