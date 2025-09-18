@echo off
echo ========================================
echo Hebrew Audio Siddur - Deployment Package
echo ========================================
echo.

REM Check if we're in the right directory
if not exist "src\tefilla_rules.py" (
    echo ❌ Error: This script must be run from the siddur directory
    echo Please navigate to the siddur folder and run this script again.
    pause
    exit /b 1
)

echo Creating deployment package...
echo.

REM Create deployment directory with timestamp to avoid conflicts
set TIMESTAMP=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set DEPLOY_DIR=siddur_deployment_%TIMESTAMP%

echo Creating deployment directory: %DEPLOY_DIR%...
mkdir "%DEPLOY_DIR%"
if %errorlevel% neq 0 (
    echo ❌ Failed to create deployment directory
    goto :error
)
cd "%DEPLOY_DIR%"

echo.
echo Copying source files...
xcopy "..\src\*" "src\" /E /I /Q >nul
if %errorlevel% neq 0 (
    echo ❌ Failed to copy source files
    goto :error
)

echo Copying scripts...
xcopy "..\scripts\*" "scripts\" /E /I /Q >nul
if %errorlevel% neq 0 (
    echo ❌ Failed to copy scripts
    goto :error
)

echo Copying UI files...
xcopy "..\ui\*" "ui\" /E /I /Q >nul
if %errorlevel% neq 0 (
    echo ❌ Failed to copy UI files
    goto :error
)

echo Copying deployment files...
xcopy "..\deployment\*" "deployment\" /E /I /Q >nul
if %errorlevel% neq 0 (
    echo ❌ Failed to copy deployment files
    goto :error
)

echo Copying documentation...
xcopy "..\docs\*" "docs\" /E /I /Q >nul
if %errorlevel% neq 0 (
    echo ❌ Failed to copy documentation
    goto :error
)

echo Copying configuration files...
xcopy "..\config\*" "config\" /E /I /Q >nul
if %errorlevel% neq 0 (
    echo ❌ Failed to copy configuration files
    goto :error
)

echo Copying requirements file...
if exist "..\requirements.txt" (
    copy "..\requirements.txt" . >nul
) else (
    echo python-dateutil>=2.8.0 > requirements.txt
    echo pyluach>=2.0.0 >> requirements.txt
    echo google-cloud-texttospeech>=2.0.0 >> requirements.txt
)

echo.
echo Copying generated audio content...
if exist "..\data\chunk_cache" (
    echo Copying chunk cache...
    xcopy "..\data\chunk_cache" "data\chunk_cache\" /E /I /Q >nul
    if %errorlevel% neq 0 (
        echo ❌ Failed to copy chunk cache
        goto :error
    )
) else (
    echo ⚠ Warning: data\chunk_cache directory not found
    echo You may need to generate audio chunks first.
)

if exist "..\data\output" (
    echo Copying output directory...
    xcopy "..\data\output" "data\output\" /E /I /Q >nul
    if %errorlevel% neq 0 (
        echo ❌ Failed to copy output directory
        goto :error
    )
) else (
    echo ⚠ Warning: data\output directory not found
    echo You may need to generate tefillos first.
)

echo.
echo Creating deployment requirements file...
echo python-dateutil>=2.8.0 > requirements_deployment.txt
echo pyluach>=2.0.0 >> requirements_deployment.txt
echo google-cloud-texttospeech>=2.0.0 >> requirements_deployment.txt

echo.
echo Verifying deployment package...
echo.
echo Files in deployment package:
dir /b /s *.py | find /c /v "" > temp_count.txt
set /p PYTHON_COUNT=<temp_count.txt
echo ✓ Python files: %PYTHON_COUNT%

dir /b /s *.bat | find /c /v "" > temp_count.txt
set /p BATCH_COUNT=<temp_count.txt
echo ✓ Batch files: %BATCH_COUNT%

dir /b /s *.md | find /c /v "" > temp_count.txt
set /p DOC_COUNT=<temp_count.txt
echo ✓ Documentation files: %DOC_COUNT%

if exist "config\google_api_key.json" (
    echo ✓ Google API key file
) else (
    echo ❌ Google API key file missing!
    goto :error
)

if exist "data\chunk_cache" (
    echo ✓ Chunk cache directory
) else (
    echo ⚠ Chunk cache directory missing
)

if exist "data\output" (
    echo ✓ Output directory
) else (
    echo ⚠ Output directory missing
)

del temp_count.txt >nul 2>&1

echo.
echo Creating deployment package zip file...
cd ..
powershell -Command "Compress-Archive -Path '%DEPLOY_DIR%\*' -DestinationPath 'siddur_deployment.zip' -Force" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Failed to create zip file
    goto :error
)

echo.
echo ========================================
echo Deployment Package Created!
echo ========================================
echo.
echo ✓ Deployment package created: siddur_deployment.zip
echo ✓ Size: 
for %%A in (siddur_deployment.zip) do echo   %%~zA bytes
echo.
echo Package contents:
echo - All Python source files
echo - Installation and setup scripts
echo - User manual and documentation
echo - Google API key file
echo - Generated audio chunks (if available)
echo - Generated tefillos (if available)
echo.
echo Next steps:
echo 1. Transfer siddur_deployment.zip to the target computer
echo 2. Extract to C:\HebrewSiddur\
echo 3. Run install_python.bat
echo 4. Run test_installation.bat
echo 5. Run setup_scheduler.bat as Administrator
echo.
echo Deployment package creation completed successfully!
exit /b 0

:error
echo.
echo ========================================
echo Deployment Package Creation Failed!
echo ========================================
echo.
echo ❌ An error occurred while creating the deployment package.
echo Please check the error messages above and try again.
echo.
echo Common issues:
echo 1. Make sure you're running from the correct directory
echo 2. Check that all required files exist
echo 3. Make sure you have write permissions
echo 4. Try running as Administrator
echo.
exit /b 1
