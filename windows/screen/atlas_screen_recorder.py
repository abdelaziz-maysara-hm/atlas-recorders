#!/usr/bin/env python3
import customtkinter as ctk
import subprocess, shutil, time, os, sys, threading, json
from datetime import datetime
from pathlib import Path
from tkinter import messagebox

APP = "Atlas Screen Recorder"
OUT = Path.home() / "AtlasRecordings" / "Screen"
CFG = Path.home() / "AtlasRecordings" / "atlas_settings.json"
OUT.mkdir(parents=True, exist_ok=True)
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

T = {
    "en": {
        "title": "ATLAS  Screen Recorder",
        "quality": "Quality",
        "high": "High (CRF 18)",
        "bal": "Balanced (CRF 23)",
        "small": "Smaller (CRF 28)",
        "fps": "FPS",
        "audio": "Audio",
        "mic": "Microphone",
        "sys": "System",
        "both": "Both",
        "none": "No Audio",
        "area": "Capture area",
        "full": "Full screen",
        "mouse": "Show mouse cursor",
        "hw": "Hardware encoder if available",
        "auto": "Auto-stop",
        "off": "Off",
        "ready": "Ready  ·  Ctrl+Shift+R",
        "start": "Start Recording",
        "stop": "Stop",
        "folder": "Open Folder",
        "hint": "Hotkey Ctrl+Shift+R  ·  WASAPI system audio\nNVENC used automatically when the GPU allows it",
        "rec": "Recording  ·  Ctrl+Shift+R to stop",
        "saved": "Saved",
        "stopped": "Stopped  ·  Ctrl+Shift+R",
        "count": "3-second countdown",
        "top": "Always on top while recording",
        "missing": "ffmpeg.exe missing next to the app.",
        "lang": "عربي",
    },
    "ar": {
        "title": "أطلس  مسجّل الشاشة",
        "quality": "الجودة",
        "high": "عالية (CRF 18)",
        "bal": "متوازنة (CRF 23)",
        "small": "أصغر حجمًا (CRF 28)",
        "fps": "الإطارات",
        "audio": "الصوت",
        "mic": "مايك",
        "sys": "صوت النظام",
        "both": "الاثنين",
        "none": "بدون صوت",
        "area": "منطقة التصوير",
        "full": "الشاشة كاملة",
        "mouse": "إظهار مؤشر الماوس",
        "hw": "ترميز العتاد إن وُجد",
        "auto": "إيقاف تلقائي",
        "off": "بدون",
        "ready": "جاهز  ·  Ctrl+Shift+R",
        "start": "ابدأ التسجيل",
        "stop": "إيقاف",
        "folder": "فتح المجلد",
        "hint": "اختصار Ctrl+Shift+R  ·  صوت النظام عبر WASAPI\nNVENC يُستخدم تلقائيًا لو كرت الشاشة يدعمه",
        "rec": "جاري التسجيل  ·  Ctrl+Shift+R للإيقاف",
        "saved": "تم الحفظ",
        "stopped": "توقف  ·  Ctrl+Shift+R",
        "count": "عدّ تنازلي 3 ثوانٍ",
        "top": "دائمًا في المقدمة أثناء التسجيل",
        "missing": "ffmpeg.exe غير موجود بجانب البرنامج.",
        "lang": "EN",
    },
}


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


def load_cfg():
    try:
        return json.loads(CFG.read_text(encoding="utf-8"))
    except Exception:
        return {}


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.cfg = load_cfg()
        self.lang = self.cfg.get("lang", "en")
        if self.lang not in T:
            self.lang = "en"
        self.title(APP)
        self.geometry("740x780")
        self.ff = find_ffmpeg()
        self.nvenc = self.detect_nvenc()
        self.proc = None
        self.recording = False
        self.t0 = None
        self.out = None
        self.auto_limit = 0
        self.build()
        self.after(250, self.tick)
        threading.Thread(target=self.hotkey_loop, daemon=True).start()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def t(self, k):
        return T[self.lang][k]

    def persist(self):
        CFG.parent.mkdir(parents=True, exist_ok=True)
        CFG.write_text(json.dumps({**self.cfg, "lang": self.lang}), encoding="utf-8")

    def detect_nvenc(self):
        if not self.ff:
            return False
        try:
            out = subprocess.check_output([self.ff, "-hide_banner", "-encoders"], stderr=subprocess.STDOUT, timeout=8)
            return b"h264_nvenc" in out
        except Exception:
            return False

    def toggle_lang(self):
        self.lang = "ar" if self.lang == "en" else "en"
        self.persist()
        for w in self.winfo_children():
            w.destroy()
        self.build()

    def build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(16, 0))
        ctk.CTkLabel(top, text=self.t("title"), font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        ctk.CTkButton(top, text=self.t("lang"), width=70, command=self.toggle_lang).pack(side="right")
        ff_txt = "FFmpeg: " + (self.ff or "NOT FOUND")
        if self.nvenc:
            ff_txt += "  ·  NVENC"
        ctk.CTkLabel(self, text=ff_txt, text_color=("#22c55e" if self.ff else "#ef4444"), font=ctk.CTkFont(size=12)).pack()
        box = ctk.CTkFrame(self)
        box.pack(fill="x", padx=24, pady=16)
        ctk.CTkLabel(box, text=self.t("quality")).pack(anchor="w", padx=12, pady=(12, 0))
        self.quality = ctk.CTkOptionMenu(box, values=[self.t("high"), self.t("bal"), self.t("small")])
        self.quality.set(self.t("high"))
        self.quality.pack(fill="x", padx=12, pady=6)
        ctk.CTkLabel(box, text=self.t("fps")).pack(anchor="w", padx=12)
        self.fps = ctk.CTkOptionMenu(box, values=["24", "30", "60"])
        self.fps.set("30")
        self.fps.pack(fill="x", padx=12, pady=6)
        ctk.CTkLabel(box, text=self.t("area")).pack(anchor="w", padx=12)
        self.area = ctk.CTkOptionMenu(box, values=[self.t("full"), "1920x1080", "1280x720", "854x480"])
        self.area.set(self.t("full"))
        self.area.pack(fill="x", padx=12, pady=6)
        ctk.CTkLabel(box, text=self.t("audio")).pack(anchor="w", padx=12)
        self.audio = ctk.CTkOptionMenu(box, values=[self.t("mic"), self.t("sys"), self.t("both"), self.t("none")])
        self.audio.set(self.t("both"))
        self.audio.pack(fill="x", padx=12, pady=6)
        ctk.CTkLabel(box, text=self.t("auto")).pack(anchor="w", padx=12)
        self.auto = ctk.CTkOptionMenu(box, values=[self.t("off"), "5", "15", "30", "60"])
        self.auto.set(self.t("off"))
        self.auto.pack(fill="x", padx=12, pady=6)
        self.use_mouse = ctk.CTkCheckBox(box, text=self.t("mouse"))
        self.use_mouse.select()
        self.use_mouse.pack(anchor="w", padx=12, pady=4)
        self.use_hw = ctk.CTkCheckBox(box, text=self.t("hw"))
        if self.nvenc:
            self.use_hw.select()
        self.use_hw.pack(anchor="w", padx=12, pady=4)
        self.use_count = ctk.CTkCheckBox(box, text=self.t("count"))
        self.use_count.select()
        self.use_count.pack(anchor="w", padx=12, pady=4)
        self.use_top = ctk.CTkCheckBox(box, text=self.t("top"))
        self.use_top.select()
        self.use_top.pack(anchor="w", padx=12, pady=(4, 14))
        self.timer = ctk.CTkLabel(self, text="00:00:00", font=ctk.CTkFont(size=40, weight="bold"))
        self.timer.pack(pady=8)
        self.status = ctk.CTkLabel(self, text=self.t("ready"), text_color="gray")
        self.status.pack()
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(pady=16)
        self.b_rec = ctk.CTkButton(btns, text=self.t("start"), fg_color="#dc2626", width=180, height=48, command=self.start)
        self.b_rec.pack(side="left", padx=6)
        self.b_stop = ctk.CTkButton(btns, text=self.t("stop"), width=120, height=48, state="disabled", command=self.stop)
        self.b_stop.pack(side="left", padx=6)
        ctk.CTkButton(btns, text=self.t("folder"), width=120, height=48, fg_color="#1e293b", command=self.open_dir).pack(side="left", padx=6)
        ctk.CTkLabel(self, text=self.t("hint"), text_color="gray", font=ctk.CTkFont(size=12)).pack(pady=8)

    def audio_args(self):
        mode = self.audio.get()
        none, mic, sys_, both = self.t("none"), self.t("mic"), self.t("sys"), self.t("both")
        if mode == none:
            return []
        if mode == mic:
            return ["-f", "dshow", "-i", "audio=default"]
        if mode == sys_:
            return ["-f", "wasapi", "-loopback", "1", "-i", "default"]
        return [
            "-f", "wasapi", "-loopback", "1", "-i", "default",
            "-f", "dshow", "-i", "audio=default",
            "-filter_complex", "amix=inputs=2:duration=longest",
        ]

    def start(self):
        if not self.ff:
            messagebox.showerror("FFmpeg", self.t("missing"))
            return
        if self.recording:
            return
        if self.use_count.get():
            for n in (3, 2, 1):
                self.status.configure(text=str(n), text_color="#facc15")
                self.update()
                time.sleep(0.7)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.out = OUT / f"Atlas_Screen_{ts}.mp4"
        q = self.quality.get()
        crf = "18" if "18" in q else "23" if "23" in q else "28"
        cmd = [self.ff, "-y"]
        grab = ["-f", "gdigrab", "-framerate", self.fps.get(), "-draw_mouse", "1" if self.use_mouse.get() else "0"]
        if self.area.get() != self.t("full") and "x" in self.area.get():
            grab += ["-video_size", self.area.get(), "-offset_x", "0", "-offset_y", "0"]
        grab += ["-i", "desktop"]
        if sys.platform == "win32":
            cmd += grab
            cmd += self.audio_args()
        else:
            cmd += ["-f", "x11grab", "-framerate", self.fps.get(), "-i", ":0.0"]
        if self.use_hw.get() and self.nvenc:
            vcodec = ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", crf, "-pix_fmt", "yuv420p"]
        else:
            vcodec = ["-c:v", "libx264", "-preset", "veryfast", "-crf", crf, "-pix_fmt", "yuv420p"]
        if self.audio.get() == self.t("none"):
            cmd += vcodec + ["-an", str(self.out)]
        else:
            cmd += vcodec + ["-c:a", "aac", "-b:a", "192k", str(self.out)]
        si = None
        if sys.platform == "win32":
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        try:
            self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=si)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        try:
            self.auto_limit = 0 if self.auto.get() == self.t("off") else int(self.auto.get()) * 60
        except Exception:
            self.auto_limit = 0
        self.recording = True
        self.t0 = time.time()
        self.b_rec.configure(state="disabled")
        self.b_stop.configure(state="normal")
        self.status.configure(text=self.t("rec"), text_color="#ef4444")
        if self.use_top.get():
            self.attributes("-topmost", True)

    def stop(self):
        if not self.recording:
            return
        self.recording = False
        self.attributes("-topmost", False)
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
            self.status.configure(text=f"{self.t('saved')} {self.out.name} ({mb:.1f} MB)", text_color="#22c55e")
        else:
            self.status.configure(text=self.t("stopped"))
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
            if self.auto_limit and s >= self.auto_limit:
                self.stop()
        self.after(250, self.tick)

    def on_close(self):
        if self.recording:
            self.stop()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
