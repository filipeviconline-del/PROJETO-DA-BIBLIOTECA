; Script do instalador do ToschiBook para Windows (Inno Setup)
; -----------------------------------------------------------------
; Pré-requisitos:
;   1. Gerar o executável antes:  python build.py
;      (isso cria dist\ToschiBook.exe)
;   2. Instalar o Inno Setup: https://jrsoftware.org/isdl.php
;   3. Abrir este arquivo no Inno Setup e clicar em "Compile" (ou
;      rodar:  iscc instalador.iss ), gerando o instalador final em
;      Output\ToschiBook-Setup.exe
; -----------------------------------------------------------------

#define NomeApp "ToschiBook"
#define VersaoApp "1.0.0"
#define Publicadora "ToschiBook"
#define ExeApp "ToschiBook.exe"

[Setup]
AppId={{B7A3F1E2-9C4D-4A6B-8E2F-TOSCHIBOOK01}
AppName={#NomeApp}
AppVersion={#VersaoApp}
AppPublisher={#Publicadora}
DefaultDirName={autopf}\{#NomeApp}
DefaultGroupName={#NomeApp}
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename={#NomeApp}-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=html\favicon.ico
UninstallDisplayIcon={app}\{#ExeApp}
; Instalação por usuário não exige privilégios de administrador.
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar um atalho na área de trabalho"; GroupDescription: "Atalhos:"

[Files]
; Executável gerado pelo PyInstaller (modo one-file).
Source: "dist\{#ExeApp}"; DestDir: "{app}"; Flags: ignoreversion
; Caso o build seja em modo "one-folder", descomente a linha abaixo:
; Source: "dist\{#NomeApp}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{group}\{#NomeApp}"; Filename: "{app}\{#ExeApp}"
Name: "{group}\Desinstalar {#NomeApp}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#NomeApp}"; Filename: "{app}\{#ExeApp}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#ExeApp}"; Description: "Iniciar o {#NomeApp} agora"; Flags: nowait postinstall skipifsilent
