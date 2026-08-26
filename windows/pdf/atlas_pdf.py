#!/usr/bin/env python3
import customtkinter as ctk
import json, os, sys
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

APP = "Atlas PDF"
OUT = Path.home() / "AtlasRecordings" / "PDF"
CFG = Path.home() / "AtlasRecordings" / "atlas_settings.json"
OUT.mkdir(parents=True, exist_ok=True)
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

T = {
    "en": {
        "title": "ATLAS  PDF",
        "add": "Add files",
        "merge": "Merge",
        "split": "Split pages",
        "rotate": "Rotate 90°",
        "images": "Images to PDF",
        "folder": "Open folder",
        "hint": "Files stay on this PC  ·  no upload",
        "lang": "عربي",
        "done": "Saved",
        "need": "Add a PDF or image first.",
    },
    "ar": {
        "title": "أطلس  PDF",
        "add": "إضافة ملفات",
        "merge": "دمج",
        "split": "تقسيم صفحات",
        "rotate": "تدوير 90°",
        "images": "صور إلى PDF",
        "folder": "فتح المجلد",
        "hint": "الملفات على الجهاز  ·  من غير رفع",
        "lang": "EN",
        "done": "تم الحفظ",
        "need": "ضيف PDF أو صورة أولاً.",
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
        self.files = []
        self.title(APP)
        self.geometry("640x520")
        self.build()

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
        self.refresh()

    def build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(16, 6))
        ctk.CTkLabel(top, text=self.t("title"), font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        ctk.CTkButton(top, text=self.t("lang"), width=70, command=self.toggle_lang).pack(side="right")
        self.box = ctk.CTkTextbox(self, height=180)
        self.box.pack(fill="x", padx=20, pady=8)
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(pady=6)
        ctk.CTkButton(row, text=self.t("add"), command=self.add).pack(side="left", padx=4)
        ctk.CTkButton(row, text=self.t("merge"), command=self.merge).pack(side="left", padx=4)
        ctk.CTkButton(row, text=self.t("split"), command=self.split).pack(side="left", padx=4)
        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(pady=6)
        ctk.CTkButton(row2, text=self.t("rotate"), command=self.rotate).pack(side="left", padx=4)
        ctk.CTkButton(row2, text=self.t("images"), command=self.images).pack(side="left", padx=4)
        ctk.CTkButton(row2, text=self.t("folder"), fg_color="#1e293b", command=self.open_dir).pack(side="left", padx=4)
        self.status = ctk.CTkLabel(self, text=self.t("hint"), text_color="gray")
        self.status.pack(pady=10)

    def refresh(self):
        self.box.delete("1.0", "end")
        self.box.insert("end", "\n".join(Path(f).name for f in self.files) or "")

    def add(self):
        paths = filedialog.askopenfilenames(filetypes=[("PDF / images", "*.pdf *.png *.jpg *.jpeg")])
        self.files.extend(paths)
        self.refresh()

    def stamp(self, prefix):
        return OUT / f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    def merge(self):
        pdfs = [f for f in self.files if f.lower().endswith(".pdf")]
        if not pdfs:
            messagebox.showinfo(APP, self.t("need"))
            return
        from pypdf import PdfWriter
        w = PdfWriter()
        for f in pdfs:
            w.append(f)
        dest = self.stamp("Atlas_Merge")
        w.write(str(dest))
        w.close()
        self.status.configure(text=f"{self.t('done')} {dest.name}", text_color="#22c55e")

    def split(self):
        pdfs = [f for f in self.files if f.lower().endswith(".pdf")]
        if not pdfs:
            messagebox.showinfo(APP, self.t("need"))
            return
        from pypdf import PdfReader, PdfWriter
        src = PdfReader(pdfs[0])
        for i, page in enumerate(src.pages, 1):
            w = PdfWriter()
            w.add_page(page)
            dest = OUT / f"Atlas_Page_{i}.pdf"
            w.write(str(dest))
            w.close()
        self.status.configure(text=f"{self.t('done')} {len(src.pages)}", text_color="#22c55e")

    def rotate(self):
        pdfs = [f for f in self.files if f.lower().endswith(".pdf")]
        if not pdfs:
            messagebox.showinfo(APP, self.t("need"))
            return
        from pypdf import PdfReader, PdfWriter
        src = PdfReader(pdfs[0])
        w = PdfWriter()
        for page in src.pages:
            page.rotate(90)
            w.add_page(page)
        dest = self.stamp("Atlas_Rotate")
        w.write(str(dest))
        w.close()
        self.status.configure(text=f"{self.t('done')} {dest.name}", text_color="#22c55e")

    def images(self):
        imgs = [f for f in self.files if Path(f).suffix.lower() in {".png", ".jpg", ".jpeg"}]
        if not imgs:
            messagebox.showinfo(APP, self.t("need"))
            return
        from PIL import Image
        opened = [Image.open(f).convert("RGB") for f in imgs]
        dest = self.stamp("Atlas_Images")
        opened[0].save(dest, save_all=True, append_images=opened[1:])
        self.status.configure(text=f"{self.t('done')} {dest.name}", text_color="#22c55e")

    def open_dir(self):
        OUT.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(OUT)


if __name__ == "__main__":
    App().mainloop()
