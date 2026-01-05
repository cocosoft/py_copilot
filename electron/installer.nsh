; Py Copilot 安装程序脚本
; 基于 NSIS 3.08

; 包含必要的头文件
!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "WordFunc.nsh"

; 定义变量
!define APP_NAME "Py Copilot"
!define APP_VERSION "1.0.0"
!define APP_PUBLISHER "Py Copilot Team"
!define APP_URL "https://pycopilot.com"
!define APP_EXECUTABLE "Py Copilot.exe"
!define APP_DESKTOP_SHORTCUT_NAME "Py Copilot"
!define APP_START_MENU_SHORTCUT_NAME "Py Copilot"

; 安装程序设置
Name "${APP_NAME} ${APP_VERSION}"
OutFile "..\release\Py Copilot-${APP_VERSION}-Setup.exe"
InstallDir "$PROGRAMFILES\${APP_NAME}"
InstallDirRegKey HKCU "Software\${APP_NAME}" ""
RequestExecutionLevel admin

; 界面设置
!define MUI_ABORTWARNING
!define MUI_ICON "..\icons\icon.ico"
!define MUI_UNICON "..\icons\icon.ico"
!define MUI_WELCOMEFINISHPAGE_BITMAP "installer-welcome.bmp"
!define MUI_FINISHPAGE_BITMAP "installer-finish.bmp"
!define MUI_FINISHPAGE_RUN_TEXT "启动 ${APP_NAME}"
!define MUI_FINISHPAGE_RUN "$INSTDIR\${APP_EXECUTABLE}"

; 页面
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; 语言
!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_LANGUAGE "English"

; 安装程序部分
Section "MainSection" SEC01
  SetOutPath "$INSTDIR"
  SetOverwrite on
  
  ; 复制主要文件
  File "main.js"
  File "preload.js"
  
  ; 复制构建后的前端文件
  File /r "..\frontend\dist"
  
  ; 复制公共资源
  File /r "..\frontend\public"
  
  ; 创建卸载程序
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  
  ; 注册表项
  WriteRegStr HKCU "Software\${APP_NAME}" "" $INSTDIR
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayName" "${APP_NAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayIcon" "$INSTDIR\${APP_EXECUTABLE}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "Publisher" "${APP_PUBLISHER}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "URLInfoAbout" "${APP_URL}"
  
  ; 32位系统兼容性
  ${If} ${RunningX64}
    WriteRegStr HKLM "Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayIcon" "$INSTDIR\${APP_EXECUTABLE}"
    WriteRegStr HKLM "Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayVersion" "${APP_VERSION}"
    WriteRegStr HKLM "Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "Publisher" "${APP_PUBLISHER}"
    WriteRegStr HKLM "Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "URLInfoAbout" "${APP_URL}"
  ${EndIf}
  
  ; 创建桌面快捷方式
  CreateShortcut "$DESKTOP\${APP_DESKTOP_SHORTCUT_NAME}.lnk" "$INSTDIR\${APP_EXECUTABLE}" "" "$INSTDIR\${APP_EXECUTABLE}" 0
  
  ; 创建开始菜单快捷方式
  CreateDirectory "$SMPROGRAMS\${APP_START_MENU_SHORTCUT_NAME}"
  CreateShortcut "$SMPROGRAMS\${APP_START_MENU_SHORTCUT_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXECUTABLE}"
  CreateShortcut "$SMPROGRAMS\${APP_START_MENU_SHORTCUT_NAME}\卸载 ${APP_NAME}.lnk" "$INSTDIR\Uninstall.exe"
  
  ; 添加到PATH环境变量（可选）
  ReadRegStr $R0 HKCU "Environment" "PATH"
  StrCmp $R0 "" NoAddToPath
  StrCmp $R0 "$INSTDIR;" NoAddToPath
  StrCpy $R0 "$R0;$INSTDIR"
  WriteRegStr HKCU "Environment" "PATH" $R0
  NoAddToPath:
SectionEnd

; 卸载部分
Section "Uninstall"
  ; 删除文件
  RMDir /r "$INSTDIR"
  
  ; 删除注册表项
  DeleteRegKey HKCU "Software\${APP_NAME}"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
  ${If} ${RunningX64}
    DeleteRegKey HKLM "Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
  ${EndIf}
  
  ; 删除快捷方式
  Delete "$DESKTOP\${APP_DESKTOP_SHORTCUT_NAME}.lnk"
  RMDir /r "$SMPROGRAMS\${APP_START_MENU_SHORTCUT_NAME}"
  
  ; 从PATH中移除（可选）
  ReadRegStr $R0 HKCU "Environment" "PATH"
  StrCpy $R1 "$INSTDIR;"
  ${WordReplace} $R0 $R1 "" $R2
  WriteRegStr HKCU "Environment" "PATH" $R2
SectionEnd

; 函数定义
Function .onInit
  ; 检查是否已经安装
  ReadRegStr $R0 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString"
  StrCmp $R0 "" done
  
  MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION "检测到 ${APP_NAME} 已经安装。$\n$\n点击确定继续安装（将覆盖现有安装），或点击取消退出安装。" IDOK uninst
  
  ; 运行卸载程序
  ClearErrors
  ExecWait '$R0 _?=$INSTDIR'
  IfErrors no_remove_uninstaller done
  
  ; 删除卸载程序
  Delete "$INSTDIR\Uninstall.exe"
  no_remove_uninstaller:
  
  uninst:
  done:
FunctionEnd