import customtkinter as ctk
import requests
import re
import threading
import time
import os
import sys
from PIL import Image, ImageDraw, ImageFont

def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

BASE_DIR  = os.path.dirname(os.path.abspath(sys.argv[0]))
CONF_FILE = os.path.join(BASE_DIR, "sites.conf")

C_BG      = "#0d0d14"
C_CARD    = "#13131f"
C_CARD2   = "#17172a"
C_BORDER  = "#22223a"
C_GREEN   = "#22d37a"
C_BLUE    = "#4d9cff"
C_RED     = "#ff4d6a"
C_AMBER   = "#ffb347"
C_TEXT    = "#eeeef8"
C_MUTED   = "#55556a"
C_MUTED2  = "#888898"

def conf_oku():
    siteler = {}
    if not os.path.exists(CONF_FILE):
        return siteler
    try:
        with open(CONF_FILE, encoding="utf-8") as f:
            for satir in f:
                satir = satir.strip()
                if not satir or satir.startswith("#"):
                    continue
                if "=" in satir:
                    isim, kod = satir.split("=", 1)
                    siteler[isim.strip()] = kod.strip()
    except:
        pass
    return siteler

def conf_yaz(siteler):
    try:
        with open(CONF_FILE, "w", encoding="utf-8") as f:
            f.write("# Online Sayaç - Site Listesi\n")
            f.write("# Format: Site Adı = swidget_kodu\n\n")
            for isim, kod in siteler.items():
                f.write(f"{isim} = {kod}\n")
    except:
        pass

def online_al(kod):
    try:
        r = requests.get(
            f"https://whos.amung.us/swidget/{kod}",
            allow_redirects=False, timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        m = re.search(r"/(\d+)\.png", r.headers.get("location", ""))
        return int(m.group(1)) if m else None
    except:
        return None


class SiteKart(ctk.CTkFrame):
    def __init__(self, master, isim, kod, on_sil, **kw):
        super().__init__(master, fg_color=C_CARD, corner_radius=16,
                         border_width=1, border_color=C_BORDER, **kw)
        self.isim = isim
        self.kod  = kod
        self.on_sil = on_sil
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        ust = ctk.CTkFrame(self, fg_color="transparent")
        ust.grid(row=0, column=0, sticky="ew", padx=18, pady=(16,0))
        ust.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(ust, text=self.isim, font=ctk.CTkFont("Helvetica", 13, "bold"),
                     text_color=C_TEXT, anchor="w").grid(row=0, column=0, sticky="w")

        sil = ctk.CTkButton(ust, text="✕", width=26, height=26,
                             fg_color="transparent", hover_color="#2a0a14",
                             text_color=C_MUTED, font=ctk.CTkFont(size=12),
                             corner_radius=6,
                             command=lambda: self.on_sil(self.isim))
        sil.grid(row=0, column=1, sticky="e")

        ctk.CTkLabel(self, text=self.kod, font=ctk.CTkFont("Courier", 10),
                     text_color=C_MUTED, anchor="w").grid(row=1, column=0, sticky="w", padx=18)

        self.lbl_sayi = ctk.CTkLabel(self, text="—",
                                      font=ctk.CTkFont("Helvetica", 42, "bold"),
                                      text_color=C_MUTED2, anchor="w")
        self.lbl_sayi.grid(row=2, column=0, sticky="w", padx=18, pady=(8,0))

        ctk.CTkLabel(self, text="online kullanıcı",
                     font=ctk.CTkFont("Helvetica", 10),
                     text_color=C_MUTED, anchor="w").grid(row=3, column=0, sticky="w", padx=18)

        self.bar = ctk.CTkProgressBar(self, height=4, corner_radius=2,
                                       progress_color=C_BLUE, fg_color=C_BORDER)
        self.bar.set(0)
        self.bar.grid(row=4, column=0, sticky="ew", padx=18, pady=(12,16))

    def guncelle(self, sayi, maksimum):
        if sayi is None:
            self.lbl_sayi.configure(text="hata", text_color=C_RED,
                                     font=ctk.CTkFont("Helvetica", 18, "bold"))
            self.configure(border_color="#3a1020")
            self.bar.configure(progress_color=C_RED)
            self.bar.set(0.1)
        elif sayi == 0:
            self.lbl_sayi.configure(text="0", text_color=C_MUTED2,
                                     font=ctk.CTkFont("Helvetica", 42, "bold"))
            self.configure(border_color=C_BORDER)
            self.bar.configure(progress_color=C_MUTED)
            self.bar.set(0)
        else:
            self.lbl_sayi.configure(text=str(sayi), text_color=C_GREEN,
                                     font=ctk.CTkFont("Helvetica", 42, "bold"))
            self.configure(border_color="#1a3a2a")
            self.bar.configure(progress_color=C_GREEN)
            self.bar.set(sayi / maksimum if maksimum > 0 else 0)

    def yukleniyor(self):
        self.lbl_sayi.configure(text="...", text_color=C_AMBER,
                                  font=ctk.CTkFont("Helvetica", 28, "bold"))
        self.configure(border_color="#2a2010")
        self.bar.configure(progress_color=C_AMBER)
        self.bar.set(0.3)


class SiteEkleDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Site Ekle")
        self.geometry("420x290")
        self.resizable(False, False)
        self.configure(fg_color=C_BG)
        self.transient(parent)
        self.grab_set()
        self.sonuc = None
        self._build()
        self.after(100, self.lift)

    def _build(self):
        ctk.CTkLabel(self, text="Yeni Site Ekle",
                     font=ctk.CTkFont("Helvetica", 16, "bold"),
                     text_color=C_TEXT).pack(pady=(24,20))

        f = ctk.CTkFrame(self, fg_color="transparent")
        f.pack(fill="x", padx=32)

        ctk.CTkLabel(f, text="Site Adı", font=ctk.CTkFont(size=11),
                     text_color=C_MUTED2).pack(anchor="w")
        self.e_isim = ctk.CTkEntry(f, height=38, fg_color=C_CARD,
                                    border_color=C_BORDER, text_color=C_TEXT,
                                    font=ctk.CTkFont(size=13))
        self.e_isim.pack(fill="x", pady=(2,10))

        ctk.CTkLabel(f, text="swidget Kodu", font=ctk.CTkFont(size=11),
                     text_color=C_MUTED2).pack(anchor="w")
        self.e_kod = ctk.CTkEntry(f, height=38, fg_color=C_CARD,
                                   border_color=C_BORDER, text_color=C_TEXT,
                                   font=ctk.CTkFont("Courier", 12),
                                   placeholder_text="whos.amung.us/swidget/KOD veya direkt kod")
        self.e_kod.pack(fill="x", pady=(2,16))

        ctk.CTkButton(f, text="Ekle", height=40, corner_radius=10,
                      fg_color=C_GREEN, hover_color="#1aaa5a", text_color="#000",
                      font=ctk.CTkFont("Helvetica", 13, "bold"),
                      command=self._tamam).pack(fill="x")

        self.bind("<Return>", lambda e: self._tamam())
        self.e_isim.focus_set()

    def _tamam(self):
        isim = self.e_isim.get().strip()
        kod  = re.sub(r'.*/swidget/', '', self.e_kod.get().strip()).strip("/")
        if not isim or not kod:
            return
        self.sonuc = (isim, kod)
        self.destroy()


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.app_name = "Online Sayaç"
        self.title(self.app_name)
        
        self.icon_base_path = get_resource_path("logo.ico")
        self.temp_icon_path = os.path.join(os.environ.get('TEMP', BASE_DIR), f"icon_{int(time.time())}.ico")
        
        try:
            if os.path.exists(self.icon_base_path):
                self.iconbitmap(self.icon_base_path)
        except:
            pass

        self.geometry("860x620")
        self.minsize(640, 480)
        self.configure(fg_color=C_BG)

        self.siteler    = conf_oku()
        self.kartlar    = {}
        self._yukleniyor = False
        self._auto_on   = True
        self._last_count = -1

        self._build_ui()
        
        self.after(300, self.hepsini_guncelle)
        self.after(30000, self._auto_loop)

    def _build_ui(self):
        sidebar = ctk.CTkFrame(self, width=220, fg_color=C_CARD,
                                corner_radius=0, border_width=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        ctk.CTkLabel(sidebar, text="◉  Online\n    Sayaç",
                     font=ctk.CTkFont("Helvetica", 20, "bold"),
                     text_color=C_TEXT, justify="left").pack(anchor="w", padx=24, pady=(32,8))

        ctk.CTkLabel(sidebar, text="whos.amung.us",
                     font=ctk.CTkFont("Courier", 10),
                     text_color=C_MUTED).pack(anchor="w", padx=24, pady=(0,32))

        ctk.CTkFrame(sidebar, height=1, fg_color=C_BORDER).pack(fill="x", padx=20, pady=(0,24))

        toplam_frame = ctk.CTkFrame(sidebar, fg_color=C_CARD2, corner_radius=12)
        toplam_frame.pack(fill="x", padx=16, pady=(0,24))

        ctk.CTkLabel(toplam_frame, text="TOPLAM ONLİNE",
                     font=ctk.CTkFont("Helvetica", 9, "bold"),
                     text_color=C_MUTED).pack(pady=(14,2))
        self.lbl_toplam = ctk.CTkLabel(toplam_frame, text="—",
                                        font=ctk.CTkFont("Helvetica", 48, "bold"),
                                        text_color=C_GREEN)
        self.lbl_toplam.pack(pady=(0,14))

        ctk.CTkButton(sidebar, text="↻   Yenile", height=42, corner_radius=10,
                      fg_color=C_CARD2, hover_color="#1e1e38",
                      text_color=C_TEXT, font=ctk.CTkFont("Helvetica", 13),
                      command=self.hepsini_guncelle).pack(fill="x", padx=16, pady=(0,8))

        ctk.CTkButton(sidebar, text="+   Site Ekle", height=42, corner_radius=10,
                      fg_color=C_GREEN, hover_color="#1aaa5a",
                      text_color="#000", font=ctk.CTkFont("Helvetica", 13, "bold"),
                      command=self.site_ekle).pack(fill="x", padx=16, pady=(0,8))

        btn_text = "⏱   Otomatik: 30s" if self._auto_on else "⏱   Otomatik: Kapalı"
        btn_color = C_GREEN if self._auto_on else C_MUTED
        btn_fg = "#0d2018" if self._auto_on else C_CARD2
        
        self.btn_auto = ctk.CTkButton(sidebar, text=btn_text,
                                       height=42, corner_radius=10,
                                       fg_color=btn_fg, hover_color="#1e1e38",
                                       text_color=btn_color,
                                       font=ctk.CTkFont("Helvetica", 12),
                                       command=self.toggle_auto)
        self.btn_auto.pack(fill="x", padx=16)

        self.lbl_zaman = ctk.CTkLabel(sidebar, text="",
                                       font=ctk.CTkFont("Courier", 9),
                                       text_color=C_MUTED)
        self.lbl_zaman.pack(side="bottom", pady=16)

        main = ctk.CTkFrame(self, fg_color=C_BG, corner_radius=0)
        main.pack(side="left", fill="both", expand=True)

        self.scroll = ctk.CTkScrollableFrame(main, fg_color=C_BG,
                                              scrollbar_button_color=C_BORDER,
                                              scrollbar_button_hover_color=C_MUTED)
        self.scroll.pack(fill="both", expand=True, padx=20, pady=20)

        self._kartlari_ciz()

    def _update_taskbar_icon(self, count):
        if count == self._last_count:
            return
        
        self._last_count = count
        try:
            img = Image.new("RGBA", (256, 256), color=(13, 13, 20, 255))
            draw = ImageDraw.Draw(img)
            
            try:
                font_size = 180 if count < 100 else 140
                font = ImageFont.truetype("arialbd.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            text = str(count)
            bbox = draw.textbbox((0, 0), text, font=font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            
            draw.text(((256 - w) / 2, (256 - h) / 2 - 20), 
                      text, fill="#22d37a", font=font)
            
            draw.rectangle([20, 230, 236, 245], fill="#4d9cff")
            
            img.save(self.temp_icon_path, format="ICO", sizes=[(256, 256), (64, 64), (32, 32), (16, 16)])
            self.iconbitmap(self.temp_icon_path)
            
            del draw
            del img
            
        except Exception as e:
            print(f"İkon hatası: {e}")

    def _kartlari_ciz(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        self.kartlar = {}

        if not self.siteler:
            ctk.CTkLabel(self.scroll,
                         text="Henüz site eklenmedi.\n\nSol panelden '+ Site Ekle' butonuna tıklayın.",
                         font=ctk.CTkFont("Helvetica", 13),
                         text_color=C_MUTED).pack(pady=100)
            return

        self.scroll.grid_columnconfigure((0,1,2), weight=1)
        for i, (isim, kod) in enumerate(self.siteler.items()):
            kart = SiteKart(self.scroll, isim, kod, self.site_sil)
            kart.grid(row=i//3, column=i%3, padx=8, pady=8, sticky="nsew")
            self.kartlar[isim] = kart

    def hepsini_guncelle(self):
        if self._yukleniyor:
            return
        self._yukleniyor = True
        for k in self.kartlar.values():
            k.yukleniyor()
        
        t = threading.Thread(target=self._fetch_all, daemon=True)
        t.start()

    def _fetch_all(self):
        sonuclar = {}
        threads  = []
        def fetch(isim, kod):
            sonuclar[isim] = online_al(kod)
        
        for isim, kod in self.siteler.items():
            t = threading.Thread(target=fetch, args=(isim, kod), daemon=True)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join(timeout=15)
            
        self.after(0, lambda: self._guncelle_ui(sonuclar))

    def _guncelle_ui(self, sonuclar):
        try:
            toplam  = sum(v for v in sonuclar.values() if v is not None)
            valid_values = [v for v in sonuclar.values() if v is not None]
            maksimum = max(valid_values, default=1)
            
            for isim, sayi in sonuclar.items():
                if isim in self.kartlar:
                    self.kartlar[isim].guncelle(sayi, maksimum)
            
            self.lbl_toplam.configure(text=str(toplam))
            self.title(f"({toplam}) {self.app_name}")
            self._update_taskbar_icon(toplam)
            
            self.lbl_zaman.configure(text=f"güncellendi\n{time.strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"UI Güncelleme hatası: {e}")
        finally:
            self._yukleniyor = False

    def site_ekle(self):
        dlg = SiteEkleDialog(self)
        self.wait_window(dlg)
        if dlg.sonuc:
            isim, kod = dlg.sonuc
            self.siteler[isim] = kod
            conf_yaz(self.siteler)
            self._kartlari_ciz()
            self.hepsini_guncelle()

    def site_sil(self, isim):
        if isim in self.siteler:
            del self.siteler[isim]
            conf_yaz(self.siteler)
            self._kartlari_ciz()
            self.hepsini_guncelle()

    def toggle_auto(self):
        self._auto_on = not self._auto_on
        if self._auto_on:
            self.btn_auto.configure(text="⏱   Otomatik: 30s",
                                     text_color=C_GREEN, fg_color="#0d2018")
            self._auto_loop()
        else:
            self.btn_auto.configure(text="⏱   Otomatik: Kapalı",
                                     text_color=C_MUTED, fg_color=C_CARD2)

    def _auto_loop(self):
        if not self._auto_on:
            return
        self.hepsini_guncelle()
        self.after(30000, self._auto_loop)

    def on_closing(self):
        try:
            if os.path.exists(self.temp_icon_path):
                os.remove(self.temp_icon_path)
        except:
            pass
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()