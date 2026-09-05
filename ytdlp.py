import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font as tkfont
import ctypes
import threading
import subprocess
import json
import os
import sys
import re
import shutil
import urllib.request
import webbrowser
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import requests
from io import BytesIO

APP_VERSION = "1.3.0"
CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".ytdlp_gui_config.json")
YTDLP_RELEASE_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
GITHUB_URL = "https://github.com/Shiraken12T"

THEME = {
    "bg": "#08080d",
    "surface": "#0d0d13",
    "card": "#13131b",
    "card_hover": "#1b1b26",
    "elevated": "#1a1a24",
    "input": "#0c0c12",
    "input_focus": "#12121c",
    "accent": "#8b7cff",
    "accent_hover": "#a599ff",
    "accent_soft": "#2b2652",
    "accent_dim": "#1a1730",
    "accent_text": "#ffffff",
    "text": "#f3f3f7",
    "text_sec": "#9a9aab",
    "text_muted": "#5c5c6e",
    "success": "#34d399",
    "success_bg": "#10291e",
    "warning": "#fbbf24",
    "warning_bg": "#2a210f",
    "error": "#f87171",
    "error_bg": "#2c1416",
    "border": "#232333",
    "border_light": "#2f2f42",
    "disabled": "#4d4d60",
    "shadow": "#000000",
}

FONT = "Segoe UI"
FONT_MONO = "Consolas"
THUMB_W, THUMB_H = 300, 168
_ICON_CACHE = {}
_CORNER_CACHE = {}


def _enable_dpi():
    if os.name != "nt":
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def _rgb(color):
    c = color.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def _rgba(color, a=255):
    return _rgb(color) + (a,)


def pick_ui_font(root):
    families = set(tkfont.families(root))
    for name in ("Segoe UI Variable", "Segoe UI", "Inter", "Arial"):
        if name in families:
            return name
    return "Segoe UI"


def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def local_ytdlp_path():
    return os.path.join(app_dir(), "yt-dlp.exe")


def get_ytdlp_cmd():
    local = local_ytdlp_path()
    if os.path.isfile(local):
        return [local]
    found = shutil.which("yt-dlp")
    if found:
        return [found]
    if getattr(sys, "frozen", False):
        return ["yt-dlp"]
    return [sys.executable, "-m", "yt_dlp"]


def get_pip_cmd():
    return [sys.executable, "-m", "pip"]


def startup_info():
    if os.name == "nt":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return si
    return None


def download_ytdlp_exe(dest_path=None):
    dest = dest_path or local_ytdlp_path()
    urllib.request.urlretrieve(YTDLP_RELEASE_URL, dest)
    return dest


def _rounded_image(w, h, radius, fill, outline=None, outline_w=1):
    img = Image.new("RGBA", (max(w, 1), max(h, 1)), (0, 0, 0, 0))
    if w < 2 or h < 2:
        return img
    d = ImageDraw.Draw(img)
    r = max(1, min(radius, w // 2, h // 2))
    box = (0, 0, w - 1, h - 1)
    if outline:
        d.rounded_rectangle(box, radius=r, fill=_rgba(fill), outline=_rgba(outline), width=outline_w)
    else:
        d.rounded_rectangle(box, radius=r, fill=_rgba(fill))
    return img


def get_card_corners(radius, fill, outline, parent_bg):
    key = (radius, fill, outline, parent_bg)
    cached = _CORNER_CACHE.get(key)
    if cached:
        return cached
    cs = max(int(radius) + 2, 4)
    side = cs * 2
    base = Image.new("RGBA", (side, side), _rgba(parent_bg))
    overlay = _rounded_image(side, side, radius, fill, outline)
    img = Image.alpha_composite(base, overlay)
    parts = (
        cs,
        ImageTk.PhotoImage(img.crop((0, 0, cs, cs))),
        ImageTk.PhotoImage(img.crop((side - cs, 0, side, cs))),
        ImageTk.PhotoImage(img.crop((0, side - cs, cs, side))),
        ImageTk.PhotoImage(img.crop((side - cs, side - cs, side, side))),
    )
    _CORNER_CACHE[key] = parts
    return parts


def round_photo(img, radius, size):
    img = img.convert("RGBA")
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    ratio = min(size[0] / img.width, size[1] / img.height)
    nw, nh = max(1, int(img.width * ratio)), max(1, int(img.height * ratio))
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    x, y = (size[0] - nw) // 2, (size[1] - nh) // 2
    canvas.paste(img, (x, y))
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=radius, fill=255)
    canvas.putalpha(mask)
    bg = Image.new("RGBA", size, _rgba(THEME["input"]))
    return Image.alpha_composite(bg, canvas)


def _render_icon(name, size, color):
    scale = 4
    s = max(int(size * scale), 32)
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rgb = _rgba(color)
    sw = max(int(s * 0.08), 3)

    def pt(x, y):
        return x / 24.0 * s, y / 24.0 * s

    def line(a, b, c, e):
        p1, p2 = pt(a, b), pt(c, e)
        d.line([p1, p2], fill=rgb, width=sw)
        r = sw / 2.0
        for p in (p1, p2):
            d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=rgb)

    def ellipse(a, b, c, e, width=None, fill=None):
        box = [*pt(a, b), *pt(c, e)]
        d.ellipse(box, outline=rgb if width else None, fill=fill, width=width or 0)

    def poly(points, fill=None, width=None):
        pts = [pt(*p) for p in points]
        if fill:
            d.polygon(pts, fill=fill)
        if width:
            d.line(pts + [pts[0]], fill=rgb, width=width)

    if name == "download":
        line(12, 4, 12, 15)
        line(7, 11, 12, 16)
        line(17, 11, 12, 16)
        line(5, 19, 19, 19)
        line(5, 19, 5, 17)
        line(19, 19, 19, 17)
    elif name == "clipboard":
        d.rounded_rectangle([*pt(6, 5), *pt(18, 21)], radius=s * 0.06, outline=rgb, width=sw)
        line(9, 10, 15, 10)
        line(9, 13.5, 15, 13.5)
        line(9, 17, 13, 17)
    elif name == "clock":
        ellipse(4, 4, 20, 20, width=sw)
        line(12, 12, 12, 8)
        line(12, 12, 16.5, 14)
    elif name == "search":
        ellipse(4.5, 4.5, 15.5, 15.5, width=sw)
        line(14.8, 14.8, 20, 20)
    elif name == "folder":
        d.rounded_rectangle([*pt(3, 8), *pt(21, 20)], radius=s * 0.06, outline=rgb, width=sw)
        d.polygon([pt(3, 10), pt(3, 7.5), pt(10, 7.5), pt(12, 10)], outline=rgb)
        line(3, 10, 12, 10)
    elif name == "refresh":
        d.arc([*pt(5, 5), *pt(19, 19)], start=40, end=300, fill=rgb, width=sw)
        line(18.5, 5.5, 18.5, 10.5)
        line(18.5, 5.5, 14.2, 6.2)
    elif name == "sliders":
        line(5, 8, 19, 8)
        line(5, 12, 19, 12)
        line(5, 16, 19, 16)
        ellipse(8, 6.4, 11.2, 9.6, fill=rgb)
        ellipse(14, 10.4, 17.2, 13.6, fill=rgb)
        ellipse(9.5, 14.4, 12.7, 17.6, fill=rgb)
    elif name == "film":
        d.rounded_rectangle([*pt(4, 5), *pt(20, 19)], radius=s * 0.05, outline=rgb, width=sw)
        line(8, 5, 8, 19)
        line(16, 5, 16, 19)
        for y in (7, 10, 13, 16):
            ellipse(5.3, y, 6.8, y + 1.5, fill=rgb)
            ellipse(17.2, y, 18.7, y + 1.5, fill=rgb)
    elif name == "music":
        d.ellipse([*pt(5, 14), *pt(11, 20)], outline=rgb, width=sw)
        d.ellipse([*pt(13, 12), *pt(19, 18)], outline=rgb, width=sw)
        line(11, 17, 11, 5)
        line(19, 15, 19, 5)
        line(11, 5, 19, 5)
    elif name == "layers":
        d.rounded_rectangle([*pt(6, 5), *pt(18, 11)], radius=s * 0.04, outline=rgb, width=sw)
        d.rounded_rectangle([*pt(5, 10), *pt(19, 16)], radius=s * 0.04, outline=rgb, width=sw)
        d.rounded_rectangle([*pt(6, 15), *pt(18, 20.5)], radius=s * 0.04, outline=rgb, width=sw)
    elif name == "zap":
        poly([(13, 3), (7, 13), (12, 13), (11, 21), (18, 10), (13, 10)], fill=rgb)
    elif name == "clapper":
        d.rounded_rectangle([*pt(4, 9), *pt(20, 20)], radius=s * 0.05, outline=rgb, width=sw)
        d.polygon([pt(4, 9), pt(20, 6), pt(20, 9), pt(4, 12)], outline=rgb)
        line(8, 8.2, 9.6, 11.2)
        line(13, 7.2, 14.6, 10.2)
    elif name == "captions":
        d.rounded_rectangle([*pt(3, 7), *pt(21, 17)], radius=s * 0.08, outline=rgb, width=sw)
        line(7, 11, 12, 11)
        line(7, 14, 17, 14)
    elif name == "image":
        d.rounded_rectangle([*pt(4, 5), *pt(20, 19)], radius=s * 0.06, outline=rgb, width=sw)
        ellipse(7, 8, 10.5, 11.5, width=max(sw - 1, 2))
        line(5.5, 16.5, 10, 12)
        line(10, 12, 14, 16)
        line(13, 14.5, 17, 11)
        line(17, 11, 19, 13.5)
    elif name == "link":
        d.arc([*pt(3, 8), *pt(12, 17)], start=40, end=220, fill=rgb, width=sw)
        d.arc([*pt(12, 7), *pt(21, 16)], start=220, end=40, fill=rgb, width=sw)
        line(9.5, 12, 14.5, 12)
    elif name == "check":
        line(5, 12, 10, 17)
        line(10, 17, 19, 7)
    elif name == "x":
        line(7, 7, 17, 17)
        line(17, 7, 7, 17)
    elif name == "sparkle":
        poly([(12, 3), (14, 10), (21, 12), (14, 14), (12, 21), (10, 14), (3, 12), (10, 10)], fill=rgb)
    elif name == "play":
        poly([(8, 6), (18, 12), (8, 18)], fill=rgb)
    elif name == "globe":
        ellipse(4, 4, 20, 20, width=sw)
        ellipse(8.5, 4, 15.5, 20, width=max(sw - 1, 2))
        line(4, 12, 20, 12)
    else:
        ellipse(6, 6, 18, 18, width=sw)

    return img.resize((size, size), Image.Resampling.LANCZOS)


def get_icon(name, size, color):
    key = (name, size, color)
    cached = _ICON_CACHE.get(key)
    if cached:
        return cached
    photo = ImageTk.PhotoImage(_render_icon(name, size, color))
    _ICON_CACHE[key] = photo
    return photo


def make_logo(size=42):
    s = size * 3
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    glow = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.rounded_rectangle((int(s * 0.06), int(s * 0.06), int(s * 0.94), int(s * 0.94)), radius=int(s * 0.28), fill=(139, 124, 255, 80))
    img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(int(s * 0.08))))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((int(s * 0.12), int(s * 0.12), int(s * 0.88), int(s * 0.88)), radius=int(s * 0.24), fill=_rgba(THEME["accent"]))
    inner = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    arrow = _render_icon("download", int(size * 0.48 * 3), "#ffffff")
    ax = (s - arrow.width) // 2
    ay = (s - arrow.height) // 2
    inner.paste(arrow, (ax, ay), arrow)
    img = Image.alpha_composite(img, inner)
    return ImageTk.PhotoImage(img.resize((size, size), Image.Resampling.LANCZOS))


VARIANTS = {
    "primary": (THEME["accent"], THEME["accent_text"], THEME["accent_hover"]),
    "danger": (THEME["error"], "#ffffff", "#ef5a5a"),
    "ghost": (THEME["elevated"], THEME["text_sec"], THEME["card_hover"]),
    "outline": (THEME["accent_dim"], THEME["accent"], THEME["accent_soft"]),
    "subtle": (THEME["surface"], THEME["text_muted"], THEME["elevated"]),
    "chip_on": (THEME["accent_soft"], THEME["accent"], THEME["accent_soft"]),
    "chip_off": (THEME["input"], THEME["text_sec"], THEME["elevated"]),
}


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self.show_tip, add="+")
        widget.bind("<Leave>", self.hide_tip, add="+")

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        x = (event.x_root + 14) if event else self.widget.winfo_rootx() + 20
        y = (event.y_root + 14) if event else self.widget.winfo_rooty() + 20
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.configure(bg=THEME["border_light"])
        frame = tk.Frame(tw, bg=THEME["elevated"], padx=1, pady=1)
        frame.pack()
        tk.Label(
            frame, text=self.text, justify=tk.LEFT, bg=THEME["elevated"], fg=THEME["text"],
            font=(FONT, 9), padx=10, pady=6,
        ).pack()

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


class RoundedFrame(tk.Frame):
    def __init__(self, master, radius=18, fill=None, outline=None, pad=18):
        parent_bg = THEME["bg"]
        try:
            parent_bg = master.cget("bg")
        except tk.TclError:
            pass
        super().__init__(master, bg=parent_bg)
        self._radius = radius
        self._fill = fill or THEME["card"]
        self._outline = outline or THEME["border"]
        self._parent_bg = parent_bg
        cs, tl, tr, bl, br = get_card_corners(radius, self._fill, self._outline, parent_bg)
        self._cs = cs
        self._tl = tk.Label(self, image=tl, bd=0, bg=parent_bg)
        self._tr = tk.Label(self, image=tr, bd=0, bg=parent_bg)
        self._bl = tk.Label(self, image=bl, bd=0, bg=parent_bg)
        self._br = tk.Label(self, image=br, bd=0, bg=parent_bg)
        self._top = tk.Frame(self, bg=self._outline, height=cs)
        self._top_fill = tk.Frame(self._top, bg=self._fill)
        self._top_fill.pack(fill="both", expand=True, pady=(1, 0))
        self._bot = tk.Frame(self, bg=self._outline, height=cs)
        self._bot_fill = tk.Frame(self._bot, bg=self._fill)
        self._bot_fill.pack(fill="both", expand=True, pady=(0, 1))
        self._left = tk.Frame(self, bg=self._outline, width=cs)
        self._left_fill = tk.Frame(self._left, bg=self._fill)
        self._left_fill.pack(fill="both", expand=True, padx=(1, 0))
        self._right = tk.Frame(self, bg=self._outline, width=cs)
        self._right_fill = tk.Frame(self._right, bg=self._fill)
        self._right_fill.pack(fill="both", expand=True, padx=(0, 1))
        self.inner = tk.Frame(self, bg=self._fill)
        extra = max(0, pad - cs)
        self.grid_columnconfigure(0, minsize=cs, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, minsize=cs, weight=0)
        self.grid_rowconfigure(0, minsize=cs, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, minsize=cs, weight=0)
        self._tl.grid(row=0, column=0)
        self._top.grid(row=0, column=1, sticky="nsew")
        self._tr.grid(row=0, column=2)
        self._left.grid(row=1, column=0, sticky="nsew")
        self.inner.grid(row=1, column=1, sticky="nsew", padx=extra, pady=extra)
        self._right.grid(row=1, column=2, sticky="nsew")
        self._bl.grid(row=2, column=0)
        self._bot.grid(row=2, column=1, sticky="nsew")
        self._br.grid(row=2, column=2)

    def set_outline(self, color):
        self._outline = color
        _, tl, tr, bl, br = get_card_corners(self._radius, self._fill, color, self._parent_bg)
        self._tl.configure(image=tl)
        self._tr.configure(image=tr)
        self._bl.configure(image=bl)
        self._br.configure(image=br)
        self._top.configure(bg=color)
        self._bot.configure(bg=color)
        self._left.configure(bg=color)
        self._right.configure(bg=color)


class RoundedButton(tk.Canvas):
    def __init__(
        self, master, text="", command=None, variant="ghost", icon=None,
        radius=12, padx=16, font_size=9, height=38, width=None, icon_only=False,
        expand=False, icon_size=16,
    ):
        parent_bg = THEME["bg"]
        try:
            parent_bg = master.cget("bg")
        except tk.TclError:
            pass
        super().__init__(master, highlightthickness=0, bd=0, bg=parent_bg, cursor="hand2")
        self._parent_bg = parent_bg
        self._text = text
        self._command = command
        self._variant = variant
        self._icon = icon
        self._icon_size = icon_size
        self._radius = radius
        self._padx = 10 if icon_only else padx
        self._font_size = font_size
        self._height = 38 if icon_only else height
        self._width = 38 if icon_only else width
        self._icon_only = icon_only
        self._expand = expand
        self._state = "normal"
        self._hover = False
        self._photo = None
        self._icon_ref = None
        self._painting = False
        self._resize_job = None
        self._tkfont = tkfont.Font(family=FONT, size=self._font_size, weight="bold")
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        if expand:
            self.bind("<Configure>", self._on_resize)
        self._paint()

    def configure(self, cnf=None, **kw):
        kw = dict(cnf or {}, **kw)
        mapped = False
        if "text" in kw:
            self._text = kw.pop("text")
            mapped = True
        if "command" in kw:
            self._command = kw.pop("command")
            mapped = True
        if "state" in kw:
            self._state = kw.pop("state")
            mapped = True
        if "variant" in kw:
            self._variant = kw.pop("variant")
            mapped = True
        if "icon" in kw:
            self._icon = kw.pop("icon")
            mapped = True
        if "bg" in kw:
            kw.pop("bg")
            mapped = True
        if "fg" in kw:
            kw.pop("fg")
            mapped = True
        if mapped:
            self._paint()
        if kw:
            super().configure(**kw)

    config = configure

    def _colors(self):
        bg, fg, hover = VARIANTS.get(self._variant, VARIANTS["ghost"])
        if self._state == "disabled":
            if self._variant == "primary":
                return THEME["accent_soft"], THEME["disabled"]
            return THEME["elevated"], THEME["disabled"]
        if self._hover:
            return hover, fg
        return bg, fg

    def _on_enter(self, _=None):
        if self._state == "disabled":
            return
        self._hover = True
        self._paint()

    def _on_leave(self, _=None):
        self._hover = False
        self._paint()

    def _on_click(self, _=None):
        if self._state != "disabled" and self._command:
            self._command()

    def _on_resize(self, event=None):
        if self._painting:
            return
        bg, _ = self._colors()
        super().configure(bg=bg)
        if self._resize_job:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(80, self._finish_resize)

    def _finish_resize(self):
        self._resize_job = None
        self._paint_sig = None
        super().configure(bg=self._parent_bg)
        self._paint()

    def _paint(self):
        if self._painting:
            return
        self._painting = True
        try:
            bg, fg = self._colors()
            fnt = (FONT, self._font_size, "bold")
            text_w = self._tkfont.measure(self._text) if self._text else 0
            icon_w = (self._icon_size + (8 if self._text else 0)) if self._icon else 0
            content = icon_w + text_w
            w = self._width or (content + self._padx * 2)
            h = self._height
            if self._expand:
                w = max(w, max(self.winfo_width(), 40))
            super().configure(width=w, height=h, cursor="arrow" if self._state == "disabled" else "hand2")
            if (w, h, self._text, self._variant, self._state, self._hover, self._icon) == getattr(self, "_paint_sig", None):
                return
            self._paint_sig = (w, h, self._text, self._variant, self._state, self._hover, self._icon)
            img = _rounded_image(w, h, self._radius, bg)
            self._photo = ImageTk.PhotoImage(img)
            self.delete("all")
            self.create_image(0, 0, image=self._photo, anchor="nw")
            cx = w // 2
            if self._icon and self._text:
                start = (w - content) // 2
                self._icon_ref = get_icon(self._icon, self._icon_size, fg)
                self.create_image(start + self._icon_size // 2, h // 2, image=self._icon_ref)
                self.create_text(start + icon_w, h // 2, text=self._text, fill=fg, font=fnt, anchor="w")
            elif self._icon:
                self._icon_ref = get_icon(self._icon, self._icon_size, fg)
                self.create_image(cx, h // 2, image=self._icon_ref)
            else:
                self.create_text(cx, h // 2, text=self._text, fill=fg, font=fnt)
        finally:
            self._painting = False


class ChoiceChip(RoundedButton):
    def __init__(self, master, text, value, on_pick, icon=None, padx=12):
        self.value = value
        self._on_pick = on_pick
        super().__init__(
            master, text=text, icon=icon, variant="chip_off",
            command=lambda: self._on_pick(self.value),
            radius=10, padx=padx, font_size=8, height=34, icon_size=14,
        )

    def set_active(self, active, disabled=False):
        self._state = "disabled" if disabled else "normal"
        self._variant = "chip_on" if active and not disabled else "chip_off"
        if disabled:
            self._variant = "subtle"
        self._paint()


class ToggleChip(RoundedButton):
    def __init__(self, master, text, variable, icon=None, tip=""):
        self.variable = variable
        super().__init__(
            master, text=text, icon=icon, variant="chip_off",
            command=self._toggle, radius=10, padx=12, font_size=8, height=32, icon_size=14,
        )
        variable.trace_add("write", lambda *a: self._sync())
        self._sync()
        if tip:
            ToolTip(self, tip)

    def _toggle(self):
        self.variable.set(not self.variable.get())

    def _sync(self):
        self._variant = "chip_on" if self.variable.get() else "chip_off"
        self._paint()


class StatusPill(tk.Canvas):
    def __init__(self, master, label):
        parent_bg = master.cget("bg")
        super().__init__(master, highlightthickness=0, bd=0, bg=parent_bg, height=30)
        self._parent_bg = parent_bg
        self._label = label
        self._photo = None
        self.set_status(False, label)

    def set_status(self, ok, text):
        bg = THEME["success_bg"] if ok else THEME["error_bg"]
        fg = THEME["success"] if ok else THEME["error"]
        mark = "●"
        fnt = tkfont.Font(family=FONT, size=8, weight="bold")
        label = f"{mark}  {text}"
        w = fnt.measure(label) + 24
        h = 28
        self.configure(width=w, height=h)
        img = _rounded_image(w, h, 14, bg)
        self._photo = ImageTk.PhotoImage(img)
        self.delete("all")
        self.create_image(0, 0, image=self._photo, anchor="nw")
        self.create_text(w // 2, h // 2, text=label, fill=fg, font=(FONT, 8, "bold"))


class YtDlpManager:
    def __init__(self):
        self.cancel_flag = False
        self.process = None
        self.current_file = None
        self.last_error = ""

    def run_cmd(self, cmd, timeout=60):
        try:
            return subprocess.run(
                cmd, capture_output=True, text=True, encoding="utf-8",
                errors="ignore", startupinfo=startup_info(), timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            self.last_error = "Command timed out"
            return None
        except Exception as e:
            self.last_error = str(e)
            return None

    def check_dependencies(self):
        status = {"ytdlp": False, "ffmpeg": False, "deno": False, "ytdlp_version": ""}
        res = self.run_cmd(get_ytdlp_cmd() + ["--version"], timeout=30)
        if res and res.returncode == 0:
            status["ytdlp"] = True
            status["ytdlp_version"] = res.stdout.strip().split("\n")[0]
        res = self.run_cmd(["ffmpeg", "-version"], timeout=15)
        if res and res.returncode == 0:
            status["ffmpeg"] = True
        res = self.run_cmd(["deno", "--version"], timeout=15)
        if res and res.returncode == 0:
            status["deno"] = True
        return status

    def install_update(self):
        log = []
        try:
            if getattr(sys, "frozen", False) or os.path.isfile(local_ytdlp_path()):
                try:
                    path = download_ytdlp_exe()
                    log.append(f"yt-dlp.exe updated in app folder\n  {path}")
                except Exception as e:
                    log.append(f"yt-dlp download failed: {e}")
            else:
                try:
                    res = subprocess.run(
                        get_pip_cmd() + ["install", "--upgrade", "yt-dlp[default]"],
                        capture_output=True, text=True, encoding="utf-8",
                        errors="ignore", startupinfo=startup_info(), timeout=180,
                    )
                    if res and res.returncode == 0:
                        log.append("yt-dlp updated via pip (with [default] extras)")
                    else:
                        err = res.stderr.strip()[:300] if res and res.stderr else "Unknown error"
                        log.append(f"yt-dlp pip install failed: {err}")
                except subprocess.TimeoutExpired:
                    log.append("yt-dlp update timed out")
                except Exception as e:
                    log.append(f"yt-dlp failed: {e}")

            for req in ["pillow", "requests"]:
                res = self.run_cmd(get_pip_cmd() + ["install", req], timeout=120)
                log.append(f"{req} ready" if res and res.returncode == 0 else f"{req} skipped (not required for EXE)")

            res = self.run_cmd(["ffmpeg", "-version"], timeout=15)
            log.append("FFmpeg found" if res and res.returncode == 0 else "FFmpeg missing — run setup.bat")

            res = self.run_cmd(["deno", "--version"], timeout=15)
            log.append("Deno found" if res and res.returncode == 0 else "Deno missing — run setup.bat")

            return True, "\n".join(log)
        except Exception as e:
            return False, str(e)

    def fetch_info(self, url, retries=1):
        cmd = get_ytdlp_cmd() + ["--dump-json", "--no-warnings", "--no-playlist", "--ignore-errors", url]
        for attempt in range(retries + 1):
            res = self.run_cmd(cmd, timeout=180)
            if res and res.stdout.strip():
                for line in res.stdout.splitlines():
                    try:
                        data = json.loads(line)
                        if data:
                            return data, None
                    except json.JSONDecodeError:
                        continue
                try:
                    return json.loads(res.stdout), None
                except json.JSONDecodeError:
                    pass
            if res is None and attempt < retries:
                continue
            if res is None:
                return None, "Connection timed out. Try again."
            if res.stdout.strip():
                return None, f"Parse error. Output: {res.stdout.strip()[:300]}"
            return None, res.stderr if res else "Unknown error"
        return None, "Could not fetch video info."

    def _build_format_args(self, fmt, qual, d_type, compat):
        h_map = {"8K": 4320, "4K": 2160, "2K": 1440, "1080p": 1080, "720p": 720, "480p": 480}
        h = h_map.get(qual.split(" ")[0], None)
        merge_fmt = "mp4" if compat else fmt
        if d_type == "audio":
            return ["-x", "--audio-format", fmt if fmt in ["mp3", "m4a"] else "mp3"]
        if compat:
            if d_type == "video":
                f_str = f"bestvideo[vcodec^=avc1][height<={h}]/bestvideo[vcodec^=avc1]/best[ext=mp4]/best" if h else "bestvideo[vcodec^=avc1]/best[ext=mp4]/best"
            else:
                f_str = (
                    f"bestvideo[vcodec^=avc1][height<={h}]+bestaudio[acodec^=mp4a]/bestvideo[vcodec^=avc1]+bestaudio/best[ext=mp4]/best"
                    if h else "bestvideo[vcodec^=avc1]+bestaudio[acodec^=mp4a]/best[ext=mp4]/best"
                )
            return ["-f", f_str, "--merge-output-format", merge_fmt]
        if d_type == "video":
            f_str = f"bestvideo[height<={h}]/bestvideo/best" if h else "bestvideo/best"
        else:
            f_str = (
                f"bestvideo[height<={h}]+bestaudio[ext=m4a]/bestvideo[height<={h}]+bestaudio/bestvideo+bestaudio/best"
                if h else "bestvideo+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
            )
        return ["-f", f_str, "--merge-output-format", merge_fmt]

    def _build_download_cmd(self, url, path, opts):
        fmt, qual, d_type, compat, turbo, subs = opts
        cmd = get_ytdlp_cmd() + ["-o", os.path.join(path, "%(title)s.%(ext)s"), "--newline", "--no-playlist", url]
        if turbo:
            cmd.extend(["-N", "16", "--http-chunk-size", "10M", "--no-mtime", "--resize-buffer"])
        cmd.extend(self._build_format_args(fmt, qual, d_type, compat))
        if subs:
            cmd.extend(["--write-subs", "--sub-langs", "en", "--convert-subs", "srt"])
        return cmd

    def _should_fallback(self, error_text):
        triggers = ["format is not available", "HTTP Error 403", "Sign in to confirm", "Requested format is not available"]
        return any(t.lower() in error_text.lower() for t in triggers)

    def _run_download_process(self, cmd, progress_callback, startupinfo):
        last_lines = []
        self.process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            universal_newlines=True, bufsize=1, startupinfo=startupinfo,
        )
        for line in self.process.stdout:
            if self.cancel_flag:
                self.process.terminate()
                return False, "Cancelled", last_lines
            if "[download] Destination:" in line:
                self.current_file = line.split("Destination:", 1)[1].strip()
            elif "[Merger] Merging formats into" in line:
                self.current_file = line.split("into", 1)[1].strip().replace('"', "")
            last_lines.append(line.strip())
            if len(last_lines) > 15:
                last_lines.pop(0)
            progress_callback(line)
        self.process.wait()
        if self.process.returncode == 0:
            return True, "Completed", last_lines
        return False, "\n".join(last_lines), last_lines

    def download(self, url, path, opts, progress_callback):
        self.cancel_flag = False
        si = startup_info()
        cmd = self._build_download_cmd(url, path, opts)
        _, _, _, compat, turbo, _ = opts
        try:
            ok, msg, last_lines = self._run_download_process(cmd, progress_callback, si)
            if ok:
                return True, msg
            if self.cancel_flag:
                return False, "Cancelled"
            if self._should_fallback(msg):
                simple_cmd = get_ytdlp_cmd() + ["-o", os.path.join(path, "%(title)s.%(ext)s"), "--newline", "--no-playlist", "-f", "best", url]
                if turbo:
                    simple_cmd.extend(["-N", "16", "--http-chunk-size", "10M", "--no-mtime", "--resize-buffer"])
                ok, msg, last_lines = self._run_download_process(simple_cmd, progress_callback, si)
                if ok:
                    return True, "Completed"
                if self.cancel_flag:
                    return False, "Cancelled"
            err_msg = "Download failed."
            for line in reversed(last_lines):
                if "ERROR:" in line or "Error:" in line:
                    err_msg = line
                    break
            return False, err_msg
        except Exception as e:
            return False, str(e)

    def cancel(self):
        self.cancel_flag = True
        if self.process:
            try:
                self.process.terminate()
            except Exception:
                pass
        if self.current_file and os.path.exists(self.current_file):
            try:
                for f in [self.current_file, self.current_file + ".part", self.current_file + ".ytdl"]:
                    if os.path.exists(f):
                        os.remove(f)
            except Exception:
                pass
        self.current_file = None


class ModernUI(tk.Tk):
    def __init__(self):
        _enable_dpi()
        super().__init__()
        global FONT
        FONT = pick_ui_font(self)
        self.title(f"YT-DLP Studio v{APP_VERSION}")
        self.geometry("1020x900")
        self.configure(bg=THEME["bg"])
        self.minsize(920, 760)
        self.manager = YtDlpManager()
        self.cfg = self.load_config()
        self._images = []

        self.url_var = tk.StringVar()
        self.path_var = tk.StringVar(value=self.cfg.get("path", os.path.expanduser("~/Downloads")))
        self.type_var = tk.StringVar(value="both")
        self.fmt_var = tk.StringVar(value="mp4")
        self.qual_var = tk.StringVar()
        self.compat_var = tk.BooleanVar(value=False)
        self.turbo_var = tk.BooleanVar(value=True)
        self.subs_var = tk.BooleanVar(value=False)
        self.video_data = None
        self._cancelled = False
        self._fetch_anim_id = None
        self._fetch_dots = 0
        self.dep_badges = {}
        self.fmt_buttons = {}
        self.type_buttons = {}
        self._downloading = False

        try:
            self._app_icon = make_logo(32)
            self.iconphoto(True, self._app_icon)
        except Exception:
            pass

        self._setup_styles()
        self.setup_ui()
        self.bind("<Return>", lambda e: self.fetch())
        self.after(400, self.refresh_dependencies)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Modern.Horizontal.TProgressbar",
            troughcolor=THEME["input"], background=THEME["accent"],
            borderwidth=0, lightcolor=THEME["accent"], darkcolor=THEME["accent"], thickness=10,
        )
        style.configure(
            "Success.Horizontal.TProgressbar",
            troughcolor=THEME["input"], background=THEME["success"],
            borderwidth=0, lightcolor=THEME["success"], darkcolor=THEME["success"], thickness=10,
        )
        style.configure(
            "Modern.TCombobox",
            fieldbackground=THEME["input"], background=THEME["elevated"],
            foreground=THEME["text"], arrowcolor=THEME["accent"],
            bordercolor=THEME["border"], lightcolor=THEME["border"], darkcolor=THEME["border"],
            padding=6,
        )
        style.map(
            "Modern.TCombobox",
            fieldbackground=[("readonly", THEME["input"])],
            foreground=[("readonly", THEME["text"])],
            selectbackground=[("readonly", THEME["accent_soft"])],
            selectforeground=[("readonly", THEME["text"])],
        )
        style.configure(
            "Modern.Vertical.TScrollbar",
            troughcolor=THEME["bg"], background=THEME["elevated"],
            bordercolor=THEME["bg"], arrowcolor=THEME["text_muted"],
            darkcolor=THEME["elevated"], lightcolor=THEME["elevated"],
        )

    def load_config(self):
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_config(self):
        self.cfg["path"] = self.path_var.get()
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.cfg, f, indent=2)
        except Exception:
            pass

    def add_recent_url(self, url):
        recent = self.cfg.get("recent_urls", [])
        if url in recent:
            recent.remove(url)
        recent.insert(0, url)
        self.cfg["recent_urls"] = recent[:10]
        self.save_config()

    def make_button(self, parent, text, cmd, variant="ghost", icon=None, **kwargs):
        mapped = {
            "padx": kwargs.pop("padx", 14),
            "font_size": 8 if kwargs.get("font") else kwargs.pop("font_size", 9),
            "height": 32 if kwargs.get("pady") and kwargs.get("pady") <= 6 else kwargs.pop("height", 38),
        }
        kwargs.pop("font", None)
        kwargs.pop("pady", None)
        return RoundedButton(parent, text=text, command=cmd, variant=variant, icon=icon, **mapped)

    def section_label(self, parent, text):
        return tk.Label(
            parent, text=text.upper(), font=(FONT, 8, "bold"),
            fg=THEME["text_muted"], bg=parent.cget("bg"), anchor="w",
        )

    def show_scrollable_error(self, title, message):
        win = tk.Toplevel(self)
        win.title(title)
        win.configure(bg=THEME["bg"])
        win.geometry("540x360")
        win.transient(self)
        win.grab_set()
        body = tk.Frame(win, bg=THEME["bg"])
        body.pack(fill="both", expand=True, padx=22, pady=20)
        tk.Label(body, text=title, font=(FONT, 15, "bold"), fg=THEME["error"], bg=THEME["bg"]).pack(anchor="w")
        card = RoundedFrame(body, radius=14, fill=THEME["input"], pad=12)
        card.pack(fill="both", expand=True, pady=(14, 16))
        text = tk.Text(
            card.inner, wrap=tk.WORD, bg=THEME["input"], fg=THEME["text"],
            font=(FONT_MONO, 9), relief=tk.FLAT, padx=8, pady=8, bd=0, highlightthickness=0,
        )
        text.pack(fill="both", expand=True)
        text.insert("1.0", message)
        text.config(state=tk.DISABLED)
        RoundedButton(body, text="Dismiss", command=win.destroy, variant="primary", icon="check", height=40).pack()

    def setup_ui(self):
        shell = tk.Frame(self, bg=THEME["bg"])
        shell.pack(fill="both", expand=True)

        accent_bar = tk.Canvas(shell, height=3, bg=THEME["bg"], highlightthickness=0, bd=0)
        accent_bar.pack(fill="x")
        self._accent_bar = accent_bar
        accent_bar.bind("<Configure>", self._paint_accent)

        outer = tk.Frame(shell, bg=THEME["bg"])
        outer.pack(fill="both", expand=True, padx=36, pady=(18, 10))

        header = tk.Frame(outer, bg=THEME["bg"])
        header.pack(fill="x", pady=(0, 12))

        brand = tk.Frame(header, bg=THEME["bg"])
        brand.pack(side="left")
        self._logo = make_logo(44)
        tk.Label(brand, image=self._logo, bg=THEME["bg"], bd=0).pack(side="left", padx=(0, 14))
        titles = tk.Frame(brand, bg=THEME["bg"])
        titles.pack(side="left")
        name = tk.Frame(titles, bg=THEME["bg"])
        name.pack(anchor="w")
        tk.Label(name, text="YT-DLP", font=(FONT, 22, "bold"), fg=THEME["text"], bg=THEME["bg"]).pack(side="left")
        tk.Label(name, text="Studio", font=(FONT, 22, "bold"), fg=THEME["accent"], bg=THEME["bg"]).pack(side="left", padx=(7, 0))
        self.version_lbl = tk.Label(
            titles, text=f"Premium downloader  ·  v{APP_VERSION}",
            font=(FONT, 10), fg=THEME["text_sec"], bg=THEME["bg"],
        )
        self.version_lbl.pack(anchor="w", pady=(2, 0))

        actions = tk.Frame(header, bg=THEME["bg"])
        actions.pack(side="right")
        reset_btn = RoundedButton(actions, icon="refresh", icon_only=True, variant="ghost", command=self.reset_ui)
        reset_btn.pack(side="left", padx=(0, 8))
        ToolTip(reset_btn, "Reset and clear the current video")
        deps_btn = RoundedButton(actions, text="Fix deps", icon="sliders", variant="outline", command=self.do_install, padx=14, height=38)
        deps_btn.pack(side="left")
        ToolTip(deps_btn, "Update yt-dlp and check FFmpeg / Deno")

        dep_row = tk.Frame(outer, bg=THEME["bg"])
        dep_row.pack(fill="x", pady=(0, 10))
        tk.Label(dep_row, text="SYSTEM", font=(FONT, 8, "bold"), fg=THEME["text_muted"], bg=THEME["bg"]).pack(side="left", padx=(2, 12))
        for key, name in [("ytdlp", "yt-dlp"), ("ffmpeg", "FFmpeg"), ("deno", "Deno")]:
            pill = StatusPill(dep_row, name)
            pill.pack(side="left", padx=(0, 8))
            self.dep_badges[key] = pill

        url_card = RoundedFrame(outer, radius=20, pad=18)
        url_card.pack(fill="x", pady=(0, 14))
        inner = url_card.inner
        self.section_label(inner, "Video link").pack(anchor="w", pady=(0, 10))

        url_row = tk.Frame(inner, bg=THEME["card"])
        url_row.pack(fill="x")

        self.url_shell = RoundedFrame(url_row, radius=14, fill=THEME["input"], outline=THEME["border"], pad=0)
        self.url_shell.pack(side="left", fill="x", expand=True, padx=(0, 10))
        entry_row = tk.Frame(self.url_shell.inner, bg=THEME["input"])
        entry_row.pack(fill="x", padx=4, pady=4)
        tk.Label(entry_row, image=get_icon("globe", 16, THEME["text_muted"]), bg=THEME["input"], bd=0).pack(side="left", padx=(10, 6))
        entry_hold = tk.Frame(entry_row, bg=THEME["input"])
        entry_hold.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.url_entry = tk.Entry(
            entry_hold, textvariable=self.url_var, bg=THEME["input"], fg=THEME["text"],
            insertbackground=THEME["accent"], relief=tk.FLAT, font=(FONT, 12),
            highlightthickness=0, bd=0,
        )
        self.url_entry.pack(fill="x", ipady=8)
        self.url_ph = tk.Label(
            entry_hold, text="Paste a YouTube, TikTok or Instagram URL",
            font=(FONT, 11), fg=THEME["text_muted"], bg=THEME["input"],
        )
        self.url_ph.place(relx=0, rely=0.5, anchor="w")
        self.url_ph.bind("<Button-1>", lambda e: self.url_entry.focus_set())
        self.url_entry.bind("<FocusIn>", lambda e: self.url_shell.set_outline(THEME["accent"]))
        self.url_entry.bind("<FocusOut>", lambda e: self.url_shell.set_outline(THEME["border"]))
        self.url_var.trace_add("write", lambda *a: self._on_url_change())

        btn_group = tk.Frame(url_row, bg=THEME["card"])
        btn_group.pack(side="right")
        paste_btn = RoundedButton(btn_group, icon="clipboard", icon_only=True, variant="ghost", command=self.paste_url)
        paste_btn.pack(side="left", padx=(0, 6))
        ToolTip(paste_btn, "Paste from clipboard")
        recent_btn = RoundedButton(btn_group, icon="clock", icon_only=True, variant="ghost", command=self.show_recent)
        recent_btn.pack(side="left", padx=(0, 8))
        ToolTip(recent_btn, "Recent URLs")
        self.fetch_btn = RoundedButton(btn_group, text="Analyze", icon="search", variant="primary", command=self.fetch, padx=18)
        self.fetch_btn.pack(side="left")
        self._update_fetch_btn()

        path_row = tk.Frame(inner, bg=THEME["card"])
        path_row.pack(fill="x", pady=(14, 0))
        tk.Label(path_row, image=get_icon("folder", 15, THEME["text_muted"]), bg=THEME["card"], bd=0).pack(side="left")
        tk.Label(path_row, text="Save to", font=(FONT, 9), fg=THEME["text_muted"], bg=THEME["card"]).pack(side="left", padx=(8, 8))
        tk.Label(path_row, textvariable=self.path_var, font=(FONT, 9), fg=THEME["text"], bg=THEME["card"]).pack(side="left")
        browse = RoundedButton(path_row, text="Browse", icon="folder", variant="ghost", command=self.browse_path, padx=10, height=30, font_size=8)
        browse.pack(side="left", padx=(12, 0))

        canvas = tk.Canvas(outer, bg=THEME["bg"], highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview, style="Modern.Vertical.TScrollbar")
        self.scroll_body = tk.Frame(canvas, bg=THEME["bg"])
        self._scroll_win = canvas.create_window((0, 0), window=self.scroll_body, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(fill="both", expand=True, pady=(4, 0))
        self._scrollbar = scrollbar

        self._scroll_job = None
        self._scroll_needed = None

        def _stretch(event):
            canvas.itemconfigure(self._scroll_win, width=event.width)
            self._queue_scrollbar()

        def _sync_scrollregion(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            self._queue_scrollbar()

        self.scroll_body.bind("<Configure>", _sync_scrollregion)
        canvas.bind("<Configure>", _stretch)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self._canvas = canvas

        self.empty = RoundedFrame(self.scroll_body, radius=20, fill=THEME["card"], pad=36)
        self.empty.pack(fill="x")
        empty_inner = self.empty.inner
        self._empty_logo = make_logo(56)
        tk.Label(empty_inner, image=self._empty_logo, bg=THEME["card"], bd=0).pack(pady=(8, 14))
        tk.Label(empty_inner, text="Drop a link. Get the file.", font=(FONT, 16, "bold"), fg=THEME["text"], bg=THEME["card"]).pack()
        tk.Label(
            empty_inner, text="Paste a YouTube, TikTok, Instagram or 1000+ other URLs,\nthen analyze to pick quality and download.",
            font=(FONT, 10), fg=THEME["text_sec"], bg=THEME["card"], justify="center",
        ).pack(pady=(8, 4))

        self.card_wrap = RoundedFrame(self.scroll_body, radius=20, pad=16)
        self.card = self.card_wrap.inner
        self.card_wrap.pack(fill="x")
        self.card_wrap.pack_forget()

        preview = tk.Frame(self.card, bg=THEME["card"])
        preview.pack(fill="x", pady=(0, 18))

        thumb_wrap = RoundedFrame(preview, radius=16, fill=THEME["input"], outline=THEME["border_light"], pad=0)
        thumb_wrap.pack(side="left")
        thumb_wrap.configure(width=THUMB_W + 4, height=THUMB_H + 4)
        thumb_wrap.pack_propagate(False)
        self.thumb = tk.Label(
            thumb_wrap.inner, bg=THEME["input"], text="Preview",
            fg=THEME["text_muted"], font=(FONT, 9),
        )
        self.thumb.pack(expand=True, fill="both")

        info = tk.Frame(preview, bg=THEME["card"])
        info.pack(side="left", fill="both", expand=True, padx=(20, 0))
        self.title_lbl = tk.Label(
            info, text="", font=(FONT, 16, "bold"), fg=THEME["text"],
            bg=THEME["card"], wraplength=520, justify="left", anchor="w",
        )
        self.title_lbl.pack(anchor="w")
        self.meta_lbl = tk.Label(info, text="", font=(FONT, 10), fg=THEME["text_sec"], bg=THEME["card"], anchor="w")
        self.meta_lbl.pack(anchor="w", pady=(8, 0))

        tk.Frame(self.card, bg=THEME["border"], height=1).pack(fill="x", pady=(0, 18))

        self.section_label(self.card, "Media type").pack(anchor="w", pady=(0, 8))
        type_row = tk.Frame(self.card, bg=THEME["card"])
        type_row.pack(anchor="w", pady=(0, 16))
        for label, val, icon in [("Video + Audio", "both", "layers"), ("Video only", "video", "film"), ("Audio only", "audio", "music")]:
            btn = ChoiceChip(type_row, label, val, self._set_type, icon=icon, padx=13)
            btn.pack(side="left", padx=(0, 8))
            self.type_buttons[val] = btn
        self._highlight_type_btn("both")

        opts = tk.Frame(self.card, bg=THEME["card"])
        opts.pack(fill="x", pady=(0, 8))

        fmt_col = tk.Frame(opts, bg=THEME["card"])
        fmt_col.pack(side="left", fill="y", padx=(0, 36))
        self.section_label(fmt_col, "Format").pack(anchor="w", pady=(0, 8))
        fmt_row = tk.Frame(fmt_col, bg=THEME["card"])
        fmt_row.pack(anchor="w")
        for f in ["mp4", "webm", "mp3", "m4a"]:
            btn = ChoiceChip(fmt_row, f.upper(), f, self._set_format, padx=12)
            btn.pack(side="left", padx=(0, 6))
            self.fmt_buttons[f] = btn
        self._highlight_fmt_btn("mp4")

        qual_col = tk.Frame(opts, bg=THEME["card"])
        qual_col.pack(side="left", fill="y")
        self.section_label(qual_col, "Quality").pack(anchor="w", pady=(0, 8))
        self.qual_box = ttk.Combobox(qual_col, textvariable=self.qual_var, state="readonly", width=18, style="Modern.TCombobox", font=(FONT, 10))
        self.qual_box.pack(anchor="w")
        self.qual_var.trace_add("write", lambda *a: self._sync_dl_label())

        self.section_label(self.card, "Options").pack(anchor="w", pady=(16, 8))
        opt_row = tk.Frame(self.card, bg=THEME["card"])
        opt_row.pack(anchor="w")
        ToggleChip(opt_row, "Turbo", self.turbo_var, icon="zap", tip="16 parallel connections for faster downloads").pack(side="left", padx=(0, 8))
        ToggleChip(opt_row, "Premiere", self.compat_var, icon="clapper", tip="H.264 + AAC for video editors").pack(side="left", padx=(0, 8))
        ToggleChip(opt_row, "Subs EN", self.subs_var, icon="captions", tip="Download English SRT subtitles").pack(side="left", padx=(0, 8))
        RoundedButton(
            opt_row, text="Save thumb", icon="image", variant="ghost",
            command=self.save_thumb, padx=12, height=32, font_size=8,
        ).pack(side="left")

        self.dl_btn = RoundedButton(
            self.card, text="Download", icon="download", variant="primary",
            command=self.start_download, expand=True, height=48, font_size=12, radius=14, icon_size=18,
        )
        self.dl_btn.pack(fill="x", pady=(20, 0))

        self.prog_fr = tk.Frame(self.card, bg=THEME["card"])
        stats = tk.Frame(self.prog_fr, bg=THEME["card"])
        stats.pack(fill="x")
        self.stat_size = self._make_stat(stats, "Total")
        self.stat_done = self._make_stat(stats, "Done")
        self.stat_speed = self._make_stat(stats, "Speed")
        self.stat_eta = self._make_stat(stats, "ETA")
        prog_header = tk.Frame(self.prog_fr, bg=THEME["card"])
        prog_header.pack(fill="x", pady=(16, 6))
        tk.Label(prog_header, text="PROGRESS", font=(FONT, 8, "bold"), fg=THEME["text_muted"], bg=THEME["card"]).pack(side="left")
        self.pct_lbl = tk.Label(prog_header, text="0%", font=(FONT, 10, "bold"), fg=THEME["accent"], bg=THEME["card"])
        self.pct_lbl.pack(side="right")
        self.prog_bar = ttk.Progressbar(self.prog_fr, style="Modern.Horizontal.TProgressbar", mode="determinate")
        self.prog_bar.pack(fill="x", pady=(0, 4))

        footer = tk.Frame(self, bg=THEME["surface"], highlightbackground=THEME["border"], highlightthickness=1)
        footer.pack(side="bottom", fill="x")
        footer_inner = tk.Frame(footer, bg=THEME["surface"], padx=36, pady=11)
        footer_inner.pack(fill="x")
        self.status_dot = tk.Label(footer_inner, text="●", font=(FONT, 10), fg=THEME["success"], bg=THEME["surface"])
        self.status_dot.pack(side="left")
        self.status = tk.Label(footer_inner, text="Ready", font=(FONT, 9), fg=THEME["text_sec"], bg=THEME["surface"])
        self.status.pack(side="left", padx=(8, 0))
        credit = tk.Frame(footer_inner, bg=THEME["surface"])
        credit.pack(side="right")
        tk.Label(credit, text="Made by", font=(FONT, 9), fg=THEME["text_muted"], bg=THEME["surface"]).pack(side="left")
        gh = tk.Label(
            credit, text="Shiraken12T", font=(FONT, 9, "bold"),
            fg=THEME["accent"], bg=THEME["surface"], cursor="hand2",
        )
        gh.pack(side="left", padx=(5, 0))
        gh.bind("<Button-1>", lambda e: webbrowser.open(GITHUB_URL))
        gh.bind("<Enter>", lambda e: gh.config(fg=THEME["accent_hover"]))
        gh.bind("<Leave>", lambda e: gh.config(fg=THEME["accent"]))
        ToolTip(gh, GITHUB_URL)

    def _paint_accent(self, event=None):
        c = self._accent_bar
        w = c.winfo_width()
        if w < 2 or abs(w - getattr(self, "_accent_w", 0)) < 12:
            return
        self._accent_w = w
        c.delete("all")
        colors = ["#5b4dff", "#8b7cff", "#c4b5fd", "#8b7cff", "#3ee0c0"]
        seg = max(w // (len(colors) - 1), 1)
        for i in range(len(colors) - 1):
            c.create_rectangle(i * seg, 0, (i + 1) * seg + 2, 3, fill=colors[i], outline="")
        c.create_rectangle((len(colors) - 1) * seg, 0, w, 3, fill=colors[-1], outline="")

    def _make_stat(self, parent, title):
        wrap = RoundedFrame(parent, radius=12, fill=THEME["input"], outline=THEME["border"], pad=8)
        wrap.pack(side="left", expand=True, fill="x", padx=(0, 8))
        tk.Label(wrap.inner, text=title.upper(), font=(FONT, 7, "bold"), fg=THEME["text_muted"], bg=THEME["input"]).pack()
        lbl = tk.Label(wrap.inner, text="—", font=(FONT, 12, "bold"), fg=THEME["text"], bg=THEME["input"])
        lbl.pack()
        return lbl

    def _set_type(self, val):
        self.type_var.set(val)
        self._highlight_type_btn(val)
        self.update_opts()
        self._sync_dl_label()

    def _highlight_type_btn(self, active):
        for val, btn in self.type_buttons.items():
            btn.set_active(val == active)

    def _set_format(self, val):
        if self.type_var.get() == "audio" and val in ("mp4", "webm"):
            return
        if self.type_var.get() != "audio" and val in ("mp3", "m4a"):
            return
        self.fmt_var.set(val)
        self._highlight_fmt_btn(val)
        self._sync_dl_label()

    def _highlight_fmt_btn(self, active):
        for val, btn in self.fmt_buttons.items():
            disabled = (
                (self.type_var.get() == "audio" and val in ("mp4", "webm"))
                or (self.type_var.get() != "audio" and val in ("mp3", "m4a"))
            )
            btn.set_active(val == active, disabled=disabled)

    def _on_url_change(self):
        if hasattr(self, "url_ph"):
            if self.url_var.get().strip():
                self.url_ph.place_forget()
            else:
                self.url_ph.place(relx=0, rely=0.5, anchor="w")
        if hasattr(self, "fetch_btn"):
            self._update_fetch_btn()

    def _queue_scrollbar(self):
        if self._scroll_job:
            self.after_cancel(self._scroll_job)
        self._scroll_job = self.after(80, self._sync_scrollbar)

    def _sync_scrollbar(self):
        self._scroll_job = None
        bbox = self._canvas.bbox("all")
        needs = bool(bbox) and bbox[3] > self._canvas.winfo_height() + 4
        if needs == self._scroll_needed:
            return
        self._scroll_needed = needs
        if needs:
            self._scrollbar.pack(side="right", fill="y")
        else:
            self._scrollbar.pack_forget()

    def _update_fetch_btn(self):
        has_url = bool(self.url_var.get().strip())
        self.fetch_btn.config(state="normal" if has_url else "disabled")

    def _sync_dl_label(self):
        if self._downloading:
            return
        qual = self.qual_var.get() or "Best"
        fmt = self.fmt_var.get().upper()
        self.dl_btn.config(text=f"Download  ·  {qual} {fmt}", icon="download", variant="primary")

    def _set_status(self, text, kind="ready"):
        colors = {"ready": THEME["success"], "busy": THEME["warning"], "error": THEME["error"], "info": THEME["accent"]}
        self.status.config(text=text)
        self.status_dot.config(fg=colors.get(kind, THEME["text_sec"]))

    def refresh_dependencies(self):
        def run():
            status = self.manager.check_dependencies()
            self.after(0, lambda: self._update_dep_badges(status))
        threading.Thread(target=run, daemon=True).start()

    def _update_dep_badges(self, status):
        names = {"ytdlp": "yt-dlp", "ffmpeg": "FFmpeg", "deno": "Deno"}
        for key, badge in self.dep_badges.items():
            ok = status.get(key, False)
            extra = f"  {status['ytdlp_version']}" if key == "ytdlp" and status.get("ytdlp_version") else ""
            badge.set_status(ok, f"{names[key]}{extra}")
        if status.get("ytdlp_version"):
            self.version_lbl.config(text=f"Premium downloader  ·  v{APP_VERSION}  ·  yt-dlp {status['ytdlp_version']}")

    def paste_url(self):
        try:
            text = self.clipboard_get().strip()
            if text:
                self.url_var.set(text)
        except tk.TclError:
            messagebox.showwarning("Clipboard", "Clipboard is empty or unavailable.")

    def show_recent(self):
        recent = self.cfg.get("recent_urls", [])
        if not recent:
            messagebox.showinfo("Recent URLs", "No recent URLs yet.")
            return
        win = tk.Toplevel(self)
        win.title("Recent URLs")
        win.configure(bg=THEME["bg"])
        win.geometry("560x340")
        win.transient(self)
        body = tk.Frame(win, bg=THEME["bg"])
        body.pack(fill="both", expand=True, padx=22, pady=20)
        tk.Label(body, text="Recent URLs", font=(FONT, 15, "bold"), fg=THEME["text"], bg=THEME["bg"]).pack(anchor="w")
        card = RoundedFrame(body, radius=14, fill=THEME["input"], pad=8)
        card.pack(fill="both", expand=True, pady=(12, 14))
        lb = tk.Listbox(
            card.inner, bg=THEME["input"], fg=THEME["text"], font=(FONT, 10),
            selectbackground=THEME["accent"], selectforeground=THEME["accent_text"],
            relief=tk.FLAT, highlightthickness=0, bd=0, activestyle="none",
        )
        lb.pack(fill="both", expand=True)
        for url in recent:
            lb.insert(tk.END, url)

        def pick():
            sel = lb.curselection()
            if sel:
                self.url_var.set(lb.get(sel[0]))
                win.destroy()

        lb.bind("<Double-Button-1>", lambda e: pick())
        RoundedButton(body, text="Use selected", command=pick, variant="primary", icon="link", height=40).pack()

    def browse_path(self):
        d = filedialog.askdirectory(initialdir=self.path_var.get())
        if d:
            self.path_var.set(d)
            self.save_config()

    def update_opts(self):
        t = self.type_var.get()
        is_aud = t == "audio"
        cur = self.fmt_var.get()
        if is_aud and cur in ("mp4", "webm"):
            self.fmt_var.set("mp3")
        if not is_aud and cur in ("mp3", "m4a"):
            self.fmt_var.set("mp4")
        self._highlight_fmt_btn(self.fmt_var.get())

    def reset_ui(self):
        self.url_var.set("")
        self.card_wrap.pack_forget()
        self.empty.pack(fill="x")
        self._cancelled = True
        self._downloading = False
        self.manager.cancel()
        self._set_status("Ready", "ready")
        self._stop_fetch_anim()

    def _start_fetch_anim(self):
        self._fetch_dots = 0
        self._animate_fetch()

    def _animate_fetch(self):
        self._fetch_dots = (self._fetch_dots % 3) + 1
        self._set_status("Analyzing" + "." * self._fetch_dots, "busy")
        self._fetch_anim_id = self.after(400, self._animate_fetch)

    def _stop_fetch_anim(self):
        if self._fetch_anim_id:
            self.after_cancel(self._fetch_anim_id)
            self._fetch_anim_id = None

    def fetch(self):
        url = self.url_var.get().strip()
        if not url:
            return
        self.fetch_btn.config(state="disabled")
        self._start_fetch_anim()

        def run():
            data, err = self.manager.fetch_info(url, retries=1)
            self.after(0, lambda: self._on_fetch(data, err, url))
        threading.Thread(target=run, daemon=True).start()

    def _on_fetch(self, data, err, url):
        self._stop_fetch_anim()
        self._update_fetch_btn()

        if not data:
            msg = "Could not fetch video info."
            if err:
                msg += f"\n\n{err}"
            self.show_scrollable_error("Fetch Error", msg)
            self._set_status("Fetch failed", "error")
            return

        self.add_recent_url(url)
        self.video_data = data
        title = data.get("title") or data.get("url", "Unknown").split("/")[-1].split("?")[0]
        self.title_lbl.config(text=title)
        d = data.get("duration")
        if d:
            d = int(d)
        dur_str = f"{d // 60}:{d % 60:02d}" if d else "N/A"
        views = data.get("view_count", "-")
        if isinstance(views, int):
            views = f"{views:,}"
        uploader = data.get("uploader", "Unknown")
        self.meta_lbl.config(text=f"{uploader}  ·  {dur_str}  ·  {views} views")

        thumb_url = data.get("thumbnail")
        thumbs = data.get("thumbnails")
        if thumbs and isinstance(thumbs, list):
            try:
                best_t = max(thumbs, key=lambda t: t.get("width", 0) or 0)
                if best_t.get("url"):
                    thumb_url = best_t["url"]
            except Exception:
                pass

        if thumb_url:
            try:
                raw = requests.get(thumb_url, timeout=10).content
                img = Image.open(BytesIO(raw))
                rounded = round_photo(img, 14, (THUMB_W, THUMB_H))
                photo = ImageTk.PhotoImage(rounded)
                self.thumb.config(image=photo, text="", width=THUMB_W, height=THUMB_H)
                self.thumb.image = photo
            except Exception:
                self.thumb.config(image="", text="No preview", fg=THEME["text_muted"])
        else:
            self.thumb.config(image="", text="No preview", fg=THEME["text_muted"])

        avail = []
        for s in ["8K", "4K", "2K", "1080p", "720p", "480p", "360p"]:
            limit = int(s.replace("p", "").replace("K", "000").replace("8000", "4320").replace("4000", "2160").replace("2000", "1440"))
            if any(f.get("height") == limit for f in data.get("formats", []) if f.get("height")):
                avail.append(s)
        self.qual_box["values"] = avail if avail else ["Best Available"]
        self.qual_box.current(0)

        self.empty.pack_forget()
        self.card_wrap.pack(fill="x")
        self._set_status("Ready to download", "ready")
        self.update_opts()
        self._sync_dl_label()

    def start_download(self):
        if not self.video_data:
            return
        self._cancelled = False
        self._downloading = True
        self.dl_btn.config(text="Cancel download", icon="x", variant="danger", command=self.cancel_download)
        self.prog_fr.pack(fill="x", pady=(18, 0))
        self.prog_bar.config(style="Modern.Horizontal.TProgressbar", value=0)
        self.pct_lbl.config(text="0%", fg=THEME["accent"])

        fmt = self.fmt_var.get()
        if self.compat_var.get() and self.type_var.get() != "audio":
            fmt = "mp4"
        opts = (fmt, self.qual_var.get(), self.type_var.get(), self.compat_var.get(), self.turbo_var.get(), self.subs_var.get())

        def run():
            s, m = self.manager.download(self.url_var.get(), self.path_var.get(), opts, self._update_progress)
            self.after(0, lambda: self._on_end(s, m))
        threading.Thread(target=run, daemon=True).start()
        self._set_status("Downloading...", "busy")

    def cancel_download(self):
        if messagebox.askyesno("Cancel", "Stop download and delete partial files?"):
            self._cancelled = True
            self.manager.cancel()
            self._set_status("Cancelled", "error")

    def _update_progress(self, line):
        try:
            if "%" in line:
                m = re.search(r"(\d+\.?\d*)%", line)
                if m:
                    pct = float(m.group(1))
                    self.after(0, lambda p=pct: self.prog_bar.config(value=p))
                    self.after(0, lambda p=pct: self.pct_lbl.config(text=f"{p:.1f}%"))
            spd = re.search(r"at\s+(\d+\.?\d*[KMG]iB/s)", line)
            if spd:
                self.after(0, lambda s=spd.group(1): self.stat_speed.config(text=s))
            sz = re.search(r"of\s+~?\s*(\d+\.?\d*[KMG]iB)", line)
            if sz:
                self.after(0, lambda s=sz.group(1): self.stat_size.config(text=s))
            dl = re.search(r"(\d+\.?\d*[KMG]iB)\s+of", line) or re.search(r"\[download\]\s+(\d+\.?\d*[KMG]iB)", line)
            if dl:
                self.after(0, lambda d=dl.group(1): self.stat_done.config(text=d))
            eta = re.search(r"ETA\s+(\d+:\d+)", line)
            if eta:
                self.after(0, lambda e=eta.group(1): self.stat_eta.config(text=e))
            if "Merging" in line:
                self.after(0, lambda: self._set_status("Merging audio & video...", "busy"))
        except Exception:
            pass

    def _on_end(self, success, msg):
        self._downloading = False
        if self._cancelled and not success:
            self.dl_btn.config(command=self.start_download)
            self._sync_dl_label()
            self.prog_fr.pack_forget()
            self.prog_bar["value"] = 0
            return

        self.dl_btn.config(command=self.start_download)
        self._sync_dl_label()
        self.prog_fr.pack_forget()

        if success:
            self.prog_bar.config(style="Success.Horizontal.TProgressbar", value=100)
            self.pct_lbl.config(text="100%", fg=THEME["success"])
            self._set_status("Download complete", "ready")
            if messagebox.askyesno("Success", f"Saved to:\n{self.path_var.get()}\n\nOpen folder?"):
                try:
                    os.startfile(self.path_var.get())
                except Exception as e:
                    messagebox.showerror("Error", str(e))
        else:
            if msg != "Cancelled":
                self.show_scrollable_error("Download Error", msg)
            self._set_status("Cancelled" if msg == "Cancelled" else "Download failed", "error")

        self.prog_bar["value"] = 0
        self.pct_lbl.config(text="0%", fg=THEME["accent"])
        for s in [self.stat_size, self.stat_done, self.stat_speed, self.stat_eta]:
            s.config(text="—")

    def do_install(self):
        self._set_status("Updating dependencies...", "busy")

        def run():
            _, m = self.manager.install_update()
            self.after(0, lambda: messagebox.showinfo("Dependencies", m))
            self.after(0, lambda: self._set_status("Ready", "ready"))
            self.after(0, self.refresh_dependencies)
        threading.Thread(target=run, daemon=True).start()

    def save_thumb(self):
        if not self.video_data:
            return
        url = self.video_data.get("thumbnail")
        if not url:
            messagebox.showwarning("Thumbnail", "No thumbnail available.")
            return
        try:
            title = "".join(x for x in self.video_data.get("title", "thumbnail") if x.isalnum() or x in " -_")
            path = os.path.join(self.path_var.get(), f"{title}_thumb.jpg")
            with open(path, "wb") as f:
                f.write(requests.get(url, timeout=10).content)
            messagebox.showinfo("Saved", f"Thumbnail saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    app = ModernUI()
    app.mainloop()
