@echo off
cd /d "%~dp0"
set PYTHON=%~dp0Python\python.exe
"%PYTHON%" -c "import customtkinter,sounddevice,soundfile,numpy" 2>nul
if errorlevel 1 call Setup.bat
"%PYTHON%" "%~dp0atlas_sound_recorder.py"
if errorlevel 1 pause
