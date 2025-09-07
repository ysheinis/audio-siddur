"""
Chunk processing module for Hebrew Audio Siddur.
Handles the complete process of converting Hebrew text chunks to audio files.
"""

import os
import re
from pathlib import Path
from google.cloud import texttospeech
from pydub import AudioSegment
from chunk_cache import ChunkCache


class ChunkProcessor:
    """Processes Hebrew text chunks into audio files with caching."""
    
    def __init__(self, cache_dir: Path = None, temp_dir: Path = None, credentials_file: str = None):
        # Set up Google Cloud credentials
        if credentials_file:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_file
        
        # Set up directories
        self.cache_dir = cache_dir or Path("chunk_cache")
        self.temp_dir = temp_dir or Path("temp_sentences")
        self.directory_file = self.cache_dir / "directory.json"
        
        # Initialize chunk cache
        self.chunk_cache = ChunkCache(self.cache_dir, self.directory_file)
        
        # Set up TTS client and parameters
        self.client = texttospeech.TextToSpeechClient()
        self.voice_params = texttospeech.VoiceSelectionParams(
            language_code="he-IL",
            name="he-IL-Standard-B",
            ssml_gender=texttospeech.SsmlVoiceGender.MALE,
        )
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            pitch=-4.0,
            speaking_rate=0.8
        )
        
        # Create directories
        self.cache_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        
        # Hebrew text processing patterns
        self.HEBREW_LETTER = r'[\u05D0-\u05EA]'
        self.HEBREW_MARK = r'[\u0591-\u05C7]'  # includes vowels, dagesh, meteg, taamim
        self.MARK_OPT = f'{self.HEBREW_MARK}*'
        self.WORD_END = r'(?=\s|$|[.,;!?־״"])'
        
        self.SUFFIXES = [
            ('\u05E0' + self.MARK_OPT + '\u05D5' + self.MARK_OPT),  # נוּ
            ('\u05E0' + self.MARK_OPT + '\u05D9' + self.MARK_OPT),  # נִי
            ('\u05DB' + self.MARK_OPT + '\u05DD' + self.MARK_OPT),  # כֶם
            ('\u05E0' + self.MARK_OPT + '\u05D5' + self.MARK_OPT),  # נוֹ
        ]
        
        # TTS fixes for problematic Hebrew characters
        self.TTS_FIXES = {
            "כְוֹל": "כֹּל",
            "כָל": "כֹּל", 
            "כָּל": "כֹּל",
            "ה'": "אֲדֹנָי",
            "יְהֹוָה": "אֲדֹנָי",
        }
    
    def clean_text(self, text):
        """Clean Hebrew text for TTS processing."""
        # Apply manual fixes
        for wrong, right in self.TTS_FIXES.items():
            text = text.replace(wrong, right)

        # Remove meteg and cantillation marks
        text = re.sub(r"[\u0591-\u05AF\u05BD]", "", text)

        # Fix stress by inserting zero-width joiner before suffix
        for suffix in self.SUFFIXES:
            pattern = re.compile(
                rf'((?:{self.HEBREW_LETTER}{self.MARK_OPT})+?)' +  # word base (non-greedy)
                f'({suffix})' +                          # the suffix
                self.WORD_END                                 # followed by space/punct/EOL
            )
            text = pattern.sub('\\1\u200D\\2', text)

        return text
    
    def ssmlify(self, text: str, word_pause_ms=50, punctuation_pause_ms=400) -> str:
        """Convert text to SSML with proper timing."""
        # Step 1: Split original text into words
        words = text.split()

        # Step 2: Rejoin with word breaks
        spaced_text = f'<break time="{word_pause_ms}ms"/>'.join(words)

        # Step 3: Add punctuation breaks (after word breaks are inserted)
        spaced_text = spaced_text.replace('.', f'.<break time="{punctuation_pause_ms}ms"/>')
        spaced_text = spaced_text.replace('?', f'?<break time="{punctuation_pause_ms}ms"/>')
        spaced_text = spaced_text.replace('!', f'!<break time="{punctuation_pause_ms}ms"/>')
        spaced_text = spaced_text.replace(':', f'!<break time="{punctuation_pause_ms}ms"/>')
        spaced_text = spaced_text.replace(',', f',<break time="200ms"/>')

        return f"<speak>{spaced_text}</speak>"
    
    def split_into_sentences(self, text):
        """Split text into sentences."""
        # Split on . ! ? : followed by space/newline
        return [s.strip() for s in re.split(r'(?<=[.!?:])\s+', text.strip()) if s]
    
    def synthesize_sentence(self, sentence: str, index: int) -> Path:
        """Synthesize a single sentence to audio."""
        ssml = self.ssmlify(sentence)
        synthesis_input = texttospeech.SynthesisInput(ssml=ssml)
        response = self.client.synthesize_speech(
            input=synthesis_input,
            voice=self.voice_params,
            audio_config=self.audio_config
        )
        temp_file = self.temp_dir / f"sentence_{index:03}.mp3"
        with open(temp_file, "wb") as f:
            f.write(response.audio_content)
        return temp_file
    
    def combine_mp3s(self, mp3_paths, output_path):
        """Combine multiple MP3 files into one."""
        combined = AudioSegment.empty()
        for path in mp3_paths:
            combined += AudioSegment.from_mp3(path)
        combined.export(output_path, format="mp3")
    
    def process_chunk(self, key, text):
        """Process a text chunk into an audio file with caching."""
        print(f"🔹 Processing chunk: {key}")
        cleaned_text = self.clean_text(text)
        text_checksum = self.chunk_cache.calculate_text_checksum(cleaned_text)
        
        # Check if chunk is already cached
        if self.chunk_cache.is_chunk_cached(key, text_checksum):
            cached_path = self.chunk_cache.get_cached_path(key)
            print(f"   ⚡ Using cached chunk: {cached_path}")
            return cached_path
        
        print(f"   🎵 Generating new audio (checksum: {text_checksum[:8]}...)")
        sentences = self.split_into_sentences(cleaned_text)

        sentence_files = []
        for i, sentence in enumerate(sentences):
            print(f"   ↳ Synthesizing sentence {i+1}/{len(sentences)}")
            sentence_file = self.synthesize_sentence(sentence, i)
            sentence_files.append(sentence_file)

        # Save to cache directory
        chunk_mp3_path = self.chunk_cache.get_cached_path(key)
        self.combine_mp3s(sentence_files, chunk_mp3_path)

        # Update directory with new chunk
        self.chunk_cache.update_directory(key, text_checksum)

        # Clean up temporary files
        for f in sentence_files:
            f.unlink()

        print(f"✅ Chunk cached: {chunk_mp3_path}")
        return chunk_mp3_path
