#ifndef AppSourceDir
#define AppSourceDir "dist_cpu\\FlaskTranscriber"
#endif

#ifndef OutputDir
#define OutputDir "dist_installer"
#endif

#define AppName "FlaskTranscriber"
#define AppVersion "1.0.0"
#define AppPublisher "FlaskTranscriber"
#define AppExeName "FlaskTranscriber.exe"
#define IconFile "app.ico"

[Setup]
AppId={{0C81207E-7E22-4E24-9E7E-7B8C4D8A1F45}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir={#OutputDir}
OutputBaseFilename=FlaskTranscriber_Setup
Compression=lzma
SolidCompression=yes
SetupIconFile={#IconFile}
UninstallDisplayIcon={app}\{#AppExeName}
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a Desktop shortcut"; Flags: unchecked

[Files]
Source: "{#AppSourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
