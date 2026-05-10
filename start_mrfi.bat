@echo off
echo Starting MRFI - Metabolic Resonance Field Intelligence...
echo.
echo Please wait while the application starts...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed. Please install Python first.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Start the application
echo Starting MRFI application...
python run.py

pause
