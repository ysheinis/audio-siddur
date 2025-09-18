@echo off
echo Starting Hebrew Audio Siddur...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Check if required packages are installed
python -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo Error: tkinter is not available
    echo Please install Python with tkinter support
    pause
    exit /b 1
)

REM Start the application
python siddur_ui.py

REM If there was an error, pause so the user can see it
if errorlevel 1 (
    echo.
    echo An error occurred. Press any key to close.
    pause
)
