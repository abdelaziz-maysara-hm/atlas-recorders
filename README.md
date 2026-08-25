# Atlas Recorders

برنامجين للتسجيل المحلي: شاشة/فيديو، وصوت.

## تحميل سريع (ملفات HTML — من غير تثبيت)

اضغط على الملف ثم زر **Download raw file**:

- [Atlas_Screen_Recorder.html](https://github.com/abdelaziz-maysara-hm/atlas-recorders/raw/main/Atlas_Screen_Recorder.html)
- [Atlas_Sound_Recorder.html](https://github.com/abdelaziz-maysara-hm/atlas-recorders/raw/main/Atlas_Sound_Recorder.html)

تحميل المشروع كله:
https://github.com/abdelaziz-maysara-hm/atlas-recorders/archive/refs/heads/main.zip

بعد التحميل: افتح ملف الـ HTML في Chrome أو Edge.

## نسخة ويندوز (Python)

1. ثبّت [Python 3.12](https://www.python.org/downloads/) وفعّل Add to PATH
2. للصوت:
```
pip install customtkinter sounddevice soundfile numpy
python windows/sound/atlas_sound_recorder.py
```
3. للشاشة ثبّت [FFmpeg](https://www.gyan.dev/ffmpeg/builds/) على PATH ثم:
```
pip install customtkinter
python windows/screen/atlas_screen_recorder.py
```

التسجيلات في `Documents\\AtlasRecordings`
