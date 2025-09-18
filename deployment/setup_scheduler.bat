@echo off
echo ========================================
echo Hebrew Audio Siddur - Scheduler Setup
echo ========================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] This script must be run as Administrator!
    echo.
    echo Right-click on this file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo [OK] Running as Administrator
echo.

REM Get current directory
set SIDDUR_DIR=%CD%
set PYTHON_CMD=python "%SIDDUR_DIR%\scripts\scheduled_tefilla.py"

echo Setting up Windows Task Scheduler for Hebrew Audio Siddur...
echo.
echo Directory: %SIDDUR_DIR%
echo Command: %PYTHON_CMD%
echo.

REM Create Shacharis task (7:00 AM daily)
echo Creating Shacharis task (7:00 AM daily)...
schtasks /create /tn "Hebrew Siddur - Shacharis" /tr "%PYTHON_CMD%" /sc daily /st 07:00 /f >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Shacharis task created successfully
) else (
    echo [ERROR] Failed to create Shacharis task
)

REM Create Mincha task (1:00 PM daily)  
echo Creating Mincha task (1:00 PM daily)...
schtasks /create /tn "Hebrew Siddur - Mincha" /tr "%PYTHON_CMD%" /sc daily /st 13:00 /f >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Mincha task created successfully
) else (
    echo [ERROR] Failed to create Mincha task
)

REM Create Maariv task (7:00 PM daily)
echo Creating Maariv task (7:00 PM daily)...
schtasks /create /tn "Hebrew Siddur - Maariv" /tr "%PYTHON_CMD%" /sc daily /st 19:00 /f >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Maariv task created successfully
) else (
    echo [ERROR] Failed to create Maariv task
)

echo.
echo ========================================
echo Scheduler Setup Complete!
echo ========================================
echo.

REM Verify tasks were created
echo Verifying tasks were created...
schtasks /query /tn "Hebrew Siddur - Shacharis" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Shacharis task verified
) else (
    echo [ERROR] Shacharis task not found
)

schtasks /query /tn "Hebrew Siddur - Mincha" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Mincha task verified
) else (
    echo [ERROR] Mincha task not found
)

schtasks /query /tn "Hebrew Siddur - Maariv" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Maariv task verified
) else (
    echo [ERROR] Maariv task not found
)

echo.
echo Tasks will run daily and only play tefillos on Shabbat and Yom Tov.
echo.
echo To test the scheduler:
echo 1. Run: python scheduled_tefilla.py --date 2025-09-23
echo 2. Check scheduled_tefilla.log for activity
echo.
echo To view tasks in Task Scheduler:
echo 1. Press Windows key + R
echo 2. Type: taskschd.msc
echo 3. Press Enter
echo 4. Look for "Hebrew Siddur" tasks
echo.
echo Press any key to continue...
pause >nul
