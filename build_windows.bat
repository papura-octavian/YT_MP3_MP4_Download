@echo off
setlocal
set APP_NAME=YT_Downloader
set VERSION=1.0.0

echo ========================================
echo Building %APP_NAME% (Windows)
echo ========================================

echo.
echo [1/3] Install PyInstaller
pip install --upgrade pip pyinstaller
if errorlevel 1 goto :error

echo.
echo [2/3] Build EXE with PyInstaller
pyinstaller pyinstaller_windows.spec
if errorlevel 1 goto :error

echo.
echo [3/3] Build installer with Inno Setup
set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist %ISCC% (
    %ISCC% installer.iss
) else (
    echo Could not find ISCC at %ISCC%
    echo Please adjust the path to ISCC.exe if Inno Setup is installed elsewhere.
    goto :error
)

echo.
echo Success!
echo EXE: dist\%APP_NAME%\%APP_NAME%.exe
echo Installer: dist\yt_mp3_mp4_download-setup-1.0.0.exe
goto :eof

:error
echo Build failed. See messages above.
exit /b 1
