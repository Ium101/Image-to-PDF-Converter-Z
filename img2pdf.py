#!/usr/bin/env python3
"""
Img2Pdf - Image to PDF Converter / Conversor de Imagens para PDF
Supports / Suporta: PNG, JPG, JPEG, BMP, GIF, TIFF, WEBP
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import threading
import subprocess
import queue
import base64
import re
import configparser
from PIL import Image
import io


# ═══════════════════════════════════════════════════════════════════════════
#  FILE DIALOGS
#  Windows : native Tk dialogs (already modern).
#  Linux   : modern native dialogs via kdialog (KDE/Plasma) or zenity (GTK),
#            falling back to the classic Tk dialogs if neither is installed.
# ═══════════════════════════════════════════════════════════════════════════
_IMG_EXTS = ["png", "jpg", "jpeg", "bmp", "gif", "tiff", "tif", "webp"]


def _img_patterns():
    pats = []
    for e in _IMG_EXTS:
        pats += ["*." + e, "*." + e.upper()]
    return pats


def _linux_dialog_tools():
    """Installed native dialog tools, best match for the current desktop first."""
    import shutil
    desktop = (os.environ.get("XDG_CURRENT_DESKTOP", "") + " " +
               os.environ.get("DESKTOP_SESSION", "")).lower()
    order = (["kdialog", "zenity"] if ("kde" in desktop or "plasma" in desktop)
             else ["zenity", "kdialog"])
    return [t for t in order if shutil.which(t)]


def _run_dialog(cmd):
    """Run an external dialog. Returns ('ok', stdout) | ('cancel', '') | ('error', '')."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
    except Exception:
        return "error", ""
    if r.returncode == 0:
        return "ok", r.stdout
    if r.returncode == 1:
        return "cancel", ""
    return "error", ""


def _start_dir(initialdir):
    d = initialdir if initialdir and os.path.isdir(initialdir) else os.path.expanduser("~")
    return d.rstrip("/") + "/"


def _native_linux(kind, title, initialdir):
    """kind: 'open_images' | 'save_pdf' | 'directory'.
    Returns a list of paths ([] = cancelled) or None when no native tool worked."""
    if not sys.platform.startswith("linux"):
        return None
    start = _start_dir(initialdir)
    for tool in _linux_dialog_tools():
        if tool == "kdialog":
            cmd = ["kdialog", "--title", title]
            if kind == "open_images":
                flt = " ".join(_img_patterns()) + "|Images / Imagens\n*|All / Todos"
                cmd += ["--multiple", "--separate-output",
                        "--getopenfilename", start, flt]
            elif kind == "save_pdf":
                cmd += ["--getsavefilename", start + "Output.pdf", "*.pdf|PDF"]
            else:
                cmd += ["--getexistingdirectory", start]
        else:  # zenity
            cmd = ["zenity", "--file-selection", "--title=" + title]
            if kind == "open_images":
                cmd += ["--multiple", "--separator=\n", "--filename=" + start,
                        "--file-filter=Images / Imagens | " + " ".join(_img_patterns()),
                        "--file-filter=All / Todos | *"]
            elif kind == "save_pdf":
                cmd += ["--save", "--confirm-overwrite",
                        "--filename=" + start + "Output.pdf",
                        "--file-filter=PDF | *.pdf *.PDF"]
            else:
                cmd += ["--directory", "--filename=" + start]
        status, out = _run_dialog(cmd)
        if status == "cancel":
            return []
        if status == "ok":
            paths = [p for p in out.rstrip("\r\n").split("\n") if p.strip()]
            if paths:
                return paths
            return []
        # status == "error" -> try the next tool / Tk fallback
    return None


def ask_open_images(title, initialdir=None, parent=None, P=None, S=None):
    """Select one or more image files. Returns a list of paths ([] if cancelled).
    On Linux this opens the built-in thumbnail picker (needs parent/P/S); if that
    cannot be shown it falls back to kdialog/zenity and then to the Tk dialog."""
    if sys.platform.startswith("linux") and parent is not None and P and S:
        try:
            picker = ThumbnailPicker(parent, title, initialdir, P, S)
            picker.wait_window()
            return picker.result
        except Exception:
            pass
    res = _native_linux("open_images", title, initialdir)
    if res is not None:
        return res
    kw = {"initialdir": initialdir} if initialdir else {}
    paths = filedialog.askopenfilenames(
        title=title,
        filetypes=[("Images / Imagens", " ".join("*." + e for e in _IMG_EXTS)),
                   ("All / Todos", "*.*")],
        **kw)
    return list(paths) if paths else []


def ask_save_pdf(title, initialdir=None):
    """Choose where to save a PDF. Returns a path ('' if cancelled)."""
    res = _native_linux("save_pdf", title, initialdir)
    if res is not None:
        path = res[0] if res else ""
        if path and not path.lower().endswith(".pdf"):
            path += ".pdf"
        return path
    kw = {"initialdir": initialdir} if initialdir else {}
    return filedialog.asksaveasfilename(
        defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
        title=title, initialfile="Output.pdf", **kw) or ""


def ask_directory(title, initialdir=None):
    """Choose a folder. Returns a path ('' if cancelled)."""
    res = _native_linux("directory", title, initialdir)
    if res is not None:
        return res[0] if res else ""
    kw = {"initialdir": initialdir} if initialdir else {}
    return filedialog.askdirectory(title=title, **kw) or ""

# ═══════════════════════════════════════════════════════════════════════════
#  THUMBNAIL PICKER (Linux)
#  A modern image picker with real thumbnails, built into the app.
#  GTK (zenity) and KDE (kdialog) dialogs cannot be told to show thumbnails,
#  so this is drawn by the app itself: places sidebar, thumbnail grid,
#  size slider, search, multi-select across folders, numbered selection order.
# ═══════════════════════════════════════════════════════════════════════════
def _natural_key(name):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", name)]


def _xdg_user_dirs():
    """Read ~/.config/user-dirs.dirs  ->  {'PICTURES': '/home/me/Imagens', ...}"""
    home = os.path.expanduser("~")
    dirs = {}
    try:
        with open(os.path.join(home, ".config", "user-dirs.dirs"),
                  encoding="utf-8") as f:
            for ln in f:
                m = re.match(r'\s*XDG_(\w+)_DIR\s*=\s*"(.*)"', ln)
                if m:
                    dirs[m.group(1)] = m.group(2).replace("$HOME", home)
    except OSError:
        pass
    return dirs


class ThumbnailPicker(tk.Toplevel):
    PAD = 10
    _last_size = 128            # remembered while the program is open

    def __init__(self, parent, title, initialdir, P, S):
        super().__init__(parent)
        try:
            self._init(parent, title, initialdir, P, S)
        except Exception:
            try:
                self.destroy()
            except Exception:
                pass
            raise

    # ── setup ────────────────────────────────────────────────────────────────
    def _init(self, parent, title, initialdir, P, S):
        self.P, self.S = P, S
        self.result = []
        self._alive = True
        self._sel = []                 # chosen files, in click order
        self._selset = set()
        self._view = []                # [(kind, path, name)] shown now
        self._all = []                 # same, before the search filter
        self._cache = {}               # (path, size) -> PhotoImage | None
        self._pending = set()
        self._visible = set()
        self._gen = 0
        self._anchor = None
        self._size = ThumbnailPicker._last_size
        self._geom = (1, 0, 160, 180)
        self._cwd = ""
        self._q = queue.Queue()
        self._done = queue.Queue()
        self._size_job = None

        self.title(title)
        self.configure(bg=P["BG"])
        self.minsize(680, 440)
        pw, ph = 980, 640
        try:
            x = parent.winfo_rootx() + max(0, (parent.winfo_width() - pw) // 2)
            y = parent.winfo_rooty() + max(0, (parent.winfo_height() - ph) // 2)
        except Exception:
            x, y = 80, 60
        self.geometry(f"{pw}x{ph}+{max(0, x)}+{max(0, y)}")
        self.transient(parent)

        self._build(P, S)
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.bind("<Escape>", lambda e: self._cancel())
        self.bind("<Return>", self._on_return)
        self.bind("<Control-a>", lambda e: self._select_all())
        self.bind("<BackSpace>", self._on_backspace)

        self._workers = [threading.Thread(target=self._worker, daemon=True)
                         for _ in range(2)]
        for t in self._workers:
            t.start()

        start = initialdir if initialdir and os.path.isdir(initialdir) else None
        if not start:
            pics = _xdg_user_dirs().get("PICTURES", "")
            start = pics if os.path.isdir(pics) else os.path.expanduser("~")
        self._goto(start)
        self.after(40, self._poll)

        try:
            self.wait_visibility()
            self.grab_set()
        except tk.TclError:
            pass
        self.canvas.focus_set()

    def _btn(self, parent, text, cmd, bg, fg="white", **kw):
        return tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg,
                         activebackground=self.P["ACCENT2"], activeforeground="white",
                         font=("Segoe UI", 9, "bold"), relief="flat", bd=0,
                         padx=12, pady=6, cursor="hand2", **kw)

    def _build(self, P, S):
        # top bar
        top = tk.Frame(self, bg=P["BG"])
        top.pack(fill="x", padx=10, pady=(10, 6))
        self._b_up = self._btn(top, "↑", self._go_up, P["THEME_BTN"], P["TEXT"], width=2)
        self._b_up.pack(side="left")
        self._path_var = tk.StringVar()
        self._path_ent = tk.Entry(top, textvariable=self._path_var, bg=P["SURFACE"],
                                  fg=P["TEXT"], insertbackground=P["TEXT"],
                                  relief="flat", font=("Segoe UI", 10),
                                  highlightthickness=1,
                                  highlightbackground=P["BORDER"],
                                  highlightcolor=P["ACCENT"])
        self._path_ent.pack(side="left", fill="x", expand=True, padx=8, ipady=5)
        self._path_ent.bind("<Return>", self._on_path_enter)
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *a: self._apply_filter())
        tk.Label(top, text="🔍", bg=P["BG"], fg=P["TEXT_DIM"]).pack(side="left")
        tk.Entry(top, textvariable=self._search_var, width=16, bg=P["SURFACE"],
                 fg=P["TEXT"], insertbackground=P["TEXT"], relief="flat",
                 font=("Segoe UI", 10), highlightthickness=1,
                 highlightbackground=P["BORDER"],
                 highlightcolor=P["ACCENT"]).pack(side="left", padx=(4, 10), ipady=5)
        tk.Label(top, text=S["pick_size"], bg=P["BG"], fg=P["TEXT_DIM"],
                 font=("Segoe UI", 9)).pack(side="left")
        try:
            ttk.Style(self).configure("Pick.Horizontal.TScale",
                                      background=P["BG"], troughcolor=P["BORDER"])
        except tk.TclError:
            pass
        self._scale = ttk.Scale(top, from_=80, to=260, orient="horizontal",
                                length=110, command=self._on_scale,
                                style="Pick.Horizontal.TScale")
        self._scale.set(self._size)
        self._scale.pack(side="left", padx=(6, 0))

        # footer first (so it never gets pushed out when the window is small)
        foot = tk.Frame(self, bg=P["BG"])
        foot.pack(side="bottom", fill="x", padx=10, pady=(6, 10))
        self._hidden_var = tk.BooleanVar(value=False)
        tk.Checkbutton(foot, text=S["pick_hidden"], variable=self._hidden_var,
                       command=self._reload, bg=P["BG"], fg=P["TEXT_DIM"],
                       selectcolor=P["SURFACE"], activebackground=P["BG"],
                       activeforeground=P["TEXT"], font=("Segoe UI", 9),
                       highlightthickness=0, bd=0).pack(side="left")
        self._count_lbl = tk.Label(foot, bg=P["BG"], fg=P["TEXT"],
                                   font=("Segoe UI", 10, "bold"))
        self._count_lbl.pack(side="left", padx=16)
        self._b_add = self._btn(foot, "", self._confirm, P["BTN_GREEN"])
        self._b_add.pack(side="right")
        self._btn(foot, S["pick_cancel"], self._cancel,
                  P["THEME_BTN"], P["TEXT"]).pack(side="right", padx=8)
        self._btn(foot, S["pick_clear"], self._clear_sel,
                  P["THEME_BTN"], P["TEXT"]).pack(side="right")
        self._btn(foot, S["pick_select_all"], self._select_all,
                  P["THEME_BTN"], P["TEXT"]).pack(side="right", padx=8)

        # body: places | thumbnails
        body = tk.Frame(self, bg=P["BG"])
        body.pack(fill="both", expand=True, padx=10)
        self._side = tk.Frame(body, bg=P["SURFACE"], width=190)
        self._side.pack(side="left", fill="y")
        self._side.pack_propagate(False)
        self._place_widgets = []
        self._build_places()

        right = tk.Frame(body, bg=P["BORDER"])
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))
        self.canvas = tk.Canvas(right, bg=P["LB_BG"], highlightthickness=0, bd=0,
                                yscrollincrement=40)
        vsb = ttk.Scrollbar(right, orient="vertical", command=self._yview)
        self.canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        self.canvas.bind("<Configure>", lambda e: self._redraw())
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Button-4>", lambda e: self._wheel(-1))
        self.canvas.bind("<Button-5>", lambda e: self._wheel(1))
        self.canvas.bind("<MouseWheel>",
                         lambda e: self._wheel(-1 if e.delta > 0 else 1))
        self._update_footer()

    def _build_places(self):
        P, S = self.P, self.S
        for w in self._place_widgets:
            w.destroy()
        self._place_widgets = []
        home = os.path.expanduser("~")
        ud = _xdg_user_dirs()
        places = [("🏠  " + S["pick_home"], home)]
        for key, icon in (("PICTURES", "🖼"), ("DESKTOP", "🖥"),
                          ("DOWNLOAD", "⬇"), ("DOCUMENTS", "📄")):
            p = ud.get(key, "")
            if p and os.path.isdir(p) and os.path.abspath(p) != home:
                places.append((f"{icon}  {os.path.basename(p.rstrip('/'))}", p))
        user = os.environ.get("USER") or os.path.basename(home)
        for base in (f"/media/{user}", f"/run/media/{user}"):
            try:
                for name in sorted(os.listdir(base)):
                    full = os.path.join(base, name)
                    if os.path.isdir(full):
                        places.append((f"💾  {name}", full))
            except OSError:
                pass
        places.append(("🗂  " + S["pick_root"], "/"))
        for label, path in places:
            lb = tk.Label(self._side, text=label, anchor="w", bg=P["SURFACE"],
                          fg=P["TEXT"], font=("Segoe UI", 10), padx=12, pady=7,
                          cursor="hand2")
            lb.pack(fill="x")
            lb.bind("<Button-1>", lambda e, p=path: self._goto(p))
            lb.bind("<Enter>", lambda e, w=lb: w.config(bg=self.P["BORDER"]))
            lb.bind("<Leave>", lambda e, w=lb, p=path: self._paint_place(w, p))
            lb._place_path = path
            self._place_widgets.append(lb)

    def _paint_place(self, w, path):
        cur = os.path.abspath(self._cwd) == os.path.abspath(path)
        w.config(bg=self.P["SELECT_BG"] if cur else self.P["SURFACE"],
                 fg="white" if cur else self.P["TEXT"])

    # ── navigation ───────────────────────────────────────────────────────────
    def _goto(self, path):
        path = os.path.abspath(os.path.expanduser(path))
        try:
            entries = list(os.scandir(path))
        except OSError:
            self._path_var.set(self._cwd)
            self._flash(self.S["pick_error"])
            return
        self._cwd = path
        self._path_var.set(path)
        show_hidden = self._hidden_var.get()
        dirs, files = [], []
        for e in entries:
            name = e.name
            if name.startswith(".") and not show_hidden:
                continue
            try:
                if e.is_dir():
                    dirs.append(("d", e.path, name))
                elif name.lower().endswith(SUPPORTED) and e.is_file():
                    files.append(("f", e.path, name))
            except OSError:
                continue
        dirs.sort(key=lambda t: _natural_key(t[2]))
        files.sort(key=lambda t: _natural_key(t[2]))
        self._all = dirs + files
        self._gen += 1
        self._pending.clear()
        self._drain(self._q)
        self._anchor = None
        self.canvas.yview_moveto(0)
        self._apply_filter()
        for w in self._place_widgets:
            self._paint_place(w, w._place_path)

    def _reload(self):
        self._goto(self._cwd)

    def _go_up(self):
        parent = os.path.dirname(self._cwd.rstrip("/")) or "/"
        if parent != self._cwd:
            self._goto(parent)

    def _on_path_enter(self, _e):
        p = os.path.expanduser(self._path_var.get().strip())
        if os.path.isdir(p):
            self._goto(p)
            self.canvas.focus_set()
        else:
            self._path_var.set(self._cwd)
            self._flash(self.S["pick_error"])
        return "break"

    def _on_backspace(self, _e):
        if not isinstance(self.focus_get(), tk.Entry):
            self._go_up()

    def _on_return(self, _e):
        if not isinstance(self.focus_get(), tk.Entry):
            self._confirm()

    def _flash(self, text):
        self._count_lbl.config(text=text, fg=self.P["ERROR"])
        self.after(2000, self._update_footer)

    @staticmethod
    def _drain(q):
        try:
            while True:
                q.get_nowait()
        except queue.Empty:
            pass

    # ── filter / selection ───────────────────────────────────────────────────
    def _apply_filter(self):
        q = self._search_var.get().strip().lower()
        self._view = [it for it in self._all if q in it[2].lower()] if q else list(self._all)
        self._anchor = None
        self._redraw()

    def _images_in_view(self):
        return [it[1] for it in self._view if it[0] == "f"]

    def _select_all(self):
        for p in self._images_in_view():
            if p not in self._selset:
                self._selset.add(p)
                self._sel.append(p)
        self._redraw()
        self._update_footer()

    def _clear_sel(self):
        self._sel.clear()
        self._selset.clear()
        self._redraw()
        self._update_footer()

    def _toggle(self, path):
        if path in self._selset:
            self._selset.discard(path)
            self._sel.remove(path)
        else:
            self._selset.add(path)
            self._sel.append(path)

    def _update_footer(self):
        n = len(self._sel)
        self._count_lbl.config(text=self.S["pick_selected"].format(n=n),
                               fg=self.P["TEXT"])
        self._b_add.config(text=self.S["pick_add"].format(n=n),
                           state="normal" if n else "disabled",
                           bg=self.P["BTN_GREEN"] if n else self.P["THEME_BTN"],
                           fg="white" if n else self.P["TEXT_DIM"])

    def _confirm(self):
        if not self._sel:
            return
        self.result = list(self._sel)
        self._close()

    def _cancel(self):
        self.result = []
        self._close()

    def _close(self):
        self._alive = False
        ThumbnailPicker._last_size = self._size
        for _ in self._workers:
            self._q.put(None)
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()

    # ── thumbnail grid ───────────────────────────────────────────────────────
    def _on_scale(self, val):
        if self._size_job:
            self.after_cancel(self._size_job)
        self._size_job = self.after(250, lambda: self._apply_size(int(float(val))))

    def _apply_size(self, size):
        size = max(80, min(260, (size // 8) * 8))
        if size == self._size:
            return
        self._size = size
        self._gen += 1
        self._pending.clear()
        self._drain(self._q)
        self._cache.clear()
        self._redraw()

    def _yview(self, *args):
        self.canvas.yview(*args)
        self._redraw()

    def _wheel(self, direction):
        self.canvas.yview_scroll(direction * 3, "units")
        self._redraw()

    @staticmethod
    def _short(name, limit):
        if len(name) <= limit:
            return name
        keep = max(4, limit - 1)
        head = keep * 2 // 3
        return name[:head] + "…" + name[-(keep - head):]

    def _draw_folder(self, c, cx, cy, s):
        w, h = s * 0.62, s * 0.44
        x0, y0 = cx - w / 2, cy - h / 2 + s * 0.05
        c.create_polygon(x0, y0, x0, y0 - h * 0.17, x0 + w * 0.38, y0 - h * 0.17,
                         x0 + w * 0.47, y0, fill="#E0A030", outline="")
        c.create_rectangle(x0, y0, x0 + w, y0 + h, fill="#F5B942", outline="#D99A1F")

    def _redraw(self):
        if not self._alive:
            return
        c, P = self.canvas, self.P
        c.delete("all")
        w = max(c.winfo_width(), 120)
        size = self._size
        cw, ch = size + 20, size + 52
        cols = max(1, w // cw)
        xoff = (w - cols * cw) // 2
        n = len(self._view)
        rows = (n + cols - 1) // cols
        self._geom = (cols, xoff, cw, ch)
        c.configure(scrollregion=(0, 0, w, max(rows * ch + 10, c.winfo_height())))
        if n == 0:
            c.create_text(w // 2, 90, text=self.S["pick_empty"],
                          fill=P["TEXT_DIM"], font=("Segoe UI", 11))
            self._visible = set()
            return
        top = c.canvasy(0)
        bottom = top + c.winfo_height()
        r0 = max(0, int(top // ch))
        r1 = min(rows - 1, int(bottom // ch))
        visible = set()
        chars = max(8, (cw - 12) // 6)
        for idx in range(r0 * cols, min(n, (r1 + 1) * cols)):
            kind, path, name = self._view[idx]
            x = xoff + (idx % cols) * cw
            y = (idx // cols) * ch + 5
            sel = path in self._selset
            c.create_rectangle(x + 4, y + 2, x + cw - 4, y + ch - 6,
                               fill=P["SELECT_BG"] if sel else P["BG"],
                               outline=P["ACCENT2"] if sel else P["BORDER"],
                               width=2 if sel else 1)
            cx, cy = x + cw // 2, y + 8 + size // 2
            if kind == "d":
                self._draw_folder(c, cx, cy, size)
            else:
                visible.add(path)
                key = (path, size)
                if key in self._cache:
                    img = self._cache[key]
                    if img is not None:
                        c.create_image(cx, cy, image=img)
                    else:
                        c.create_text(cx, cy, text="?", fill=P["TEXT_DIM"],
                                      font=("Segoe UI", max(14, size // 4)))
                else:
                    c.create_text(cx, cy, text="…", fill=P["TEXT_DIM"],
                                  font=("Segoe UI", max(14, size // 4)))
                    if key not in self._pending:
                        self._pending.add(key)
                        self._q.put((self._gen, path, size))
            c.create_text(x + cw // 2, y + size + 16, text=self._short(name, chars * 2 - 2),
                          fill="white" if sel else P["TEXT"], width=cw - 14,
                          justify="center", anchor="n", font=("Segoe UI", 9))
            if sel:
                num = self._sel.index(path) + 1
                bx, by = x + 18, y + 16
                c.create_oval(bx - 11, by - 11, bx + 11, by + 11,
                              fill=P["ACCENT"], outline="white", width=2)
                c.create_text(bx, by, text=str(num), fill="white",
                              font=("Segoe UI", 8, "bold"))
        self._visible = visible

    def _on_click(self, e):
        self.canvas.focus_set()
        cols, xoff, cw, ch = self._geom
        cx, cy = self.canvas.canvasx(e.x), self.canvas.canvasy(e.y)
        col = int((cx - xoff) // cw)
        row = int((cy - 5) // ch)
        if not (0 <= col < cols) or row < 0:
            return
        idx = row * cols + col
        if idx >= len(self._view):
            return
        kind, path, _name = self._view[idx]
        if kind == "d":
            self._search_var.set("")
            self._goto(path)
            return
        if (e.state & 0x0001) and self._anchor is not None:      # Shift = range
            a, b = sorted((self._anchor, idx))
            for k in range(a, b + 1):
                it = self._view[k]
                if it[0] == "f" and it[1] not in self._selset:
                    self._selset.add(it[1])
                    self._sel.append(it[1])
        else:
            self._toggle(path)
            self._anchor = idx
        self._redraw()
        self._update_footer()

    # ── background thumbnail loading ─────────────────────────────────────────
    def _worker(self):
        while True:
            job = self._q.get()
            if job is None:
                return
            gen, path, size = job
            if gen != self._gen:
                continue
            if path not in self._visible:           # scrolled away meanwhile
                self._done.put((gen, path, size, "SKIP"))
                continue
            self._done.put((gen, path, size, self._make_thumb(path, size)))

    @staticmethod
    def _make_thumb(path, size):
        try:
            from PIL import ImageOps
            with Image.open(path) as im:
                try:
                    im.draft("RGB", (size * 2, size * 2))   # fast JPEG decode
                except Exception:
                    pass
                im.load()
                try:
                    im = ImageOps.exif_transpose(im)
                except Exception:
                    pass
                if im.mode in ("RGBA", "LA", "P"):
                    im = im.convert("RGBA")
                    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
                    im = Image.alpha_composite(bg, im)
                im = im.convert("RGB")
                im.thumbnail((size, size), getattr(Image, "LANCZOS", 1))
                buf = io.BytesIO()
                im.save(buf, "PNG", compress_level=1)
                return base64.b64encode(buf.getvalue()).decode("ascii")
        except Exception:
            return None

    def _poll(self):
        if not self._alive:
            return
        changed = False
        for _ in range(24):
            try:
                gen, path, size, data = self._done.get_nowait()
            except queue.Empty:
                break
            self._pending.discard((path, size))
            if gen != self._gen or size != self._size:
                continue
            if data == "SKIP":
                changed = True            # re-request if it is visible again
                continue
            if len(self._cache) > 900:
                for k in list(self._cache)[:300]:
                    del self._cache[k]
            try:
                self._cache[(path, size)] = (tk.PhotoImage(data=data)
                                             if data else None)
            except tk.TclError:
                self._cache[(path, size)] = None
            changed = True
        if changed:
            self._redraw()
        self.after(40, self._poll)


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
        "pick_home":        "Início",
        "pick_root":        "Sistema de arquivos",
        "pick_size":        "Tamanho",
        "pick_hidden":      "Mostrar ocultos",
        "pick_selected":    "{n} selecionada(s)",
        "pick_select_all":  "Selecionar todas",
        "pick_clear":       "Limpar seleção",
        "pick_cancel":      "Cancelar",
        "pick_add":         "Adicionar ({n})",
        "pick_empty":       "Nenhuma imagem ou pasta aqui",
        "pick_error":       "Não foi possível abrir esta pasta",
        "btn_add":          "➕ Adicionar",
        "list_hdr":         "📋  Imagens selecionadas",
        "files_count":      "{n} arquivo(s)",
        "btn_up":           "▲ Subir",
        "btn_down":         "▼ Descer",
        "btn_remove":       "✕ Remover",
        "btn_clear":        "🗑 Limpar",
        "ready":            "Pronto.",
        "files_added":      "{n} imagem(ns) adicionada(s). Clique em um dos botões abaixo para iniciar.",
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
        "pick_home":        "Home",
        "pick_root":        "File system",
        "pick_size":        "Size",
        "pick_hidden":      "Show hidden",
        "pick_selected":    "{n} selected",
        "pick_select_all":  "Select all",
        "pick_clear":       "Clear selection",
        "pick_cancel":      "Cancel",
        "pick_add":         "Add ({n})",
        "pick_empty":       "No images or folders here",
        "pick_error":       "Cannot open this folder",
        "btn_add":          "➕ Add",
        "list_hdr":         "📋  Selected images",
        "files_count":      "{n} file(s)",
        "btn_up":           "▲ Up",
        "btn_down":         "▼ Down",
        "btn_remove":       "✕ Remove",
        "btn_clear":        "🗑 Clear",
        "ready":            "Ready.",
        "files_added":      "{n} image(s) added. Click one of the buttons below to start.",
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

    def __init__(self, master, get_S, get_P, on_add=None, **kw):
        self._get_S = get_S
        self._get_P = get_P
        self._on_add = on_add
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
        self._btn_add  = self._mk_btn(self._btn_row, self._add,       P["BTN_GREEN"])
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
        self._btn_add.config(text=S["btn_add"])
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
        self._btn_add.config(bg=P["BTN_GREEN"])
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

    def _add(self):
        if self._on_add:
            self._on_add()

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
        self.minsize(800, 680)
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
        self._last_in_dir  = ""
        self._last_out_dir = ""
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
            self._last_in_dir     = sec.get("last_input_dir", "")
            self._last_out_dir    = sec.get("last_output_dir", "")
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
            "last_input_dir":  self._last_in_dir,
            "last_output_dir": self._last_out_dir,
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
            self._center, get_S=lambda: self.S, get_P=lambda: self.P,
            on_add=self._add_images)
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
        self._job_from_button = False   # True only after one of the 4 action buttons is clicked

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
        paths = ask_open_images(
            self.S["add_images_btn"].replace("➕", "").strip(),
            parent=self, P=self.P, S=self.S, **self._dlg_kw("in"))
        if paths:
            self._remember_dir("in", paths[0])
            added = self.file_list.add(paths)
            # Selecting files never starts anything: just tell the user what to do next.
            self.prog_lbl.config(
                text=self.S["files_added"].format(n=added), fg=self.P["TEXT_DIM"])

    # ── remembered folders ────────────────────────────────────────────────────
    def _dlg_kw(self, kind):
        """initialdir kwargs for file dialogs. kind: 'in' (images) or 'out' (destination)."""
        d = self._last_in_dir if kind == "in" else (self._last_out_dir or self._last_in_dir)
        return {"initialdir": d} if d and os.path.isdir(d) else {}

    def _remember_dir(self, kind, path):
        """Remember the folder of `path` (file or folder) and persist it silently."""
        if not path:
            return
        folder = path if os.path.isdir(path) else os.path.dirname(path)
        if not folder or not os.path.isdir(folder):
            return
        if kind == "in":
            self._last_in_dir = folder
        else:
            self._last_out_dir = folder
        self._save_config()

    def _open_output_dir(self):
        path = self._last_output or os.path.expanduser("~")
        folder = os.path.dirname(path) if os.path.isfile(path) else path
        if not os.path.isdir(folder):
            return
        try:
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception:
            pass

    def _notify_done(self, title, message):
        """Show the success dialog, then open the output folder automatically
        (only when the job was started by one of the 4 action buttons)."""
        started_by_button = self._job_from_button
        self._job_from_button = False
        messagebox.showinfo(title, message)
        if started_by_button:
            self._open_output_dir()

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
        out_dir = ask_directory(self.S["dlg_jpg_dest"], **self._dlg_kw("out"))
        if not out_dir:
            return
        self._remember_dir("out", out_dir)
        self._job_from_button = True
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
            self.after(0, lambda: self._notify_done(
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
        out_path = ask_save_pdf(self.S["dlg_pdf_comp"], **self._dlg_kw("out"))
        if not out_path:
            return
        self._remember_dir("out", out_path)
        self._job_from_button = True
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
            self.after(0, lambda: self._notify_done(
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
        out_dir = ask_directory(self.S["dlg_each_dest"], **self._dlg_kw("out"))
        if not out_dir:
            return
        self._remember_dir("out", out_dir)
        self._job_from_button = True
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
            self.after(0, lambda: self._notify_done(
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
        out_path = ask_save_pdf(self.S["dlg_pdf_save"], **self._dlg_kw("out"))
        if not out_path:
            return
        self._remember_dir("out", out_path)
        self._job_from_button = True
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
            self.after(0, lambda: self._notify_done(
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
