"""
Img2Pdf - Image to PDF Converter / Conversor de Imagens para PDF
Supports / Suporta: PNG, JPG, JPEG, BMP, GIF, TIFF, WEBP
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import threading
import configparser
from PIL import Image
import io

# ── PyInstaller compatibility ────────────────────────────────────────────────
def resource_path(relative):
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)

def _exe_dir():
    """Directory of the running executable (frozen or script)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def _config_path():
    suffix = "windows" if sys.platform == "win32" else "linux"
    return os.path.join(_exe_dir(), f"img2pdf_z_config_{suffix}.ini")

# ── colour palettes ──────────────────────────────────────────────────────────
DARK = {
    "BG":         "#1E1E2E",
    "SURFACE":    "#2A2A3E",
    "ACCENT":     "#7C5CFC",
    "ACCENT2":    "#A78BFA",
    "TEXT":       "#E2E8F0",
    "TEXT_DIM":   "#94A3B8",
    "SUCCESS":    "#4ADE80",
    "ERROR":      "#F87171",
    "BORDER":     "#3A3A54",
    "BTN_TEAL":   "#0D9488",
    "BTN_AMBER":  "#B45309",
    "BTN_INDIGO": "#3730A3",
    "BTN_GREEN":  "#16A34A",
    "HEADER_FG":  "white",
    "HEADER_SUB": "#EDE9FE",
    "LANG_BTN":   "#5B3FD4",
    "LANG_BTN_H": "#4C32B0",
    "THEME_BTN":  "#3A3A54",
    "THEME_BTN_H":"#2A2A3E",
    "SELECT_BG":  "#7C5CFC",
    "SELECT_FG":  "white",
    "LB_FG":      "#E2E8F0",
    "LB_BG":      "#2A2A3E",
}

LIGHT = {
    "BG":         "#F0F4F8",
    "SURFACE":    "#FFFFFF",
    "ACCENT":     "#7C5CFC",
    "ACCENT2":    "#6D4EE8",
    "TEXT":       "#1E1E2E",
    "TEXT_DIM":   "#64748B",
    "SUCCESS":    "#16A34A",
    "ERROR":      "#DC2626",
    "BORDER":     "#CBD5E1",
    "BTN_TEAL":   "#0D9488",
    "BTN_AMBER":  "#B45309",
    "BTN_INDIGO": "#3730A3",
    "BTN_GREEN":  "#16A34A",
    "HEADER_FG":  "white",
    "HEADER_SUB": "#EDE9FE",
    "LANG_BTN":   "#5B3FD4",
    "LANG_BTN_H": "#4C32B0",
    "THEME_BTN":  "#E2E8F0",
    "THEME_BTN_H":"#CBD5E1",
    "SELECT_BG":  "#7C5CFC",
    "SELECT_FG":  "white",
    "LB_FG":      "#1E1E2E",
    "LB_BG":      "#FFFFFF",
}

SUPPORTED = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".tif", ".webp")

# ── i18n strings ─────────────────────────────────────────────────────────────
STRINGS = {
    "pt": {
        "title":            "Img2PdfZ — Conversor de Imagens",
        "subtitle":         "Converta imagens em PDF com facilidade",
        "lang_toggle":      "EN",
        "theme_dark":       "☀ Claro",
        "theme_light":      "☾ Escuro",
        "options_hdr":      "⚙  Opções",
        "page_size_lbl":    "Tamanho da página",
        "page_auto":        "Automático",
        "page_values":      ["Automático", "A4", "A3", "Letter", "Legal"],
        "orientation_lbl":  "Orientação",
        "portrait":         "Retrato",
        "landscape":        "Paisagem",
        "jpeg_quality_lbl": "Qualidade JPEG (%)",
        "margin_lbl":       "Margem (pt)",
        "one_per_page":     "Uma imagem por página",
        "add_images_btn":   "➕  Adicionar imagens",
        "list_hdr":         "📋  Imagens selecionadas",
        "files_count":      "{n} arquivo(s)",
        "btn_up":           "▲ Subir",
        "btn_down":         "▼ Descer",
        "btn_remove":       "✕ Remover",
        "btn_clear":        "🗑 Limpar",
        "ready":            "Pronto.",
        "btn_png2jpg":      "🎨  PNG → JPG",
        "btn_via_jpg":      "📦  PNG → JPG → PDF\n(menor tamanho)",
        "btn_each_pdf":     "📄  Cada imagem\n→ PDF separado",
        "btn_convert":      "🚀  Converter\ntodas → PDF",
        "btn_open_folder":  "📂  Abrir pasta de saída",
        "credits":          "Feito por Ium101",
        "warn_title":       "Aviso",
        "warn_add":         "Adicione ao menos uma imagem para {action}!",
        "warn_no_png":      "Nenhuma imagem PNG na lista.\nAdicione arquivos .png para usar esta função.",
        "dlg_jpg_dest":     "Escolha a pasta de destino para os arquivos JPG",
        "dlg_pdf_save":     "Salvar PDF como...",
        "dlg_pdf_comp":     "Salvar PDF comprimido como...",
        "dlg_each_dest":    "Escolha a pasta de destino para os PDFs individuais",
        "success_title":    "Concluído!",
        "success_pdf":      "PDF gerado com sucesso!\n\n{path}",
        "success_pdf_jpg":  "PDF gerado com sucesso (via JPG)!\n\n{path}",
        "success_jpg":      "{n} PNG(s) convertido(s) para JPG.\n\nPasta: {folder}",
        "success_each":     "{n} imagem(ns) convertida(s) para PDFs individuais.\n\nPasta: {folder}",
        "err_title":        "Erro",
        "err_msg":          "Falha:\n{e}",
        "err_convert":      "Falha ao converter:\n{e}",
        "prog_loading":     "Carregando {i}/{n}: {name}",
        "prog_converting":  "Convertendo {i}/{n}...",
        "prog_assembling":  "Montando PDF...",
        "prog_done":        "Concluído! {n} imagem(ns) → {name}",
        "prog_png2jpg":     "Convertendo {i}/{n}: {name}.png → .jpg",
        "prog_via_jpg":     "PNG→JPG {i}/{n}: {name}",
        "prog_each":        "Gerando PDF {i}/{n}: {name}.pdf",
        "out_jpg":          "{n} arquivo(s) JPG salvos em: {folder}",
        "out_pdf":          "Salvo em: {name}",
        "out_pdf_comp":     "PDF comprimido salvo: {name}",
        "out_each":         "{n} PDF(s) salvos em: {folder}",
    },
    "en": {
        "title":            "Img2PdfZ — Image Converter",
        "subtitle":         "Convert images to PDF with ease",
        "lang_toggle":      "PT",
        "theme_dark":       "☀ Light",
        "theme_light":      "☾ Dark",
        "options_hdr":      "⚙  Options",
        "page_size_lbl":    "Page size",
        "page_auto":        "Automatic",
        "page_values":      ["Automatic", "A4", "A3", "Letter", "Legal"],
        "orientation_lbl":  "Orientation",
        "portrait":         "Portrait",
        "landscape":        "Landscape",
        "jpeg_quality_lbl": "JPEG Quality (%)",
        "margin_lbl":       "Margin (pt)",
        "one_per_page":     "One image per page",
        "add_images_btn":   "➕  Add images",
        "list_hdr":         "📋  Selected images",
        "files_count":      "{n} file(s)",
        "btn_up":           "▲ Up",
        "btn_down":         "▼ Down",
        "btn_remove":       "✕ Remove",
        "btn_clear":        "🗑 Clear",
        "ready":            "Ready.",
        "btn_png2jpg":      "🎨  PNG → JPG",
        "btn_via_jpg":      "📦  PNG → JPG → PDF\n(smaller size)",
        "btn_each_pdf":     "📄  Each image\n→ separate PDF",
        "btn_convert":      "🚀  Convert\nall → PDF",
        "btn_open_folder":  "📂  Open output folder",
        "credits":          "Made by Ium101",
        "warn_title":       "Warning",
        "warn_add":         "Add at least one image to {action}!",
        "warn_no_png":      "No PNG images in the list.\nAdd .png files to use this function.",
        "dlg_jpg_dest":     "Choose destination folder for JPG files",
        "dlg_pdf_save":     "Save PDF as...",
        "dlg_pdf_comp":     "Save compressed PDF as...",
        "dlg_each_dest":    "Choose destination folder for individual PDFs",
        "success_title":    "Done!",
        "success_pdf":      "PDF generated successfully!\n\n{path}",
        "success_pdf_jpg":  "PDF generated successfully (via JPG)!\n\n{path}",
        "success_jpg":      "{n} PNG(s) converted to JPG.\n\nFolder: {folder}",
        "success_each":     "{n} image(s) converted to individual PDFs.\n\nFolder: {folder}",
        "err_title":        "Error",
        "err_msg":          "Failed:\n{e}",
        "err_convert":      "Conversion failed:\n{e}",
        "prog_loading":     "Loading {i}/{n}: {name}",
        "prog_converting":  "Converting {i}/{n}...",
        "prog_assembling":  "Assembling PDF...",
        "prog_done":        "Done! {n} image(s) → {name}",
        "prog_png2jpg":     "Converting {i}/{n}: {name}.png → .jpg",
        "prog_via_jpg":     "PNG→JPG {i}/{n}: {name}",
        "prog_each":        "Generating PDF {i}/{n}: {name}.pdf",
        "out_jpg":          "{n} JPG file(s) saved to: {folder}",
        "out_pdf":          "Saved to: {name}",
        "out_pdf_comp":     "Compressed PDF saved: {name}",
        "out_each":         "{n} PDF(s) saved to: {folder}",
    },
}

_AUTO_LABELS = {"Automático", "Automatic"}


# ─────────────────────────────────────────────────────────────────────────────
class DragListbox(tk.Frame):
    """Image list with reorder buttons. Supports live language + theme switching."""

    def __init__(self, master, get_S, get_P, **kw):
        self._get_S = get_S
        self._get_P = get_P
        P = get_P()
        kw.setdefault("bg", P["SURFACE"])
        kw.setdefault("highlightthickness", 0)
        kw.setdefault("bd", 0)
        super().__init__(master, **kw)
        self._build()

    def _build(self):
        P = self._get_P()
        hdr = tk.Frame(self, bg=P["SURFACE"], highlightthickness=0)
        hdr.pack(fill="x", padx=8, pady=(8, 4))
        self._hdr_lbl = tk.Label(hdr, bg=P["SURFACE"], fg=P["TEXT"],
                                  font=("Segoe UI", 10, "bold"))
        self._hdr_lbl.pack(side="left")
        self._count_lbl = tk.Label(hdr, bg=P["SURFACE"], fg=P["TEXT_DIM"],
                                    font=("Segoe UI", 9))
        self._count_lbl.pack(side="right")

        self._lb_frame = tk.Frame(self, bg=P["BORDER"], bd=0, highlightthickness=0)
        self._lb_frame.pack(fill="both", expand=True, padx=8, pady=4)
        self.lb = tk.Listbox(
            self._lb_frame, bg=P["LB_BG"], fg=P["LB_FG"],
            selectbackground=P["SELECT_BG"],
            selectforeground=P["SELECT_FG"],
            font=("Segoe UI", 9),
            relief="flat", bd=0, highlightthickness=0, activestyle="none")
        sb = ttk.Scrollbar(self._lb_frame, orient="vertical", command=self.lb.yview)
        self.lb.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.lb.pack(fill="both", expand=True, padx=1, pady=1)

        self._btn_row = tk.Frame(self, bg=P["SURFACE"], highlightthickness=0)
        self._btn_row.pack(fill="x", padx=8, pady=(0, 8))
        self._btn_up   = self._mk_btn(self._btn_row, self._move_up,   P["ACCENT"])
        self._btn_down = self._mk_btn(self._btn_row, self._move_down, P["ACCENT"])
        self._btn_rem  = self._mk_btn(self._btn_row, self._remove,    "#E05252")
        self._btn_clr  = self._mk_btn(self._btn_row, self._clear,     "#555577")

        self.update_lang()

    def _mk_btn(self, parent, cmd, color):
        b = tk.Button(parent, text="", command=cmd,
                      bg=color, fg="white", font=("Segoe UI", 8, "bold"),
                      relief="flat", bd=0, padx=8, pady=4,
                      cursor="hand2", activebackground=self._get_P()["ACCENT2"],
                      activeforeground="white")
        b.pack(side="left", padx=(0, 4))
        return b

    # ── public ───────────────────────────────────────────────────────────────
    def update_lang(self):
        S = self._get_S()
        self._hdr_lbl.config(text=S["list_hdr"])
        self._btn_up.config(text=S["btn_up"])
        self._btn_down.config(text=S["btn_down"])
        self._btn_rem.config(text=S["btn_remove"])
        self._btn_clr.config(text=S["btn_clear"])
        self._update_count()

    def apply_theme(self):
        P = self._get_P()
        self.config(bg=P["SURFACE"])
        for child in self.winfo_children():
            child.config(bg=P["SURFACE"])
        self._lb_frame.config(bg=P["BORDER"])
        self._hdr_lbl.config(bg=P["SURFACE"], fg=P["TEXT"])
        self._count_lbl.config(bg=P["SURFACE"], fg=P["TEXT_DIM"])
        self._btn_row.config(bg=P["SURFACE"])
        self.lb.config(bg=P["LB_BG"], fg=P["LB_FG"],
                       selectbackground=P["SELECT_BG"],
                       selectforeground=P["SELECT_FG"])
        self._btn_up.config(bg=P["ACCENT"], activebackground=P["ACCENT2"])
        self._btn_down.config(bg=P["ACCENT"], activebackground=P["ACCENT2"])

    def add(self, paths):
        existing = list(self.lb.get(0, "end"))
        added = 0
        for p in paths:
            if p not in existing and p.lower().endswith(SUPPORTED):
                self.lb.insert("end", p)
                added += 1
        self._update_count()
        return added

    def get_all(self):
        return list(self.lb.get(0, "end"))

    def clear(self):
        self.lb.delete(0, "end")
        self._update_count()

    # ── private ──────────────────────────────────────────────────────────────
    def _update_count(self):
        n = self.lb.size()
        self._count_lbl.config(
            text=self._get_S()["files_count"].format(n=n))

    def _move_up(self):
        sel = self.lb.curselection()
        if not sel or sel[0] == 0:
            return
        i, txt = sel[0], self.lb.get(sel[0])
        self.lb.delete(i)
        self.lb.insert(i - 1, txt)
        self.lb.selection_set(i - 1)

    def _move_down(self):
        sel = self.lb.curselection()
        if not sel or sel[0] == self.lb.size() - 1:
            return
        i, txt = sel[0], self.lb.get(sel[0])
        self.lb.delete(i)
        self.lb.insert(i + 1, txt)
        self.lb.selection_set(i + 1)

    def _remove(self):
        sel = self.lb.curselection()
        if sel:
            self.lb.delete(sel[0])
            self._update_count()

    def _clear(self):
        self.lb.delete(0, "end")
        self._update_count()


# ─────────────────────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.lang  = "pt"
        self.theme = "dark"
        self._page_was_auto = True
        self._load_config()

        self.geometry("800x700")
        self.minsize(800, 580)
        self.maxsize(800, 4096)
        self.configure(bg=self.P["BG"])
        self._style()
        self._build()
        self._try_dnd()
        self._apply_lang()
        self._apply_theme()

    # ── palette shortcut ─────────────────────────────────────────────────────
    @property
    def P(self):
        return DARK if self.theme == "dark" else LIGHT

    @property
    def S(self):
        return STRINGS[self.lang]

    # ── config persistence ───────────────────────────────────────────────────
    def _load_config(self):
        cfg = configparser.ConfigParser()
        path = _config_path()
        try:
            cfg.read(path, encoding="utf-8")
            sec = cfg["settings"]
            lang = sec.get("language", "pt")
            if lang in STRINGS:
                self.lang = lang
            theme = sec.get("theme", "dark")
            if theme in ("dark", "light"):
                self.theme = theme
            # restore slider/option values — will be applied after widgets built
            self._cfg_quality     = sec.getint("jpeg_quality", 85)
            self._cfg_margin      = sec.getint("margin", 20)
            self._cfg_page        = sec.get("page_size", "")
            self._cfg_orientation = sec.get("orientation", "Portrait")
            self._cfg_one_per     = sec.getboolean("one_per_page", True)
        except Exception:
            self._cfg_quality     = 85
            self._cfg_margin      = 20
            self._cfg_page        = ""
            self._cfg_orientation = "Portrait"
            self._cfg_one_per     = True

    def _save_config(self):
        cfg = configparser.ConfigParser()
        cfg["settings"] = {
            "language":     self.lang,
            "theme":        self.theme,
            "jpeg_quality": str(self.quality_var.get()),
            "margin":       str(self.margin_var.get()),
            "page_size":    self.page_var.get(),
            "orientation":  self.orient_var.get(),
            "one_per_page": str(self.one_per_page.get()),
        }
        try:
            with open(_config_path(), "w", encoding="utf-8") as f:
                cfg.write(f)
        except Exception:
            pass

    # ── ttk styles ───────────────────────────────────────────────────────────
    def _style(self):
        P = self.P
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TScrollbar", background=P["BORDER"], troughcolor=P["SURFACE"],
                    bordercolor=P["SURFACE"], arrowcolor=P["TEXT_DIM"])
        s.configure("TCombobox", fieldbackground=P["SURFACE"], background=P["SURFACE"],
                    foreground=P["TEXT"], selectbackground=P["ACCENT"])
        s.map("TCombobox", fieldbackground=[("readonly", P["SURFACE"])])
        s.configure("TProgressbar", troughcolor=P["BORDER"],
                    background=P["ACCENT"], bordercolor=P["SURFACE"])

    def _restyle(self):
        """Re-apply ttk styles after theme change."""
        P = self.P
        s = ttk.Style(self)
        s.configure("TScrollbar", background=P["BORDER"], troughcolor=P["SURFACE"],
                    bordercolor=P["SURFACE"], arrowcolor=P["TEXT_DIM"])
        s.configure("TCombobox", fieldbackground=P["SURFACE"], background=P["SURFACE"],
                    foreground=P["TEXT"], selectbackground=P["ACCENT"])
        s.map("TCombobox", fieldbackground=[("readonly", P["SURFACE"])])
        s.configure("TProgressbar", troughcolor=P["BORDER"],
                    background=P["ACCENT"], bordercolor=P["SURFACE"])

    # ── main layout ──────────────────────────────────────────────────────────
    def _build(self):
        self._build_header()

        self._center = tk.Frame(self, bg=self.P["BG"], highlightthickness=0)
        self._center.pack(fill="both", expand=True, padx=16, pady=12)

        self._left = tk.Frame(self._center, bg=self.P["SURFACE"],
                              bd=0, highlightthickness=0, width=224)
        self._left.pack(side="left", fill="y", padx=(0, 10))
        self._left.pack_propagate(False)
        self._build_options(self._left)

        self.file_list = DragListbox(
            self._center, get_S=lambda: self.S, get_P=lambda: self.P)
        self.file_list.pack(side="left", fill="both", expand=True)

        self._build_footer()

        # restore saved option values now that widgets exist
        self.quality_var.set(self._cfg_quality)
        self.qual_lbl.config(text=str(self._cfg_quality))
        self.margin_var.set(self._cfg_margin)
        self.marg_lbl.config(text=str(self._cfg_margin))
        self.orient_var.set(self._cfg_orientation)
        self.one_per_page.set(self._cfg_one_per)
        # page_size restored in _apply_lang via _page_was_auto logic

    # ── header ───────────────────────────────────────────────────────────────
    def _build_header(self):
        P = self.P
        self._top = tk.Frame(self, bg=P["ACCENT"], height=56)
        self._top.pack(fill="x")
        self._top.pack_propagate(False)

        tk.Label(self._top, text="  Img2PdfZ", bg=P["ACCENT"], fg=P["HEADER_FG"],
                 font=("Segoe UI", 16, "bold")).pack(side="left", padx=20)
        self._lbl_subtitle = tk.Label(self._top, bg=P["ACCENT"], fg=P["HEADER_SUB"],
                                       font=("Segoe UI", 10))
        self._lbl_subtitle.pack(side="left")

        # language toggle
        self._lang_btn = tk.Button(
            self._top, text="", command=self._toggle_lang,
            bg=P["LANG_BTN"], fg="white", font=("Segoe UI", 9, "bold"),
            relief="flat", bd=0, padx=14, pady=6,
            cursor="hand2", activebackground=P["LANG_BTN_H"],
            activeforeground="white")
        self._lang_btn.pack(side="right", padx=(8, 16), pady=10)

        # theme toggle
        self._theme_btn = tk.Button(
            self._top, text="", command=self._toggle_theme,
            bg=P["THEME_BTN"], fg=P["TEXT"], font=("Segoe UI", 9, "bold"),
            relief="flat", bd=0, padx=14, pady=6,
            cursor="hand2", activebackground=P["THEME_BTN_H"],
            activeforeground=P["TEXT"])
        self._theme_btn.pack(side="right", padx=(0, 4), pady=10)

    # ── options panel ────────────────────────────────────────────────────────
    def _build_options(self, parent):
        P = self.P

        def sep():
            tk.Frame(parent, bg=P["BORDER"], height=1).pack(
                fill="x", padx=12, pady=6)

        self._lbl_options_hdr = tk.Label(
            parent, bg=P["SURFACE"], fg=P["TEXT"], font=("Segoe UI", 11, "bold"))
        self._lbl_options_hdr.pack(anchor="w", padx=14, pady=(14, 6))

        sep()
        self._lbl_page_size = tk.Label(
            parent, bg=P["SURFACE"], fg=P["TEXT_DIM"], font=("Segoe UI", 9))
        self._lbl_page_size.pack(anchor="w", padx=14)
        self.page_var = tk.StringVar()
        self._cb_page = ttk.Combobox(
            parent, textvariable=self.page_var, state="readonly",
            width=18, font=("Segoe UI", 9))
        self._cb_page.pack(padx=14, pady=(2, 8))

        sep()
        self._lbl_orientation = tk.Label(
            parent, bg=P["SURFACE"], fg=P["TEXT_DIM"], font=("Segoe UI", 9))
        self._lbl_orientation.pack(anchor="w", padx=14)
        self.orient_var = tk.StringVar(value="Portrait")
        self._rb_portrait = tk.Radiobutton(
            parent, variable=self.orient_var, value="Portrait",
            bg=P["SURFACE"], fg=P["TEXT"], selectcolor=P["SURFACE"],
            activebackground=P["SURFACE"], activeforeground=P["ACCENT2"],
            font=("Segoe UI", 9))
        self._rb_portrait.pack(anchor="w", padx=22)
        self._rb_landscape = tk.Radiobutton(
            parent, variable=self.orient_var, value="Landscape",
            bg=P["SURFACE"], fg=P["TEXT"], selectcolor=P["SURFACE"],
            activebackground=P["SURFACE"], activeforeground=P["ACCENT2"],
            font=("Segoe UI", 9))
        self._rb_landscape.pack(anchor="w", padx=22)

        sep()
        self._lbl_jpeg_quality = tk.Label(
            parent, bg=P["SURFACE"], fg=P["TEXT_DIM"], font=("Segoe UI", 9))
        self._lbl_jpeg_quality.pack(anchor="w", padx=14)
        self.quality_var = tk.IntVar(value=85)
        qual_row = tk.Frame(parent, bg=P["SURFACE"], highlightthickness=0)
        qual_row.pack(fill="x", padx=14)
        self.qual_lbl = tk.Label(qual_row, text="85", bg=P["SURFACE"], fg=P["ACCENT2"],
                                  font=("Segoe UI", 9, "bold"), width=3)
        self.qual_lbl.pack(side="right")
        self._scale_quality = tk.Scale(
            qual_row, from_=10, to=100, orient="horizontal",
            variable=self.quality_var, bg=P["SURFACE"], fg=P["TEXT"],
            troughcolor=P["BORDER"], highlightthickness=0,
            sliderrelief="flat", bd=0,
            command=lambda v: self.qual_lbl.config(text=v))
        self._scale_quality.pack(fill="x", expand=True, side="left")

        sep()
        self._lbl_margin = tk.Label(
            parent, bg=P["SURFACE"], fg=P["TEXT_DIM"], font=("Segoe UI", 9))
        self._lbl_margin.pack(anchor="w", padx=14)
        self.margin_var = tk.IntVar(value=20)
        mr = tk.Frame(parent, bg=P["SURFACE"], highlightthickness=0)
        mr.pack(fill="x", padx=14)
        self.marg_lbl = tk.Label(mr, text="20", bg=P["SURFACE"], fg=P["ACCENT2"],
                                  font=("Segoe UI", 9, "bold"), width=3)
        self.marg_lbl.pack(side="right")
        self._scale_margin = tk.Scale(
            mr, from_=0, to=72, orient="horizontal",
            variable=self.margin_var, bg=P["SURFACE"], fg=P["TEXT"],
            troughcolor=P["BORDER"], highlightthickness=0,
            sliderrelief="flat", bd=0,
            command=lambda v: self.marg_lbl.config(text=v))
        self._scale_margin.pack(fill="x", expand=True, side="left")

        sep()
        self.one_per_page = tk.BooleanVar(value=True)
        self._cb_one_per_page = tk.Checkbutton(
            parent, variable=self.one_per_page,
            bg=P["SURFACE"], fg=P["TEXT"], selectcolor=P["SURFACE"],
            activebackground=P["SURFACE"], activeforeground=P["ACCENT2"],
            font=("Segoe UI", 9))
        self._cb_one_per_page.pack(anchor="w", padx=14)

        sep()
        self._btn_add = tk.Button(
            parent, command=self._add_images,
            bg=P["ACCENT"], fg="white", font=("Segoe UI", 9, "bold"),
            relief="flat", bd=0, pady=8, cursor="hand2",
            activebackground=P["ACCENT2"], activeforeground="white")
        self._btn_add.pack(fill="x", padx=14, pady=(4, 14))

    # ── footer ───────────────────────────────────────────────────────────────
    def _build_footer(self):
        P = self.P
        self._foot = tk.Frame(self, bg=P["SURFACE"], bd=0, highlightthickness=0)
        self._foot.pack(fill="x", padx=16, pady=(0, 12))

        inner = tk.Frame(self._foot, bg=P["SURFACE"], highlightthickness=0)
        inner.pack(fill="both", padx=12, pady=10)
        self._foot_inner = inner

        self.prog_lbl = tk.Label(inner, bg=P["SURFACE"], fg=P["TEXT_DIM"],
                                  font=("Segoe UI", 9))
        self.prog_lbl.pack(anchor="w")
        self.progress = ttk.Progressbar(inner, mode="determinate")
        self.progress.pack(fill="x", pady=(4, 10))

        grid = tk.Frame(inner, bg=P["SURFACE"], highlightthickness=0)
        grid.pack(fill="x", pady=(0, 8))
        self._btn_grid = grid
        for c in range(4):
            grid.columnconfigure(c, weight=1, uniform="btn")

        btn_defs = [
            ("_btn_png2jpg",  P["BTN_TEAL"],   "#0F766E",  0, self._png_to_jpg),
            ("_btn_via_jpg",  P["BTN_AMBER"],  "#92400E",  1, self._convert_via_jpg),
            ("_btn_each_pdf", P["BTN_INDIGO"], "#312E81",  2, self._convert_each_to_pdf),
            ("_btn_convert",  P["BTN_GREEN"],  "#15803D",  3, self._convert),
        ]
        for attr, bg, hover, col, cmd in btn_defs:
            btn = tk.Button(
                grid, text="", command=cmd,
                bg=bg, fg="white", font=("Segoe UI", 9, "bold"),
                relief="flat", bd=0, padx=6, pady=10,
                cursor="hand2", wraplength=130, justify="center",
                activebackground=hover, activeforeground="white")
            btn.grid(row=0, column=col, sticky="nsew",
                     padx=(0, 6) if col < 3 else 0)
            setattr(self, attr, btn)

        util_row = tk.Frame(inner, bg=P["SURFACE"], highlightthickness=0)
        util_row.pack(fill="x", pady=(2, 0))
        self._util_row = util_row

        self._btn_open_folder = tk.Button(
            util_row, command=self._open_output_dir,
            bg=P["BORDER"], fg=P["TEXT"], font=("Segoe UI", 9),
            relief="flat", bd=0, padx=12, pady=5,
            cursor="hand2", activebackground=P["SURFACE"])
        self._btn_open_folder.pack(side="left")

        self.output_lbl = tk.Label(util_row, text="", bg=P["SURFACE"], fg=P["SUCCESS"],
                                    font=("Segoe UI", 9))
        self.output_lbl.pack(side="left", padx=(12, 0))

        self._lbl_credits = tk.Label(
            util_row, bg=P["SURFACE"], fg=P["TEXT_DIM"],
            font=("Segoe UI", 8, "italic"))
        self._lbl_credits.pack(side="right")

        self._last_output = ""

    # ── theme toggle & apply ──────────────────────────────────────────────────
    def _toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        self._restyle()
        self._apply_theme()
        self._save_config()

    @staticmethod
    def _all_descendants(widget):
        """Recursive replacement for the non-existent winfo_descendants()."""
        result = []
        for child in widget.winfo_children():
            result.append(child)
            result.extend(App._all_descendants(child))
        return result

    def _apply_theme(self):
        P = self.P
        S = self.S

        self.configure(bg=P["BG"])
        self._center.config(bg=P["BG"])

        # header
        self._top.config(bg=P["ACCENT"])
        for w in self._top.winfo_children():
            if isinstance(w, tk.Label):
                w.config(bg=P["ACCENT"])
        self._lbl_subtitle.config(bg=P["ACCENT"], fg=P["HEADER_SUB"])
        self._lang_btn.config(bg=P["LANG_BTN"], activebackground=P["LANG_BTN_H"])
        self._theme_btn.config(
            bg=P["THEME_BTN"], fg=P["TEXT"],
            activebackground=P["THEME_BTN_H"], activeforeground=P["TEXT"],
            text=S["theme_dark"] if self.theme == "dark" else S["theme_light"])

        # left panel + all option widgets
        self._left.config(bg=P["SURFACE"])
        for w in self._all_descendants(self._left):
            cls = type(w).__name__
            if cls == "Label":
                w.config(bg=P["SURFACE"])
                # dim labels
                if w in (self._lbl_page_size, self._lbl_orientation,
                          self._lbl_jpeg_quality, self._lbl_margin):
                    w.config(fg=P["TEXT_DIM"])
                else:
                    w.config(fg=P["TEXT"])
            elif cls == "Frame":
                w.config(bg=P["SURFACE"])
            elif cls == "Radiobutton":
                w.config(bg=P["SURFACE"], fg=P["TEXT"], selectcolor=P["SURFACE"],
                          activebackground=P["SURFACE"], activeforeground=P["ACCENT2"])
            elif cls == "Checkbutton":
                w.config(bg=P["SURFACE"], fg=P["TEXT"], selectcolor=P["SURFACE"],
                          activebackground=P["SURFACE"], activeforeground=P["ACCENT2"])
            elif cls == "Scale":
                w.config(bg=P["SURFACE"], fg=P["TEXT"], troughcolor=P["BORDER"])

        # separator lines (1px height Frames)
        for w in self._all_descendants(self._left):
            if isinstance(w, tk.Frame) and w.winfo_height() == 1:
                w.config(bg=P["BORDER"])

        self._lbl_options_hdr.config(fg=P["TEXT"])
        self.qual_lbl.config(bg=P["SURFACE"], fg=P["ACCENT2"])
        self.marg_lbl.config(bg=P["SURFACE"], fg=P["ACCENT2"])
        self._btn_add.config(bg=P["ACCENT"], activebackground=P["ACCENT2"])

        # footer
        self._foot.config(bg=P["SURFACE"])
        self._foot_inner.config(bg=P["SURFACE"])
        self._btn_grid.config(bg=P["SURFACE"])
        self._util_row.config(bg=P["SURFACE"])
        self.prog_lbl.config(bg=P["SURFACE"], fg=P["TEXT_DIM"])
        self.output_lbl.config(bg=P["SURFACE"], fg=P["SUCCESS"])
        self._lbl_credits.config(bg=P["SURFACE"], fg=P["TEXT_DIM"])
        self._btn_open_folder.config(bg=P["BORDER"], fg=P["TEXT"],
                                      activebackground=P["SURFACE"])

        # file list widget
        self.file_list.apply_theme()

    # ── language toggle & apply ───────────────────────────────────────────────
    def _toggle_lang(self):
        self._page_was_auto = self.page_var.get() in _AUTO_LABELS
        self.lang = "en" if self.lang == "pt" else "pt"
        self._apply_lang()
        self._save_config()

    def _apply_lang(self):
        S = self.S

        self.title(S["title"])
        self._lbl_subtitle.config(text=S["subtitle"])
        self._lang_btn.config(text=S["lang_toggle"])
        self._theme_btn.config(
            text=S["theme_dark"] if self.theme == "dark" else S["theme_light"])

        self._lbl_options_hdr.config(text=S["options_hdr"])
        self._lbl_page_size.config(text=S["page_size_lbl"])
        self._cb_page.config(values=S["page_values"])
        if self._page_was_auto or self.page_var.get() in _AUTO_LABELS:
            self.page_var.set(S["page_auto"])
        self._page_was_auto = False

        self._lbl_orientation.config(text=S["orientation_lbl"])
        self._rb_portrait.config(text=S["portrait"])
        self._rb_landscape.config(text=S["landscape"])
        self._lbl_jpeg_quality.config(text=S["jpeg_quality_lbl"])
        self._lbl_margin.config(text=S["margin_lbl"])
        self._cb_one_per_page.config(text=S["one_per_page"])
        self._btn_add.config(text=S["add_images_btn"])

        self.file_list.update_lang()

        idle_texts = {STRINGS["pt"]["ready"], STRINGS["en"]["ready"], ""}
        if self.prog_lbl.cget("text") in idle_texts:
            self.prog_lbl.config(text=S["ready"])

        self._btn_png2jpg.config(text=S["btn_png2jpg"])
        self._btn_via_jpg.config(text=S["btn_via_jpg"])
        self._btn_each_pdf.config(text=S["btn_each_pdf"])
        self._btn_convert.config(text=S["btn_convert"])
        self._btn_open_folder.config(text=S["btn_open_folder"])
        self._lbl_credits.config(text=S["credits"])

    # ── drag-and-drop (optional tkinterdnd2) ─────────────────────────────────
    def _try_dnd(self):
        try:
            from tkinterdnd2 import DND_FILES, TkinterDnD  # type: ignore
            pass
        except ImportError:
            pass

    # ── shared helpers ────────────────────────────────────────────────────────
    def _add_images(self):
        paths = filedialog.askopenfilenames(
            title=self.S["add_images_btn"].strip(),
            filetypes=[
                ("Images / Imagens",
                 "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.tif *.webp"),
                ("All / Todos", "*.*"),
            ])
        if paths:
            self.file_list.add(paths)

    def _open_output_dir(self):
        path = self._last_output or os.path.expanduser("~")
        folder = os.path.dirname(path) if os.path.isfile(path) else path
        if os.path.isdir(folder):
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                os.system(f'open "{folder}"')
            else:
                os.system(f'xdg-open "{folder}"')

    def _require_images(self, action_key="btn_convert"):
        images = self.file_list.get_all()
        if not images:
            action = self.S[action_key].replace("\n", " ").strip()
            messagebox.showwarning(
                self.S["warn_title"],
                self.S["warn_add"].format(action=action))
        return images

    def _to_rgb(self, img):
        if img.mode in ("RGBA", "LA", "P"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            bg.paste(img, mask=(img.split()[-1]
                                if img.mode in ("RGBA", "LA") else None))
            return bg
        return img if img.mode == "RGB" else img.convert("RGB")

    # ════════════════════════════════════════════════════════════════════════
    # 1.  PNG -> JPG  (individual files)
    # ════════════════════════════════════════════════════════════════════════
    def _png_to_jpg(self):
        images = self._require_images("btn_png2jpg")
        if not images:
            return
        pngs = [p for p in images if p.lower().endswith(".png")]
        if not pngs:
            messagebox.showwarning(self.S["warn_title"], self.S["warn_no_png"])
            return
        out_dir = filedialog.askdirectory(title=self.S["dlg_jpg_dest"])
        if not out_dir:
            return
        threading.Thread(target=self._do_png_to_jpg,
                         args=(pngs, out_dir), daemon=True).start()

    def _do_png_to_jpg(self, pngs, out_dir):
        self._set_ui_state(False)
        S, quality, total = self.S, self.quality_var.get(), len(pngs)
        try:
            for idx, path in enumerate(pngs):
                base = os.path.splitext(os.path.basename(path))[0]
                self.after(0, lambda i=idx, n=base: self.prog_lbl.config(
                    text=S["prog_png2jpg"].format(i=i+1, n=total, name=n),
                    fg=self.P["TEXT_DIM"]))
                self.after(0, lambda i=idx: self.progress.config(
                    value=int((i + 1) / total * 100)))
                img = self._to_rgb(Image.open(path))
                img.save(os.path.join(out_dir, base + ".jpg"),
                         "JPEG", quality=quality, optimize=True)

            self._last_output = out_dir
            self.after(0, lambda: self.output_lbl.config(
                text=S["out_jpg"].format(n=total, folder=out_dir), fg=self.P["SUCCESS"]))
            self.after(0, lambda: messagebox.showinfo(
                S["success_title"],
                S["success_jpg"].format(n=total, folder=out_dir)))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror(
                S["err_title"], S["err_msg"].format(e=e)))
            self.after(0, lambda: self.prog_lbl.config(
                text=S["err_msg"].format(e=e), fg=self.P["ERROR"]))
        finally:
            self.after(0, lambda: self._set_ui_state(True))
            self.after(0, lambda: self.progress.config(value=0))

    # ════════════════════════════════════════════════════════════════════════
    # 2.  PNG -> JPG -> PDF  (single smaller PDF)
    # ════════════════════════════════════════════════════════════════════════
    def _convert_via_jpg(self):
        images = self._require_images("btn_via_jpg")
        if not images:
            return
        out_path = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
            title=self.S["dlg_pdf_comp"], initialfile="Output.pdf")
        if not out_path:
            return
        threading.Thread(target=self._do_convert_via_jpg,
                         args=(images, out_path), daemon=True).start()

    def _do_convert_via_jpg(self, images, out_path):
        self._set_ui_state(False)
        S, quality, total = self.S, self.quality_var.get(), len(images)
        try:
            jpeg_images = []
            for idx, path in enumerate(images):
                nm = os.path.basename(path)
                self.after(0, lambda i=idx, n=nm: self.prog_lbl.config(
                    text=S["prog_via_jpg"].format(i=i+1, n=total, name=n),
                    fg=self.P["TEXT_DIM"]))
                self.after(0, lambda i=idx: self.progress.config(
                    value=int((i + 1) / total * 60)))
                img = self._to_rgb(Image.open(path))
                buf = io.BytesIO()
                img.save(buf, "JPEG", quality=quality, optimize=True)
                buf.seek(0)
                jpeg_images.append(Image.open(buf))

            self.after(0, lambda: self.prog_lbl.config(
                text=S["prog_assembling"], fg=self.P["TEXT_DIM"]))
            self.after(0, lambda: self.progress.config(value=80))

            first, rest = jpeg_images[0], jpeg_images[1:]
            first.save(out_path, "PDF", save_all=True,
                       append_images=rest, resolution=144.0)

            fname = os.path.basename(out_path)
            self._last_output = out_path
            self.after(0, lambda: self.output_lbl.config(
                text=S["out_pdf_comp"].format(name=fname), fg=self.P["SUCCESS"]))
            self.after(0, lambda: self.progress.config(value=100))
            self.after(0, lambda: self.prog_lbl.config(
                text=S["prog_done"].format(n=total, name=fname), fg=self.P["SUCCESS"]))
            self.after(0, lambda: messagebox.showinfo(
                S["success_title"],
                S["success_pdf_jpg"].format(path=out_path)))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror(
                S["err_title"], S["err_msg"].format(e=e)))
            self.after(0, lambda: self.prog_lbl.config(
                text=S["err_msg"].format(e=e), fg=self.P["ERROR"]))
        finally:
            self.after(0, lambda: self._set_ui_state(True))
            self.after(0, lambda: self.progress.config(value=0))

    # ════════════════════════════════════════════════════════════════════════
    # 3.  Each image -> individual PDF
    # ════════════════════════════════════════════════════════════════════════
    def _convert_each_to_pdf(self):
        images = self._require_images("btn_each_pdf")
        if not images:
            return
        out_dir = filedialog.askdirectory(title=self.S["dlg_each_dest"])
        if not out_dir:
            return
        threading.Thread(target=self._do_convert_each,
                         args=(images, out_dir), daemon=True).start()

    def _do_convert_each(self, images, out_dir):
        self._set_ui_state(False)
        S, quality, total = self.S, self.quality_var.get(), len(images)
        try:
            for idx, path in enumerate(images):
                base = os.path.splitext(os.path.basename(path))[0]
                out_path = os.path.join(out_dir, base + ".pdf")
                self.after(0, lambda i=idx, n=base: self.prog_lbl.config(
                    text=S["prog_each"].format(i=i+1, n=total, name=n),
                    fg=self.P["TEXT_DIM"]))
                self.after(0, lambda i=idx: self.progress.config(
                    value=int((i + 1) / total * 100)))
                img = self._to_rgb(Image.open(path))
                buf = io.BytesIO()
                img.save(buf, "JPEG", quality=quality, optimize=True)
                buf.seek(0)
                Image.open(buf).save(out_path, "PDF", resolution=144.0)

            self._last_output = out_dir
            self.after(0, lambda: self.output_lbl.config(
                text=S["out_each"].format(n=total, folder=out_dir), fg=self.P["SUCCESS"]))
            self.after(0, lambda: messagebox.showinfo(
                S["success_title"],
                S["success_each"].format(n=total, folder=out_dir)))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror(
                S["err_title"], S["err_msg"].format(e=e)))
            self.after(0, lambda: self.prog_lbl.config(
                text=S["err_msg"].format(e=e), fg=self.P["ERROR"]))
        finally:
            self.after(0, lambda: self._set_ui_state(True))
            self.after(0, lambda: self.progress.config(value=0))

    # ════════════════════════════════════════════════════════════════════════
    # 4.  All images -> single PDF
    # ════════════════════════════════════════════════════════════════════════
    def _convert(self):
        images = self._require_images("btn_convert")
        if not images:
            return
        out_path = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
            title=self.S["dlg_pdf_save"], initialfile="Output.pdf")
        if not out_path:
            return
        threading.Thread(target=self._do_convert,
                         args=(images, out_path), daemon=True).start()

    def _do_convert(self, images, out_path):
        self._set_ui_state(False)
        try:
            self._convert_images(images, out_path)
            self._last_output = out_path
            fname = os.path.basename(out_path)
            self.after(0, lambda: self.output_lbl.config(
                text=self.S["out_pdf"].format(name=fname), fg=self.P["SUCCESS"]))
            self.after(0, lambda: messagebox.showinfo(
                self.S["success_title"],
                self.S["success_pdf"].format(path=out_path)))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror(
                self.S["err_title"], self.S["err_convert"].format(e=e)))
            self.after(0, lambda: self.prog_lbl.config(
                text=self.S["err_convert"].format(e=e), fg=self.P["ERROR"]))
        finally:
            self.after(0, lambda: self._set_ui_state(True))
            self.after(0, lambda: self.progress.config(value=0))

    def _convert_images(self, image_paths, out_path):
        S         = self.S
        is_auto   = self.page_var.get() in _AUTO_LABELS
        landscape = self.orient_var.get() == "Landscape"
        quality   = self.quality_var.get()
        margin    = self.margin_var.get()
        total     = len(image_paths)

        PAGE_SIZES = {
            "A4":     (595.28, 841.89),
            "A3":     (841.89, 1190.55),
            "Letter": (612.0,  792.0),
            "Legal":  (612.0,  1008.0),
        }

        pil_images = []
        for idx, path in enumerate(image_paths):
            nm = os.path.basename(path)
            self.after(0, lambda i=idx, n=nm: self.prog_lbl.config(
                text=S["prog_loading"].format(i=i+1, n=total, name=n),
                fg=self.P["TEXT_DIM"]))
            self.after(0, lambda i=idx: self.progress.config(
                value=int(i / total * 50)))
            pil_images.append(self._to_rgb(Image.open(path)))

        result_pages = []
        for idx, img in enumerate(pil_images):
            self.after(0, lambda i=idx: self.prog_lbl.config(
                text=S["prog_converting"].format(i=i+1, n=total),
                fg=self.P["TEXT_DIM"]))
            self.after(0, lambda i=idx: self.progress.config(
                value=50 + int(i / total * 45)))

            w_px, h_px = img.size
            dpi = 96
            try:
                info_dpi = img.info.get("dpi") or img.info.get("jfif_density")
                if info_dpi:
                    dpi = max(info_dpi[0], info_dpi[1], 72)
            except Exception:
                pass

            w_pt, h_pt = w_px * 72.0 / dpi, h_px * 72.0 / dpi

            if is_auto:
                pw, ph = w_pt + margin * 2, h_pt + margin * 2
            else:
                key = self.page_var.get()
                pw, ph = PAGE_SIZES.get(
                    key, (w_pt + margin * 2, h_pt + margin * 2))

            if landscape:
                pw, ph = ph, pw

            avail_w, avail_h = pw - margin * 2, ph - margin * 2
            scale = min(avail_w / w_pt, avail_h / h_pt, 1.0)
            fw, fh = w_pt * scale, h_pt * scale
            result_pages.append((img, pw, ph,
                                  (pw - fw) / 2, (ph - fh) / 2,
                                  fw, fh, quality))

        self._save_pdf(result_pages, out_path)
        fname = os.path.basename(out_path)
        self.after(0, lambda: self.progress.config(value=100))
        self.after(0, lambda: self.prog_lbl.config(
            text=S["prog_done"].format(n=total, name=fname), fg=self.P["SUCCESS"]))

    def _save_pdf(self, pages, out_path):
        pil_pages = []
        for img, pw, ph, x, y, fw, fh, quality in pages:
            resized = img.resize(
                (max(1, int(fw * 2)), max(1, int(fh * 2))), Image.LANCZOS)
            pil_pages.append(resized)
        if not pil_pages:
            return
        pil_pages[0].save(
            out_path, "PDF", save_all=True,
            append_images=pil_pages[1:], resolution=144.0)

    def _set_ui_state(self, enabled):
        state = "normal" if enabled else "disabled"
        try:
            for w in self.winfo_children():
                if isinstance(w, tk.Button):
                    w.config(state=state)
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
