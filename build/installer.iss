; build/installer.iss
;
; Inno Setup script that packages the PyInstaller output (dist/FeatherPDF/)
; into a single, professional Windows installer -- the kind that shows your
; logo, creates Start Menu + Desktop shortcuts, registers an uninstaller in
; "Apps & Features", and (this is the important part) installs everything
; into ONE fixed folder so the .exe and its required _internal/ files can
; never accidentally get separated -- which is the #1 reason a raw
; dist/FeatherPDF folder "works on my machine but not others": someone
; drags just the .exe out on its own, or the folder gets partially copied.
;
; PREREQUISITE: build the PyInstaller output first --
;   python -m PyInstaller build/pyinstaller.spec --workpath build/_cache
; That must succeed and produce dist/FeatherPDF/FeatherPDF.exe before this
; script will find anything to package.
;
; HOW TO BUILD THIS INSTALLER:
;   1. Install Inno Setup (free, version 6.3+): https://jrsoftware.org/isdl.php
;      (the download on that page is always the current version, which is fine)
;   2. Open this file in the Inno Setup Compiler (or right-click ->
;      "Compile"), or from the command line:
;        ISCC.exe build\installer.iss
;   3. The installer lands in dist_installer\FeatherPDF-Setup.exe
;
; This whole file only matters on Windows -- Inno Setup itself is a
; Windows-only tool, so this step is done on a Windows machine after the
; PyInstaller build.

#define MyAppName "FeatherPDF"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Mehedy"
#define MyAppURL "https://mehedy.netlify.app"
#define MyAppExeName "FeatherPDF.exe"

[Setup]
; A fixed, unique AppId -- do not change this between versions, or Windows
; will treat future updates as a totally different program instead of an
; upgrade of this one.
AppId={{7FD1066F-7F22-4DD7-BD89-DA3159C2C3F4}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
; Lets the installer run either per-user (no admin prompt) or per-machine
; (admin prompt, installs for all users) -- the person installing picks,
; rather than the installer forcing one or the other.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
; Icon shown in the installer wizard itself and in Add/Remove Programs
SetupIconFile=..\assets\icons\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
OutputDir=..\dist_installer
OutputBaseFilename=FeatherPDF-Setup
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Pulls in the ENTIRE PyInstaller output folder -- the .exe plus its
; required _internal/ files -- so nothing can be separated after install.
Source: "..\dist\FeatherPDF\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Removes the app's own generated files (logs, settings) on uninstall too,
; not just the installed program files. {%USERPROFILE} reads the
; USERPROFILE environment variable directly -- the same one Python's
; os.path.expanduser("~") resolves against -- so this always matches
; wherever the app actually writes its ~/.featherpdf folder.
Type: filesandordirs; Name: "{%USERPROFILE}\.featherpdf"
