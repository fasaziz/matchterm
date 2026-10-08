#define AppVersion "0.1.2"
[Setup]
AppId={{AE63B932-81E2-42B6-82F3-164BEAA51E80}
AppName=MATCHTERM
AppVersion={#AppVersion}
AppPublisher=fasaziz
AppPublisherURL=https://github.com/fasaziz/matchterm
DefaultDirName={localappdata}\Programs\MATCHTERM
DefaultGroupName=MATCHTERM
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\installer-output
OutputBaseFilename=MATCHTERM-Setup-{#AppVersion}-x64
Compression=lzma2
SolidCompression=yes
ChangesEnvironment=yes
UninstallDisplayIcon={app}\matchterm.exe
CloseApplications=yes
[Files]
Source: "..\dist\matchterm\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "manage-path.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.html"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\docs\images\*"; DestDir: "{app}\docs\images"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\MATCHTERM"; Filename: "{app}\matchterm.exe"
Name: "{group}\MATCHTERM Guide"; Filename: "{app}\README.html"
[Run]
Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\manage-path.ps1"" -Action Add -Directory ""{app}"""; Flags: runhidden waituntilterminated
Filename: "{app}\matchterm.exe"; Description: "Launch MATCHTERM"; Flags: nowait postinstall skipifsilent
[UninstallRun]
Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\manage-path.ps1"" -Action Remove -Directory ""{app}"""; Flags: runhidden waituntilterminated
