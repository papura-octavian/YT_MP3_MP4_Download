# Release v1.0.0

## YouTube MP3/MP4 Downloader v1.0.0

Prima versiune release cu installer-uri standalone pentru Windows și Linux.

### Descărcări

- **Windows**: [yt_mp3_mp4_download-setup-1.0.0.exe](yt_mp3_mp4_download-setup-1.0.0.exe)
  - Installer standalone - nu necesită Python instalat
  - Include toate dependențele și FFmpeg
  - Instalează aplicația în Program Files
  
- **Linux (Ubuntu/Debian)**: [yt_mp3_mp4_download-1.0.0-x86_64.AppImage](yt_mp3_mp4_download-1.0.0-x86_64.AppImage)
  - AppImage standalone - nu necesită Python instalat
  - Rulează direct fără instalare
  - Compatibil cu majoritatea distribuțiilor Linux

### Instalare Windows

1. Descarcă `yt_mp3_mp4_download-setup-1.0.0.exe`
2. Rulează installer-ul (poate necesita drepturi de administrator)
3. Urmează instrucțiunile din wizard
4. Aplicația va fi disponibilă în Start Menu și pe Desktop (dacă ai ales opțiunea)

### Instalare Linux

1. Descarcă `yt_mp3_mp4_download-1.0.0-x86_64.AppImage`
2. Fă-l executabil:
   ```bash
   chmod +x yt_mp3_mp4_download-1.0.0-x86_64.AppImage
   ```
3. Rulează direct:
   ```bash
   ./yt_mp3_mp4_download-1.0.0-x86_64.AppImage
   ```

### Funcționalități

- ✅ Descărcare video YouTube individuale sau playlist-uri
- ✅ Conversie în MP3 (128/192/256/320 kbps)
- ✅ Descărcare MP4 (calitate maximă disponibilă)
- ✅ Suport pentru browser cookies (Chrome, Firefox, Edge, Brave)
- ✅ Alegere client YouTube (web, android, ios, tv)
- ✅ Interfață grafică modernă cu CustomTkinter
- ✅ Console integrată pentru log-uri
- ✅ FFmpeg inclus (nu necesită instalare separată)

### Cerințe

**Windows:**
- Windows 7 sau mai nou
- Nu necesită Python sau alte dependențe

**Linux:**
- Ubuntu 18.04+ / Debian 10+ sau distribuții compatibile
- Nu necesită Python sau alte dependențe
- Suport pentru AppImage (majoritatea distribuțiilor moderne)

### Note

- Aplicația include FFmpeg pentru conversie MP3
- Pentru utilizatori cu Python instalat, poți rula direct `python main.py`
- Vezi [README.md](README.md) pentru instrucțiuni detaliate de utilizare

### Build

Pentru a construi installer-ele local:

**Windows:**
```bash
build_windows.bat
```

**Linux:**
```bash
./build_linux.sh
```

### Probleme cunoscute

- Dacă întâmpini probleme cu descărcările, încearcă să schimbi client-ul YouTube (ex: android → web)
- Pentru conținut restricționat, folosește opțiunea "Use browser cookies"
