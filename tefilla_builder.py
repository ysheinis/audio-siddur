"""
Tefilla builder for Hebrew Audio Siddur.
Builds complete prayer services using the rule engine and caches results.
"""

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List, Optional
from pydub import AudioSegment

from tefilla_rules import TefillaRuleEngine, load_chunk_annotations, ChunkAnnotation
from chunk_processor import ChunkProcessor


@dataclass
class TefillaCache:
    """Cache for built tefillos."""
    tefilla_type: str
    date_conditions_hash: str
    chunk_list: List[str]
    output_file: Path


class TefillaBuilder:
    """Builds complete prayer services using rule engine and caching."""
    
    def __init__(self, chunk_processor: ChunkProcessor, output_dir: Path = None):
        self.chunk_processor = chunk_processor
        self.output_dir = output_dir or Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Load chunk annotations and create rule engine
        chunk_annotations = load_chunk_annotations()
        self.rule_engine = TefillaRuleEngine(chunk_annotations)
        
        # Cache for built tefillos
        self.tefilla_cache_file = self.output_dir / "tefilla_cache.json"
        self.tefilla_cache = self._load_tefilla_cache()
    
    def _load_tefilla_cache(self) -> dict:
        """Load tefilla cache from file."""
        if self.tefilla_cache_file.exists():
            try:
                with open(self.tefilla_cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        return {}
    
    def _save_tefilla_cache(self):
        """Save tefilla cache to file."""
        with open(self.tefilla_cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.tefilla_cache, f, indent=2, ensure_ascii=False)
    
    def build_tefilla(self, tefilla_type: str, target_date: date = None, force_rebuild: bool = False) -> Path:
        """Build a complete tefilla for the given date and type."""
        if target_date is None:
            target_date = date.today()
        
        # Generate hash for this tefilla configuration
        tefilla_hash = self.rule_engine.get_tefilla_hash(tefilla_type, target_date)
        output_file = self.output_dir / f"{tefilla_type}_{tefilla_hash}.mp3"
        
        # Check if tefilla is already cached
        if not force_rebuild and output_file.exists():
            cache_key = f"{tefilla_type}_{tefilla_hash}"
            if cache_key in self.tefilla_cache:
                print(f"⚡ Using cached tefilla: {output_file}")
                return output_file
        
        print(f"🔨 Building tefilla: {tefilla_type} for {target_date}")
        
        # Get chunk list from rule engine
        chunk_list = self.rule_engine.build_tefilla(tefilla_type, target_date)
        
        if not chunk_list:
            raise ValueError(f"No chunks found for tefilla type: {tefilla_type}")
        
        print(f"   📋 Selected chunks: {', '.join(chunk_list)}")
        
        # Ensure all chunks are processed
        chunk_paths = []
        for chunk_name in chunk_list:
            if chunk_name in self.chunk_processor.chunk_cache.load_directory():
                # Chunk exists in cache, get its path
                chunk_path = self.chunk_processor.chunk_cache.get_cached_path(chunk_name)
                if chunk_path.exists():
                    chunk_paths.append(chunk_path)
                else:
                    raise FileNotFoundError(f"Chunk file not found: {chunk_path}")
            else:
                raise ValueError(f"Chunk not found in cache: {chunk_name}")
        
        # Combine chunks into complete tefilla
        self._combine_chunks(chunk_paths, output_file)
        
        # Update cache
        cache_key = f"{tefilla_type}_{tefilla_hash}"
        self.tefilla_cache[cache_key] = {
            'tefilla_type': tefilla_type,
            'date': target_date.isoformat(),
            'chunk_list': chunk_list,
            'output_file': str(output_file),
            'hash': tefilla_hash
        }
        self._save_tefilla_cache()
        
        print(f"✅ Tefilla built: {output_file}")
        return output_file
    
    def _combine_chunks(self, chunk_paths: List[Path], output_path: Path):
        """Combine multiple chunk audio files into one tefilla."""
        combined = AudioSegment.empty()
        for path in chunk_paths:
            if path.exists():
                combined += AudioSegment.from_mp3(path)
            else:
                raise FileNotFoundError(f"Chunk file not found: {path}")
        combined.export(output_path, format="mp3")
    
    def get_available_tefillos(self) -> List[str]:
        """Get list of available tefilla types."""
        tefilla_types = set()
        for annotation in self.rule_engine.chunk_annotations.values():
            tefilla_types.update(annotation.tefilla_types)
        return sorted(list(tefilla_types))
    
    def show_cache_stats(self):
        """Display tefilla cache statistics."""
        cached_tefillos = list(self.tefilla_cache.keys())
        cached_files = list(self.output_dir.glob("*.mp3"))
        
        print(f"\n📊 Tefilla Cache Statistics:")
        print(f"   📁 Cached tefillos: {len(cached_tefillos)}")
        print(f"   🎵 Audio files: {len(cached_files)}")
        
        if cached_files:
            total_size = sum(f.stat().st_size for f in cached_files)
            print(f"   💾 Total size: {total_size / (1024*1024):.1f} MB")
        
        # Show breakdown by tefilla type
        tefilla_counts = {}
        for cache_key in cached_tefillos:
            tefilla_type = cache_key.split('_')[0]
            tefilla_counts[tefilla_type] = tefilla_counts.get(tefilla_type, 0) + 1
        
        if tefilla_counts:
            print(f"   📋 By tefilla type:")
            for tefilla_type, count in sorted(tefilla_counts.items()):
                print(f"      {tefilla_type}: {count}")
    
    def clear_cache(self):
        """Clear all cached tefillos."""
        # Remove cache file
        if self.tefilla_cache_file.exists():
            self.tefilla_cache_file.unlink()
        
        # Remove audio files
        for mp3_file in self.output_dir.glob("*.mp3"):
            mp3_file.unlink()
        
        self.tefilla_cache = {}
        print("🗑️ Tefilla cache cleared")
