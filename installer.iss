[Setup]
AppName=Anwari Accounts
AppVersion=1.0
DefaultDirName={autopf}\AnwariAccounts
DefaultGroupName=Anwari Accounts
OutputDir=dist\installer
OutputBaseFilename=AnwariAccountsInstaller
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\anwari_accounts\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Anwari Accounts"; Filename: "{app}\anwari_accounts.exe"
Name: "{group}\Uninstall Anwari Accounts"; Filename: "{uninstallexe}"
