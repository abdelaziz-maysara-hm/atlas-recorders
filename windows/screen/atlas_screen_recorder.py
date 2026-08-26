#!/usr/bin/env python3
import customtkinter as ctk
import subprocess, shutil, time, os, sys, threading, json, ctypes
from ctypes import wintypes
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, filedialog, Toplevel, Canvas

APP = "Atlas Screen Recorder"
DEFAULT_OUT = Path.home() / "AtlasRecordings" / "Screen"
CFG = Path.home() / "AtlasRecordings" / "atlas_settings.json"
DEFAULT_OUT.mkdir(parents=True, exist_ok=True)
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
        "area": "What to record",
        "full": "Full screen",
        "region": "Select region…",
        "window": "A window",
        "pickwin": "Window",
        "refresh": "Refresh windows",
        "nowin": "(no windows)",
        "savein": "Save folder",
        "change": "Change folder",
        "mouse": "Show mouse cursor",
        "hw": "Hardware encoder if available",
        "auto": "Auto-stop",
        "off": "Off",
        "ready": "Ready  ·  Ctrl+Shift+R",
        "start": "Start Recording",
        "stop": "Stop",
        "folder": "Open Folder",
        "hint": "After Stop, Explorer opens on the file.\nRegion = drag a rectangle. Window = pick from the list.",
        "rec": "Recording  ·  Ctrl+Shift+R to stop",
        "saved": "Saved",
        "stopped": "Stopped  ·  file was not written",
        "count": "3-second countdown",
        "top": "Always on top while recording",
        "missing": "ffmpeg.exe missing next to the app.",
        "needregion": "Drag a rectangle on the screen to record.",
        "needwin": "Pick a window from the list.",
        "openq": "Open the folder now?",
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
        "area": "ماذا تسجّل",
        "full": "الشاشة كاملة",
        "region": "اختيار منطقة…",
        "window": "نافذة",
        "pickwin": "النافذة",
        "refresh": "تحديث النوافذ",
        "nowin": "(لا توجد نوافذ)",
        "savein": "مجلد الحفظ",
        "change": "تغيير المجلد",
        "mouse": "إظهار مؤشر الماوس",
        "hw": "ترميز العتاد إن وُجد",
        "auto": "إيقاف تلقائي",
        "off": "بدون",
        "ready": "جاهز  ·  Ctrl+Shift+R",
        "start": "ابدأ التسجيل",
        "stop": "إيقاف",
        "folder": "فتح المجلد",
        "hint": "بعد الإيقاف يفتح المجلد على الملف.\nالمنطقة = اسحب مستطيل. النافذة = اختَر من القائمة.",
        "rec": "جاري التسجيل  ·  Ctrl+Shift+R للإيقاف",
        "saved": "تم الحفظ",
        "stopped": "توقف  ·  الملف ما اتكتبش",
        "count": "عدّ تنازلي 3 ثوانٍ",
        "top": "دائمًا في المقدمة أثناء التسجيل",
        "missing": "ffmpeg.exe غير موجود بجانب البرنامج.",
        "needregion": "اسحب مستطيل على الشاشة للتسجيل.",
        "needwin": "اختَر نافذة من القائمة.",
        "openq": "فتح المجلد الآن؟",
        "lang": "EN",
    },
}


def app_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def find_ffmpeg():
    here = app_dir()
    names = ["ffmpeg.exe", "ffmpeg"]
    for name in names:
        for p in [here / name, here / "ffmpeg" / "bin" / name, here.parent / "ffmpeg" / "bin" / name]:
            if p.exists():
                return str(p)
    return shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")


def load_cfg():
    try:
        return json.loads(CFG.read_text(encoding="utf-8"))
    except Exception:
        return {}


def list_windows():
    if sys.platform != "win32":
        return []
    user32 = ctypes.windll.user32
    result = []
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def cb(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length < 1:
            return True
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value.strip()
        if not title or title == APP:
            return True
        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        if rect.right - rect.left < 40 or rect.bottom - rect.top < 40:
            return True
        result.append((int(hwnd), title))
        return True

    user32.EnumWindows(EnumWindowsProc(cb), 0)
    return result[:40]


def pick_region(parent):
    picked = {"box": None}
    overlay = Toplevel(parent)
    overlay.attributes("-fullscreen", True)
    overlay.attributes("-topmost", True)
    overlay.attributes("-alpha", 0.3)
    overlay.configure(bg="black", cursor="crosshair")
    canvas = Canvas(overlay, bg="black", highlightthickness=0, cursor="crosshair")
    canvas.pack(fill="both", expand=True)
    start = {"x": 0, "y": 0, "id": None}

    def down(e):
        start["x"], start["y"] = e.x, e.y
        if start["id"]:
            canvas.delete(start["id"])
        start["id"] = canvas.create_rectangle(e.x, e.y, e.x, e.y, outline="#22c55e", width=3)

    def move(e):
        if start["id"]:
            canvas.coords(start["id"], start["x"], start["y"], e.x, e.y)

    def up(e):
        x1, y1 = overlay.winfo_rootx() + min(start["x"], e.x), overlay.winfo_rooty() + min(start["y"], e.y)
        w, h = abs(e.x - start["x"]), abs(e.y - start["y"])
        w -= w % 2
        h -= h % 2
        if w >= 16 and h >= 16:
            picked["box"] = (x1, y1, w, h)
        overlay.destroy()

    def cancel(_e=None):
        overlay.destroy()

    canvas.bind("<ButtonPress-1>", down)
    canvas.bind("<B1-Motion>", move)
    canvas.bind("<ButtonRelease-1>", up)
    overlay.bind("<Escape>", cancel)
    overlay.focus_force()
    overlay.grab_set()
    parent.wait_window(overlay)
    return picked["box"]


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.cfg = load_cfg()
        self.lang = self.cfg.get("lang", "en")
        if self.lang not in T:
            self.lang = "en"
        saved = self.cfg.get("out_dir")
        self.out_dir = Path(saved) if saved else DEFAULT_OUT
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.title(APP)
        self.geometry("760x900")
        self.ff = find_ffmpeg()
        self.nvenc = self.detect_nvenc()
        self.proc = None
        self.recording = False
        self.t0 = None
        self.out = None
        self.auto_limit = 0
        self.region = None
        self.windows = []
        self.build()
        self.after(250, self.tick)
        threading.Thread(target=self.hotkey_loop, daemon=True).start()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def t(self, k):
        return T[self.lang][k]

    def persist(self):
        CFG.parent.mkdir(parents=True, exist_ok=True)
        CFG.write_text(
            json.dumps({**self.cfg, "lang": self.lang, "out_dir": str(self.out_dir)}),
            encoding="utf-8",
        )

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
        box.pack(fill="x", padx=24, pady=12)

        ctk.CTkLabel(box, text=self.t("savein")).pack(anchor="w", padx=12, pady=(12, 0))
        save_row = ctk.CTkFrame(box, fg_color="transparent")
        save_row.pack(fill="x", padx=12, pady=6)
        self.path_lbl = ctk.CTkLabel(save_row, text=str(self.out_dir), text_color="gray", wraplength=480, justify="left")
        self.path_lbl.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(save_row, text=self.t("change"), width=120, command=self.change_dir).pack(side="right", padx=4)

        ctk.CTkLabel(box, text=self.t("area")).pack(anchor="w", padx=12, pady=(8, 0))
        self.area = ctk.CTkOptionMenu(box, values=[self.t("full"), self.t("region"), self.t("window")], command=self.on_area)
        self.area.set(self.t("full"))
        self.area.pack(fill="x", padx=12, pady=6)

        self.win_row = ctk.CTkFrame(box, fg_color="transparent")
        self.win_menu = ctk.CTkOptionMenu(self.win_row, values=[self.t("nowin")])
        self.win_menu.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(self.win_row, text=self.t("refresh"), width=140, command=self.refresh_windows).pack(side="right", padx=6)

        ctk.CTkLabel(box, text=self.t("quality")).pack(anchor="w", padx=12)
        self.quality = ctk.CTkOptionMenu(box, values=[self.t("high"), self.t("bal"), self.t("small")])
        self.quality.set(self.t("high"))
        self.quality.pack(fill="x", padx=12, pady=6)
        ctk.CTkLabel(box, text=self.t("fps")).pack(anchor="w", padx=12)
        self.fps = ctk.CTkOptionMenu(box, values=["24", "30", "60"])
        self.fps.set("30")
        self.fps.pack(fill="x", padx=12, pady=6)
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
        ctk.CTkButton(btns, text=self.t("folder"), width=140, height=48, fg_color="#1e293b", command=self.open_dir).pack(side="left", padx=6)
        ctk.CTkLabel(self, text=self.t("hint"), text_color="gray", font=ctk.CTkFont(size=12)).pack(pady=8)
        self.refresh_windows()

    def on_area(self, value):
        if value == self.t("window"):
            self.win_row.pack(fill="x", padx=12, pady=4)
            self.refresh_windows()
        else:
            self.win_row.pack_forget()
        if value == self.t("region"):
            self.after(120, self.choose_region)

    def choose_region(self):
        self.withdraw()
        self.update()
        time.sleep(0.15)
        box = pick_region(self)
        self.deiconify()
        if box:
            self.region = box
            self.status.configure(text=f"{box[2]}×{box[3]} @ {box[0]},{box[1]}", text_color="#22c55e")
        else:
            self.area.set(self.t("full"))
            self.status.configure(text=self.t("needregion"), text_color="#facc15")

    def refresh_windows(self):
        self.windows = list_windows()
        labels = [f"{title[:48]}" for _hwnd, title in self.windows] or [self.t("nowin")]
        self.win_menu.configure(values=labels)
        self.win_menu.set(labels[0])

    def change_dir(self):
        chosen = filedialog.askdirectory(initialdir=str(self.out_dir))
        if chosen:
            self.out_dir = Path(chosen)
            self.out_dir.mkdir(parents=True, exist_ok=True)
            self.path_lbl.configure(text=str(self.out_dir))
            self.persist()

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

    def grab_args(self):
        mouse = "1" if self.use_mouse.get() else "0"
        fps = self.fps.get()
        grab = ["-f", "gdigrab", "-framerate", fps, "-draw_mouse", mouse]
        mode = self.area.get()
        if mode == self.t("region"):
            if not self.region:
                return None
            x, y, w, h = self.region
            grab += ["-offset_x", str(x), "-offset_y", str(y), "-video_size", f"{w}x{h}", "-i", "desktop"]
            return grab
        if mode == self.t("window"):
            label = self.win_menu.get()
            hwnd = None
            for handle, title in self.windows:
                if title[:48] == label:
                    hwnd = handle
                    break
            if hwnd is None:
                return None
            grab += ["-i", f"hwnd={hwnd}"]
            return grab
        grab += ["-i", "desktop"]
        return grab

    def start(self):
        if not self.ff:
            messagebox.showerror("FFmpeg", self.t("missing"))
            return
        if self.recording:
            return
        grab = self.grab_args()
        if grab is None:
            messagebox.showinfo(APP, self.t("needregion") if self.area.get() == self.t("region") else self.t("needwin"))
            return
        if self.use_count.get():
            for n in (3, 2, 1):
                self.status.configure(text=str(n), text_color="#facc15")
                self.update()
                time.sleep(0.7)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.out = self.out_dir / f"Atlas_Screen_{ts}.mp4"
        q = self.quality.get()
        crf = "18" if "18" in q else "23" if "23" in q else "28"
        cmd = [self.ff, "-y"]
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
        self.timer.configure(text="00:00:00")
        if self.out and self.out.exists() and self.out.stat().st_size > 0:
            mb = self.out.stat().st_size / 1024 / 1024
            self.status.configure(text=f"{self.t('saved')}\n{self.out}", text_color="#22c55e")
            if messagebox.askyesno(APP, f"{self.t('saved')}\n{self.out}\n({mb:.1f} MB)\n\n{self.t('openq')}"):
                self.reveal()
        else:
            self.status.configure(text=self.t("stopped"), text_color="#ef4444")

    def reveal(self):
        if sys.platform == "win32" and self.out and self.out.exists():
            subprocess.run(["explorer", "/select,", str(self.out)])
        else:
            self.open_dir()

    def toggle_hotkey(self):
        if self.recording:
            self.stop()
        else:
            self.start()

    def hotkey_loop(self):
        if sys.platform != "win32":
            return
        try:
            user32 = ctypes.windll.user32
            if not user32.RegisterHotKey(None, 1, 0x0002 | 0x0004, 0x52):
                return
            from ctypes import wintypes
            msg = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == 0x0312:
                    self.after(0, self.toggle_hotkey)
        except Exception:
            return

    def open_dir(self):
        self.out_dir.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(self.out_dir)
        else:
            subprocess.run(["xdg-open", str(self.out_dir)])

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
