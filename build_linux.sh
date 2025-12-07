#!/usr/bin/env bash
set -euo pipefail

APP_NAME="yt_mp3_mp4_download"
VERSION="1.0.0"
ARCH="x86_64"

echo "========================================"
echo "Building ${APP_NAME} (Linux AppImage)"
echo "========================================"

echo ""
echo "[1/4] Installing Python dependencies"
pip install --upgrade pip pyinstaller >/dev/null 2>&1

echo ""
echo "[2/4] Building PyInstaller binary (Linux)"
pyinstaller pyinstaller_linux.spec --clean

echo ""
echo "[3/4] Creating AppDir structure"
APP_DIR="dist/${APP_NAME}.AppDir"
rm -rf "${APP_DIR}"
mkdir -p "${APP_DIR}/usr/bin"
mkdir -p "${APP_DIR}/usr/share/applications"
mkdir -p "${APP_DIR}/usr/share/icons/hicolor/256x256/apps"

# Copy PyInstaller output (could be a single file or a directory)
if [ -d "dist/YT_Downloader" ]; then
    # PyInstaller created a directory (onefile=False)
    cp -r dist/YT_Downloader/* "${APP_DIR}/usr/bin/"
elif [ -f "dist/YT_Downloader" ]; then
    # PyInstaller created a single executable (onefile=True)
    cp dist/YT_Downloader "${APP_DIR}/usr/bin/YT_Downloader"
    chmod +x "${APP_DIR}/usr/bin/YT_Downloader"
else
    echo "ERROR: Could not find PyInstaller output in dist/YT_Downloader"
    exit 1
fi

# Copy ffmpeg binaries if they exist
if [ -d "dist/YT_Downloader/ffmpeg" ]; then
    cp -r dist/YT_Downloader/ffmpeg "${APP_DIR}/usr/bin/"
elif [ -d "ffmpeg/linux" ]; then
    mkdir -p "${APP_DIR}/usr/bin/ffmpeg/linux"
    cp ffmpeg/linux/ffmpeg "${APP_DIR}/usr/bin/ffmpeg/linux/" 2>/dev/null || true
    cp ffmpeg/linux/ffprobe "${APP_DIR}/usr/bin/ffmpeg/linux/" 2>/dev/null || true
fi

# Copy icons if they exist
if [ -d "dist/YT_Downloader/icons" ]; then
    cp -r dist/YT_Downloader/icons "${APP_DIR}/usr/bin/"
elif [ -d "icons" ]; then
    mkdir -p "${APP_DIR}/usr/bin/icons"
    cp -r icons/* "${APP_DIR}/usr/bin/icons/" 2>/dev/null || true
fi

# Create desktop file
cat > "${APP_DIR}/usr/share/applications/${APP_NAME}.desktop" <<EOF
[Desktop Entry]
Name=YouTube MP3/MP4 Downloader
Comment=Download YouTube videos and playlists as MP3 or MP4
Exec=AppRun
Icon=${APP_NAME}
Type=Application
Categories=AudioVideo;Network;
StartupNotify=true
EOF

# Copy icon
if [ -f "icons/YT_download_icon.png" ]; then
    cp "icons/YT_download_icon.png" "${APP_DIR}/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png"
    cp "icons/YT_download_icon.png" "${APP_DIR}/${APP_NAME}.png"
elif [ -f "icons/YT_download_icon.ico" ]; then
    # Try to convert ico to png if imagemagick is available
    if command -v convert >/dev/null 2>&1; then
        convert "icons/YT_download_icon.ico" "${APP_DIR}/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png"
        convert "icons/YT_download_icon.ico" "${APP_DIR}/${APP_NAME}.png"
    else
        echo "Warning: No PNG icon found and imagemagick not available. AppImage may not have icon."
    fi
fi

# Create AppRun script
cat > "${APP_DIR}/AppRun" <<'EOF'
#!/usr/bin/env bash
HERE="$(dirname "$(readlink -f "${0}")")"
exec "${HERE}/usr/bin/YT_Downloader" "$@"
EOF
chmod +x "${APP_DIR}/AppRun"

echo ""
echo "[4/4] Building AppImage"
# Check if appimagetool is available
if command -v appimagetool >/dev/null 2>&1; then
    appimagetool "${APP_DIR}" "dist/${APP_NAME}-${VERSION}-${ARCH}.AppImage"
elif [ -f "appimagetool-x86_64.AppImage" ]; then
    chmod +x appimagetool-x86_64.AppImage
    ./appimagetool-x86_64.AppImage "${APP_DIR}" "dist/${APP_NAME}-${VERSION}-${ARCH}.AppImage"
else
    echo ""
    echo "ERROR: appimagetool not found!"
    echo "Please install it:"
    echo "  wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    echo "  chmod +x appimagetool-x86_64.AppImage"
    echo "  sudo mv appimagetool-x86_64.AppImage /usr/local/bin/appimagetool"
    echo ""
    echo "Or download manually from:"
    echo "  https://github.com/AppImage/AppImageKit/releases"
    echo ""
    echo "Creating tar.gz as fallback..."
    tar -C dist -czf "dist/${APP_NAME}-${VERSION}-${ARCH}.tar.gz" "${APP_NAME}.AppDir"
    exit 1
fi

echo ""
echo "========================================"
echo "Build completed successfully!"
echo "========================================"
echo "AppImage: dist/${APP_NAME}-${VERSION}-${ARCH}.AppImage"
echo ""
echo "To make it executable:"
echo "  chmod +x dist/${APP_NAME}-${VERSION}-${ARCH}.AppImage"
echo ""
echo "To run:"
echo "  ./dist/${APP_NAME}-${VERSION}-${ARCH}.AppImage"
