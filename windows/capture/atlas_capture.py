#!/usr/bin/env python3
import customtkinter as ctk
import io, json, os, sys, threading, time
from datetime import datetime
from pathlib import Path
from tkinter import Toplevel, Canvas, messagebox

try:
    from PIL import Image, ImageGrab, ImageTk, ImageDraw
except ImportError:
    raise SystemExit("Pillow is required")

APP = "Atlas Capture"
OUT = Path.home() / "AtlasRecordings" / "Capture"
CFG = Path.home() / "AtlasRecordings" / "atlas_settings.json"
OUT.mkdir(parents=True, exist_ok=True)
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

T = {
    "en": {
        "title": "ATLAS  Capture",
        "full": "Full screen",
        "region": "Region",
        "delay": "Delay (sec)",
        "grab": "Capture",
        "copy": "Copy",
        "save": "Save PNG",
        "folder": "Open Folder",
        "hint": "Print Screen alternative · no ads · Ctrl+Shift+S",
        "ready": "Ready",
        "copied": "Copied to clipboard",
        "saved": "Saved",
        "lang": "عربي",
    },
    "ar": {
        "title": "أطلس  اللقطة",
        "full": "الشاشة كاملة",
        "region": "منطقة",
        "delay": "تأخير (ث)",
        "grab": "التقاط",
        "copy": "نسخ",
        "save": "حفظ PNG",
        "folder": "فتح المجلد",
        "hint": "بديل Print Screen · من غير إعلانات · Ctrl+Shift+S",
        "ready": "جاهز",
        "copied": "اتنسخ للحافظة",
        "saved": "تم الحفظ",
        "lang": "EN",
    },
}


def load_cfg():
    try:
        return json.loads(CFG.read_text(encoding="utf-8"))
    except Exception:
        return {}


def copy_image(img):
    if sys.platform != "win32":
        return False
    import ctypes
    from ctypes import wintypes

    buf = io.BytesIO()
    img.convert("RGB").save(buf, "BMP")
    data = buf.getvalue()[14:]
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    CF_DIB = 8
    GMEM_MOVEABLE = 0x0002
    user32.OpenClipboard(None)
    user32.EmptyClipboard()
    handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
    locked = kernel32.GlobalLock(handle)
    ctypes.memmove(locked, data, len(data))
    kernel32.GlobalUnlock(handle)
    user32.SetClipboardData(CF_DIB, handle)
    user32.CloseClipboard()
    return True


class RegionPicker:
    def __init__(self, root):
        self.result = None
        self.start = None
        win = Toplevel(root)
        self.win = win
        win.attributes("-fullscreen", True)
        win.attributes("-topmost", True)
        win.attributes("-alpha", 0.25)
        win.configure(bg="black")
        cv = Canvas(win, cursor="cross", bg="black", highlightthickness=0)
        cv.pack(fill="both", expand=True)
        self.cv = cv
        self.rect = None
        cv.bind("<Button-1>", self.down)
        cv.bind("<B1-Motion>", self.move)
        cv.bind("<ButtonRelease-1>", self.up)
        win.bind("<Escape>", lambda e: self.cancel())
        win.focus_force()
        win.grab_set()
        root.wait_window(win)

    def down(self, e):
        self.start = (e.x_root, e.y_root)
        self.rect = self.cv.create_rectangle(e.x, e.y, e.x, e.y, outline="white", width=2)

    def move(self, e):
        if self.rect and self.start:
            x0, y0 = self.start
            self.cv.coords(self.rect, self.cv.canvasx(x0 - self.win.winfo_rootx()), self.cv.canvasy(y0 - self.win.winfo_rooty()), e.x, e.y)

    def up(self, e):
        if not self.start:
            self.cancel()
            return
        x0, y0 = self.start
        x1, y1 = e.x_root, e.y_root
        a, b = min(x0, x1), min(y0, y1)
        c, d = max(x0, x1), max(y0, y1)
        if c - a < 4 or d - b < 4:
            self.cancel()
            return
        self.result = (a, b, c, d)
        self.win.destroy()

    def cancel(self):
        self.result = None
        self.win.destroy()


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.cfg = load_cfg()
        self.lang = self.cfg.get("lang", "en")
        if self.lang not in T:
            self.lang = "en"
        self.title(APP)
        self.geometry("560x420")
        self.img = None
        self.preview = None
        self.build()
        threading.Thread(target=self.hotkey_loop, daemon=True).start()

    def t(self, k):
        return T[self.lang][k]

    def persist(self):
        CFG.parent.mkdir(parents=True, exist_ok=True)
        CFG.write_text(json.dumps({**self.cfg, "lang": self.lang}), encoding="utf-8")

    def toggle_lang(self):
        self.lang = "ar" if self.lang == "en" else "en"
        self.persist()
        for w in self.winfo_children():
            w.destroy()
        self.build()

    def build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(18, 6))
        ctk.CTkLabel(top, text=self.t("title"), font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        ctk.CTkButton(top, text=self.t("lang"), width=70, command=self.toggle_lang).pack(side="right")
        self.mode = ctk.CTkOptionMenu(self, values=[self.t("full"), self.t("region")], width=280)
        self.mode.set(self.t("region"))
        self.mode.pack(pady=8)
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack()
        ctk.CTkLabel(row, text=self.t("delay")).pack(side="left", padx=6)
        self.delay = ctk.CTkOptionMenu(row, values=["0", "2", "3", "5"], width=80)
        self.delay.set("0")
        self.delay.pack(side="left")
        self.status = ctk.CTkLabel(self, text=self.t("ready"), text_color="gray")
        self.status.pack(pady=10)
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(pady=8)
        ctk.CTkButton(btns, text=self.t("grab"), fg_color="#dc2626", width=130, height=44, command=self.grab).pack(side="left", padx=6)
        self.b_copy = ctk.CTkButton(btns, text=self.t("copy"), width=110, height=44, state="disabled", command=self.copy)
        self.b_copy.pack(side="left", padx=6)
        self.b_save = ctk.CTkButton(btns, text=self.t("save"), width=110, height=44, state="disabled", command=self.save)
        self.b_save.pack(side="left", padx=6)
        ctk.CTkButton(self, text=self.t("folder"), width=160, height=40, fg_color="#1e293b", command=self.open_dir).pack(pady=8)
        ctk.CTkLabel(self, text=self.t("hint"), text_color="gray", font=ctk.CTkFont(size=12)).pack(pady=8)

    def grab(self):
        d = int(self.delay.get())
        if d:
            self.withdraw()
            time.sleep(d)
        else:
            self.withdraw()
            time.sleep(0.25)
        try:
            if self.mode.get() == self.t("region"):
                self.deiconify()
                picker = RegionPicker(self)
                self.withdraw()
                time.sleep(0.15)
                if not picker.result:
                    self.deiconify()
                    return
                img = ImageGrab.grab(bbox=picker.result)
            else:
                img = ImageGrab.grab()
        except Exception as e:
            self.deiconify()
            messagebox.showerror("Error", str(e))
            return
        self.img = img
        self.deiconify()
        self.b_copy.configure(state="normal")
        self.b_save.configure(state="normal")
        self.save()
        self.copy()

    def save(self):
        if not self.img:
            return
        name = OUT / f"Atlas_Capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        self.img.save(name, "PNG")
        self.status.configure(text=f"{self.t('saved')} {name.name}", text_color="#22c55e")

    def copy(self):
        if not self.img:
            return
        try:
            copy_image(self.img)
            self.status.configure(text=self.t("copied"), text_color="#22c55e")
        except Exception as e:
            messagebox.showerror("Clipboard", str(e))

    def open_dir(self):
        OUT.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(OUT)
        else:
            os.system(f'xdg-open "{OUT}"')

    def hotkey_loop(self):
        if sys.platform != "win32":
            return
        try:
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            if not user32.RegisterHotKey(None, 3, 0x0002 | 0x0004, 0x53):  # Ctrl+Shift+S
                return
            msg = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == 0x0312:
                    self.after(0, self.grab)
        except Exception:
            return


if __name__ == "__main__":
    App().mainloop()
