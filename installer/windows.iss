; Small online installer. The app download is pinned to a verified release hash.
#include "payload.iss"

[Setup]
AppId={{D28EFED5-ED17-4DCC-AB98-D18B68C78BF8}
AppName=Pumpkin Patch
AppVersion=1.0.0
AppPublisher=BugByteDev
DefaultDirName={localappdata}\Programs\Pumpkin Patch
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
DisableDirPage=yes
DisableProgramGroupPage=yes
DisableWelcomePage=no
WizardStyle=modern
SetupIconFile=..\assets\icons\pumpkin-patch.ico
UninstallDisplayName=Pumpkin Patch
UninstallDisplayIcon={app}\Pumpkin Patch.exe
OutputDir=..\installer-output
OutputBaseFilename=Pumpkin-Patch-Setup
Compression=lzma2
SolidCompression=yes
ArchiveExtraction=full
ExtraDiskSpaceRequired=300000000
CloseApplications=yes
RestartApplications=no
Uninstallable=yes

[Messages]
WelcomeLabel1=Welcome to Pumpkin Patch
WelcomeLabel2=Make your own pumpkins with scary faces, goofy grins, and your own carvings.%n%nSetup will download and install Pumpkin Patch. You need an internet connection during setup.%n%nClick Next to get started.
FinishedHeadingLabel=Pumpkin Patch is ready!
FinishedLabel=You can open Pumpkin Patch from the shortcut on your desktop or the Start menu.

[Files]
Source: "{tmp}\payload\Pumpkin Patch\*"; DestDir: "{app}"; Flags: external ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userprograms}\Pumpkin Patch"; Filename: "{app}\Pumpkin Patch.exe"; WorkingDir: "{app}"
Name: "{userdesktop}\Pumpkin Patch"; Filename: "{app}\Pumpkin Patch.exe"; WorkingDir: "{app}"

[Run]
Filename: "{app}\Pumpkin Patch.exe"; Description: "Open Pumpkin Patch"; Flags: nowait postinstall skipifsilent

[Code]
var
  DownloadPage: TDownloadWizardPage;

procedure InitializeWizard;
begin
  DownloadPage := CreateDownloadPage('Downloading Pumpkin Patch', 'Your pumpkin patch is on its way. Please keep your internet connected.', nil);
  DownloadPage.ShowBaseNameInsteadOfUrl := True;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  DownloadPage.Clear;
  DownloadPage.Add('{#PayloadURL}', 'Pumpkin-Patch.zip', '{#PayloadSHA256}');
  DownloadPage.Show;
  try
    try
      DownloadPage.Download;
      DownloadPage.SetText('Unpacking Pumpkin Patch', 'Almost ready. This may take a moment.');
      ExtractArchive(ExpandConstant('{tmp}\Pumpkin-Patch.zip'), ExpandConstant('{tmp}\payload'), '', True, nil);
    except
      if DownloadPage.AbortedByUser then
        Result := 'The download was cancelled. Click Install to try again.'
      else
        Result := 'Pumpkin Patch could not finish downloading. Check your internet connection and click Install to try again.' + #13#10 + GetExceptionMessage;
    end;
  finally
    DownloadPage.Hide;
  end;
end;
