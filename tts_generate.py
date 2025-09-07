import os
import re
import shutil
import hashlib
import json
from pathlib import Path
from google.cloud import texttospeech
from pydub import AudioSegment

# --- CONFIGURATION ---

from tts_map import TEXT_MAP
from tts_audio_groups import AUDIO_GROUPS  # Optional
TTS_FIXES = {
    "כְוֹל": "כֹּל",  # Add known problematic substitutions here
    "כָל": "כֹּל",
    "כָּל": "כֹּל",
    "ה'": "אֲדֹנָי",
    "יְהֹוָה": "אֲדֹנָי",
}

CHUNK_CACHE_DIR = Path("chunk_cache")
GROUP_OUTPUT_DIR = Path("output")
TEMP_DIR = Path("temp_sentences")
CHUNK_DIRECTORY_FILE = CHUNK_CACHE_DIR / "directory.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "innate-rite-449719-j9-e3536a2d6cb9.json"

# --- SETUP ---

client = texttospeech.TextToSpeechClient()
CHUNK_CACHE_DIR.mkdir(exist_ok=True)
GROUP_OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

voice_params = texttospeech.VoiceSelectionParams(
    language_code="he-IL",
    name="he-IL-Standard-B",
    ssml_gender=texttospeech.SsmlVoiceGender.MALE,
)

audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.MP3,
    pitch=-4.0,
    speaking_rate=0.8
)

# --- HELPERS ---

def calculate_text_checksum(text: str) -> str:
    """Calculate SHA-256 checksum of the cleaned text."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def load_chunk_directory() -> dict:
    """Load the chunk directory from JSON file."""
    if CHUNK_DIRECTORY_FILE.exists():
        try:
            with open(CHUNK_DIRECTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}

def save_chunk_directory(directory: dict):
    """Save the chunk directory to JSON file."""
    with open(CHUNK_DIRECTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(directory, f, indent=2, ensure_ascii=False)

def is_chunk_cached(chunk_name: str, text_checksum: str) -> bool:
    """Check if a chunk with the given checksum is already cached."""
    directory = load_chunk_directory()
    if chunk_name in directory:
        cached_checksum = directory[chunk_name].get('checksum')
        cached_file = CHUNK_CACHE_DIR / f"{chunk_name}.mp3"
        return (cached_checksum == text_checksum and cached_file.exists())
    return False

def update_chunk_directory(chunk_name: str, text_checksum: str):
    """Update the directory with a new chunk entry."""
    directory = load_chunk_directory()
    directory[chunk_name] = {
        'checksum': text_checksum,
        'timestamp': str(Path().cwd())  # Simple timestamp placeholder
    }
    save_chunk_directory(directory)

def show_cache_stats():
    """Display cache statistics."""
    directory = load_chunk_directory()
    cached_files = list(CHUNK_CACHE_DIR.glob("*.mp3"))
    
    print(f"\n📊 Cache Statistics:")
    print(f"   📁 Cached chunks: {len(cached_files)}")
    print(f"   📋 Directory entries: {len(directory)}")
    
    if cached_files:
        total_size = sum(f.stat().st_size for f in cached_files)
        print(f"   💾 Total cache size: {total_size / (1024*1024):.1f} MB")

HEBREW_LETTER = r'[\u05D0-\u05EA]'
HEBREW_MARK   = r'[\u0591-\u05C7]'  # includes vowels, dagesh, meteg, taamim
MARK_OPT      = f'{HEBREW_MARK}*'
WORD_END      = r'(?=\s|$|[.,;!?־״”])'

SUFFIXES = [
    ('\u05E0' + MARK_OPT + '\u05D5' + MARK_OPT),  # נוּ
    ('\u05E0' + MARK_OPT + '\u05D9' + MARK_OPT),  # נִי
    ('\u05DB' + MARK_OPT + '\u05DD' + MARK_OPT),  # כֶם
    ('\u05E0' + MARK_OPT + '\u05D5' + MARK_OPT),  # נוֹ
]

def clean_text(text):
    # Apply manual fixes (your TTS_FIXES map)
    for wrong, right in TTS_FIXES.items():
        text = text.replace(wrong, right)

    # Remove meteg and cantillation marks
    text = re.sub(r"[\u0591-\u05AF\u05BD]", "", text)

    # Fix stress by inserting zero-width joiner before suffix
    for suffix in SUFFIXES:
        pattern = re.compile(
            rf'((?:{HEBREW_LETTER}{MARK_OPT})+?)' +  # word base (non-greedy)
            f'({suffix})' +                          # the suffix
            WORD_END                                 # followed by space/punct/EOL
        )
        text = pattern.sub('\\1\u200D\\2', text)

    return text


def ssmlify(text: str, word_pause_ms=50, punctuation_pause_ms=400) -> str:
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

def split_into_sentences(text):
    # Split on . ! ? : followed by space/newline
    return [s.strip() for s in re.split(r'(?<=[.!?:])\s+', text.strip()) if s]

def synthesize_sentence(sentence: str, index: int) -> Path:
    ssml = ssmlify(sentence)
    synthesis_input = texttospeech.SynthesisInput(ssml=ssml)
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice_params,
        audio_config=audio_config
    )
    temp_file = TEMP_DIR / f"sentence_{index:03}.mp3"
    with open(temp_file, "wb") as f:
        f.write(response.audio_content)
    return temp_file

def combine_mp3s(mp3_paths, output_path):
    combined = AudioSegment.empty()
    for path in mp3_paths:
        combined += AudioSegment.from_mp3(path)
    combined.export(output_path, format="mp3")

# --- MAIN PROCESSING ---

def process_chunk(key, text):
    print(f"🔹 Processing chunk: {key}")
    cleaned_text = clean_text(text)
    text_checksum = calculate_text_checksum(cleaned_text)
    
    # Check if chunk is already cached
    if is_chunk_cached(key, text_checksum):
        cached_path = CHUNK_CACHE_DIR / f"{key}.mp3"
        print(f"   ⚡ Using cached chunk: {cached_path}")
        return cached_path
    
    print(f"   🎵 Generating new audio (checksum: {text_checksum[:8]}...)")
    sentences = split_into_sentences(cleaned_text)

    sentence_files = []
    for i, sentence in enumerate(sentences):
        print(f"   ↳ Synthesizing sentence {i+1}/{len(sentences)}")
        sentence_file = synthesize_sentence(sentence, i)
        sentence_files.append(sentence_file)

    # Save to cache directory
    chunk_mp3_path = CHUNK_CACHE_DIR / f"{key}.mp3"
    combine_mp3s(sentence_files, chunk_mp3_path)

    # Update directory with new chunk
    update_chunk_directory(key, text_checksum)

    # Clean up temporary files
    for f in sentence_files:
        f.unlink()

    print(f"✅ Chunk cached: {chunk_mp3_path}")
    return chunk_mp3_path

def process_group(group_key, chunk_keys):
    print(f"\n📦 Combining group: {group_key}")
    chunk_paths = [CHUNK_CACHE_DIR / f"{k}.mp3" for k in chunk_keys]
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
        process_chunk(key, text)

    # Show cache statistics
    show_cache_stats()

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
