import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font
import threading
import subprocess
import json
import os
import re
from PIL import Image, ImageTk, ImageDraw
import requests
from io import BytesIO
import datetime

# --- Configuration & Theme (Midnight Gold) ---
THEME = {
    "bg": "#050505",           # Pure Dark
    "card_bg": "#121212",      # Material Dark
    "input_bg": "#1E1E1E",     # Slightly Lighter
    "accent": "#D4AF37",       # Metallic Gold
    "accent_hover": "#C5A028",
    "text_main": "#E0E0E0",
    "text_sec": "#A0A0A0",
    "success": "#27ae60",
    "warning": "#f39c12",
    "error": "#c0392b",
    "border": "#333333"
}

class ToolTip(object):
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text: return
        x, y, _, _ = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + self.widget.winfo_rooty() + 25
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                       background="#333", foreground="#D4AF37",
                       relief=tk.SOLID, borderwidth=1,
                       font=("Segoe UI", 9))
        label.pack(ipadx=4, ipady=4)

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

class YtDlpManager:
    """Handles logic for yt-dlp operations"""
    def __init__(self):
        self.cancel_flag = False
        self.process = None
        self.current_file = None

    def run_cmd(self, cmd):
        try:
            # Hide console window on Windows
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            # Add timeout to prevent hanging forever
            return subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', startupinfo=startupinfo, timeout=60)
        except subprocess.TimeoutExpired:
            return None
        except Exception as e:
            return None

    def install_update(self):
        log = []
        try:
            # yt-dlp
            res = self.run_cmd(['pip', 'install', 'yt-dlp', '--upgrade'])
            log.append("✅ yt-dlp updated" if res and res.returncode == 0 else f"❌ yt-dlp failed: {res.stderr if res else 'Unknown'}")
            
            # deps
            for req in ['pillow', 'requests']:
                res = self.run_cmd(['pip', 'install', req])
                log.append(f"✅ {req} ready" if res and res.returncode == 0 else f"❌ {req} failed")
                
            # ffmpeg check
            if self.run_cmd(['ffmpeg', '-version']).returncode == 0:
                log.append("✅ ffmpeg found")
            else:
                log.append("⚠️ ffmpeg missing (needed for merging)")
                
            return True, "\n".join(log)
        except Exception as e:
            return False, str(e)

    def fetch_info(self, url):
        try:
            # Optimized fetch: No playlist, no warnings, ignore errors (for generic streams)
            cmd = ['yt-dlp', '--dump-json', '--no-warnings', '--no-playlist', '--ignore-errors', url]
            res = self.run_cmd(cmd)
            
            if res and res.stdout.strip():
                # Success (or partial success)
                # Handle NDJSON (Multiple JSONs, e.g. Instagram Carousel)
                for line in res.stdout.splitlines():
                    try:
                        data = json.loads(line)
                        if data: return data, None
                    except: continue
                
                # If partial parsing failed but we have output, try full load
                try: return json.loads(res.stdout), None
                except: pass
            
            # Failure
            # Failure
            if res is None:
                return None, "Connection timed out. Try again."
            
            # If we got output but couldn't parse it
            if res.stdout.strip():
                return None, f"Parse Error. Output start: {res.stdout.strip()[:200]}"

            err = res.stderr if res else "Unknown error"
            return None, err
        except Exception as e:
            return None, str(e)

    def download(self, url, path, opts, progress_callback):
        self.cancel_flag = False
        cmd = ['yt-dlp', '-o', os.path.join(path, '%(title)s.%(ext)s'), '--newline', '--no-playlist', url]
        
        # Build command based on options
        fmt, qual, d_type, compat, turbo = opts
        
        # Parallel / Turbo
        if turbo:
            # Super Turbo: 16 threads, large chunks, no mtime
            cmd.extend(['-N', '16', '--http-chunk-size', '10M', '--no-mtime', '--resize-buffer'])
        
        if d_type == "audio":
            cmd.extend(['-x', '--audio-format', fmt if fmt in ['mp3', 'm4a'] else 'mp3'])
        else: # video or both
            h_map = {'8K': 4320, '4K': 2160, '2K': 1440, '1080p': 1080, '720p': 720, '480p': 480}
            h = h_map.get(qual.split(' ')[0], None) # None means Best/Unknown
            
            # Helper to build format string
            def get_fmt(base, fallback):
                if h: return f"{base}[height<={h}]{fallback}"
                return f"{base}{fallback}" # No height limit for Best Available

            if d_type == "video":
                 # Video only
                f_str = get_fmt('bestvideo', '')
                if compat: f_str = get_fmt('bestvideo', '') 
                cmd.extend(['-f', f_str, '--merge-output-format', fmt])
            else:
                # Both
                if fmt == 'mp4':
                    if compat:
                        # Strict (H.264 + AAC)
                        limit = f"[height<={h}]" if h else ""
                        f_str = f'bestvideo{limit}[vcodec^=avc]+bestaudio[ext=m4a]/best{limit}'
                        cmd.extend(['-f', f_str, '--merge-output-format', 'mp4'])
                    else:
                        # MAX QUALITY
                        if h:
                            f_str = f'bestvideo[height<={h}]+bestaudio/best[height<={h}]/best'
                        else:
                            f_str = f'bestvideo+bestaudio/best'
                        cmd.extend(['-f', f_str, '--merge-output-format', 'mp4'])
                else:
                    # Other formats
                    if h:
                        f_str = f'bestvideo[height<={h}]+bestaudio/best[height<={h}]'
                    else:
                        f_str = f'bestvideo+bestaudio/best'
                    cmd.extend(['-f', f_str, '--merge-output-format', fmt])

        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                universal_newlines=True, bufsize=1, startupinfo=startupinfo
            )
            
            last_lines = []
            for line in self.process.stdout:
                if self.cancel_flag: 
                    self.process.terminate()
                    return False, "Cancelled"
                
                # Capture filename for deletion on cancel
                if '[download] Destination:' in line:
                    self.current_file = line.split('Destination:', 1)[1].strip()
                elif '[Merger] Merging formats into' in line:
                    self.current_file = line.split('into', 1)[1].strip().replace('"', '')

                last_lines.append(line.strip())
                if len(last_lines) > 10: last_lines.pop(0) # Keep last 10 lines
                
                progress_callback(line)
            
            self.process.wait()
            
            if self.process.returncode == 0:
                return True, "Completed"
            
            # --- FALLBACK LOGIC ---
            # If failed due to "format not available" (generic M3U8 issue), retry simplistically
            full_err = "\n".join(last_lines)
            if "format is not available" in full_err:
                print("Retry with simple formats...")
                # Simple cmd: no merge, no complex selector, just best
                simple_cmd = ['yt-dlp', '-o', os.path.join(path, '%(title)s.%(ext)s'), '--newline', '--no-playlist', '-f', 'best', url]
                if turbo: simple_cmd.extend(['-N', '16', '--http-chunk-size', '10M', '--no-mtime', '--resize-buffer'])
                
                # Retry
                self.process = subprocess.Popen(
                    simple_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                    universal_newlines=True, bufsize=1, startupinfo=startupinfo
                )
                
                last_lines = []
                for line in self.process.stdout:
                    if self.cancel_flag: 
                        self.process.terminate()
                        return False, "Cancelled"
                    last_lines.append(line.strip())
                    if len(last_lines) > 10: last_lines.pop(0)
                    progress_callback(line)
                
                self.process.wait()
                if self.process.returncode == 0: return True, "Completed"
            
            # --- END FALLBACK ---

            # Find meaningful error
            err_msg = "Download failed."
            for l in reversed(last_lines):
                if "ERROR:" in l or "Error:" in l:
                    err_msg = l
                    break
            return False, err_msg
        except Exception as e:
            return False, str(e)

    def cancel(self):
        self.cancel_flag = True
        if self.process:
            try: self.process.terminate() 
            except: pass
        
        # Cleanup incomplete files
        if self.current_file and os.path.exists(self.current_file):
            try:
                # Try deleting main file and potential partials
                for f in [self.current_file, self.current_file + ".part", self.current_file + ".ytdl"]:
                    if os.path.exists(f): 
                        os.remove(f)
            except: pass
        self.current_file = None

class ModernUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YT-DLP Modern")
        self.geometry("900x750")
        self.configure(bg=THEME["bg"])
        self.minsize(800, 600)
        self.manager = YtDlpManager()
        self.config_path = os.path.join(os.path.expanduser("~"), ".ytdlp_gui_config.json")
        self.cfg = self.load_config()
        
        # State
        self.url_var = tk.StringVar()
        self.path_var = tk.StringVar(value=self.cfg.get("path", os.path.expanduser("~/Downloads")))
        self.type_var = tk.StringVar(value="both")
        self.fmt_var = tk.StringVar(value="mp4")
        self.qual_var = tk.StringVar()
        self.compat_var = tk.BooleanVar(value=False)
        self.turbo_var = tk.BooleanVar(value=True)
        self.video_data = None

        self.setup_ui()

    def load_config(self):
        try: 
            with open(self.config_path) as f: return json.load(f)
        except: return {}

    def save_config(self):
        self.cfg["path"] = self.path_var.get()
        try:
            with open(self.config_path, 'w') as f: json.dump(self.cfg, f)
        except: pass

    # --- UI Helpers ---
    def frame(self, parent, **kwargs):
        cfg = {"bg": THEME["bg"]}
        cfg.update(kwargs)
        return tk.Frame(parent, **cfg)

    def label(self, parent, text, font=("Segoe UI", 10), fg=THEME["text_main"], **kwargs):
        cfg = {"bg": parent["bg"] if "bg" in parent.keys() else THEME["bg"]}
        cfg.update(kwargs)
        return tk.Label(parent, text=text, font=font, fg=fg, **cfg)

    def btn(self, parent, text, cmd, bg=THEME["card_bg"], fg=THEME["accent"], **kwargs):
        cfg = {
            "font": ("Segoe UI", 9, "bold"), "relief": "flat", "cursor": "hand2",
            "activebackground": bg, "activeforeground": THEME["accent_hover"],
            "borderwidth": 0
        }
        cfg.update(kwargs)
        return tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg, **cfg)
        
    def entry(self, parent, var, **kwargs):
        cfg = {
            "bg": THEME["input_bg"], "fg": "#FFF", "insertbackground": THEME["accent"],
            "relief": "flat", "font": ("Segoe UI", 11)
        }
        cfg.update(kwargs)
        return tk.Entry(parent, textvariable=var, **cfg)

    def setup_ui(self):
        # 1. Header Area
        header = self.frame(self, bg=THEME["bg"], height=100)
        header.pack(fill="x", padx=40, pady=(30, 10))
        
        self.label(header, "YT-DLP", font=("Segoe UI", 28, "bold"), fg=THEME["accent"]).pack(anchor="w")
        self.label(header, "PREMIUM DOWNLOADER", font=("Segoe UI", 10, "bold"), fg=THEME["text_sec"]).pack(anchor="w")
        
        # Tools (Top Right)
        tools = self.frame(header, bg=THEME["bg"])
        tools.place(relx=1, rely=0, anchor="ne")
        self.btn(tools, "📦 INSTALL", self.do_install, bg=THEME["bg"], fg=THEME["text_sec"]).pack(side="left", padx=10)
        self.btn(tools, "🔄 RESET", self.reset_ui, bg=THEME["bg"], fg=THEME["text_sec"]).pack(side="left")

        # 2. Input Section
        input_fr = self.frame(self, bg=THEME["bg"])
        input_fr.pack(fill="x", padx=40, pady=20)
        
        # URL Input
        url_box = self.frame(input_fr, bg=THEME["input_bg"], padx=15, pady=5)
        url_box.pack(fill="x", pady=5)
        
        info_icon = self.label(url_box, "ℹ", font=("Segoe UI", 14), fg=THEME["accent"], bg=THEME["input_bg"], cursor="hand2")
        info_icon.pack(side="left", padx=(0, 10))
        ToolTip(info_icon, "Supports: YouTube, Instagram, TikTok, Twitter, Twitch & more")
        
        self.entry(url_box, self.url_var, bg=THEME["input_bg"]).pack(side="left", fill="x", expand=True, ipady=8)
        self.url_var.trace("w", lambda *a: self.fetch_btn.config(state="normal" if self.url_var.get() else "disabled"))
        
        self.fetch_btn = self.btn(url_box, "SEARCH", self.fetch, bg=THEME["accent"], fg="#000", padx=20, pady=5)
        self.fetch_btn.pack(side="right") # Pack inside the box for integrated look
        
        # Path
        path_box = self.frame(input_fr, bg=THEME["bg"])
        path_box.pack(fill="x", pady=(10, 0))
        self.label(path_box, "SAVING TO:", font=("Segoe UI", 8, "bold"), fg=THEME["text_sec"]).pack(side="left")
        self.label(path_box, "...", textvariable=self.path_var, font=("Segoe UI", 8), fg=THEME["text_main"]).pack(side="left", padx=5)
        self.btn(path_box, "CHANGE", self.browse_path, bg=THEME["bg"], fg=THEME["accent"], font=("Segoe UI", 8, "bold")).pack(side="left", padx=10)

        # 3. Content Card (Glass-like)
        self.card = self.frame(self, bg=THEME["card_bg"])
        
        # Two columns: Thumb | Info
        top_row = self.frame(self.card, bg=THEME["card_bg"])
        top_row.pack(fill="x", padx=20, pady=20)
        
        self.thumb = tk.Label(top_row, bg="#000")
        self.thumb.pack(side="left")
        
        info = self.frame(top_row, bg=THEME["card_bg"])
        info.pack(side="left", fill="both", expand=True, padx=20)
        
        self.title_lbl = self.label(info, "", font=("Segoe UI", 14, "bold"), bg=THEME["card_bg"], wraplength=450, justify="left")
        self.title_lbl.pack(anchor="w")
        self.meta_lbl = self.label(info, "", font=("Segoe UI", 9), fg=THEME["text_sec"], bg=THEME["card_bg"])
        self.meta_lbl.pack(anchor="w", pady=(5, 0))
        
        # Options Grid
        opts = self.frame(self.card, bg=THEME["card_bg"])
        opts.pack(fill="x", padx=20, pady=(0, 20))
        
        # Col 1: Type
        c1 = self.frame(opts, bg=THEME["card_bg"])
        c1.pack(side="left", fill="y", padx=(0, 20))
        self.label(c1, "TYPE", font=("Segoe UI", 8, "bold"), fg=THEME["accent"], bg=THEME["card_bg"]).pack(anchor="w")
        for t, v in [("Video + Audio", "both"), ("Video Only", "video"), ("Audio Only", "audio")]:
            tk.Radiobutton(c1, text=t, variable=self.type_var, value=v, bg=THEME["card_bg"], fg=THEME["text_main"],
                           selectcolor=THEME["card_bg"], activebackground=THEME["card_bg"], command=self.update_opts, cursor="hand2").pack(anchor="w")

        # Col 2: Format
        c2 = self.frame(opts, bg=THEME["card_bg"])
        c2.pack(side="left", fill="y", padx=20)
        self.label(c2, "FORMAT", font=("Segoe UI", 8, "bold"), fg=THEME["accent"], bg=THEME["card_bg"]).pack(anchor="w")
        self.radios = {}
        for f in ["mp4", "webm", "mp3", "m4a"]:
            r = tk.Radiobutton(c2, text=f.upper(), variable=self.fmt_var, value=f, bg=THEME["card_bg"], fg=THEME["text_main"],
                           selectcolor=THEME["card_bg"], activebackground=THEME["card_bg"], cursor="hand2")
            r.pack(anchor="w")
            self.radios[f] = r

        # Col 3: Quality & Extras
        c3 = self.frame(opts, bg=THEME["card_bg"])
        c3.pack(side="left", fill="y", padx=20)
        self.label(c3, "QUALITY", font=("Segoe UI", 8, "bold"), fg=THEME["accent"], bg=THEME["card_bg"]).pack(anchor="w")
        self.qual_box = ttk.Combobox(c3, textvariable=self.qual_var, state="readonly", width=12)
        self.qual_box.pack(anchor="w", pady=(2, 10))
        
        cb_turbo = tk.Checkbutton(c3, text="🚀 Turbo Mode", variable=self.turbo_var, bg=THEME["card_bg"], fg=THEME["success"],
                       selectcolor=THEME["card_bg"], activebackground=THEME["card_bg"], cursor="hand2")
        cb_turbo.pack(anchor="w")
        ToolTip(cb_turbo, "ENABLES PARALLEL DOWNLOADING.\nStarts 8 download connections simultaneously.\nGreatly improves speed for large files.")

        cb_compat = tk.Checkbutton(c3, text="Premiere Compat.", variable=self.compat_var, bg=THEME["card_bg"], fg=THEME["warning"],
                       selectcolor=THEME["card_bg"], activebackground=THEME["card_bg"], cursor="hand2")
        cb_compat.pack(anchor="w")
        ToolTip(cb_compat, "EDITOR MODE (H.264 + AAC).\nForces video format to be compatible with editors like\nAdobe Premiere, DaVinci Resolve, and Sony Vegas.\nMay be slower to process but ensures importability.")

        self.btn(c3, "🖼️ Save Thumb", self.save_thumb, bg=THEME["input_bg"], fg=THEME["text_main"], font=("Segoe UI", 8)).pack(anchor="w", pady=(10, 0), ipadx=5)

        # Action Button (Big Gold Button)
        self.dl_btn = self.btn(self.card, "START DOWNLOAD", self.start_download, bg=THEME["accent"], fg="#000", font=("Segoe UI", 11, "bold"), height=2)
        self.dl_btn.pack(fill="x", padx=20, pady=20)
        
        # 4. Progress Section (Advanced)
        self.prog_fr = self.frame(self.card, bg=THEME["card_bg"])
        
        # Stats Grid
        stats = self.frame(self.prog_fr, bg=THEME["card_bg"])
        stats.pack(fill="x", padx=5)
        
        self.stat_size = self.make_stat(stats, "TOTAL SIZE")
        self.stat_done = self.make_stat(stats, "DOWNLOADED")
        self.stat_speed = self.make_stat(stats, "SPEED")
        self.stat_eta = self.make_stat(stats, "ETA")
        
        # Styling the bar (Gold)
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Gold.Horizontal.TProgressbar", troughcolor=THEME["input_bg"], background=THEME["accent"], borderwidth=0, lightcolor=THEME["accent"], darkcolor=THEME["accent"])
        
        self.prog_bar = ttk.Progressbar(self.prog_fr, style="Gold.Horizontal.TProgressbar", mode="determinate")
        self.prog_bar.pack(fill="x", pady=(15, 5))
        
        self.status = self.label(self, "READY", font=("Segoe UI", 9, "bold"), fg=THEME["success"])
        self.status.pack(side="bottom", pady=10)

    def make_stat(self, parent, title):
        fr = self.frame(parent, bg=THEME["card_bg"])
        fr.pack(side="left", expand=True, fill="x")
        self.label(fr, title, font=("Segoe UI", 7, "bold"), fg=THEME["text_sec"], bg=THEME["card_bg"]).pack()
        lbl = self.label(fr, "-", font=("Segoe UI", 10, "bold"), fg="#FFF", bg=THEME["card_bg"])
        lbl.pack()
        return lbl

    # --- Logic ---
    def browse_path(self):
        d = filedialog.askdirectory(initialdir=self.path_var.get())
        if d: 
            self.path_var.set(d)
            self.save_config()

    def update_opts(self):
        t = self.type_var.get()
        is_aud = t == "audio"
        for f in ["mp4", "webm"]: self.radios[f].config(state="disabled" if is_aud else "normal")
        for f in ["mp3", "m4a"]: self.radios[f].config(state="normal" if is_aud else "disabled")
        
        cur = self.fmt_var.get()
        if is_aud and cur in ["mp4", "webm"]: self.fmt_var.set("mp3")
        if not is_aud and cur in ["mp3", "m4a"]: self.fmt_var.set("mp4")

    def reset_ui(self):
        self.url_var.set("")
        self.card.pack_forget()
        self.status.config(text="READY", fg=THEME["success"])
        self.manager.cancel()

    def fetch(self):
        url = self.url_var.get().strip()
        if not url: return
        self.fetch_btn.config(state="disabled", text="FETCHING...")
        self.status.config(text="LOADING METADATA...", fg=THEME["warning"])
        
        def run():
            data, err = self.manager.fetch_info(url)
            self.after(0, lambda: self._on_fetch(data, err))
        threading.Thread(target=run, daemon=True).start()

    def _on_fetch(self, data, err):
        self.fetch_btn.config(state="normal", text="SEARCH")
        if not data:
            # Clean up error message
            msg = "Could not fetch video info."
            if err:
                # Extract last line or useful part of stderr
                clean_err = err.strip().split('\n')[-1]
                msg += f"\n\nDetails: {clean_err}"
            
            messagebox.showerror("Error", msg)
            self.status.config(text="ERROR", fg=THEME["error"])
            return

        self.video_data = data
        
        # Fallback for generic URLs
        title = data.get('title')
        if not title:
             title = data.get('url', 'Unknown Video').split('/')[-1].split('?')[0]
        
        self.title_lbl.config(text=title)
        
        # Fix: Cast duration to int to avoid "Unknown format code 'd' for object of type 'float'"
        d = data.get('duration')
        if d: d = int(d)
        dur_str = f"{d//60}:{d%60:02d}" if d else "N/A"
        self.meta_lbl.config(text=f"By {data.get('uploader','?')}  •  {dur_str}  •  {data.get('view_count','-')} views")
        
        # Load Thumb (Robust & High Res)
        thumb_url = data.get('thumbnail')
        
        # Try to find better resolution from 'thumbnails' list
        thumbs = data.get('thumbnails')
        if thumbs and isinstance(thumbs, list):
            try:
                # Sort by width (desc) or preference
                best_t = max(thumbs, key=lambda t: t.get('width', 0) if t.get('width') else 0)
                if best_t.get('url'):
                    thumb_url = best_t.get('url')
            except: pass
            
        if thumb_url:
            try:
                raw = requests.get(thumb_url, timeout=5).content
                # Aspect Ratio Preserving Resize
                img = Image.open(BytesIO(raw))
                target_w, target_h = 240, 135
                
                # Create black background
                bg = Image.new('RGB', (target_w, target_h), (0, 0, 0))
                
                # Calc ratio to fit within box
                ratio = min(target_w/img.width, target_h/img.height)
                new_w = int(img.width * ratio)
                new_h = int(img.height * ratio)
                
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
                # Center
                x = (target_w - new_w) // 2
                y = (target_h - new_h) // 2
                bg.paste(img, (x, y))
                
                photo = ImageTk.PhotoImage(bg)
                self.thumb.config(image=photo, width=240, height=135)
                self.thumb.image = photo
                self.thumb.image = photo
            except: 
                self.thumb.config(image='', text="No Image", fg="white")
        else:
             self.thumb.config(image='', text="No Thumbnail", fg="white")

        # Qualities
        avail = []
        std = ['8K', '4K', '2K', '1080p', '720p', '480p', '360p']
        for s in std:
             limit = int(s.replace('p','').replace('K','000').replace('8000','4320').replace('4000','2160').replace('2000','1440'))
             if any(f.get('height') == limit for f in data.get('formats', []) if f.get('height')):
                 avail.append(s)
        
        self.qual_box['values'] = avail if avail else ["Best Available"]
        self.qual_box.current(0)
        
        self.card.pack(fill="x", padx=40, pady=20)
        self.status.config(text="READY TO DOWNLOAD", fg=THEME["success"])
        self.update_opts()

    def start_download(self):
        if not self.video_data: return
        self.dl_btn.config(state="normal", text="CANCEL", bg=THEME["error"], command=self.cancel_download)
        self.prog_fr.pack(fill="x", padx=20, pady=(0, 20)) # Show progress
        
        opts = (self.fmt_var.get(), self.qual_var.get(), self.type_var.get(), self.compat_var.get(), self.turbo_var.get())
        
        def run():
            s, m = self.manager.download(self.url_var.get(), self.path_var.get(), opts, self._update_progress)
            self.after(0, lambda: self._on_end(s, m))
        threading.Thread(target=run, daemon=True).start()

    def cancel_download(self):
        if messagebox.askyesno("Cancel", "Stop download and delete partial files?"):
            self.manager.cancel()
            self.status.config(text="CANCELLING...", fg=THEME["error"])

    def _update_progress(self, line):
        try:
            # 1. Percent
            if "%" in line:
                pct = float(re.search(r'(\d+\.?\d*)%', line).group(1))
                self.after(0, lambda: self.prog_bar.config(value=pct))
            
            # 2. Speed
            spd = re.search(r'(\d+\.?\d*[KMG]iB/s)', line)
            if spd: self.after(0, lambda: self.stat_speed.config(text=spd.group(1)))
            
            # 3. Size / Downloaded
            # yt-dlp output: [download]  15.2% of ~  20.00MiB at  2.50MiB/s ETA 00:05
            # or: [download] 100% of   10.00MiB in 00:01
            sz = re.search(r'of\s+~?\s*(\d+\.?\d*[KMG]iB)', line)
            if sz: self.after(0, lambda: self.stat_size.config(text=sz.group(1)))
            
            dl = re.search(r'^\s*\[download\]\s+(\d+\.?\d*%)', line) # Not exact bytes usually shown easily, stick to percent or try to calc
            # Actually yt-dlp doesn't always show "X MiB / Y MiB" clearly in one regex, but 'of X MiB' is consistent.
            
            # 4. ETA
            eta = re.search(r'ETA\s+(\d+:\d+)', line)
            if eta: self.after(0, lambda: self.stat_eta.config(text=eta.group(1)))
            
            if "Merging" in line: self.after(0, lambda: self.status.config(text="MERGING...", fg=THEME["warning"]))

        except: pass

    def _on_end(self, success, msg):
        self.dl_btn.config(state="normal", text="START DOWNLOAD", bg=THEME["accent"], command=self.start_download)
        self.prog_fr.pack_forget()
        self.prog_bar['value'] = 0
        for s in [self.stat_size, self.stat_done, self.stat_speed, self.stat_eta]: s.config(text="-")
        
        if success:
            messagebox.showinfo("Success", f"Download Completed!\nSaved to: {self.path_var.get()}")
            self.status.config(text="COMPLETED", fg=THEME["success"])
        else:
            if msg != "Cancelled": messagebox.showerror("Error", msg)
            self.status.config(text="FAILED", fg=THEME["error"])

    def do_install(self):
        self.status.config(text="INSTALLING...", fg=THEME["warning"])
        def run():
            s, m = self.manager.install_update()
            self.after(0, lambda: messagebox.showinfo("Install Result", m))
            self.after(0, lambda: self.status.config(text="READY", fg=THEME["success"]))
        threading.Thread(target=run, daemon=True).start()

    def save_thumb(self):
        if not self.video_data: return
        url = self.video_data.get('thumbnail')
        if not url: return

        try:
            # Clean title
            title = "".join(x for x in self.video_data.get('title','thumbnail') if x.isalnum() or x in " -_")
            path = os.path.join(self.path_var.get(), f"{title}_thumb.jpg")
            
            raw = requests.get(url, timeout=10).content
            with open(path, 'wb') as f:
                f.write(raw)
            messagebox.showinfo("Saved", f"Thumbnail saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save thumbnail:\n{e}")

if __name__ == "__main__":
    app = ModernUI()
    app.mainloop()