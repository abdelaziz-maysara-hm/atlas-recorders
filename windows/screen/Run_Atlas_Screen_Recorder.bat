@echo off
cd /d "%~dp0"
set PATH=%~dp0ffmpeg\bin;%PATH%
set PYTHON=%~dp0Python\python.exe
"%PYTHON%" -c "import customtkinter" 2>nul
if errorlevel 1 call Setup.bat
"%PYTHON%" "%~dp0atlas_screen_recorder.py"
if errorlevel 1 pause
