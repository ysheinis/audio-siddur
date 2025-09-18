# Hebrew Audio Siddur - Deployment Checklist

## 🏠 **Phase 1: Preparation on Your Computer**

### 1.1 **Generate All Required Audio Content**
```bash
# Generate all chunks for the next year
cd scripts
python tts_generate.py --all-chunks

# Build all tefillos for the next year (2025-2026)
python tts_generate.py --date-range 2025-01-01 2026-12-31 --all-tefillos

# Verify cache is complete
python -c "
import sys; sys.path.append('../src')
from chunk_processor import ChunkProcessor
from tefilla_builder import TefillaBuilder
cp = ChunkProcessor()
tb = TefillaBuilder(cp)
print(f'Chunks: {len(cp.get_chunk_cache())}')
print(f'Tefillos: {len(tb.get_tefilla_cache())}')
"
```

### 1.2 **Test Everything Works**
```bash
# Run all tests
cd tests
python -m unittest test_rule_engine.py -v
python -m unittest test_tts_map_validation.py -v

# Test UI
cd ../ui
python siddur_ui.py

# Test command line tools
cd ../scripts
python play_tefilla.py --date 2025-09-23 --tefilla shacharis
python scheduled_tefilla.py --date 2025-09-23
```

### 1.3 **Create Deployment Package**
```bash
# Run the automated deployment package script
cd deployment
.\create_deployment_package.bat
```

**That's it!** The script automatically:
- ✅ Creates deployment directory
- ✅ Copies all Python files, batch files, and documentation
- ✅ Copies generated audio chunks and tefillos
- ✅ Creates requirements file
- ✅ Creates `siddur_deployment.zip` for transfer

---

## 🖥️ **Phase 2: Installation on Mom's Computer**

### 2.1 **System Requirements Check**
- [ ] Windows 10 or 11
- [ ] At least 2GB free disk space
- [ ] Internet connection (for initial setup)
- [ ] Audio output device (speakers/headphones)

### 2.2 **Install Python**
- [ ] Download Python 3.8+ from https://python.org
- [ ] **IMPORTANT**: Check "Add Python to PATH" during installation
- [ ] Verify installation: Open Command Prompt and run `python --version`

### 2.3 **Extract and Install Siddur**
- [ ] Extract `siddur_deployment.zip` to `C:\HebrewSiddur\`
- [ ] Open Command Prompt as Administrator
- [ ] Navigate to installation directory: `cd C:\HebrewSiddur`
- [ ] Run installation script: `cd deployment && install_python.bat`
- [ ] Run test script: `cd deployment && test_installation.bat`

### 2.4 **Setup Automatic Playback**
- [ ] Run `cd deployment && setup_scheduler.bat` as Administrator
- [ ] Verify tasks were created in Windows Task Scheduler:
  - [ ] Open Task Scheduler (search in Start menu)
  - [ ] Look for "Hebrew Siddur" tasks
  - [ ] Verify they're set to run daily at correct times
- [ ] Test scheduler manually:
  ```bash
  cd scripts
  python scheduled_tefilla.py --date 2025-09-23
  ```
- [ ] Check `logs/scheduled_tefilla.log` for activity

### 2.5 **Create Desktop Shortcut**
- [ ] Right-click on `ui/start_siddur.bat`
- [ ] Select "Create shortcut"
- [ ] Move shortcut to Desktop
- [ ] Rename shortcut to "Hebrew Siddur"

### 2.6 **Final Testing**
- [ ] Test on a Shabbat or Yom Tov (or simulate by changing system date)
- [ ] Verify automatic playback works at scheduled times
- [ ] Test manual playback on regular weekdays
- [ ] Verify different prayer types work correctly
- [ ] Check that audio quality is acceptable

### 2.7 **User Training**
- [ ] Show mom how to use the UI buttons
- [ ] Explain automatic playback schedule
- [ ] Show how to check logs if needed
- [ ] Provide contact information for support
- [ ] Leave printed copy of USER_MANUAL.md

---

## 🔧 **Phase 3: Post-Installation Maintenance**

### 3.1 **Regular Updates**
- [ ] Plan to update tefillos annually (before Rosh Hashana)
- [ ] Update Hebrew calendar data if needed
- [ ] Update TTS credentials if they expire

### 3.2 **Monitoring**
- [ ] Check `scheduled_tefilla.log` monthly for any issues
- [ ] Verify tasks are still running in Task Scheduler
- [ ] Test manual playback occasionally

### 3.3 **Backup**
- [ ] Backup the entire `C:\HebrewSiddur\` directory
- [ ] Include `data\chunk_cache\` and `data\output\` directories
- [ ] Store backup in case of system issues

---

## 🚨 **Troubleshooting Guide**

### Common Issues:

**"Python not found"**
- Reinstall Python with "Add to PATH" checked
- Restart computer after installation

**"Audio won't play"**
- Check Windows audio settings
- Test with other audio applications
- Run `test_installation.bat`

**"Scheduled tasks not running"**
- Check Task Scheduler for task status
- Verify tasks are enabled
- Check `logs/scheduled_tefilla.log` for errors

**"TTS API errors"**
- Verify `config/google_api_key.json` file is present
- Check internet connection
- Verify Google Cloud credentials are valid

**"UI won't start"**
- Run `cd deployment && test_installation.bat`
- Check for Python/tkinter issues
- Try running `cd ui && python siddur_ui.py` directly

---

## 📞 **Support Information**

- **Installation Issues**: jsheinis@gmail.com
- **Technical Support**: jsheinis@gmail.com  
- **Emergency Contact**: jsheinis@gmail.com

**Log Files to Check:**
- `logs/scheduled_tefilla.log` - Automatic playback activity
- `data/chunk_cache/directory.json` - Audio chunk status
- `data/output/directory.json` - Complete tefilla status

**Key Files:**
- `ui/start_siddur.bat` - Main program launcher
- `ui/siddur_ui.py` - User interface
- `scripts/scheduled_tefilla.py` - Automatic playback
- `scripts/play_tefilla.py` - Manual playback

---

## 🎯 **Quick Summary**

### **On Your Computer:**
1. Generate audio content: `cd scripts && python tts_generate.py --all-chunks`
2. Build tefillos: `cd scripts && python tts_generate.py --date-range 2025-01-01 2026-12-31 --all-tefillos`
3. Create package: `cd deployment && .\create_deployment_package.bat`

### **On Mom's Computer:**
1. Install Python (with PATH)
2. Extract `siddur_deployment.zip` to `C:\HebrewSiddur\`
3. Run `install_python.bat`
4. Run `test_installation.bat`
5. Run `setup_scheduler.bat` as Administrator
6. Create desktop shortcut
7. Test and train user

**That's it!** The automated scripts handle all the complex setup.
