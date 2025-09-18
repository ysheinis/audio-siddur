# Hebrew Audio Siddur - User Manual

## 🎵 Quick Start

1. **Double-click** `start_siddur.bat` to open the program
2. **Click the green "NOW" button** to play the current prayer
3. **Or click specific prayer buttons** (Shacharis, Mincha, Maariv)

## 🕐 Automatic Playback

The program is set to automatically play prayers on Shabbat and Yom Tov at:
- **7:00 AM** (Shacharis - Morning prayers)
- **1:00 PM** (Mincha - Afternoon prayers) 
- **7:00 PM** (Maariv - Evening prayers)

The program is smart - it only plays on Shabbat and Yom Tov. On regular weekdays, it runs silently in the background.

## 🎮 Manual Playback

### Main Buttons:
- **🟢 Green "NOW" button**: Plays the prayer appropriate for the current time
- **🔵 Blue "Shacharis" button**: Morning prayers
- **🟠 Orange "Mincha" button**: Afternoon prayers
- **🟣 Purple "Maariv" button**: Evening prayers

### What Happens When You Click:
1. The button shows "Building..." while preparing your prayer
2. Then shows "Playing..." and starts the audio
3. You'll hear the complete prayer service
4. When done, it says "Ready to play prayers"

## 📅 The Program is Smart!

- **Knows what day it is** (weekday, Shabbat, holidays)
- **Knows what time it is** (morning, afternoon, evening)
- **Automatically includes the right prayers** for each day
- **Remembers what it prepared** so it's faster the next time
- **Includes seasonal prayers** (like rain prayers in winter)

## 🎧 Audio Controls

- **Volume**: Use your computer's volume controls
- **Stop**: Click the red "Stop" button to stop playback
- **Close**: Click the X in the top-right corner to close the program

## 📝 Logs and Monitoring

The program keeps logs of its activity:
- **`scheduled_tefilla.log`**: Shows when automatic prayers were played
- You can check this file to see if the automatic system is working

## 🔧 Troubleshooting Guide

### Audio Won't Play
- **Check Windows volume**: Make sure your computer's volume is up
- **Check audio device**: Make sure speakers or headphones are connected
- **Test other audio**: Try playing music or videos to test your audio
- **Restart the program**: Close and reopen the program
- **Run test script**: Double-click `test_installation.bat` to check setup

### Program Won't Start
- **Check Python**: The program needs Python to run
- **Run test script**: Double-click `test_installation.bat` to check setup
- **Restart computer**: Sometimes a restart helps
- **Check for updates**: Make sure all files are properly installed

### Automatic Playback Not Working
- **Check Task Scheduler**: 
  - Press Windows key + R, type `taskschd.msc`, press Enter
  - Look for "Hebrew Siddur" tasks
  - Make sure they're enabled and set to run daily
- **Check log file**: Look at `scheduled_tefilla.log` for error messages
- **Test manually**: Run `python scheduled_tefilla.py` to test

### Error Messages
- **"Python not found"**: Python needs to be installed and added to PATH
- **"Audio player not found"**: Windows Media Player or default audio player issue
- **"TTS API error"**: Internet connection or Google API key issue
- **"File not found"**: Some program files may be missing

### Performance Issues
- **Slow startup**: First time may be slow as it prepares audio
- **Audio quality**: Make sure you have good internet connection for TTS
- **Storage space**: Make sure you have at least 2GB free disk space

### Date and Time Issues
- **Wrong prayers**: Make sure your computer's date and time are correct
- **Time zone**: The program uses your computer's local time
- **Hebrew calendar**: The program automatically calculates Hebrew dates

## 🆘 Getting Help

### Before Contacting Support:
1. **Try restarting** the program
2. **Check the log files** for error messages
3. **Run the test script** (`test_installation.bat`)
4. **Check your internet connection**
5. **Verify your computer's date and time**

### Contact Information:
- **Email**: jsheinis@gmail.com
- **Subject**: "Hebrew Siddur - [Brief description of issue]"
- **Include**: 
  - What you were trying to do
  - What error message you saw (if any)
  - Contents of `scheduled_tefilla.log` (if relevant)

### Emergency Contact:
If the program stops working completely and you need prayers immediately:
- Use the manual buttons in the program
- Or contact jsheinis@gmail.com for urgent support

## 📚 Additional Information

### Supported Holidays:
- Rosh Hashana, Yom Kippur
- Sukkot, Shmini Atzeret
- Pesach, Shavuot
- Chanukkah, Purim
- Rosh Chodesh (New Month)

### Prayer Types:
- **Shacharis**: Morning prayers (includes full service)
- **Mincha**: Afternoon prayers (shorter service)
- **Maariv**: Evening prayers (includes Shema)

### Seasonal Features:
- **Winter prayers**: Includes rain prayers (VeTen Tal UMattar)
- **Summer prayers**: Includes dew prayers (Mashiv HaRuach)
- **Holiday prayers**: Special insertions for each holiday

---

*This manual covers the basic operation of the Hebrew Audio Siddur. For technical support or advanced features, contact jsheinis@gmail.com.*
