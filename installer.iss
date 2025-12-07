; Inno Setup script for Windows installer
; Build steps (run on Windows):
;   1) pip install pyinstaller
;   2) pyinstaller pyinstaller_windows.spec
;   3) "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss

#define MyAppName "YouTube MP3/MP4 Downloader"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "yt_mp3_mp4_downlaoder"
#define MyAppURL "https://example.com"
#define MyAppExeName "YT_Downloader.exe"

[Setup]
AppId={{7F0520B7-39F3-49E3-9C0E-5E0E78F6E2B1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=admin
OutputDir=dist
OutputBaseFilename=yt_mp3_mp4_download-setup-1.0.0
SetupIconFile=icons\YT_download_icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\YT_Downloader\YT_Downloader.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\YT_Downloader\ffmpeg\windows\*"; DestDir: "{app}\ffmpeg\windows"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\YT_Downloader\icons\*"; DestDir: "{app}\icons"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icons\YT_download_icon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\icons\YT_download_icon.ico"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
