#!/usr/bin/env python3
import subprocess, sys, os, re, threading, time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

if sys.platform == "win32":
    import ctypes, winsound
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

FFMPEG = r"C:\ffmpeg-8.1.1-essentials_build\bin\ffmpeg.exe"
YT_DLP = [sys.executable, "-m", "yt_dlp"]
CFLAG  = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

BG, SURFACE, BORDER = "#f8f9fa", "#ffffff", "#dee2e6"
BLUE, BLUE_H        = "#0d6efd", "#0b5ed7"
TEXT, MUTED         = "#212529", "#6c757d"
GREEN, RED, ORANGE  = "#198754", "#dc3545", "#fd7e14"
FONT    = ("Segoe UI", 10)
FONT_SM = ("Segoe UI", 9)
FONT_LG = ("Segoe UI", 11, "bold")

def sanitize(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip()

def play_done_sound():
    if sys.platform == "win32":
        for freq, dur in [(600, 120), (800, 120), (1050, 200)]:
            winsound.Beep(freq, dur)

def parse_progress(line):
    m = re.search(r'(\d+\.?\d*)%', line)
    return float(m.group(1)) if m else None

def parse_speed(line):
    speed = re.search(r'at\s+([\d.]+\s*\w+/s)', line)
    eta   = re.search(r'ETA\s+([\d:]+)', line)
    parts = []
    if speed: parts.append(speed.group(1))
    if eta:   parts.append(f"ETA {eta.group(1)}")
    return "  ".join(parts)

def build_episode_name(show, season, episode):
    return f"{sanitize(show)}_S{int(season):02d}E{int(episode):02d}"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Streamrip")
        self.geometry("580x400")
        self.resizable(False, False)
        self.configure(bg=BG)
        self._running = False
        self._build_ui()
        self.eval('tk::PlaceWindow . center')

    def _build_ui(self):

        def card(pady_top=8):
            f = tk.Frame(self, bg=SURFACE, padx=14, pady=8,
                         highlightthickness=1, highlightbackground=BORDER)
            f.pack(fill="x", padx=16, pady=(pady_top, 0))
            return f

        # ── URL ──
        url_card = card(pady_top=14)
        tk.Label(url_card, text="URL", font=FONT_SM, bg=SURFACE,
                 fg=MUTED, width=6, anchor="w").pack(side="left")
        self.url_entry = tk.Entry(url_card, font=FONT, bg=BG, fg=TEXT,
                                  insertbackground=TEXT, relief="flat", bd=0,
                                  highlightthickness=1, highlightbackground=BORDER)
        self.url_entry.pack(side="left", fill="x", expand=True, ipady=4, padx=(4, 0))

        # ── Name + Season + Episode (one line) ──
        meta_card = card()
        tk.Label(meta_card, text="Name", font=FONT_SM, bg=SURFACE,
                 fg=MUTED, width=6, anchor="w").pack(side="left")
        self.show_entry = tk.Entry(meta_card, font=FONT, bg=BG, fg=TEXT,
                                   insertbackground=TEXT, relief="flat", bd=0,
                                   highlightthickness=1, highlightbackground=BORDER,
                                   width=20)
        self.show_entry.pack(side="left", ipady=4, padx=(4, 12))

        tk.Label(meta_card, text="S", font=FONT_SM, bg=SURFACE, fg=MUTED).pack(side="left")
        self.season_spin = tk.Spinbox(meta_card, from_=1, to=99, width=3, font=FONT,
                                      bg=BG, fg=TEXT, relief="flat", bd=0,
                                      highlightthickness=1, highlightbackground=BORDER,
                                      buttonbackground=BORDER, justify="center")
        self.season_spin.pack(side="left", ipady=4, padx=(2, 10))

        tk.Label(meta_card, text="E", font=FONT_SM, bg=SURFACE, fg=MUTED).pack(side="left")
        self.ep_spin = tk.Spinbox(meta_card, from_=1, to=999, width=3, font=FONT,
                                  bg=BG, fg=TEXT, relief="flat", bd=0,
                                  highlightthickness=1, highlightbackground=BORDER,
                                  buttonbackground=BORDER, justify="center")
        self.ep_spin.pack(side="left", ipady=4, padx=(2, 8))

        self.plus_btn = tk.Button(meta_card, text="＋", font=FONT_LG,
                                  bg=BLUE, fg="white", activebackground=BLUE_H,
                                  relief="flat", bd=0, padx=8, pady=1,
                                  cursor="hand2", command=self._increment_episode)
        self.plus_btn.pack(side="left", padx=(0, 10))
        self.plus_btn.bind("<Enter>", lambda e: self.plus_btn.config(bg=BLUE_H))
        self.plus_btn.bind("<Leave>", lambda e: self.plus_btn.config(bg=BLUE))

        self.preview_var = tk.StringVar(value="")
        tk.Label(meta_card, textvariable=self.preview_var, font=("Consolas", 8),
                 bg=SURFACE, fg=ORANGE).pack(side="left")

        for w in [self.show_entry, self.season_spin, self.ep_spin]:
            w.bind("<KeyRelease>",    lambda e: self._update_preview())
            w.bind("<ButtonRelease>", lambda e: self._update_preview())

        # ── Save to ──
        save_card = card()
        tk.Label(save_card, text="Save to", font=FONT_SM, bg=SURFACE,
                 fg=MUTED, width=6, anchor="w").pack(side="left")
        self.folder_entry = tk.Entry(save_card, font=FONT, bg=BG, fg=TEXT,
                                     insertbackground=TEXT, relief="flat", bd=0,
                                     highlightthickness=1, highlightbackground=BORDER)
        self.folder_entry.insert(0, os.path.expanduser("~\\Videos"))
        self.folder_entry.pack(side="left", fill="x", expand=True, ipady=4, padx=(4, 6))
        tk.Button(save_card, text="Browse", font=FONT_SM, bg=BORDER, fg=TEXT,
                  activebackground="#ced4da", relief="flat", bd=0, padx=8,
                  cursor="hand2", command=self._browse).pack(side="left")

        # ── Progress ──
        prog_card = card()

        # Percentage + bar on same row
        bar_row = tk.Frame(prog_card, bg=SURFACE)
        bar_row.pack(fill="x")
        self.pct_var = tk.StringVar(value="0%")
        self.pct_lbl = tk.Label(bar_row, textvariable=self.pct_var,
                                font=("Segoe UI", 10, "bold"),
                                bg=SURFACE, fg=BLUE, width=6, anchor="e")
        self.pct_lbl.pack(side="left")
        self.bar = ttk.Progressbar(bar_row, mode="determinate", maximum=100)
        self.bar.pack(side="left", fill="x", expand=True, padx=(6, 0), pady=2)

        # Speed + status on same row
        info_row = tk.Frame(prog_card, bg=SURFACE)
        info_row.pack(fill="x", pady=(2, 0))
        self.status_var = tk.StringVar(value="Ready.")
        tk.Label(info_row, textvariable=self.status_var, font=("Consolas", 8),
                 bg=SURFACE, fg=MUTED, anchor="w").pack(side="left", fill="x", expand=True)
        self.speed_var = tk.StringVar(value="")
        tk.Label(info_row, textvariable=self.speed_var, font=("Consolas", 8),
                 bg=SURFACE, fg=MUTED, anchor="e").pack(side="right")

        # ── Downloaded episodes ──
        ep_card = card()
        tk.Label(ep_card, text="Downloaded:", font=FONT_SM,
                 bg=SURFACE, fg=MUTED).pack(side="left")
        self.ep_list_var = tk.StringVar(value="Browse a folder to see episodes.")
        tk.Label(ep_card, textvariable=self.ep_list_var, font=FONT_SM,
                 bg=SURFACE, fg=TEXT, wraplength=420,
                 justify="left").pack(side="left", padx=6)

        # ── Buttons ──
        btns = tk.Frame(self, bg=BG)
        btns.pack(pady=10)
        self.dl_btn = self._btn(btns, "⬇  Download", BLUE,     BLUE_H,    self._start, big=True)
        self._btn(btns,               "Clear",        "#6c757d","#5c636a", self._clear)
        self._btn(btns,               "Exit",         RED,      "#b02a37", self.destroy)

        self._update_preview()

    def _btn(self, parent, text, bg, hover, cmd, big=False):
        b = tk.Button(parent, text=text, font=FONT_LG if big else FONT,
                      bg=bg, fg="white", activebackground=hover, activeforeground="white",
                      relief="flat", bd=0, padx=16, pady=7, cursor="hand2", command=cmd)
        b.bind("<Enter>", lambda e, b=b, c=hover: b.config(bg=c))
        b.bind("<Leave>", lambda e, b=b, c=bg:    b.config(bg=c))
        b.pack(side="left", padx=5)
        return b

    def _browse(self):
        d = filedialog.askdirectory()
        if d:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, d)
            self._refresh_episodes(d)

    def _update_preview(self):
        show = self.show_entry.get().strip()
        try:
            name = build_episode_name(show, self.season_spin.get(), self.ep_spin.get())
            self.preview_var.set(f"→ {name}.mp4" if show else "")
        except:
            self.preview_var.set("")

    def _increment_episode(self):
        try:
            val = int(self.ep_spin.get())
            self.ep_spin.delete(0, tk.END)
            self.ep_spin.insert(0, str(val + 1))
            self._update_preview()
        except:
            pass

    def _refresh_episodes(self, folder):
        try:
            files = sorted(
                [f[:-4] for f in os.listdir(folder) if f.lower().endswith(".mp4")],
                key=lambda f: os.path.getmtime(os.path.join(folder, f + ".mp4")),
                reverse=True
            )
            self.ep_list_var.set("  ·  ".join(files[:5]) if files else "No episodes found.")
        except:
            self.ep_list_var.set("Could not read folder.")

    def _clear(self):
        self.url_entry.delete(0, tk.END)
        self.bar["value"] = 0
        self.pct_var.set("0%")
        self.pct_lbl.config(fg=BLUE)
        self.speed_var.set("")
        self.status_var.set("Ready.")

    def _set_progress(self, pct, speed=""):
        self.bar["value"] = pct
        self.pct_var.set(f"{pct:.1f}%")
        if speed:
            self.speed_var.set(speed)

    def _start(self):
        if self._running: return
        url    = self.url_entry.get().strip()
        show   = self.show_entry.get().strip()
        folder = self.folder_entry.get().strip() or os.path.expanduser("~\\Videos")

        if not url or not show:
            messagebox.showwarning("Missing info", "Fill in the URL and show name.")
            return
        try:
            name = build_episode_name(show, self.season_spin.get(), self.ep_spin.get())
        except:
            messagebox.showerror("Error", "Invalid season or episode number.")
            return

        self._running = True
        self.dl_btn.config(state="disabled", text="⏳  Downloading…")
        self.bar["value"] = 0
        self.pct_var.set("0%")
        self.pct_lbl.config(fg=BLUE)
        self.speed_var.set("")
        self.status_var.set(f"→ {name}.mp4")
        threading.Thread(target=self._download, args=(url, name, folder), daemon=True).start()

    def _download(self, url, name, folder):
        os.makedirs(folder, exist_ok=True)
        final = os.path.join(folder, f"{name}.mp4")
        t0    = time.time()

        cmd = YT_DLP + [
            url, "-f", "bestvideo+bestaudio/best",
            "-o", final, "--ffmpeg-location", FFMPEG,
            "--concurrent-fragments", "16", "--retries", "10",
            "--fragment-retries", "10", "--no-part",
            "--merge-output-format", "mp4", "--newline",
        ]

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                text=True, creationflags=CFLAG)
        for line in proc.stdout:
            line = line.strip()
            pct  = parse_progress(line)
            if pct is not None:
                self.after(0, lambda p=pct, s=parse_speed(line): self._set_progress(p, s))
            if any(k in line for k in ["[download]", "[hlsnative]", "[ffmpeg]", "[Fixup"]):
                self.after(0, lambda l=line[:80]: self.status_var.set(l))
        proc.wait()

        if proc.returncode != 0:
            self.after(0, lambda: self.status_var.set("Download failed."))
            self._done(False); return

        mb  = os.path.getsize(final) / 1024 / 1024 if os.path.exists(final) else 0
        msg = f"✓ {name}.mp4  {mb:.1f}MB  {time.time()-t0:.0f}s"
        self.after(0, lambda: self.status_var.set(msg))
        self.after(0, lambda: self._set_progress(100))
        self.after(0, lambda: self.pct_lbl.config(fg=GREEN))
        self.after(0, lambda: self._refresh_episodes(folder))
        # auto-increment removed
        threading.Thread(target=play_done_sound, daemon=True).start()
        self._done(True)

    def _done(self, ok):
        self._running = False
        if not ok:
            self.after(0, lambda: self.pct_lbl.config(fg=RED))
            self.after(0, lambda: self.pct_var.set("✗"))
        self.after(0, lambda: self.dl_btn.config(state="normal", text="⬇  Download"))


if __name__ == "__main__":
    app = App()
    style = ttk.Style(app)
    try: style.theme_use("clam")
    except: pass
    style.configure("Horizontal.TProgressbar",
                    troughcolor=BORDER, background=BLUE,
                    darkcolor=BLUE, lightcolor=BLUE,
                    bordercolor=BORDER, relief="flat")
    app.mainloop()
