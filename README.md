# YouTube MP3 / MP4 Downloader (GUI)

Simple desktop application (Python + CustomTkinter) for downloading YouTube **videos** or **playlists** as **MP3** or **MP4** files.

Features:

* Download a **single video** or an entire **playlist** (`https://youtube.com/playlist?...`)
* Download as **MP3** (configurable bitrate) or **MP4**
* Save to a user-chosen folder
* Download from a list of links stored in a `.txt` file
* Choose YouTube “client” (web / android / ios / tv)
* Optional browser cookies support (for logged-in accounts, YouTube Premium, etc.)
* Built-in mini console for logs

---

## Project structure

Recommended:

```text
yt_mp3_mp4_downlaoder/
├── main.py
├── ffmpeg/
│   ├── linux/
│   │   ├── ffmpeg        # Linux binary (no extension)
│   │   └── ffprobe       # Linux binary (no extension)
│   └── windows/
│       ├── ffmpeg.exe    # Windows binary
│       └── ffprobe.exe   # Windows binary
├── README.md
└── ...
```

> Note: if ffmpeg is not found in these folders, the app will try to use **ffmpeg from the system PATH** (if installed).

---

## Requirements

* **Python 3.10+** (3.12 recommended)
* Python packages:

  * `customtkinter`
  * `yt-dlp`
* **ffmpeg** and **ffprobe** must be available:

  * either included in the `ffmpeg/` folder (see structure above)
  * or installed system-wide (available in PATH)

---

## Installation (Linux)

1. Clone / download the project:

   ```bash
   git clone <repo-url>
   cd yt_mp3_mp4_downlaoder
   ```

2. Create and activate a virtual environment (optional, but recommended):

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install customtkinter yt-dlp
   ```

4. Install ffmpeg in the system (if you don’t want to bundle it inside `ffmpeg/linux`):

   ```bash
   sudo apt update
   sudo apt install ffmpeg
   ```

5. (Optional) Copy system binaries into the project structure:

   ```bash
   mkdir -p ffmpeg/linux
   cp /usr/bin/ffmpeg ffmpeg/linux/
   cp /usr/bin/ffprobe ffmpeg/linux/
   chmod +x ffmpeg/linux/ffmpeg ffmpeg/linux/ffprobe
   ```

6. Run the application:

   ```bash
   python main.py
   ```

---

## Installation (Windows)

1. Download or clone the project.

2. Install Python (make sure to tick **“Add Python to PATH”** during setup).

3. Inside the project folder, open Command Prompt / PowerShell:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install customtkinter yt-dlp
   ```

4. Download ffmpeg for Windows:

   * from the official website or a pre-built distribution
   * place the binaries like this:

   ```text
   ffmpeg/windows/ffmpeg.exe
   ffmpeg/windows/ffprobe.exe
   ```

   If you prefer using a system-wide installation (e.g. via `choco install ffmpeg`), that also works – the app will detect ffmpeg from PATH.

5. Run the application:

   ```bash
   python main.py
   ```

---

## How to use the app (GUI)

1. **Choose destination folder**

   * Click `📁 Choose destination…`
   * Select the folder where MP3/MP4 files should be saved.

2. **Enter the link**

   * Paste a YouTube **video** or **playlist** link in the big entry field.

3. **Choose format**

   * In the “Format” menu select:

     * `MP3` – download audio and convert to MP3
     * `MP4` – download video (best available MP4)
   * When MP3 is selected, you can choose bitrate: `128 / 192 / 256 / 320` kbps.
     Recommended: **192 kbps** (very compatible with car stereos).

4. **Client & cookies**

   * **Client**: how the app identifies itself to YouTube:

     * `android`, `web`, `ios`, `tv`
   * **Use browser cookies**:

     * when checked, yt-dlp will read cookies from the selected browser (Chrome / Firefox / Edge / Brave)
     * useful for:

       * members-only videos
       * YouTube Premium
       * age / region restricted content

5. **User-Agent (optional)**

   * You can leave this field empty (a default User-Agent string will be used).
   * If you run into site-specific issues, you can paste a custom UA.

6. **Download a single link**

   * Click **“⬇️ Download single link to destination”**
   * Progress is shown in:

     * the progress bar
     * the status label (title, percent, speed, ETA)
     * the console at the bottom (detailed log)

7. **Download from a list (TXT file)**

   * Prepare a `.txt` file with:

     * one URL per line
     * lines starting with `#` are treated as comments and ignored
   * Click **“📄 Choose links file (TXT)”** and select the file.
   * Then click **“🗂️ Process whole list (MP3/MP4) to destination”**.
   * The app will download each link in order.
   * The label `Item X/Y` shows overall batch progress.

---

## Playlist support

The app accepts playlist URLs such as:

* `https://youtube.com/playlist?list=...`
* `https://www.youtube.com/watch?v=...&list=...`

For playlists:

* each item is saved as
  `Destination/<Playlist Title>/<Video Title>.<ext>`
* for single videos (non-playlist URLs), files are saved directly as
  `Destination/<Video Title>.<ext>` (no extra folder).

---

## Common errors & troubleshooting

### 1. HTTP Error 503: Service Unavailable

Possible causes:

* temporary issues on YouTube / CDN side
* throttling / rate limiting (too many requests in a short time)
* unstable or blocked network / IP

What you can try:

* try again later
* change **Client** (e.g. from `android` to `web`)
* enable **Use browser cookies** and select your browser
* try from a different network connection

### 2. ERROR: Requested format is not available

YouTube does not provide the requested format (for example, a certain MP4 combination for that client).

What you can try:

* change **Client** (e.g. `android` → `web`)
* switch between **MP3** and **MP4**
* keep the default “best” format settings (the app already falls back to the best available stream).

### 3. ERROR: ffmpeg / ffprobe not found

If ffmpeg or ffprobe are missing, MP3 conversion and some MP4 operations will fail.

Fixes:

* install ffmpeg system-wide
  (Linux example: `sudo apt install ffmpeg`)
* or place both binaries in the project under:

  * `ffmpeg/linux/ffmpeg` & `ffmpeg/linux/ffprobe` (Linux)
  * `ffmpeg/windows/ffmpeg.exe` & `ffmpeg/windows/ffprobe.exe` (Windows)
* make sure they are executable (on Linux: `chmod +x ffmpeg/linux/*`).

---

## Technical notes

* Download logic uses `yt_dlp.YoutubeDL` with:

  * `retries = 10`
  * `fragment_retries = 10`
  * `concurrent_fragment_downloads = 1`
  * `http_chunk_size = 10 * 1024 * 1024`
* A custom logger (`YTDLogger`) redirects yt-dlp output into the GUI console.
* `detect_ffmpeg_location()`:

  * first tries to find `ffmpeg` and `ffprobe` in **PATH**
  * if not found, looks in the project directory (`sys._MEIPASS` when bundled) under:

    * `ffmpeg/linux/`
    * `ffmpeg/windows/`
  * returns the path to `ffmpeg` so yt-dlp can use it for post-processing.

