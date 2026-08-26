# Atlas Apps — setup and usage

Portable Windows apps. No installer, no account, files stay on your PC.

## Setup (once per app)

1. Download the ZIP from [NetSec Atlas / Apps](https://netsecatlas.com/tools).
2. Extract the folder anywhere (Desktop is fine).
3. Run `Setup.bat` once. Internet is needed for this step only (Python packages).
4. After that, start the app with `Run_Atlas_….bat`.

If Windows SmartScreen says **Windows protected your PC**: **More info** → **Run anyway**.

## Apps

| App | Hotkey | Saves to |
| --- | --- | --- |
| Atlas Capture | Ctrl+Shift+S | Documents\AtlasRecordings\Capture |
| Atlas Clip | Ctrl+Shift+V | Documents\AtlasRecordings\clip_history.json |
| Atlas PDF | — | Documents\AtlasRecordings\PDF |
| Atlas Screen Recorder | Ctrl+Shift+R | Documents\AtlasRecordings\Screen |
| Atlas Sound Recorder | Ctrl+Shift+R | Documents\AtlasRecordings\Sound |

### Capture
Region or full screen. Optional delay. Copies PNG to the clipboard and saves the file.

### Clip
Leave it running. Copied text is stored locally. Pin items you need. The hotkey brings the window forward.

### PDF
Add PDFs or images. Merge, split pages, rotate 90°, images → PDF. Nothing is uploaded.

### Screen Recorder
Quality, FPS, audio = Microphone / System / Both. Countdown, auto-stop, NVENC when the GPU supports it. Output is MP4.

### Sound Recorder
Pick the mic, Mono or Stereo, 48 kHz. Live level meter and clip warning. Pause. Output is WAV.

## Language
EN / عربي in the window. The choice is remembered.

## If something fails
- Setup failed: check the internet and run `Setup.bat` again.
- No system audio on screen capture: set Audio to **System** or **Both**.
- Hotkey does nothing: another app owns the shortcut, or start Atlas first.
