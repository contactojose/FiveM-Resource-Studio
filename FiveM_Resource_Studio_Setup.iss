#define MyAppName "FiveM Resource Studio"
#define MyAppVersion "0.2.0"
#define MyAppPublisher "FiveM Resource Studio"
#define MyAppExeName "FiveM_Resource_Studio.exe"

[Setup]
AppId={{8A8A7E7B-7A41-4E30-9F21-6A9C8F7D2A10}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\FiveM Resource Studio
DefaultGroupName={#MyAppName}
OutputDir=installer
OutputBaseFilename=FiveM_Resource_Studio_Setup_Windows_x64
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupLogging=yes

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir FiveM Resource Studio"; Flags: postinstall nowait skipifsilent
