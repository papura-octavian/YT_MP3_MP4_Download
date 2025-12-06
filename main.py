import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
import threading
import yt_dlp
import sys
import time

SELECTED_DIR: Path | None = None
LINKS_FILE = None
MP3_DEFAULT = "192"

# ---------- Mini Console (UI logger) ----------

def append_log_line(text: str):
    app.after(0, lambda: _append(text))

def _append(text: str):
    console_text.configure(state="normal")
    console_text.insert("end", text.rstrip() + "\n")
    console_text.see("end")
    console_text.configure(state="disabled")


class YTDLogger:
    def __init__(self, write_fn):
        self._write = write_fn

    def debug(self, msg):
        if verbose_var.get():
            self._write(str(msg))

    def info(self, msg):
        self._write(str(msg))

    def warning(self, msg):
        self._write("WARNING: " + str(msg))

    def error(self, msg):
        self._write("ERROR: " + str(msg))


# ---------- FFmpeg location helper ----------

def detect_ffmpeg_location() -> str | None:
    """
    Caută ffmpeg atât în structura proiectului, cât și în folderul PyInstaller.
    Structură suportată:

    Cantari-de-Slava/
    ├── main.py
    ├── ffmpeg/
    │   ├── windows/
    │   │   └── ffmpeg.exe
    │   └── linux/
    │       └── ffmpeg
    └── ...

    Dacă nu găsește nimic aici, întoarce None și yt-dlp va folosi ffmpeg din PATH.
    """
    # Dacă e rulat ca exe PyInstaller, sys._MEIPASS indică folderul temporar.
    base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))

    candidates = [
        base_dir,
        base_dir / "bin",
        base_dir / "ffmpeg",
        base_dir / "ffmpeg" / "windows",
        base_dir / "ffmpeg" / "linux",
    ]

    for c in candidates:
        exe = c / "ffmpeg.exe"   # Windows
        nix = c / "ffmpeg"       # Linux / macOS

        if exe.exists():
            return str(exe)
        if nix.exists():
            return str(nix)

    return None


FFMPEG_PATH = detect_ffmpeg_location()

# --------- Downloader / Converter ----------

def download_media(
    url: str,
    outdir: Path,
    kind: str,
    bitrate_kbps: str,
    progress_callback=None,
    finish_callback=None,
):
    """
    Descarcă media ca MP3 sau MP4.
    kind: 'mp3' sau 'mp4'
    bitrate_kbps: folosit doar pentru mp3 ('128','192','256','320')
    """

    def hook(d):
        if d["status"] == "downloading":
            percent = d.get("_percent_str") or ""
            speed = d.get("_speed_str") or ""
            eta = d.get("eta", 0)
            title = d.get("info_dict", {}).get("title", "")
            if progress_callback:
                progress_callback(percent, speed, eta, title)
        elif d["status"] == "finished":
            if finish_callback:
                finish_callback("✅ Salvat!")
            append_log_line("Finished processing file.")

    outdir.mkdir(parents=True, exist_ok=True)

    client_choice = client_var.get().strip().lower()  # web/android/ios/tv
    extractor_args = (
        {"youtube": {"player_client": [client_choice]}} if client_choice else {}
    )

    common = {
        'outtmpl': str(outdir / '%(playlist_title)s/%(title)s.%(ext)s'),
        "noplaylist": False,
        "download_archive": str(outdir / ".downloaded.txt"),
        "nooverwrites": True,
        "ignoreerrors": True,
        "restrictfilenames": True,
        "windowsfilenames": True,
        "addmetadata": True,
        "progress_hooks": [hook],
        "logger": YTDLogger(append_log_line),
        "quiet": False,
        "verbose": verbose_var.get(),
        "retries": 10,
        "fragment_retries": 10,
        "concurrent_fragment_downloads": 1,  # mai puțin 403 pe HLS
        "http_chunk_size": 10 * 1024 * 1024,  # 10MB chunks ajută la 403 pe unele CDN-uri
        "extractor_args": extractor_args,
        "http_headers": {
            "User-Agent": ua_entry.get().strip()
            or (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
    }

    # setează ffmpeg doar dacă l-am găsit în structura proiectului / PyInstaller
    if FFMPEG_PATH:
        common["ffmpeg_location"] = FFMPEG_PATH

    if use_cookies_var.get():
        # Folosește cookies din browserul ales (Chrome/Edge/Firefox/Brave)
        # yt-dlp va localiza singur profilul implicit.
        browser_name = browser_var.get().strip().lower()  # 'chrome', 'edge', 'firefox', 'brave'
        common["cookiesfrombrowser"] = (browser_name,)

    if kind.lower() == "mp3":
        ydl_opts = {
            **common,
            "format": "bestaudio/best",
            "writethumbnail": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": bitrate_kbps,
                },
                {"key": "FFmpegMetadata"},
                {"key": "EmbedThumbnail"},
            ],
            "postprocessor_args": ["-id3v2_version", "3", "-write_id3v1", "1"],
        }
    else:  # mp4
        ydl_opts = {
            **common,
            "format": (
                "bestvideo[ext=mp4]+bestaudio[ext=m4a]/"
                "bestvideo+bestaudio/best[ext=mp4]/best"
            ),
            "merge_output_format": "mp4",
            "postprocessors": [
                {"key": "FFmpegVideoConvertor", "preferedformat": "mp4"},
                {"key": "FFmpegMetadata"},
            ],
        }

    try:
        append_log_line(f"Starting: {url}")
        append_log_line(
            f"Client: {client_choice.upper()} | Cookies: {use_cookies_var.get()} | Browser: {browser_var.get()}"
        )
        if FFMPEG_PATH:
            append_log_line(f"Using ffmpeg at: {FFMPEG_PATH}")
        else:
            append_log_line("Using ffmpeg from system PATH")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as e:
        msg = f"ERROR: {e}"
        append_log_line(msg)
        if finish_callback:
            finish_callback("❌ Eroare la descărcare.")
    except Exception as e:
        msg = f"UNEXPECTED ERROR: {e}"
        append_log_line(msg)
        if finish_callback:
            finish_callback("❌ Eroare neașteptată.")


# --------- Handlere UI ----------

def start_download_single():
    if SELECTED_DIR is None:
        messagebox.showerror("Error", "Alege o destinație pentru descărcare!")
        return
    url = url_entry.get().strip()
    if not url:
        messagebox.showerror("Error", "Te rog introdu un link YouTube!")
        return

    kind = format_var.get().lower()
    bitrate = bitrate_var.get()

    status_label.configure(text=f"⏳ Se descarcă {kind.upper()}...", text_color="orange")
    progress_bar.set(0)
    append_log_line("=" * 72)
    append_log_line(f"Job started at {time.strftime('%H:%M:%S')} ({kind.upper()})")

    threading.Thread(
        target=download_media,
        args=(url, SELECTED_DIR, kind, bitrate, update_progress, download_finished),
        daemon=True,
    ).start()


def choose_links_file():
    global LINKS_FILE
    file_path = filedialog.askopenfilename(
        title="Alege fișierul cu linkuri (un link pe linie)",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
    )
    if file_path:
        LINKS_FILE = Path(file_path)
        file_label.configure(
            text=f"Fișier selectat: {LINKS_FILE.name}", text_color="white"
        )


def choose_dest_dir():
    global SELECTED_DIR
    dir_path = filedialog.askdirectory(title="Alege dosarul destinație")
    if dir_path:
        SELECTED_DIR = Path(dir_path)
        dest_label.configure(
            text=f"Destinație: {SELECTED_DIR}", text_color="white"
        )


def start_download_list():
    if SELECTED_DIR is None:
        messagebox.showerror("Error", "Alege o destinație pentru descărcare!")
        return
    if not LINKS_FILE:
        messagebox.showerror("Error", "Alege mai întâi fișierul cu linkuri (TXT)!")
        return

    try:
        with open(LINKS_FILE, "r", encoding="utf-8") as f:
            urls = [
                line.strip()
                for line in f
                if line.strip() and not line.strip().startswith("#")
            ]
    except Exception as e:
        messagebox.showerror("Error", f"Nu pot citi fișierul: {e}")
        return

    if not urls:
        messagebox.showerror("Error", "Fișierul nu conține linkuri valide.")
        return

    kind = format_var.get().lower()
    bitrate = bitrate_var.get()
    status_label.configure(
        text=(
            f"⏳ Încep procesarea a {len(urls)} elemente ca "
            f"{kind.upper()} în {SELECTED_DIR}"
        ),
        text_color="orange",
    )
    progress_bar.set(0)
    append_log_line("=" * 72)
    append_log_line(f"Batch started at {time.strftime('%H:%M:%S')} ({kind.upper()})")
    append_log_line(f"Total items: {len(urls)}")

    threading.Thread(
        target=download_list_worker, args=(urls, kind, bitrate), daemon=True
    ).start()


def download_list_worker(urls, kind, bitrate):
    total = len(urls)
    for idx, url in enumerate(urls, start=1):
        batch_label.configure(text=f"Elementul {idx}/{total}")
        append_log_line("-" * 48)
        append_log_line(f"[{idx}/{total}] {url}")
        try:
            download_media(
                url,
                SELECTED_DIR,
                kind,
                bitrate,
                lambda percent, speed, eta, title, i=idx, n=total: update_progress_batch(
                    percent, speed, eta, title, i, n
                ),
                lambda msg, i=idx, n=total: download_finished_batch(msg, i, n),
            )
        except Exception as e:
            # deja logat în download_media; aici doar UI
            status_label.configure(
                text=f"⚠️ Eroare la linkul {idx}/{total}: {e}", text_color="red"
            )

    status_label.configure(text="✅ Lista este gata!", text_color="green")
    progress_bar.set(1.0)
    batch_label.configure(text="")
    append_log_line("=" * 72)
    append_log_line("Batch complete.")


def update_progress(percent, speed, eta, title=""):
    try:
        p = float(percent.replace("%", "").replace(",", "."))
        progress_bar.set(p / 100)
        info = f"🎵 {title} — {percent} | {speed} | ETA: {eta}s"
        status_label.configure(text=info)
        if verbose_var.get():
            append_log_line(info)
    except Exception:
        pass


def update_progress_batch(percent, speed, eta, title, idx, total):
    try:
        p = float(percent.replace("%", "").replace(",", "."))
        progress_bar.set(p / 100)
        info = f"[{idx}/{total}] 🎵 {title} — {percent} | {speed} | ETA: {eta}s"
        status_label.configure(text=info, text_color="orange")
        if verbose_var.get():
            append_log_line(info)
    except Exception:
        pass


def download_finished(message, *_):
    status_label.configure(text=message, text_color="green")
    progress_bar.set(1.0)


def download_finished_batch(message, idx, total):
    status_label.configure(text=f"[{idx}/{total}] {message}", text_color="green")


def on_format_change(_choice):
    choice = format_var.get().lower()
    if choice == "mp3":
        bitrate_menu.configure(state="normal")
        bitrate_hint.configure(text_color="gray")
    else:
        bitrate_menu.configure(state="disabled")
        bitrate_hint.configure(text_color="gray35")


# ---------------- UI ----------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("🎧 YouTube → MP3/MP4 Downloader")
app.geometry("980x780")

title_label = ctk.CTkLabel(
    app, text="🎧 YouTube → MP3 / MP4", font=("Segoe UI", 24, "bold")
)
title_label.pack(pady=16)

# Destinație
dest_frame = ctk.CTkFrame(app)
dest_frame.pack(pady=6, padx=8, fill="x")
ctk.CTkButton(
    dest_frame,
    text="📁 Alege destinația…",
    width=180,
    height=36,
    command=choose_dest_dir,
).grid(row=0, column=0, padx=8, pady=8)
dest_label = ctk.CTkLabel(
    dest_frame,
    text="Destinație: (nealeasă)",
    font=("Segoe UI", 13),
    text_color="gray",
)
dest_label.grid(row=0, column=1, padx=8, pady=8, sticky="w")

# Link
url_entry = ctk.CTkEntry(
    app,
    width=900,
    height=40,
    placeholder_text="Lipește linkul YouTube aici (video sau playlist)...",
)
url_entry.pack(pady=8)

# Format + Bitrate + Client + Cookies + UA
format_frame = ctk.CTkFrame(app)
format_frame.pack(pady=8, padx=8, fill="x")

ctk.CTkLabel(format_frame, text="Format:", font=("Segoe UI", 13)).grid(
    row=0, column=0, padx=6, pady=6
)
format_var = ctk.StringVar(value="MP3")
format_menu = ctk.CTkOptionMenu(
    format_frame,
    values=["MP3", "MP4"],
    variable=format_var,
    width=100,
    command=on_format_change,
)
format_menu.grid(row=0, column=1, padx=6, pady=6)

ctk.CTkLabel(format_frame, text="Bitrate MP3:", font=("Segoe UI", 13)).grid(
    row=0, column=2, padx=12, pady=6
)
bitrate_var = ctk.StringVar(value=MP3_DEFAULT)
bitrate_menu = ctk.CTkOptionMenu(
    format_frame, values=["128", "192", "256", "320"], variable=bitrate_var, width=100
)
bitrate_menu.grid(row=0, column=3, padx=6, pady=6)
bitrate_hint = ctk.CTkLabel(
    format_frame,
    text="(192 kbps recomandat pentru playerele auto)",
    text_color="gray",
)
bitrate_hint.grid(row=0, column=4, padx=6)

ctk.CTkLabel(format_frame, text="Client:", font=("Segoe UI", 13)).grid(
    row=1, column=0, padx=6, pady=6, sticky="e"
)
client_var = ctk.StringVar(value="android")  # 'web', 'android', 'ios', 'tv'
ctk.CTkOptionMenu(
    format_frame,
    values=["android", "web", "ios", "tv"],
    variable=client_var,
    width=120,
).grid(row=1, column=1, padx=6, pady=6, sticky="w")

use_cookies_var = ctk.BooleanVar(value=False)
ctk.CTkCheckBox(
    format_frame, text="Folosește cookies din browser", variable=use_cookies_var
).grid(row=1, column=2, padx=12, pady=6, sticky="w")

browser_var = ctk.StringVar(value="chrome")
ctk.CTkOptionMenu(
    format_frame,
    values=["chrome", "edge", "firefox", "brave"],
    variable=browser_var,
    width=120,
).grid(row=1, column=3, padx=6, pady=6, sticky="w")

verbose_var = ctk.BooleanVar(value=True)
ctk.CTkCheckBox(
    format_frame, text="Verbose", variable=verbose_var
).grid(row=1, column=4, padx=12, pady=6, sticky="w")

ctk.CTkLabel(
    format_frame, text="User-Agent (opțional):", font=("Segoe UI", 13)
).grid(row=2, column=0, padx=6, pady=6, sticky="e")
ua_entry = ctk.CTkEntry(
    format_frame, width=600, placeholder_text="Lasă gol pentru UA implicit"
)
ua_entry.grid(row=2, column=1, columnspan=4, padx=6, pady=6, sticky="w")

# Butoane acțiune
btn_row = ctk.CTkFrame(app)
btn_row.pack(pady=8)
ctk.CTkButton(
    btn_row,
    text="⬇️ Descarcă linkul în destinația aleasă",
    width=300,
    height=40,
    command=start_download_single,
).grid(row=0, column=0, padx=8, pady=5)
ctk.CTkButton(
    btn_row,
    text="📄 Alege fișier linkuri (TXT)",
    width=250,
    height=40,
    command=choose_links_file,
).grid(row=0, column=1, padx=8, pady=5)
ctk.CTkButton(
    app,
    text="🗂️ Procesează toată lista (MP3/MP4) în destinația aleasă",
    width=380,
    height=40,
    command=start_download_list,
).pack(pady=8)

# Etichete
file_label = ctk.CTkLabel(
    app, text="Niciun fișier selectat", font=("Segoe UI", 13), text_color="gray"
)
file_label.pack(pady=4)

progress_bar = ctk.CTkProgressBar(app, width=900)
progress_bar.pack(pady=12)
progress_bar.set(0)

batch_label = ctk.CTkLabel(app, text="", font=("Segoe UI", 14))
batch_label.pack(pady=2)

status_label = ctk.CTkLabel(app, text="", font=("Segoe UI", 14))
status_label.pack(pady=6)

# Mini Console
console_frame = ctk.CTkFrame(app)
console_frame.pack(padx=8, pady=10, fill="both", expand=True)
ctk.CTkLabel(
    console_frame, text="Console", font=("Consolas", 14, "bold")
).pack(anchor="w", padx=8, pady=(8, 0))
console_text = ctk.CTkTextbox(
    console_frame, height=320, width=920, font=("Consolas", 12)
)
console_text.pack(padx=8, pady=8, fill="both", expand=True)
console_text.configure(state="disabled")

# initialize UI state
on_format_change(format_var.get())

app.mainloop()
