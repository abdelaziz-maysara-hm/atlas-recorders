#!/usr/bin/env python3
import customtkinter as ctk
import json, os, sys, threading, time
from datetime import datetime
from pathlib import Path

APP = "Atlas Clip"
DIR = Path.home() / "AtlasRecordings"
HIST = DIR / "clip_history.json"
CFG = DIR / "atlas_settings.json"
DIR.mkdir(parents=True, exist_ok=True)
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

T = {
    "en": {
        "title": "ATLAS  Clip",
        "copy": "Copy",
        "pin": "Pin",
        "clear": "Clear unpinned",
        "hint": "Watches clipboard  ·  Ctrl+Shift+V  ·  local only",
        "lang": "عربي",
        "empty": "(empty)",
    },
    "ar": {
        "title": "أطلس  الحافظة",
        "copy": "نسخ",
        "pin": "تثبيت",
        "clear": "مسح غير المثبت",
        "hint": "يتابع الحافظة  ·  Ctrl+Shift+V  ·  محلي فقط",
        "lang": "EN",
        "empty": "(فاضي)",
    },
}


def load_json(path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def read_clip():
    if sys.platform != "win32":
        return ""
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    CF_UNICODETEXT = 13
    user32.OpenClipboard(0)
    try:
        handle = user32.GetClipboardData(CF_UNICODETEXT)
        if not handle:
            return ""
        kernel32.GlobalLock.restype = ctypes.c_void_p
        locked = kernel32.GlobalLock(handle)
        text = ctypes.wstring_at(locked)
        kernel32.GlobalUnlock(handle)
        return text
    finally:
        user32.CloseClipboard()


def write_clip(text):
    if sys.platform != "win32":
        return
    import ctypes
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    CF_UNICODETEXT = 13
    GMEM_MOVEABLE = 0x0002
    data = (text + "\x00").encode("utf-16le")
    user32.OpenClipboard(0)
    user32.EmptyClipboard()
    handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
    locked = kernel32.GlobalLock(handle)
    ctypes.memmove(locked, data, len(data))
    kernel32.GlobalUnlock(handle)
    user32.SetClipboardData(CF_UNICODETEXT, handle)
    user32.CloseClipboard()


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        cfg = load_json(CFG, {})
        self.lang = cfg.get("lang", "en") if cfg.get("lang") in T else "en"
        self.items = load_json(HIST, [])
        self.last = ""
        self.title(APP)
        self.geometry("640x560")
        self.build()
        self.refresh()
        self.after(400, self.poll)
        threading.Thread(target=self.hotkey_loop, daemon=True).start()

    def t(self, k):
        return T[self.lang][k]

    def persist(self):
        HIST.write_text(json.dumps(self.items[:80], ensure_ascii=False), encoding="utf-8")
        CFG.write_text(json.dumps({"lang": self.lang}), encoding="utf-8")

    def toggle_lang(self):
        self.lang = "ar" if self.lang == "en" else "en"
        self.persist()
        for w in self.winfo_children():
            w.destroy()
        self.build()
        self.refresh()

    def build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(16, 6))
        ctk.CTkLabel(top, text=self.t("title"), font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        ctk.CTkButton(top, text=self.t("lang"), width=70, command=self.toggle_lang).pack(side="right")
        self.box = ctk.CTkScrollableFrame(self, width=580, height=380)
        self.box.pack(fill="both", expand=True, padx=16, pady=8)
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(pady=8)
        ctk.CTkButton(row, text=self.t("clear"), command=self.clear).pack(side="left", padx=6)
        ctk.CTkLabel(self, text=self.t("hint"), text_color="gray", font=ctk.CTkFont(size=12)).pack(pady=6)

    def refresh(self):
        for w in self.box.winfo_children():
            w.destroy()
        if not self.items:
            ctk.CTkLabel(self.box, text=self.t("empty"), text_color="gray").pack(pady=20)
            return
        for i, item in enumerate(self.items):
            line = ctk.CTkFrame(self.box)
            line.pack(fill="x", pady=4)
            preview = item["text"].replace("\n", " ")[:80]
            ctk.CTkButton(line, text=preview, anchor="w", width=360, fg_color="#1e293b", command=lambda t=item["text"]: self.copy(t)).pack(side="left", padx=4)
            ctk.CTkButton(line, text=self.t("pin"), width=70, command=lambda n=i: self.pin(n)).pack(side="left", padx=2)
            ctk.CTkButton(line, text="×", width=40, fg_color="#7f1d1d", command=lambda n=i: self.delete(n)).pack(side="left")

    def add(self, text):
        text = (text or "").strip()
        if not text or (self.items and self.items[0]["text"] == text):
            return
        self.items = [{"text": text, "at": datetime.now().isoformat(), "pin": False}] + [i for i in self.items if i["text"] != text]
        pinned = [i for i in self.items if i.get("pin")]
        rest = [i for i in self.items if not i.get("pin")]
        self.items = (pinned + rest)[:80]
        self.persist()
        self.refresh()

    def copy(self, text):
        write_clip(text)
        self.last = text

    def pin(self, n):
        self.items[n]["pin"] = not self.items[n].get("pin")
        pinned = [i for i in self.items if i.get("pin")]
        rest = [i for i in self.items if not i.get("pin")]
        self.items = pinned + rest
        self.persist()
        self.refresh()

    def delete(self, n):
        del self.items[n]
        self.persist()
        self.refresh()

    def clear(self):
        self.items = [i for i in self.items if i.get("pin")]
        self.persist()
        self.refresh()

    def poll(self):
        try:
            text = read_clip()
            if text and text != self.last:
                self.last = text
                self.add(text)
        except Exception:
            pass
        self.after(500, self.poll)

    def hotkey_loop(self):
        if sys.platform != "win32":
            return
        try:
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            if not user32.RegisterHotKey(None, 4, 0x0002 | 0x0004, 0x56):
                return
            msg = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == 0x0312:
                    self.after(0, lambda: (self.deiconify(), self.attributes("-topmost", True), self.after(400, lambda: self.attributes("-topmost", False))))
        except Exception:
            return


if __name__ == "__main__":
    App().mainloop()
