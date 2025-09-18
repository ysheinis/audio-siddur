@echo off
echo ========================================
echo Hebrew Audio Siddur - Installation
echo ========================================
echo.

REM Check if Python is already installed
echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Python is already installed.
    python --version
    echo.
) else (
    echo ❌ Python not found!
    echo.
    echo Please install Python 3.8 or higher from:
    echo https://www.python.org/downloads/
    echo.
    echo IMPORTANT: During installation, make sure to check:
    echo "Add Python to PATH" or "Add Python to environment variables"
    echo.
    echo After installing Python, restart this script.
    echo.
    pause
    exit /b 1
)

REM Check if pip is available
echo Checking pip (Python package installer)...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip not found! Please reinstall Python with pip included.
    pause
    exit /b 1
)
echo ✓ pip is available.
echo.

REM Install required packages
echo Installing required Python packages...
echo This may take a few minutes...
echo.

REM Install packages one by one with error checking
echo Installing python-dateutil...
pip install python-dateutil>=2.8.0
if %errorlevel% neq 0 (
    echo ❌ Failed to install python-dateutil
    pause
    exit /b 1
)

echo Installing pyluach (Hebrew calendar)...
pip install pyluach>=2.0.0
if %errorlevel% neq 0 (
    echo ❌ Failed to install pyluach
    pause
    exit /b 1
)

echo Installing Google Cloud Text-to-Speech...
pip install google-cloud-texttospeech>=2.0.0
if %errorlevel% neq 0 (
    echo ❌ Failed to install google-cloud-texttospeech
    pause
    exit /b 1
)

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo ✓ Python is installed and working
echo ✓ All required packages are installed
echo.
echo Next steps:
echo 1. Make sure google_api_key.json is in this folder
echo 2. Run test_installation.bat to verify everything works
echo 3. Run setup_scheduler.bat to set up automatic playback
echo.
echo Press any key to continue...
pause >nul
