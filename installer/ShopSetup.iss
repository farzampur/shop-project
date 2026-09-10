#define MyAppName "Shop"
#define MyAppVersion "1.0.4"
#define MyAppPublisher "Shop"
#define MyAppExeName "install.ps1"

[Setup]
AppId={{8A7C4D21-9B52-4F11-A8C3-7F6D9E2B1044}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={autopf}\Shop
DefaultGroupName=Shop

OutputDir=output
OutputBaseFilename=ShopSetup-{#MyAppVersion}

Compression=lzma2/max
SolidCompression=yes

PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64

DisableProgramGroupPage=yes
Uninstallable=yes

WizardStyle=modern

[Files]

Source: "install.ps1"; DestDir: "{app}"; Flags: ignoreversion

Source: "payload\postgres-16.tar"; \
    DestDir: "{app}\payload"; \
    Flags: ignoreversion

Source: "payload\shop-backend-1.0.4.tar"; \
    DestDir: "{app}\payload"; \
    Flags: ignoreversion

Source: "payload\docker-compose.yml"; \
    DestDir: "{app}\payload"; \
    Flags: ignoreversion

Source: "payload\.env.template"; \
    DestDir: "{app}\payload"; \
    Flags: ignoreversion

[Icons]

Name: "{group}\Shop"; \
    Filename: "http://localhost:8010/admin/login/"

Name: "{autodesktop}\Shop"; \
    Filename: "http://localhost:8010/admin/login/"; \
    Tasks: desktopicon

[Tasks]

Name: "desktopicon"; \
    Description: "Create a desktop shortcut"; \
    GroupDescription: "Additional icons:"; \
    Flags: unchecked

[Run]

Filename: "powershell.exe"; \
    Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\install.ps1"""; \
    WorkingDir: "{app}"; \
    Flags: waituntilterminated runascurrentuser

Filename: "http://localhost:8010/admin/login/"; \
    Description: "Open Shop Admin"; \
    Flags: postinstall shellexec skipifsilent