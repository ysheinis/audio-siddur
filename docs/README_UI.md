# Hebrew Audio Siddur - User Interface

## 🎵 For Mom - Simple Instructions

### How to Start the Program

1. **Navigate to the UI folder**: `cd ui`
2. **Double-click** on `start_siddur.bat` file
3. The program will open with a simple window
4. You'll see large buttons that are easy to click

### How to Use the Buttons

#### 🎯 **NOW Button** (Green, at the top)
- **What it does**: Plays the prayer that's appropriate for right now
- **When to use**: When you want to pray the current service
- **Example**: If it's morning, it will play Shacharis; if it's evening, it will play Maariv

#### 🌅 **Shacharis Button** (Blue)
- **What it does**: Plays the morning prayer service
- **When to use**: For morning prayers

#### ☀️ **Mincha Button** (Orange)  
- **What it does**: Plays the afternoon prayer service
- **When to use**: For afternoon prayers

#### 🌙 **Maariv Button** (Purple)
- **What it does**: Plays the evening prayer service  
- **When to use**: For evening prayers

### What Happens When You Click a Button

1. The button will show "Building..." while it prepares your prayer
2. Then it will show "Playing..." and start the audio
3. You'll hear the complete prayer service
4. When it's done, it will say "Ready to play prayers"

### If Something Goes Wrong

- **If you hear an error sound**: The program will show an error message
- **To stop a prayer**: Click the red "Stop" button
- **To close the program**: Click the X in the top-right corner

### The Program is Smart!

- It knows what day it is (weekday, Shabbat, holidays)
- It knows what time it is (morning, afternoon, evening)
- It automatically includes the right prayers for each day
- It remembers what it has already prepared, so it's faster the next time

### Technical Notes (For Setup)

- **Requirements**: Python 3.8+ with tkinter
- **Audio**: Uses Windows Media Player or system default audio player
- **Dependencies**: All required packages should be installed
- **Launch**: Navigate to `ui/` folder, then double-click `start_siddur.bat` or run `python siddur_ui.py`

### Troubleshooting

- **"Python not found"**: Install Python from python.org
- **"tkinter not available"**: Reinstall Python with tkinter support
- **Audio won't play**: Check Windows audio settings and default media player
- **Program crashes**: Check that all dependencies are installed (`pip install -r requirements.txt`)

### File Structure

```
siddur/
├── ui/
│   ├── siddur_ui.py          # Main UI application
│   └── start_siddur.bat      # Windows launcher
├── src/
│   ├── tefilla_rules.py      # Prayer rules and calendar
│   ├── tts_map.py           # Prayer text and conditions
│   ├── chunk_processor.py   # Audio processing
│   └── chunk_cache.py       # Audio caching
├── scripts/
│   └── tts_generate.py       # Core prayer generation
└── data/
    └── output/              # Generated audio files
```
