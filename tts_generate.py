import os
import re
import shutil
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

CHUNK_OUTPUT_DIR = GROUP_OUTPUT_DIR = Path("output")
TEMP_DIR = Path("temp_sentences")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "innate-rite-449719-j9-e3536a2d6cb9.json"

# --- SETUP ---

client = texttospeech.TextToSpeechClient()
CHUNK_OUTPUT_DIR.mkdir(exist_ok=True)
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
    text = clean_text(text)
    sentences = split_into_sentences(text)

    sentence_files = []
    for i, sentence in enumerate(sentences):
        print(f"   ↳ Synthesizing sentence {i+1}/{len(sentences)}")
        sentence_file = synthesize_sentence(sentence, i)
        sentence_files.append(sentence_file)

    chunk_mp3_path = CHUNK_OUTPUT_DIR / f"{key}.mp3"
    combine_mp3s(sentence_files, chunk_mp3_path)

    for f in sentence_files:
        f.unlink()

    print(f"✅ Chunk saved: {chunk_mp3_path}")
    return chunk_mp3_path

def process_group(group_key, chunk_keys):
    print(f"\n📦 Combining group: {group_key}")
    chunk_paths = [CHUNK_OUTPUT_DIR / f"{k}.mp3" for k in chunk_keys]
    missing = [str(p) for p in chunk_paths if not p.exists()]
    if missing:
        print(f"❌ Missing chunk MP3s: {missing}")
        return

    group_path = GROUP_OUTPUT_DIR / f"{group_key}.mp3"
    combine_mp3s(chunk_paths, group_path)
    print(f"🎉 Group saved: {group_path}")

# --- ENTRY POINT ---

def main():
    for key, text in TEXT_MAP.items():
        process_chunk(key, text)

    if 'AUDIO_GROUPS' in globals():
        for group_key, chunk_keys in AUDIO_GROUPS.items():
            process_group(group_key, chunk_keys)

    shutil.rmtree(TEMP_DIR)

if __name__ == "__main__":
    main()
