#!/usr/bin/env python3
import customtkinter as ctk
import sounddevice as sd
import soundfile as sf
import numpy as np
import queue, time, os, sys, threading
from datetime import datetime
from pathlib import Path
from tkinter import messagebox

APP = "Atlas Sound Recorder"
OUT = Path.home() / "AtlasRecordings" / "Sound"
OUT.mkdir(parents=True, exist_ok=True)
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP)
        self.geometry("640x520")
        self.recording = False
        self.paused = False
        self.frames = []
        self.stream = None
        self.q = queue.Queue()
        self.t0 = 0
        self.elapsed = 0
        self.device = None
        self.build()
        self.load_devices()
        self.after(200, self.tick)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def build(self):
        ctk.CTkLabel(self, text="ATLAS  Sound Recorder", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(18, 6))
        self.dev = ctk.CTkOptionMenu(self, values=["Default"], width=400)
        self.dev.pack(pady=8)
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack()
        self.sr = ctk.CTkOptionMenu(row, values=["44100", "48000"], width=120)
        self.sr.set("48000")
        self.sr.pack(side="left", padx=6)
        self.ch = ctk.CTkOptionMenu(row, values=["Mono", "Stereo"], width=120)
        self.ch.set("Mono")
        self.ch.pack(side="left", padx=6)
        self.timer = ctk.CTkLabel(self, text="00:00:00", font=ctk.CTkFont(size=36, weight="bold"))
        self.timer.pack(pady=16)
        self.status = ctk.CTkLabel(self, text="Ready", text_color="gray")
        self.status.pack()
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(pady=16)
        self.b_rec = ctk.CTkButton(btns, text="Record", fg_color="#dc2626", width=130, height=44, command=self.toggle)
        self.b_rec.pack(side="left", padx=6)
        self.b_pause = ctk.CTkButton(btns, text="Pause", width=110, height=44, state="disabled", command=self.pause)
        self.b_pause.pack(side="left", padx=6)
        self.b_stop = ctk.CTkButton(btns, text="Stop & Save", width=130, height=44, state="disabled", command=self.stop)
        self.b_stop.pack(side="left", padx=6)
        ctk.CTkLabel(self, text="Saves to Documents/AtlasRecordings/Sound  •  local only", text_color="gray", font=ctk.CTkFont(size=12)).pack(pady=10)

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
        self.frames = []
        self.recording = True
        self.paused = False
        self.elapsed = 0
        self.t0 = time.time()
        ch = 1 if self.ch.get() == "Mono" else 2
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
        self.status.configure(text="Recording", text_color="#ef4444")

    def pause(self):
        if not self.recording:
            return
        if self.paused:
            self.paused = False
            self.t0 = time.time() - self.elapsed
            self.b_pause.configure(text="Pause")
            self.status.configure(text="Recording", text_color="#ef4444")
        else:
            self.paused = True
            self.elapsed = time.time() - self.t0
            self.b_pause.configure(text="Resume")
            self.status.configure(text="Paused")

    def stop(self):
        if not self.recording:
            return
        self.recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.b_pause.configure(state="disabled", text="Pause")
        self.b_stop.configure(state="disabled")
        if not self.frames:
            self.status.configure(text="Nothing captured")
            return
        audio = np.concatenate(self.frames, axis=0)
        name = OUT / f"Atlas_Sound_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        sf.write(str(name), audio, int(self.sr.get()))
        self.status.configure(text=f"Saved {name.name}", text_color="#22c55e")
        self.timer.configure(text="00:00:00")

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
