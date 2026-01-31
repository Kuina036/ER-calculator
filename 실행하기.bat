@echo off
setlocal

REM Check if Python is installed
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b
)

echo Starting the program...
echo (Please wait a moment)

REM Run the GUI script
python tournament_gui.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] The program crashed. Please check the error message above.
)

echo.
pause