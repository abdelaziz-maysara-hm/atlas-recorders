# Atlas Apps — Windows EXE

No Python install. No Setup.bat.

## Install

1. Download the `*_Win.zip` for the app from [Releases](https://github.com/abdelaziz-maysara-hm/atlas-recorders/releases).
2. Extract the folder.
3. Double-click `Atlas_….exe`.

If SmartScreen says **Windows protected your PC**: **More info** → **Run anyway**.

## Apps

| App | Hotkey | Saves to |
| --- | --- | --- |
| Atlas Capture | Ctrl+Shift+S | Documents\AtlasRecordings\Capture |
| Atlas Clip | Ctrl+Shift+V | Documents\AtlasRecordings\clip_history.json |
| Atlas PDF | — | Documents\AtlasRecordings\PDF |
| Atlas Screen Recorder | Ctrl+Shift+R | Documents\AtlasRecordings\Screen |
| Atlas Sound Recorder | Ctrl+Shift+R | Documents\AtlasRecordings\Sound |

Keep `ffmpeg.exe` next to `Atlas_Screen_Recorder.exe` (it is already inside the zip).

Default save folder: `%USERPROFILE%\AtlasRecordings\Screen` (not Documents). Change it with **Change folder**. After Stop, Explorer can open on the file.

Record: full screen, drag a region, or pick a window. A browser tab is not its own window — record the browser window.

## Language

EN / عربي in the window. Remembered.

## Mac / Linux

Not in this release. The same Python sources will be packaged later (Mac: avfoundation, Linux: x11grab).
