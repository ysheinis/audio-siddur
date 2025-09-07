import os
import shutil
from pathlib import Path
from pydub import AudioSegment
from chunk_processor import ChunkProcessor

# --- CONFIGURATION ---

from tts_map import TEXT_MAP
from tts_audio_groups import AUDIO_GROUPS  # Optional

GROUP_OUTPUT_DIR = Path("output")

# --- SETUP ---

GROUP_OUTPUT_DIR.mkdir(exist_ok=True)

# Initialize chunk processor (handles its own cache and TTS setup)
chunk_processor = ChunkProcessor(credentials_file="innate-rite-449719-j9-e3536a2d6cb9.json")

# --- MAIN PROCESSING ---

def process_group(group_key, chunk_keys):
    print(f"\n📦 Combining group: {group_key}")
    chunk_paths = [chunk_processor.chunk_cache.get_cached_path(k) for k in chunk_keys]
    missing = [str(p) for p in chunk_paths if not p.exists()]
    if missing:
        print(f"❌ Missing chunk MP3s: {missing}")
        return

    group_path = GROUP_OUTPUT_DIR / f"{group_key}.mp3"
    combine_mp3s(chunk_paths, group_path)
    print(f"🎉 Group saved: {group_path}")

# --- ENTRY POINT ---

def main():
    print("🎵 Starting Hebrew Audio Siddur Generation")
    print("=" * 50)
    
    # Process all chunks (with caching)
    for key, text in TEXT_MAP.items():
        chunk_processor.process_chunk(key, text)

    # Show cache statistics
    chunk_processor.chunk_cache.show_stats()

    # Generate complete prayer services
    if 'AUDIO_GROUPS' in globals():
        print(f"\n🔄 Generating {len(AUDIO_GROUPS)} prayer services...")
        for group_key, chunk_keys in AUDIO_GROUPS.items():
            process_group(group_key, chunk_keys)

    # Clean up temporary directory
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)
    
    print("\n✅ Audio generation complete!")

if __name__ == "__main__":
    main()
