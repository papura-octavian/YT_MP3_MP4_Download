# Cum să creezi un Release pe GitHub

## Opțiunea 1: Manual (Recomandat)

1. **Construiește installer-ele:**

   **Pe Windows:**
   ```bash
   build_windows.bat
   ```
   Rezultat: `dist/yt_mp3_mp4_download-setup-1.0.0.exe`

   **Pe Linux (Ubuntu):**
   ```bash
   ./build_linux.sh
   ```
   Rezultat: `dist/yt_mp3_mp4_download-1.0.0-x86_64.AppImage`

2. **Creează release-ul pe GitHub:**
   - Mergi la: https://github.com/papura-octavian/YT_MP3_MP4_Download/releases/new
   - Selectează tag-ul: `v1.0.0`
   - Titlu: `Release v1.0.0`
   - Descriere: Copiază conținutul din `RELEASE_NOTES.md`
   - Upload fișierele:
     - `yt_mp3_mp4_download-setup-1.0.0.exe` (Windows installer)
     - `yt_mp3_mp4_download-1.0.0-x86_64.AppImage` (Linux AppImage)
   - Click "Publish release"

## Opțiunea 2: GitHub CLI (dacă ai instalat)

```bash
# Instalează GitHub CLI dacă nu ai
# Ubuntu/Debian:
sudo apt install gh

# Autentifică-te
gh auth login

# Creează release-ul
gh release create v1.0.0 \
  --title "Release v1.0.0" \
  --notes-file RELEASE_NOTES.md \
  dist/yt_mp3_mp4_download-setup-1.0.0.exe \
  dist/yt_mp3_mp4_download-1.0.0-x86_64.AppImage
```

## Opțiunea 3: GitHub Actions (Automat)

Dacă ai configurat GitHub Actions (vezi `.github/workflows/build.yml`), release-ul se va crea automat când:
1. Push-ezi un tag: `git push origin v1.0.0`
2. GitHub Actions va construi installer-ele
3. Release-ul va fi creat automat cu fișierele

**Notă:** Pentru prima dată, trebuie să construiești manual installer-ele și să le uploadezi la release.

## Verificare

După crearea release-ului, verifică:
- https://github.com/papura-octavian/YT_MP3_MP4_Download/releases/tag/v1.0.0
- Ambele fișiere sunt disponibile pentru descărcare
- Descrierea release-ului este corectă
