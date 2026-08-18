; ImageBatch Pro Windows 安装包配置
; 用法：安装 Inno Setup 6 后，打开此文件编译即可生成安装包
; 下载 Inno Setup: https://jrsoftware.org/isdl.php

#define MyAppName "ImageBatch Pro"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "ImageBatch Pro"
#define MyAppExeName "ImageBatch-Pro.exe"
#define MyAppURL "https://gitee.com/yourname/imagebatch-pro"

[Setup]
AppId={{B8F3A2E1-1234-5678-9ABC-DEF012345678}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=release
OutputBaseFilename=ImageBatch-Pro-Setup-v{#MyAppVersion}
; 如有图标文件取消下一行注释（需先放置 assets\icons\icon_256x256.ico）
; SetupIconFile=assets\icons\icon_256x256.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
ArchitecturesAllowed=x64
PrivilegesRequired=lowest

; 如需数字签名，取消注释并配置证书
; SignTool=signtool
; SignedInstaller=yes

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加图标:"; Flags: unchecked
Name: "quicklaunchicon"; Description: "创建快速启动栏图标"; GroupDescription: "附加图标:"; Flags: unchecked

[Files]
; 主程序（单文件 exe）
Source: "dist\ImageBatch-Pro.exe"; DestDir: "{app}"; Flags: ignoreversion

; 预设模板
Source: "assets\presets\*.json"; DestDir: "{app}\assets\presets"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "立即运行 {#MyAppName}"; Flags: postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
