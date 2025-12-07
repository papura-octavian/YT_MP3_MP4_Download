# -*- mode: python ; coding: utf-8 -*-
#
# Build Linux binary (run on Ubuntu):
#   pip install pyinstaller
#   pyinstaller pyinstaller_linux.spec
#
# Output lands in dist/YT_Downloader/YT_Downloader (ELF)

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

hidden = ["yt_dlp", "tkinter", "threading", "pathlib", "shutil", "time"]
hidden += collect_submodules("customtkinter")

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[
        ("ffmpeg/linux/ffmpeg", "ffmpeg/linux"),
        ("ffmpeg/linux/ffprobe", "ffmpeg/linux"),
    ],
    datas=[
        ("icons/YT_download_icon.ico", "icons"),
        ("icons/YT_download_icon.png", "icons"),
    ],
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="YT_Downloader",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="icons/YT_download_icon.ico",
)
