# Hebrew Audio Siddur - Complete System

A comprehensive Hebrew prayer audio system that automatically generates and plays complete tefillos (prayer services) based on the Hebrew calendar, time of day, and Halachic rules.

## 🎯 Overview

This system provides:
- **Automatic Hebrew calendar detection** (Shabbat, holidays, Rosh Chodesh, etc.)
- **Smart tefilla generation** based on Halachic rules
- **Audio caching** for fast playback
- **User-friendly interface** for manual playback
- **Automated scheduling** for Shabbat and Yom Tov
- **Command-line tools** for advanced users

## 🏗️ System Architecture

### Core Components

1. **Hebrew Calendar Engine** (`tefilla_rules.py`)
   - Calculates Hebrew dates and holidays
   - Determines prayer conditions (Shabbat, Yom Tov, Rosh Chodesh, etc.)
   - Handles seasonal variations (Mashiv HaRuach, VeTen Tal UMattar)

2. **Prayer Text System** (`tts_map.py`)
   - Contains all prayer texts and their conditions
   - Maps tefilla types to appropriate prayer chunks
   - Defines when each prayer component should be recited

3. **Audio Processing** (`chunk_processor.py`, `tefilla_builder.py`)
   - Converts Hebrew text to speech using TTS
   - Caches individual prayer chunks for efficiency
   - Combines chunks into complete tefillos

4. **User Interface** (`siddur_ui.py`)
   - Simple GUI for manual prayer playback
   - Large buttons for easy use
   - Real-time status updates

5. **Automation** (`scheduled_tefilla.py`)
   - Windows Task Scheduler integration
   - Automatic playback on Shabbat and Yom Tov
   - Silent operation on regular days

## 📁 File Structure

```
siddur/
├── 📁 src/                    # Core Python source files
│   ├── tefilla_rules.py       # Hebrew calendar & prayer rules
│   ├── tts_map.py            # Prayer texts & conditions
│   ├── chunk_processor.py    # TTS audio processing
│   ├── tefilla_builder.py    # Complete tefilla assembly
│   └── chunk_cache.py        # Cache management
│
├── 📁 scripts/               # Command-line tools
│   ├── tts_generate.py       # Main generation script
│   ├── play_tefilla.py       # Manual tefilla player
│   └── scheduled_tefilla.py  # Automated scheduler
│
├── 📁 ui/                    # User interface
│   ├── siddur_ui.py          # GUI application
│   └── start_siddur.bat      # Windows launcher
│
├── 📁 tests/                 # Test files
│   ├── test_rule_engine.py   # Hebrew calendar tests
│   └── test_tts_map_validation.py # Prayer text validation
│
├── 📁 deployment/            # Deployment scripts and docs
│   ├── install_python.bat    # Installation script
│   ├── test_installation.bat # Installation verification
│   ├── setup_scheduler.bat   # Windows Scheduler setup
│   ├── create_deployment_package.bat # Package creation
│   ├── DEPLOYMENT_CHECKLIST.md # Deployment guide
│   └── USER_MANUAL.md        # User manual
│
├── 📁 config/                # Configuration files
│   ├── google_api_key.json   # TTS credentials
│   ├── requirements.txt      # Python dependencies
│   └── requirements_ui.txt   # UI dependencies
│
├── 📁 data/                  # Generated content
│   ├── chunk_cache/          # Individual prayer chunks
│   │   └── directory.json    # Chunk metadata
│   ├── output/               # Complete tefillos
│   │   └── directory.json    # Tefilla metadata
│   └── temp_sentences/       # Temporary files
│
├── 📁 docs/                  # Documentation
│   ├── README.md             # This file
│   └── README_UI.md          # User interface guide
│
└── 📁 logs/                  # Log files
    └── scheduled_tefilla.log # Scheduler activity
```

## 🚀 Quick Start

### For End Users (Mom)

1. **Navigate to UI folder**: `cd ui`
2. **Double-click** `start_siddur.bat`
3. **Click the green "NOW" button** to play the current prayer
4. **Or click specific prayer buttons** (Shacharis, Mincha, Maariv)

### For Developers

1. **Install dependencies**:
   ```bash
   cd config
   pip install -r requirements.txt
   ```

2. **Run tests**:
   ```bash
   cd tests
   python -m unittest test_rule_engine.py -v
   ```

3. **Generate tefillos**:
   ```bash
   cd scripts
   python tts_generate.py --date 2025-09-23 --tefilla shacharis
   ```

4. **Play specific tefilla**:
   ```bash
   cd scripts
   python play_tefilla.py --date 2025-09-23 --tefilla maariv
   ```

## 🎵 Key Features

### Smart Calendar Detection
- **Automatic Hebrew date calculation**
- **Holiday detection** (Rosh Hashana, Yom Kippur, Sukkot, Pesach, Shavuot)
- **Shabbat recognition**
- **Rosh Chodesh detection**
- **Seasonal periods** (Aseret Yemei Teshuvah, Mashiv HaRuach, VeTen Tal UMattar)

### Intelligent Prayer Assembly
- **Context-aware tefilla building** based on date and time
- **Proper Hallel selection** (full, partial, or none)
- **Correct Shmoneh Esreh variations** (weekday, Shabbat, holiday)
- **Seasonal insertions** (Mashiv HaRuach, VeTen Tal UMattar)
- **Holiday-specific prayers** (Al Hanisim, Yaale VeYavo)

### Efficient Caching System
- **Chunk-based caching** - individual prayers cached separately
- **Condition-based deduplication** - identical tefillos reused
- **Meaningful filenames** - human-readable tefilla names
- **Metadata tracking** - complete audit trail

### Multiple Access Methods
- **GUI Interface** - Simple buttons for easy use
- **Command Line** - Flexible scripting and automation
- **Scheduled Playback** - Automatic Shabbat/Yom Tov tefillos
- **Manual Playback** - On-demand prayer services

## 🔧 Advanced Usage

### Command Line Tools

#### Generate Tefillos
```bash
cd scripts

# Single tefilla
python tts_generate.py --date 2025-09-23 --tefilla shacharis

# Date range with all tefillos
python tts_generate.py --date-range 2025-09-23 2025-09-25 --all-tefillos

# Force rebuild
python tts_generate.py --date 2025-09-23 --tefilla maariv --force
```

#### Play Tefillos
```bash
cd scripts

# Current tefilla
python play_tefilla.py

# Specific date and type
python play_tefilla.py --date 2025-09-23 --tefilla shacharis

# List available tefillos
python play_tefilla.py --date 2025-09-23 --list

# Use specific audio player
python play_tefilla.py --player "C:\Program Files\VLC\vlc.exe"
```

#### Automated Scheduling
```bash
cd scripts

# Test the scheduler
python scheduled_tefilla.py

# Check logs
type ../logs/scheduled_tefilla.log
```

### Windows Task Scheduler Setup

1. **Create 3 daily tasks**:
   - **7:00 AM** - Shacharis time
   - **1:00 PM** - Mincha time  
   - **7:00 PM** - Maariv time

2. **Task configuration**:
   - **Program**: `python`
   - **Arguments**: `scripts\scheduled_tefilla.py`
   - **Start in**: `C:\HebrewSiddur` (or your installation directory)

3. **The script will**:
   - Check if today is Shabbat or Yom Tov
   - Play appropriate tefilla if yes
   - Silently exit if no
   - Log all activity to `scheduled_tefilla.log`

## 🧪 Testing & Validation

### Run All Tests
```bash
cd tests
python -m unittest test_rule_engine.py -v
python -m unittest test_tts_map_validation.py -v
```

### Test Specific Components
```bash
cd tests

# Test Hebrew calendar logic
python -m unittest test_rule_engine.TestHebrewCalendar.test_major_holidays_2025 -v

# Validate prayer text mapping
python -m unittest test_tts_map_validation.TestTtsMapValidation.test_all_condition_values_supported -v
```

## 📊 System Capabilities

### Supported Calendar Features
- ✅ **All major holidays** (Rosh Hashana, Yom Kippur, Sukkot, Pesach, Shavuot)
- ✅ **Shabbat detection**
- ✅ **Rosh Chodesh** (1-day and 2-day months)
- ✅ **Chol Hamoed** (intermediate days)
- ✅ **Aseret Yemei Teshuvah** (10 days of repentance)
- ✅ **Mashiv HaRuach** (winter prayer insertion)
- ✅ **VeTen Tal UMattar** (rain prayer insertion)
- ✅ **Leap year handling**

### Prayer Variations
- ✅ **Weekday tefillos** (full Shmoneh Esreh)
- ✅ **Shabbat tefillos** (special Shabbat prayers)
- ✅ **Holiday tefillos** (holiday-specific insertions)
- ✅ **Hallel variations** (full, partial, none)
- ✅ **Seasonal insertions** (Mashiv HaRuach, VeTen Tal UMattar)

### Audio Features
- ✅ **High-quality TTS** (Google Cloud Text-to-Speech)
- ✅ **Hebrew pronunciation**
- ✅ **Efficient caching**
- ✅ **Multiple audio players** (Windows Media Player, VLC, system default)
- ✅ **Automatic chunk processing**

## 🔍 Troubleshooting

### Common Issues

#### Audio Won't Play
- Check Windows audio settings
- Verify default media player
- Run `python test_play.py` to test playback methods

#### Tefilla Not Building
- Check TTS credentials in `innate-rite-*.json`
- Verify internet connection for TTS API
- Check `data/chunk_cache/directory.json` for processing status

#### Calendar Issues
- Run tests: `python -m unittest test_rule_engine.py -v`
- Check Hebrew date calculations
- Verify holiday date accuracy

#### Scheduler Problems
- Check `scheduled_tefilla.log` for activity
- Verify Windows Task Scheduler configuration
- Test manually: `python scheduled_tefilla.py`

### Log Files
- **`logs/scheduled_tefilla.log`** - Automated scheduler activity
- **`data/chunk_cache/directory.json`** - Audio chunk metadata
- **`data/output/directory.json`** - Complete tefilla metadata

## 🛠️ Development

### Adding New Prayers
1. **Add text to `src/tts_map.py`** with appropriate conditions
2. **Update tests** in `tests/test_tts_map_validation.py`
3. **Test with** `cd scripts && python tts_generate.py --date [test_date] --tefilla [type]`

### Modifying Calendar Logic
1. **Update `src/tefilla_rules.py`** with new rules
2. **Add tests** in `tests/test_rule_engine.py`
3. **Run comprehensive tests** to ensure accuracy

### Extending Audio Features
1. **Modify `src/chunk_processor.py`** for new TTS options
2. **Update `scripts/play_tefilla.py`** for new audio players
3. **Test with** `cd scripts && python play_tefilla.py`

## 📝 License & Credits

- **Hebrew Calendar**: `pyluach` library
- **Text-to-Speech**: Google Cloud Text-to-Speech API
- **UI Framework**: Python tkinter
- **Audio Processing**: Python subprocess with system players

---

*This system provides a complete solution for automated Hebrew prayer audio generation and playback, combining traditional Halachic rules with modern technology for ease of use.*
