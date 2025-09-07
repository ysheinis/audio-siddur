"""
Chunk caching system for Hebrew Audio Siddur.
Handles caching of TTS-generated audio chunks to avoid redundant API calls.
"""

import hashlib
import json
from pathlib import Path


class ChunkCache:
    """Manages caching of audio chunks with checksum validation."""
    
    def __init__(self, cache_dir: Path, directory_file: Path):
        self.cache_dir = cache_dir
        self.directory_file = directory_file
        self.cache_dir.mkdir(exist_ok=True)
    
    def calculate_text_checksum(self, text: str) -> str:
        """Calculate SHA-256 checksum of the text."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def load_directory(self) -> dict:
        """Load the chunk directory from JSON file."""
        if self.directory_file.exists():
            try:
                with open(self.directory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        return {}
    
    def save_directory(self, directory: dict):
        """Save the chunk directory to JSON file."""
        with open(self.directory_file, 'w', encoding='utf-8') as f:
            json.dump(directory, f, indent=2, ensure_ascii=False)
    
    def is_chunk_cached(self, chunk_name: str, text_checksum: str) -> bool:
        """Check if a chunk with the given checksum is already cached."""
        directory = self.load_directory()
        if chunk_name in directory:
            cached_checksum = directory[chunk_name].get('checksum')
            cached_file = self.cache_dir / f"{chunk_name}.mp3"
            return (cached_checksum == text_checksum and cached_file.exists())
        return False
    
    def update_directory(self, chunk_name: str, text_checksum: str):
        """Update the directory with a new chunk entry."""
        directory = self.load_directory()
        directory[chunk_name] = {
            'checksum': text_checksum,
            'timestamp': str(Path().cwd())  # Simple timestamp placeholder
        }
        self.save_directory(directory)
    
    def get_cached_path(self, chunk_name: str) -> Path:
        """Get the path to a cached chunk file."""
        return self.cache_dir / f"{chunk_name}.mp3"
    
    def show_stats(self):
        """Display cache statistics."""
        directory = self.load_directory()
        cached_files = list(self.cache_dir.glob("*.mp3"))
        
        print(f"\n📊 Cache Statistics:")
        print(f"   📁 Cached chunks: {len(cached_files)}")
        print(f"   📋 Directory entries: {len(directory)}")
        
        if cached_files:
            total_size = sum(f.stat().st_size for f in cached_files)
            print(f"   💾 Total cache size: {total_size / (1024*1024):.1f} MB")
