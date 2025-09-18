"""
Tefilla builder for Hebrew Audio Siddur.
Builds complete prayer services using the rule engine and caches results.
"""

import json
import hashlib
from dataclasses import dataclass, asdict
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
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
    original_date: str
    original_tefilla_type: str
    conditions: dict
    creation_timestamp: str


class TefillaBuilder:
    """Builds complete prayer services using rule engine and caching."""
    
    def __init__(self, chunk_processor: ChunkProcessor, output_dir: Path = None):
        self.chunk_processor = chunk_processor
        self.output_dir = output_dir or Path("../data/output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Load chunk annotations and create rule engine
        chunk_annotations = load_chunk_annotations()
        self.rule_engine = TefillaRuleEngine(chunk_annotations)
        
        # Cache for built tefillos
        self.tefilla_cache_file = self.output_dir / "directory.json"
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
    
    def _generate_conditions_checksum(self, conditions: Dict[str, Any]) -> str:
        """Generate a checksum based on conditions to identify identical tefillos."""
        # Filter out conditions that don't affect tefilla building
        tefilla_relevant_conditions = {k: v for k, v in conditions.items() 
                                     if k not in ['fast_day', 'sefirat_haomer']}
        
        # Create a sorted string representation of conditions for consistent hashing
        conditions_str = json.dumps(tefilla_relevant_conditions, sort_keys=True, default=str)
        return hashlib.md5(conditions_str.encode()).hexdigest()[:8]
    
    def _generate_meaningful_filename(self, tefilla_type: str, conditions: Dict[str, Any]) -> str:
        """Generate a meaningful filename based on tefilla type and conditions."""
        parts = [tefilla_type]
        
        # Add day of week
        if conditions.get('day_of_week') == 'shabbat':
            parts.append('shabbat')
        else:
            parts.append('weekday')
        
        # Add holiday information
        if conditions.get('holiday'):
            holiday = conditions['holiday']
            if holiday == 'rosh_hashana':
                parts.append('rosh_hashana')
            elif holiday == 'yom_kippur':
                parts.append('yom_kippur')
            elif holiday == 'sukkot':
                parts.append('sukkot')
            elif holiday == 'shmini_atzeret':
                parts.append('shmini_atzeret')
            elif holiday == 'pesach':
                parts.append('pesach')
            elif holiday == 'shavuot':
                parts.append('shavuot')
            elif holiday == 'chanukkah':
                parts.append('chanukkah')
            elif holiday == 'purim':
                parts.append('purim')
        
        # Add special conditions (excluding fast_day and sefirat_haomer)
        if conditions.get('rosh_chodesh'):
            parts.append('rosh_chodesh')
        
        if conditions.get('chol_hamoed'):
            parts.append('chol_hamoed')
        
        if conditions.get('aseret_yemei_teshuvah'):
            parts.append('aseret_yemei_teshuvah')
        
        # Add Hallel type
        hallel_type = conditions.get('hallel_type', 'none')
        if hallel_type != 'none':
            parts.append(f'hallel_{hallel_type}')
        
        # Add seasonal variations
        if conditions.get('mashiv_haruach'):
            parts.append('mashiv_haruach')
        
        if conditions.get('veten_tal_umattar'):
            parts.append('veten_tal_umattar')
        
        # Join parts and clean up
        filename = ' '.join(parts)
        # Replace spaces with underscores and remove special characters
        filename = filename.replace(' ', '_').replace('-', '_')
        
        return filename
    
    def build_tefilla(self, tefilla_type: str, target_date: date = None, force_rebuild: bool = False) -> Path:
        """Build a complete tefilla for the given date and type."""
        if target_date is None:
            target_date = date.today()
        
        # Get conditions for this date and tefilla type
        conditions = self.rule_engine.hebrew_calendar.get_date_conditions(target_date, tefilla_type)
        conditions_dict = asdict(conditions)
        
        # Filter out conditions that don't affect tefilla building for storage
        tefilla_relevant_conditions = {k: v for k, v in conditions_dict.items() 
                                     if k not in ['fast_day', 'sefirat_haomer']}
        
        # Generate checksum based on conditions
        conditions_checksum = self._generate_conditions_checksum(conditions_dict)
        
        # Generate meaningful filename
        meaningful_name = self._generate_meaningful_filename(tefilla_type, conditions_dict)
        output_file = self.output_dir / f"{meaningful_name}_{conditions_checksum}.mp3"
        
        # Check if tefilla with same conditions already exists
        if not force_rebuild:
            for cache_entry in self.tefilla_cache.values():
                if (cache_entry.get('conditions_checksum') == conditions_checksum and 
                    cache_entry.get('tefilla_type') == tefilla_type):
                    existing_file = Path(cache_entry['output_file'])
                    if existing_file.exists():
                        print(f"⚡ Reusing existing tefilla: {existing_file.name} (same conditions)")
                        return existing_file
        
        # Check if file already exists (direct file check)
        if not force_rebuild and output_file.exists():
            print(f"⚡ Using cached tefilla: {output_file.name}")
            return output_file
        
        print(f"🔨 Building tefilla: {tefilla_type} for {target_date}")
        print(f"   📋 Conditions: {conditions_dict}")
        
        # Get chunk list from rule engine
        chunk_list = self.rule_engine.build_tefilla(tefilla_type, target_date)
        
        if not chunk_list:
            raise ValueError(f"No chunks found for tefilla type: {tefilla_type}")
        
        print(f"   📋 Selected chunks: {', '.join(chunk_list)}")
        
        # Ensure all chunks are processed (auto-process missing ones)
        chunk_paths = []
        missing_chunks = []
        
        for chunk_name in chunk_list:
            if chunk_name in self.chunk_processor.chunk_cache.load_directory():
                # Chunk exists in cache, get its path
                chunk_path = self.chunk_processor.chunk_cache.get_cached_path(chunk_name)
                if chunk_path.exists():
                    chunk_paths.append(chunk_path)
                else:
                    missing_chunks.append(chunk_name)
            else:
                missing_chunks.append(chunk_name)
        
        # Process any missing chunks
        if missing_chunks:
            print(f"   🔧 Processing {len(missing_chunks)} missing chunks...")
            for chunk_name in missing_chunks:
                # Get chunk text from tts_map
                from tts_map import TEXT_MAP
                if chunk_name in TEXT_MAP:
                    chunk_text = TEXT_MAP[chunk_name]["text"]
                    print(f"   🔹 Processing missing chunk: {chunk_name}")
                    self.chunk_processor.process_chunk(chunk_name, chunk_text)
                    # Get the newly created chunk path
                    chunk_path = self.chunk_processor.chunk_cache.get_cached_path(chunk_name)
                    chunk_paths.append(chunk_path)
                else:
                    raise ValueError(f"Chunk '{chunk_name}' not found in tts_map")
        
        # Combine chunks into complete tefilla
        self._combine_chunks(chunk_paths, output_file)
        
        # Update cache with enhanced metadata
        cache_key = f"{meaningful_name}_{conditions_checksum}"
        self.tefilla_cache[cache_key] = {
            'tefilla_type': tefilla_type,
            'original_date': target_date.isoformat(),
            'original_tefilla_type': tefilla_type,
            'conditions': tefilla_relevant_conditions,  # Use filtered conditions
            'conditions_checksum': conditions_checksum,
            'chunk_list': chunk_list,
            'output_file': str(output_file),
            'meaningful_name': meaningful_name,
            'creation_timestamp': datetime.now().isoformat()
        }
        self._save_tefilla_cache()
        
        print(f"✅ Tefilla built: {output_file.name}")
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
