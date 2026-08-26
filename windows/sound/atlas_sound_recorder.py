#!/usr/bin/env python3
import customtkinter as ctk
import sounddevice as sd
import soundfile as sf
import numpy as np
import queue, time, os, sys, threading, json
from datetime import datetime
from pathlib import Path
from tkinter import messagebox

APP = "Atlas Sound Recorder"
OUT = Path.home() / "AtlasRecordings" / "Sound"
CFG = Path.home() / "AtlasRecordings" / "atlas_lang.json"
OUT.mkdir(parents=True, exist_ok=True)
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

T = {
    "en": {
        "title": "ATLAS  Sound Recorder",
        "mono": "Mono",
        "stereo": "Stereo",
        "ready": "Ready  ·  Ctrl+Shift+R",
        "record": "Record",
        "pause": "Pause",
        "resume": "Resume",
        "stop": "Stop & Save",
        "hint": "Saves to Documents/AtlasRecordings/Sound  •  local only",
        "rec": "Recording",
        "paused": "Paused",
        "nothing": "Nothing captured",
        "saved": "Saved",
        "count": "3-second countdown",
        "top": "Always on top while recording",
        "lang": "عربي",
    },
    "ar": {
        "title": "أطلس  مسجّل الصوت",
        "mono": "أحادي",
        "stereo": "استريو",
        "ready": "جاهز  ·  Ctrl+Shift+R",
        "record": "تسجيل",
        "pause": "إيقاف مؤقت",
        "resume": "استئناف",
        "stop": "إيقاف وحفظ",
        "hint": "الحفظ في Documents/AtlasRecordings/Sound  •  محلي فقط",
        "rec": "جاري التسجيل",
        "paused": "متوقف مؤقتًا",
        "nothing": "لم يُسجَّل شيء",
        "saved": "تم الحفظ",
        "count": "عدّ تنازلي 3 ثوانٍ",
        "top": "دائمًا في المقدمة أثناء التسجيل",
        "lang": "EN",
    },
}


def load_lang():
    try:
        return json.loads(CFG.read_text(encoding="utf-8")).get("lang", "en")
    except Exception:
        return "en"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.lang = load_lang() if load_lang() in T else "en"
        self.title(APP)
        self.geometry("640x560")
        self.recording = False
        self.paused = False
        self.frames = []
        self.stream = None
        self.t0 = 0
        self.elapsed = 0
        self.build()
        self.load_devices()
        self.after(200, self.tick)
        threading.Thread(target=self.hotkey_loop, daemon=True).start()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def t(self, k):
        return T[self.lang][k]

    def persist(self):
        CFG.parent.mkdir(parents=True, exist_ok=True)
        CFG.write_text(json.dumps({"lang": self.lang}), encoding="utf-8")

    def toggle_lang(self):
        self.lang = "ar" if self.lang == "en" else "en"
        self.persist()
        for w in self.winfo_children():
            w.destroy()
        self.build()
        self.load_devices()

    def build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(18, 6))
        ctk.CTkLabel(top, text=self.t("title"), font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        ctk.CTkButton(top, text=self.t("lang"), width=70, command=self.toggle_lang).pack(side="right")
        self.dev = ctk.CTkOptionMenu(self, values=["Default"], width=400)
        self.dev.pack(pady=8)
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack()
        self.sr = ctk.CTkOptionMenu(row, values=["44100", "48000"], width=120)
        self.sr.set("48000")
        self.sr.pack(side="left", padx=6)
        self.ch = ctk.CTkOptionMenu(row, values=[self.t("mono"), self.t("stereo")], width=120)
        self.ch.set(self.t("mono"))
        self.ch.pack(side="left", padx=6)
        self.use_count = ctk.CTkCheckBox(self, text=self.t("count"))
        self.use_count.pack(pady=6)
        self.use_top = ctk.CTkCheckBox(self, text=self.t("top"))
        self.use_top.select()
        self.use_top.pack(pady=4)
        self.timer = ctk.CTkLabel(self, text="00:00:00", font=ctk.CTkFont(size=36, weight="bold"))
        self.timer.pack(pady=16)
        self.status = ctk.CTkLabel(self, text=self.t("ready"), text_color="gray")
        self.status.pack()
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(pady=16)
        self.b_rec = ctk.CTkButton(btns, text=self.t("record"), fg_color="#dc2626", width=130, height=44, command=self.toggle)
        self.b_rec.pack(side="left", padx=6)
        self.b_pause = ctk.CTkButton(btns, text=self.t("pause"), width=110, height=44, state="disabled", command=self.pause)
        self.b_pause.pack(side="left", padx=6)
        self.b_stop = ctk.CTkButton(btns, text=self.t("stop"), width=130, height=44, state="disabled", command=self.stop)
        self.b_stop.pack(side="left", padx=6)
        ctk.CTkLabel(self, text=self.t("hint"), text_color="gray", font=ctk.CTkFont(size=12)).pack(pady=10)

    def load_devices(self):
        try:
            vals = []
            for i, d in enumerate(sd.query_devices()):
                if d["max_input_channels"] > 0:
                    vals.append(f"{i}: {d['name']}")
            if vals:
                self.dev.configure(values=vals)
                self.dev.set(vals[0])
        except Exception:
            pass

    def cb(self, indata, frames, t, status):
        if self.recording and not self.paused:
            self.frames.append(indata.copy())

    def toggle(self):
        if not self.recording:
            self.start()

    def start(self):
        if self.use_count.get():
            for n in (3, 2, 1):
                self.status.configure(text=str(n), text_color="#facc15")
                self.update()
                time.sleep(0.7)
        self.frames = []
        self.recording = True
        self.paused = False
        self.elapsed = 0
        self.t0 = time.time()
        ch = 1 if self.ch.get() == self.t("mono") else 2
        sr = int(self.sr.get())
        dev = None
        try:
            if self.dev.get() and self.dev.get()[0].isdigit():
                dev = int(self.dev.get().split(":")[0])
            self.stream = sd.InputStream(device=dev, channels=ch, samplerate=sr, callback=self.cb, dtype="float32")
            self.stream.start()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.recording = False
            return
        self.b_pause.configure(state="normal")
        self.b_stop.configure(state="normal")
        self.status.configure(text=self.t("rec"), text_color="#ef4444")
        if self.use_top.get():
            self.attributes("-topmost", True)

    def pause(self):
        if not self.recording:
            return
        if self.paused:
            self.paused = False
            self.t0 = time.time() - self.elapsed
            self.b_pause.configure(text=self.t("pause"))
            self.status.configure(text=self.t("rec"), text_color="#ef4444")
        else:
            self.paused = True
            self.elapsed = time.time() - self.t0
            self.b_pause.configure(text=self.t("resume"))
            self.status.configure(text=self.t("paused"))

    def stop(self):
        if not self.recording:
            return
        self.recording = False
        self.attributes("-topmost", False)
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.b_pause.configure(state="disabled", text=self.t("pause"))
        self.b_stop.configure(state="disabled")
        if not self.frames:
            self.status.configure(text=self.t("nothing"))
            return
        audio = np.concatenate(self.frames, axis=0)
        name = OUT / f"Atlas_Sound_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        sf.write(str(name), audio, int(self.sr.get()))
        self.status.configure(text=f"{self.t('saved')} {name.name}", text_color="#22c55e")
        self.timer.configure(text="00:00:00")

    def toggle_hotkey(self):
        if self.recording:
            self.stop()
        else:
            self.start()

    def hotkey_loop(self):
        if sys.platform != "win32":
            return
        try:
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            if not user32.RegisterHotKey(None, 2, 0x0002 | 0x0004, 0x52):
                return
            msg = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == 0x0312:
                    self.after(0, self.toggle_hotkey)
        except Exception:
            return

    def tick(self):
        if self.recording and not self.paused:
            self.elapsed = time.time() - self.t0
            s = int(self.elapsed)
            self.timer.configure(text=f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}")
        self.after(200, self.tick)

    def on_close(self):
        if self.recording:
            self.stop()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
