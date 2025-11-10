@echo off
REM Orin Reasoning Engine - Windows Launcher
REM Activates virtual environment and starts the CLI

echo Activating Orin virtual environment...
call env\Scripts\activate.bat

echo Starting Orin Reasoning Engine...
python src\main.py %*

pause
