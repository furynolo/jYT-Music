; Inno Setup Script for jYT Music Desktop
; --------------------------------------

#define MyAppName "jYT Music"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "jYT Music Team"
#define MyAppURL "https://github.com/jwadagnolo/jyt-music-desktop-app"
#define MyAppExeName "jYT-Music.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
AppId={{C0A2E2A1-039B-4B96-A6F7-41DA1BEB564E}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
; Specify the output folder for the installer
OutputDir=installer_output
OutputBaseFilename=jYT-Music-Setup
SetupIconFile=src\assets\logo.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; Icon for the installer itself (use logo.ico if converted, or omit)
; SetupIconFile=src\assets\logo.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; This assumes PyInstaller was run with 'pyinstaller jyt-music.spec'
; The COLLECT block in the spec file creates a folder in dist/jYT-Music-Desktop
Source: "dist\jYT-Music-Desktop\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Option to launch the app after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
