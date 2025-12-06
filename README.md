# YouTube MP3 / MP4 Downloader (GUI)

Aplicație desktop simplă (Python + CustomTkinter) pentru descărcat videoclipuri sau playlist‑uri de pe YouTube în format **MP3** sau **MP4**.

Suportă:
- videoclip individual sau playlist (`https://youtube.com/playlist?...`)
- descărcare în **MP3** (cu bitrate configurabil) sau **MP4**
- salvare într‑un folder ales de utilizator
- descărcare listă de linkuri din fișier `.txt`
- alegerea „clientului” YouTube (web / android / ios / tv)
- folosirea cookie‑urilor din browser (pentru cont logat, YouTube Premium etc.)
- mini‑consolă de log în interfață

---

## Structura proiectului

Recomandat:
Recomandat:

```text
yt_mp3_mp4_downlaoder/
├── main.py
├── ffmpeg/
│   ├── linux/
│   │   ├── ffmpeg        # binar pentru Linux (fără extensie)
│   │   └── ffprobe       # binar pentru Linux (fără extensie)
│   └── windows/
│       ├── ffmpeg.exe    # binar pentru Windows
│       └── ffprobe.exe   # binar pentru Windows
├── README.md
└── ...
```

> Notă: dacă ffmpeg nu este găsit în aceste directoare, aplicația încearcă să folosească **ffmpeg din PATH** (instalat în sistem).

---

## Cerințe

- **Python 3.10+** (recomandat 3.12)
- Pachete Python:
  - `customtkinter`
  - `yt-dlp`
- **ffmpeg** și **ffprobe** disponibile:
  - fie incluse în folderul `ffmpeg/` din proiect (vezi structura de mai sus)
  - fie instalate în sistem (disponibile în PATH)

---

## Instalare (Linux)

1. Clonează / descarcă proiectul:
   ```bash
   git clone <link-repo>
   cd Cantari-de-Slava
   ```

2. Creează și activează un virtual env (opțional, dar recomandat):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Instalează dependențele:
   ```bash
   pip install customtkinter yt-dlp
   ```

4. Instalează ffmpeg în sistem (dacă nu vrei să îl pui în folderul `ffmpeg/linux`):
   ```bash
   sudo apt update
   sudo apt install ffmpeg
   ```

5. (Opțional) Copiază binarele locale în structura proiectului:
   ```bash
   mkdir -p ffmpeg/linux
   cp /usr/bin/ffmpeg ffmpeg/linux/
   cp /usr/bin/ffprobe ffmpeg/linux/
   chmod +x ffmpeg/linux/ffmpeg ffmpeg/linux/ffprobe
   ```

6. Rulează aplicația:
   ```bash
   python main.py
   ```

---

## Instalare (Windows)

1. Descarcă proiectul sau clonează cu Git.
2. Instalează Python (bifează „Add Python to PATH”).
3. În folderul proiectului, deschide Command Prompt / PowerShell:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install customtkinter yt-dlp
   ```
4. Descarcă ffmpeg pentru Windows:
   - de pe site‑ul oficial sau din distribuție pre‑compilată
   - pune binarul `ffmpeg.exe` în:
     ```text
     ffmpeg/windows/ffmpeg.exe
     ```
5. Rulează aplicația:
   ```bash
   python main.py
   ```

Dacă ffmpeg este deja în PATH (ex: prin `choco install ffmpeg`), aplicația îl poate folosi direct.

---

## Cum funcționează aplicația (GUI)

1. **Alege destinația**
   - Sus, apasă pe butonul `📁 Alege destinația…`
   - Selectează folderul unde vrei să fie salvate fișierele (MP3/MP4)

2. **Introdu linkul**
   - În câmpul mare de text: lipește un link de **video** sau de **playlist** YouTube.

3. **Alege formatul**
   - Din meniul „Format” selectezi:
     - `MP3` – descarcă audio + convertește în MP3
     - `MP4` – descarcă video (cel mai bun MP4 disponibil)
   - Dacă alegi MP3, poți seta bitrate-ul (128 / 192 / 256 / 320 kbps).  
     Recomandare: `192 kbps` (compatibil cu multe playere auto).

4. **Client & cookies**
   - `Client`: modul în care se prezintă aplicația către YouTube:
     - `android`, `web`, `ios`, `tv`
   - `Folosește cookies din browser`:
     - dacă bifezi, yt-dlp va extrage cookie-urile din browserul ales (Chrome / Firefox / Edge / Brave)
     - util pentru:
       - videouri doar pentru membri
       - cont YouTube Premium
       - restricții de vârstă / regiune

5. **User-Agent (opțional)**
   - Poți lăsa gol (aplicația folosește un UA implicit).
   - Dacă ai probleme cu anumite request‑uri, poți pune un User-Agent personalizat.

6. **Descarcă un singur link**
   - Apasă **„⬇️ Descarcă linkul în destinația aleasă”**
   - Progresul este afișat în:
     - bara de progres
     - eticheta de status (titlu, procent, viteză, ETA)
     - mini‑consola de jos (log detaliat)

7. **Descarcă o listă de linkuri (fișier TXT)**
   - Pregătește un fișier `.txt` cu:
     - un link pe linie
     - liniile care încep cu `#` sunt ignorate (comentarii)
   - Apasă **„📄 Alege fișier linkuri (TXT)”** și selectează fișierul.
   - Apoi apasă **„🗂️ Procesează toată lista (MP3/MP4) în destinația aleasă”**.
   - Aplicația va descărca toate linkurile, unul câte unul.
   - Eticheta „Elementul X/Y” indică progresul în listă.

---

## Suport pentru playlist-uri YouTube

Aplicația acceptă direct linkuri de tip:

- `https://youtube.com/playlist?list=...`
- sau `https://www.youtube.com/watch?v=...&list=...`

Setări relevante:
- `noplaylist = False` – permite descărcarea întregului playlist.
- `outtmpl`: poate fi setat să nu includă numele playlist‑ului în calea de salvare, de ex:
  ```python
  "outtmpl": str(outdir / "%(title)s.%(ext)s"),
  ```
  astfel, fiecare playlist nu mai creează automat propriul folder.

---

## Erori frecvente și soluții

### 1. HTTP Error 503: Service Unavailable

Cauze posibile:
- problemă temporară pe serverele YouTube / CDN
- throttling / rate limit (prea multe request-uri într-un timp scurt)
- probleme de rețea / IP

Ce poți face:
- încearcă din nou mai târziu
- schimbă „Client” (ex: de la `android` la `web`)
- bifează „Folosește cookies din browser” și selectează browserul tău
- încearcă de pe altă conexiune la internet

### 2. ERROR: Requested format is not available

YouTube nu oferă formatul cerut (de ex., nu există MP4 la rezoluția dorită pe clientul ales).

Soluții:
- schimbă `Client` (ex: `android` → `web`)
- schimbă formatul de descărcare (MP3 / MP4)
- încearcă fără setări speciale de format (aplicația deja are fallback la `best`).

---

## Note tehnice (intern)

- Download logic bazat pe `yt_dlp.YoutubeDL` cu:
  - `retries = 10`
  - `fragment_retries = 10`
  - `concurrent_fragment_downloads = 1`
  - `http_chunk_size = 10 * 1024 * 1024`
- Logger custom (`YTDLogger`) care trimite mesajele în mini‑consola UI.
- `detect_ffmpeg_location()`:
  - caută ffmpeg în:
    - folderul aplicației / PyInstaller (`sys._MEIPASS` dacă există)
    - `ffmpeg/`, `ffmpeg/windows`, `ffmpeg/linux`
  - dacă nu găsește nimic, lasă yt‑dlp să caute ffmpeg în PATH.

---