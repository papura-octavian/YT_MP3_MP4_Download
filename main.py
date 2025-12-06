import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
import threading
import yt_dlp
import sys
import time
import shutil

SELECTED_DIR: Path | None = None
LINKS_FILE = None
MP3_DEFAULT = "192"

# ---------- Mini Console (UI logger) ----------

def append_log_line(text: str):
    """Schedule a line to be appended to the console textbox from any thread."""
    app.after(0, lambda: _append(text))

def _append(text: str):
    """Actually append text to the console textbox (must run in UI thread)."""
    console_text.configure(state="normal")
    console_text.insert("end", text.rstrip() + "\n")
    console_text.see("end")
    console_text.configure(state="disabled")


class YTDLogger:
    """Simple logger adapter to redirect yt-dlp messages into our GUI console."""

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
    Try to locate ffmpeg and ffprobe.

    Strategy:
        1. Prefer system installation from PATH (Linux: `sudo apt install ffmpeg`).
        2. If not found, look for bundled binaries near main.py / PyInstaller bundle:
           - ffmpeg/linux/ffmpeg + ffmpeg/linux/ffprobe
           - ffmpeg/windows/ffmpeg.exe + ffmpeg/windows/ffprobe.exe

    Returns:
        Absolute path to ffmpeg binary as string, or None if nothing usable was found.
        (yt-dlp will look for ffprobe in the same folder or in PATH)
    """

    # 1) Try system PATH first (recommended, especially on Linux)
    ffmpeg_path = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
    ffprobe_path = shutil.which("ffprobe") or shutil.which("ffprobe.exe")
    if ffmpeg_path and ffprobe_path:
        return ffmpeg_path

    # 2) Try bundled binaries relative to this script / PyInstaller temp dir
    base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))

    if sys.platform.startswith("win"):
        # We are on Windows -> prefer ffmpeg/windows/
        search_dirs = [
            base_dir / "ffmpeg" / "windows",
            base_dir / "ffmpeg",
        ]
        ff_name = "ffmpeg.exe"
        fp_name = "ffprobe.exe"
    else:
        # We are on Linux/macOS -> prefer ffmpeg/linux/
        search_dirs = [
            base_dir / "ffmpeg" / "linux",
            base_dir / "ffmpeg",
        ]
        ff_name = "ffmpeg"
        fp_name = "ffprobe"

    for d in search_dirs:
        ff = d / ff_name
        fp = d / fp_name
        if ff.is_file() and fp.is_file():
            return str(ff)

    return None


FFMPEG_PATH = detect_ffmpeg_location()


# ---------- Helper: guess if URL is a playlist ----------

def is_probably_playlist(url: str) -> bool:
    """
    Heuristic to decide if a URL is a playlist link.

    It is NOT perfect, but good enough for:
        - https://www.youtube.com/playlist?list=...
        - https://www.youtube.com/watch?v=...&list=...
    """
    u = url.lower()
    if "list=" in u:
        return True
    if "/playlist" in u:
        return True
    return False


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
    Download media as MP3 or MP4 using yt-dlp.

    Args:
        url: Video or playlist URL.
        outdir: Base directory where files will be stored.
        kind: 'mp3' or 'mp4'.
        bitrate_kbps: Used only for MP3 (e.g. '128', '192', '256', '320').
        progress_callback: Callable(percent, speed, eta, title).
        finish_callback: Callable(message, ...).

    Behavior:
        - Single video → <outdir>/<title>.<ext>
        - Playlist    → <outdir>/<playlist_title>/<title>.<ext>
    """

    # For MP3 we *must* have ffmpeg (and ffprobe) available.
    if kind.lower() == "mp3" and not FFMPEG_PATH:
        append_log_line(
            "ERROR: FFmpeg is required for MP3 conversion but was not found.\n"
            "Install ffmpeg (e.g. `sudo apt install ffmpeg`) or place "
            "ffmpeg + ffprobe in ./ffmpeg/linux or ./ffmpeg/windows."
        )
        if finish_callback:
            finish_callback("❌ FFmpeg not found – cannot create MP3.")
        return

    def hook(d):
        """Progress hook used by yt-dlp."""
        if d["status"] == "downloading":
            percent = d.get("_percent_str") or ""
            speed = d.get("_speed_str") or ""
            eta = d.get("eta", 0)
            title = d.get("info_dict", {}).get("title", "")
            if progress_callback:
                progress_callback(percent, speed, eta, title)
        elif d["status"] == "finished":
            if finish_callback:
                finish_callback("✅ Saved!")
            append_log_line("Finished processing file.")

    # Ensure base output directory exists
    outdir.mkdir(parents=True, exist_ok=True)

    # Decide output template: playlist vs single video
    if is_probably_playlist(url):
        # Put videos into a subfolder with the playlist title
        outtmpl = str(outdir / "%(playlist_title)s" / "%(title)s.%(ext)s")
    else:
        # Just "<dest>/<title>.<ext>"
        outtmpl = str(outdir / "%(title)s.%(ext)s")

    client_choice = client_var.get().strip().lower()  # web/android/ios/tv
    extractor_args = (
        {"youtube": {"player_client": [client_choice]}} if client_choice else {}
    )

    common = {
        "outtmpl": outtmpl,
        "noplaylist": False,   # allow playlists when URL is one
        # download_archive was removed as requested
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
        "concurrent_fragment_downloads": 1,
        "http_chunk_size": 10 * 1024 * 1024,  # 10MB chunks
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

    # If we detected ffmpeg, tell yt-dlp where it is.
    if FFMPEG_PATH:
        common["ffmpeg_location"] = FFMPEG_PATH

    if use_cookies_var.get():
        # Use cookies from the chosen browser (Chrome/Edge/Firefox/Brave)
        browser_name = browser_var.get().strip().lower()
        common["cookiesfrombrowser"] = (browser_name,)

    # Per-format options
    if kind.lower() == "mp3":
        ydl_opts = {
            **common,
            "format": "bestaudio/best",
            "keepvideo": False,  # Do not keep the original video after audio extraction
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": bitrate_kbps,
                },
                {"key": "FFmpegMetadata"},
                {"key": "EmbedThumbnail"},
            ],
            # Add ID3v2.3 tags (car radios and older players are happier with this)
            "postprocessor_args": ["-id3v2_version", "3", "-write_id3v1", "1"],
        }
    else:  # MP4
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
            f"Client: {client_choice.upper()} | Cookies: {use_cookies_var.get()} | "
            f"Browser: {browser_var.get()}"
        )
        if FFMPEG_PATH:
            append_log_line(f"Using ffmpeg at: {FFMPEG_PATH}")
        else:
            append_log_line("Using ffmpeg from system PATH (if available)")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as e:
        msg = f"ERROR: {e}"
        append_log_line(msg)
        if finish_callback:
            finish_callback("❌ Download error.")
    except Exception as e:
        msg = f"UNEXPECTED ERROR: {e}"
        append_log_line(msg)
        if finish_callback:
            finish_callback("❌ Unexpected error.")


# --------- UI Handlers ----------

def start_download_single():
    if SELECTED_DIR is None:
        messagebox.showerror("Error", "Please choose a download destination first!")
        return
    url = url_entry.get().strip()
    if not url:
        messagebox.showerror("Error", "Please enter a YouTube link!")
        return

    kind = format_var.get().lower()
    bitrate = bitrate_var.get()

    status_label.configure(text=f"⏳ Downloading {kind.upper()}...", text_color="orange")
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
        title="Choose links file (one URL per line)",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
    )
    if file_path:
        LINKS_FILE = Path(file_path)
        file_label.configure(
            text=f"Selected file: {LINKS_FILE.name}", text_color="white"
        )


def choose_dest_dir():
    global SELECTED_DIR
    dir_path = filedialog.askdirectory(title="Choose destination folder")
    if dir_path:
        SELECTED_DIR = Path(dir_path)
        dest_label.configure(
            text=f"Destination: {SELECTED_DIR}", text_color="white"
        )


def start_download_list():
    if SELECTED_DIR is None:
        messagebox.showerror("Error", "Please choose a download destination first!")
        return
    if not LINKS_FILE:
        messagebox.showerror(
            "Error", "Please choose a TXT file with URLs first!"
        )
        return

    try:
        with open(LINKS_FILE, "r", encoding="utf-8") as f:
            urls = [
                line.strip()
                for line in f
                if line.strip() and not line.strip().startswith("#")
            ]
    except Exception as e:
        messagebox.showerror("Error", f"Cannot read file: {e}")
        return

    if not urls:
        messagebox.showerror("Error", "The file does not contain valid URLs.")
        return

    kind = format_var.get().lower()
    bitrate = bitrate_var.get()
    status_label.configure(
        text=(
            f"⏳ Processing {len(urls)} items as "
            f"{kind.upper()} in {SELECTED_DIR}"
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
        batch_label.configure(text=f"Item {idx}/{total}")
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
            # Error is already logged in download_media; here we only update the UI.
            status_label.configure(
                text=f"⚠️ Error on item {idx}/{total}: {e}", text_color="red"
            )

    status_label.configure(text="✅ Batch finished!", text_color="green")
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
app.title("🎧 YouTube → MP3 / MP4 Downloader")
app.geometry("980x780")

title_label = ctk.CTkLabel(
    app, text="🎧 YouTube → MP3 / MP4", font=("Segoe UI", 24, "bold")
)
title_label.pack(pady=16)

# Destination
dest_frame = ctk.CTkFrame(app)
dest_frame.pack(pady=6, padx=8, fill="x")
ctk.CTkButton(
    dest_frame,
    text="📁 Choose destination…",
    width=180,
    height=36,
    command=choose_dest_dir,
).grid(row=0, column=0, padx=8, pady=8)
dest_label = ctk.CTkLabel(
    dest_frame,
    text="Destination: (not selected)",
    font=("Segoe UI", 13),
    text_color="gray",
)
dest_label.grid(row=0, column=1, padx=8, pady=8, sticky="w")

# Single link entry
url_entry = ctk.CTkEntry(
    app,
    width=900,
    height=40,
    placeholder_text="Paste YouTube link here (video or playlist)...",
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

ctk.CTkLabel(format_frame, text="MP3 bitrate:", font=("Segoe UI", 13)).grid(
    row=0, column=2, padx=12, pady=6
)
bitrate_var = ctk.StringVar(value=MP3_DEFAULT)
bitrate_menu = ctk.CTkOptionMenu(
    format_frame, values=["128", "192", "256", "320"], variable=bitrate_var, width=100
)
bitrate_menu.grid(row=0, column=3, padx=6, pady=6)
bitrate_hint = ctk.CTkLabel(
    format_frame,
    text="(192 kbps recommended for car stereos)",
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
    format_frame, text="Use browser cookies", variable=use_cookies_var
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
    format_frame, text="User-Agent (optional):", font=("Segoe UI", 13)
).grid(row=2, column=0, padx=6, pady=6, sticky="e")
ua_entry = ctk.CTkEntry(
    format_frame, width=600, placeholder_text="Leave empty for default User-Agent"
)
ua_entry.grid(row=2, column=1, columnspan=4, padx=6, pady=6, sticky="w")

# Action buttons
btn_row = ctk.CTkFrame(app)
btn_row.pack(pady=8)
ctk.CTkButton(
    btn_row,
    text="⬇️ Download single link to destination",
    width=300,
    height=40,
    command=start_download_single,
).grid(row=0, column=0, padx=8, pady=5)
ctk.CTkButton(
    btn_row,
    text="📄 Choose links file (TXT)",
    width=250,
    height=40,
    command=choose_links_file,
).grid(row=0, column=1, padx=8, pady=5)
ctk.CTkButton(
    app,
    text="🗂️ Process whole list (MP3/MP4) to destination",
    width=380,
    height=40,
    command=start_download_list,
).pack(pady=8)

# Labels under buttons
file_label = ctk.CTkLabel(
    app, text="No file selected", font=("Segoe UI", 13), text_color="gray"
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

# Initialize UI state
on_format_change(format_var.get())

app.mainloop()
