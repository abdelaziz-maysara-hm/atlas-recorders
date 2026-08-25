#!/usr/bin/env python3
import customtkinter as ctk
import subprocess, shutil, time, os, sys, threading
from datetime import datetime
from pathlib import Path
from tkinter import messagebox

APP = "Atlas Screen Recorder"
OUT = Path.home() / "AtlasRecordings" / "Screen"
OUT.mkdir(parents=True, exist_ok=True)
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


def find_ffmpeg():
    here = Path(__file__).resolve().parent
    for p in [
        here / "ffmpeg.exe",
        here.parent / "ffmpeg" / "bin" / "ffmpeg.exe",
        here / "ffmpeg" / "bin" / "ffmpeg.exe",
    ]:
        if p.exists():
            return str(p)
    return shutil.which("ffmpeg")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP)
        self.geometry("720x620")
        self.ff = find_ffmpeg()
        self.proc = None
        self.recording = False
        self.t0 = None
        self.out = None
        self.build()
        self.after(250, self.tick)
        threading.Thread(target=self.hotkey_loop, daemon=True).start()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def build(self):
        ctk.CTkLabel(self, text="ATLAS  Screen Recorder", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(18, 4))
        ctk.CTkLabel(self, text="FFmpeg: " + (self.ff or "NOT FOUND"), text_color=("#22c55e" if self.ff else "#ef4444"), font=ctk.CTkFont(size=12)).pack()
        box = ctk.CTkFrame(self)
        box.pack(fill="x", padx=24, pady=16)
        ctk.CTkLabel(box, text="Quality").pack(anchor="w", padx=12, pady=(12, 0))
        self.quality = ctk.CTkOptionMenu(box, values=["High (CRF 18)", "Balanced (CRF 23)", "Smaller (CRF 28)"])
        self.quality.set("High (CRF 18)")
        self.quality.pack(fill="x", padx=12, pady=6)
        ctk.CTkLabel(box, text="FPS").pack(anchor="w", padx=12)
        self.fps = ctk.CTkOptionMenu(box, values=["24", "30", "60"])
        self.fps.set("30")
        self.fps.pack(fill="x", padx=12, pady=6)
        ctk.CTkLabel(box, text="Audio").pack(anchor="w", padx=12)
        self.audio = ctk.CTkOptionMenu(box, values=["Microphone", "System", "Both", "No Audio"])
        self.audio.set("Both")
        self.audio.pack(fill="x", padx=12, pady=(6, 14))
        self.timer = ctk.CTkLabel(self, text="00:00:00", font=ctk.CTkFont(size=40, weight="bold"))
        self.timer.pack(pady=8)
        self.status = ctk.CTkLabel(self, text="Ready  ·  Ctrl+Shift+R", text_color="gray")
        self.status.pack()
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(pady=16)
        self.b_rec = ctk.CTkButton(btns, text="Start Recording", fg_color="#dc2626", width=180, height=48, command=self.start)
        self.b_rec.pack(side="left", padx=6)
        self.b_stop = ctk.CTkButton(btns, text="Stop", width=120, height=48, state="disabled", command=self.stop)
        self.b_stop.pack(side="left", padx=6)
        ctk.CTkButton(btns, text="Open Folder", width=120, height=48, fg_color="#1e293b", command=self.open_dir).pack(side="left", padx=6)
        ctk.CTkLabel(
            self,
            text="Hotkey Ctrl+Shift+R  ·  System audio uses WASAPI loopback\nSaves to Documents/AtlasRecordings/Screen",
            text_color="gray",
            font=ctk.CTkFont(size=12),
        ).pack(pady=8)

    def audio_args(self):
        mode = self.audio.get()
        if mode == "No Audio":
            return []
        if mode == "Microphone":
            return ["-f", "dshow", "-i", "audio=default"]
        if mode == "System":
            return ["-f", "wasapi", "-loopback", "1", "-i", "default"]
        return [
            "-f", "wasapi", "-loopback", "1", "-i", "default",
            "-f", "dshow", "-i", "audio=default",
            "-filter_complex", "amix=inputs=2:duration=longest",
        ]

    def start(self):
        if not self.ff:
            messagebox.showerror("FFmpeg", "ffmpeg.exe missing next to the app.")
            return
        if self.recording:
            return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.out = OUT / f"Atlas_Screen_{ts}.mp4"
        q = self.quality.get()
        crf = "18" if "18" in q else "23" if "23" in q else "28"
        cmd = [self.ff, "-y"]
        if sys.platform == "win32":
            cmd += ["-f", "gdigrab", "-framerate", self.fps.get(), "-i", "desktop"]
            cmd += self.audio_args()
        else:
            cmd += ["-f", "x11grab", "-framerate", self.fps.get(), "-i", ":0.0"]
        if self.audio.get() == "No Audio":
            cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", crf, "-pix_fmt", "yuv420p", "-an", str(self.out)]
        else:
            cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", crf, "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", str(self.out)]
        si = None
        if sys.platform == "win32":
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        try:
            self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=si)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        self.recording = True
        self.t0 = time.time()
        self.b_rec.configure(state="disabled")
        self.b_stop.configure(state="normal")
        self.status.configure(text="Recording  ·  Ctrl+Shift+R to stop", text_color="#ef4444")

    def stop(self):
        if not self.recording:
            return
        self.recording = False
        if self.proc:
            try:
                self.proc.stdin.write(b"q")
                self.proc.stdin.flush()
                self.proc.wait(timeout=8)
            except Exception:
                self.proc.terminate()
            self.proc = None
        self.b_rec.configure(state="normal")
        self.b_stop.configure(state="disabled")
        if self.out and self.out.exists():
            mb = self.out.stat().st_size / 1024 / 1024
            self.status.configure(text=f"Saved {self.out.name} ({mb:.1f} MB)", text_color="#22c55e")
        else:
            self.status.configure(text="Stopped  ·  Ctrl+Shift+R")
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
            if not user32.RegisterHotKey(None, 1, 0x0002 | 0x0004, 0x52):
                return
            msg = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == 0x0312:
                    self.after(0, self.toggle_hotkey)
        except Exception:
            return

    def open_dir(self):
        OUT.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(OUT)
        else:
            subprocess.run(["xdg-open", str(OUT)])

    def tick(self):
        if self.recording and self.t0:
            s = int(time.time() - self.t0)
            self.timer.configure(text=f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}")
        self.after(250, self.tick)

    def on_close(self):
        if self.recording:
            self.stop()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
