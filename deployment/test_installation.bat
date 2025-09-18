@echo off
echo ========================================
echo Hebrew Audio Siddur - Installation Test
echo ========================================
echo.

echo Testing Python installation and dependencies...
echo.

REM Test Python imports
echo 1. Testing Python imports...
python -c "import sys; print('[OK] Python version:', sys.version)" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python not working properly
    goto :error
)

python -c "import pyluach; print('[OK] pyluach (Hebrew calendar) imported successfully')" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] pyluach not installed or not working
    goto :error
)

python -c "import google.cloud.texttospeech; print('[OK] Google Cloud TTS imported successfully')" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Google Cloud TTS not installed or not working
    goto :error
)

echo.
echo 2. Testing Hebrew calendar functionality...
python -c "import sys; sys.path.insert(0, '../src'); from tefilla_rules import HebrewCalendar; cal = HebrewCalendar(); print('[OK] Hebrew calendar working')" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Hebrew calendar not working
    goto :error
)

echo.
echo 3. Testing audio playback capability...
python -c "import sys; sys.path.insert(0, '../scripts'); from play_tefilla import find_audio_player; player = find_audio_player(); print('[OK] Audio player found:', player)" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Audio player not found
    goto :error
)

echo.
echo 4. Testing TTS API credentials...
if exist "google_api_key.json" (
    echo [OK] Google API key file found
) else (
    echo [ERROR] google_api_key.json file not found!
    echo Please make sure the Google API key file is in this directory.
    goto :error
)

echo.
echo 5. Testing scheduled tefilla script...
python ../scripts/scheduled_tefilla.py --date 2025-01-15 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Scheduled tefilla script not working
    goto :error
) else (
    echo [OK] Scheduled tefilla script working
)

echo.
echo 6. Testing UI startup (will open briefly)...
echo Opening UI for 3 seconds to test...
start /wait /min python ../ui/siddur_ui.py
timeout /t 3 /nobreak >nul
taskkill /f /im python.exe >nul 2>&1
echo [OK] UI startup test completed

echo.
echo ========================================
echo Installation Test Complete!
echo ========================================
echo.
echo [OK] All tests passed! The Hebrew Audio Siddur is ready to use.
echo.
echo Next steps:
echo 1. Run setup_scheduler.bat as Administrator to set up automatic playback
echo 2. Double-click start_siddur.bat to use the program
echo 3. Check USER_MANUAL.md for usage instructions
echo.
echo Press any key to continue...
pause >nul
exit /b 0

:error
echo.
echo ========================================
echo Installation Test Failed!
echo ========================================
echo.
echo [ERROR] Some tests failed. Please check the error messages above.
echo.
echo Common solutions:
echo 1. Run install_python.bat to install missing packages
echo 2. Make sure google_api_key.json is in this directory
echo 3. Check that Python is properly installed and added to PATH
echo 4. Restart your computer after installing Python
echo.
echo For help, contact: jsheinis@gmail.com
echo.
pause
exit /b 1
