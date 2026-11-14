#define AppName "Bloc de Notas Monaco"
#define AppVer "1.0.0"

[Setup]
AppId={{B7F1C0A2-5D3E-4C8A-9E21-3A6B1D0F7C55}
AppName={#AppName}
AppVersion={#AppVer}
DefaultDirName={autopf}\BlocDeNotasMonaco
DefaultGroupName={#AppName}
OutputDir=installer
OutputBaseFilename=BlocDeNotas-Setup
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ChangesAssociations=yes
UninstallDisplayIcon={app}\BlocDeNotas.exe
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
DisableProgramGroupPage=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear icono en el escritorio"; Flags: unchecked
Name: "assoc"; Description: "Mostrar en «Abrir con» para archivos de texto y código"
Name: "ctxmenu"; Description: "Añadir «Abrir con Bloc de Notas Monaco» al clic derecho de cualquier archivo"

[Files]
Source: "dist\BlocDeNotas\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\BlocDeNotas.exe"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\BlocDeNotas.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\BlocDeNotas.exe"; Description: "Abrir Bloc de Notas Monaco"; Flags: nowait postinstall skipifsilent

[Registry]
Root: HKA; Subkey: "Software\Classes\BlocDeNotasMonaco.File"; ValueType: string; ValueData: "Archivo de texto o código"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\BlocDeNotasMonaco.File\DefaultIcon"; ValueType: string; ValueData: "{app}\BlocDeNotas.exe,0"
Root: HKA; Subkey: "Software\Classes\BlocDeNotasMonaco.File\shell\open\command"; ValueType: string; ValueData: """{app}\BlocDeNotas.exe"" ""%1"""
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\shell\open\command"; ValueType: string; ValueData: """{app}\BlocDeNotas.exe"" ""%1"""; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\.txt\OpenWithProgids"; ValueType: string; ValueName: "BlocDeNotasMonaco.File"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\SupportedTypes"; ValueType: string; ValueName: ".txt"; ValueData: ""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.log\OpenWithProgids"; ValueType: string; ValueName: "BlocDeNotasMonaco.File"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\SupportedTypes"; ValueType: string; ValueName: ".log"; ValueData: ""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.csv\OpenWithProgids"; ValueType: string; ValueName: "BlocDeNotasMonaco.File"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\SupportedTypes"; ValueType: string; ValueName: ".csv"; ValueData: ""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.md\OpenWithProgids"; ValueType: string; ValueName: "BlocDeNotasMonaco.File"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\SupportedTypes"; ValueType: string; ValueName: ".md"; ValueData: ""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.markdown\OpenWithProgids"; ValueType: string; ValueName: "BlocDeNotasMonaco.File"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\SupportedTypes"; ValueType: string; ValueName: ".markdown"; ValueData: ""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.py\OpenWithProgids"; ValueType: string; ValueName: "BlocDeNotasMonaco.File"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\SupportedTypes"; ValueType: string; ValueName: ".py"; ValueData: ""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.js\OpenWithProgids"; ValueType: string; ValueName: "BlocDeNotasMonaco.File"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\SupportedTypes"; ValueType: string; ValueName: ".js"; ValueData: ""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.ts\OpenWithProgids"; ValueType: string; ValueName: "BlocDeNotasMonaco.File"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\SupportedTypes"; ValueType: string; ValueName: ".ts"; ValueData: ""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.json\OpenWithProgids"; ValueType: string; ValueName: "BlocDeNotasMonaco.File"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\SupportedTypes"; ValueType: string; ValueName: ".json"; ValueData: ""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.html\OpenWithProgids"; ValueType: string; ValueName: "BlocDeNotasMonaco.File"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\SupportedTypes"; ValueType: string; ValueName: ".html"; ValueData: ""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.css\OpenWithProgids"; ValueType: string; ValueName: "BlocDeNotasMonaco.File"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\SupportedTypes"; ValueType: string; ValueName: ".css"; ValueData: ""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.java\OpenWithProgids"; ValueType: string; ValueName: "BlocDeNotasMonaco.File"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\SupportedTypes"; ValueType: string; ValueName: ".java"; ValueData: ""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.c\OpenWithProgids"; ValueType: string; ValueName: "BlocDeNotasMonaco.File"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\SupportedTypes"; ValueType: string; ValueName: ".c"; ValueData: ""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.cpp\OpenWithProgids"; ValueType: string; ValueName: "BlocDeNotasMonaco.File"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\SupportedTypes"; ValueType: string; ValueName: ".cpp"; ValueData: ""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.h\OpenWithProgids"; ValueType: string; ValueName: "BlocDeNotasMonaco.File"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\SupportedTypes"; ValueType: string; ValueName: ".h"; ValueData: ""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.cs\OpenWithProgids"; ValueType: string; ValueName: "BlocDeNotasMonaco.File"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\SupportedTypes"; ValueType: string; ValueName: ".cs"; ValueData: ""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.go\OpenWithProgids"; ValueType: string; ValueName: "BlocDeNotasMonaco.File"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\SupportedTypes"; ValueType: string; ValueName: ".go"; ValueData: ""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.rs\OpenWithProgids"; ValueType: string; ValueName: "BlocDeNotasMonaco.File"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\SupportedTypes"; ValueType: string; ValueName: ".rs"; ValueData: ""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.sh\OpenWithProgids"; ValueType: string; ValueName: "BlocDeNotasMonaco.File"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\SupportedTypes"; ValueType: string; ValueName: ".sh"; ValueData: ""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.sql\OpenWithProgids"; ValueType: string; ValueName: "BlocDeNotasMonaco.File"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\SupportedTypes"; ValueType: string; ValueName: ".sql"; ValueData: ""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.yml\OpenWithProgids"; ValueType: string; ValueName: "BlocDeNotasMonaco.File"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\SupportedTypes"; ValueType: string; ValueName: ".yml"; ValueData: ""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.yaml\OpenWithProgids"; ValueType: string; ValueName: "BlocDeNotasMonaco.File"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\SupportedTypes"; ValueType: string; ValueName: ".yaml"; ValueData: ""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.xml\OpenWithProgids"; ValueType: string; ValueName: "BlocDeNotasMonaco.File"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\SupportedTypes"; ValueType: string; ValueName: ".xml"; ValueData: ""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.php\OpenWithProgids"; ValueType: string; ValueName: "BlocDeNotasMonaco.File"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\SupportedTypes"; ValueType: string; ValueName: ".php"; ValueData: ""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.rb\OpenWithProgids"; ValueType: string; ValueName: "BlocDeNotasMonaco.File"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\SupportedTypes"; ValueType: string; ValueName: ".rb"; ValueData: ""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.kt\OpenWithProgids"; ValueType: string; ValueName: "BlocDeNotasMonaco.File"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\SupportedTypes"; ValueType: string; ValueName: ".kt"; ValueData: ""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.toml\OpenWithProgids"; ValueType: string; ValueName: "BlocDeNotasMonaco.File"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\SupportedTypes"; ValueType: string; ValueName: ".toml"; ValueData: ""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.ini\OpenWithProgids"; ValueType: string; ValueName: "BlocDeNotasMonaco.File"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\SupportedTypes"; ValueType: string; ValueName: ".ini"; ValueData: ""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.bat\OpenWithProgids"; ValueType: string; ValueName: "BlocDeNotasMonaco.File"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\SupportedTypes"; ValueType: string; ValueName: ".bat"; ValueData: ""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.ps1\OpenWithProgids"; ValueType: string; ValueName: "BlocDeNotasMonaco.File"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\SupportedTypes"; ValueType: string; ValueName: ".ps1"; ValueData: ""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.lua\OpenWithProgids"; ValueType: string; ValueName: "BlocDeNotasMonaco.File"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\SupportedTypes"; ValueType: string; ValueName: ".lua"; ValueData: ""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.swift\OpenWithProgids"; ValueType: string; ValueName: "BlocDeNotasMonaco.File"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\SupportedTypes"; ValueType: string; ValueName: ".swift"; ValueData: ""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.dart\OpenWithProgids"; ValueType: string; ValueName: "BlocDeNotasMonaco.File"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Applications\BlocDeNotas.exe\SupportedTypes"; ValueType: string; ValueName: ".dart"; ValueData: ""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\*\shell\BlocDeNotasMonaco"; ValueType: string; ValueData: "Abrir con Bloc de Notas Monaco"; Flags: uninsdeletekey; Tasks: ctxmenu
Root: HKA; Subkey: "Software\Classes\*\shell\BlocDeNotasMonaco"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\BlocDeNotas.exe"; Tasks: ctxmenu
Root: HKA; Subkey: "Software\Classes\*\shell\BlocDeNotasMonaco\command"; ValueType: string; ValueData: """{app}\BlocDeNotas.exe"" ""%1"""; Tasks: ctxmenu
