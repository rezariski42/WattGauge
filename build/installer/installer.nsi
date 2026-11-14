Unicode true

!include "MUI2.nsh"

VIProductVersion "1.2.0.0"
VIAddVersionKey "ProductName" "WattGauge"
VIAddVersionKey "FileDescription" "WattGauge installer — monitor daya PC & biaya PLN"
VIAddVersionKey "FileVersion" "1.2.0.0"
VIAddVersionKey "ProductVersion" "1.2.0"
VIAddVersionKey "CompanyName" "Reza"
VIAddVersionKey "LegalCopyright" "Reza"

Name "WattGauge"
OutFile "/home/reza/wattgauge-win/build/WattGauge-Setup.exe"
!define STAGE "/home/reza/wattgauge-win/build/stage/WattGauge"
InstallDir "$LOCALAPPDATA\Programs\WattGauge"
InstallDirRegKey HKCU "Software\WattGauge" "InstallDir"
RequestExecutionLevel user
SetCompressor /SOLID lzma
SetCompressorDictSize 32
SetDatablockOptimize on
CRCCheck on
XPStyle on

!define MUI_ICON "${STAGE}/app/assets/icon.ico"
!define MUI_UNICON "${STAGE}/app/assets/icon.ico"
!define MUI_ABORTWARNING
!define MUI_WELCOMEPAGE_TITLE "WattGauge — Monitor Daya PC & Biaya PLN"
!define MUI_WELCOMEPAGE_TEXT "Aplikasi ini memasang WattGauge: monitor konsumsi daya PC real-time, riwayat jam aktif harian (Senin–Minggu) tersimpan di database, dan estimasi biaya listrik PLN.$\r$\n$\r$\nInstalasi per-user, tidak butuh admin."
!define MUI_FINISHPAGE_RUN "$INSTDIR\python\pythonw.exe"
!define MUI_FINISHPAGE_RUN_PARAMETERS "$\"$INSTDIR\app\main.py$\""
!define MUI_FINISHPAGE_RUN_TEXT "Jalankan WattGauge sekarang"
!define MUI_FINISHPAGE_SHOWREADME ""
!define MUI_FINISHPAGE_SHOWREADME_NOTCHECKED

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "Indonesian"

Section "Install"
    SetOutPath "$INSTDIR"
    SetOverwrite on
    File /r "${STAGE}/*.*"

    WriteRegStr HKCU "Software\WattGauge" "InstallDir" "$INSTDIR"

    ; autostart on boot (per-user, no admin)
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "WattGauge" '$\"$INSTDIR\python\pythonw.exe$\" $\"$INSTDIR\app\main.py$\"' 

    CreateDirectory "$SMPROGRAMS"
    CreateShortCut "$SMPROGRAMS\WattGauge.lnk" "$INSTDIR\python\pythonw.exe" "$\"$INSTDIR\app\main.py$\"" "$INSTDIR\app\assets\icon.ico" 0 SW_SHOWNORMAL "" "Monitor daya PC & biaya PLN"
    CreateShortCut "$DESKTOP\WattGauge.lnk" "$INSTDIR\python\pythonw.exe" "$\"$INSTDIR\app\main.py$\"" "$INSTDIR\app\assets\icon.ico" 0 SW_SHOWNORMAL "" "Monitor daya PC & biaya PLN"

    WriteUninstaller "$INSTDIR\Uninstall.exe"

    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WattGauge" "DisplayName" "WattGauge"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WattGauge" "DisplayIcon" "$INSTDIR\app\assets\icon.ico"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WattGauge" "DisplayVersion" "1.2.0"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WattGauge" "Publisher" "Reza"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WattGauge" "InstallLocation" "$INSTDIR"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WattGauge" "UninstallString" "$\"$INSTDIR\Uninstall.exe$\""
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WattGauge" "NoModify" 1
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WattGauge" "NoRepair" 1
SectionEnd

Section "Uninstall"
    Delete "$DESKTOP\WattGauge.lnk"
    Delete "$SMPROGRAMS\WattGauge.lnk"

    DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "WattGauge"
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WattGauge"
    DeleteRegKey HKCU "Software\WattGauge"

    MessageBox MB_YESNO "Hapus juga riwayat pemakaian dan pengaturan WattGauge?" IDNO +2
    RMDir /r "$APPDATA\WattGauge"

    RMDir /r "$INSTDIR"
SectionEnd