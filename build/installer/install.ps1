param(
    [Parameter(Mandatory = $true)][string]$Src,
    [Parameter(Mandatory = $true)][string]$Dest
)

$ErrorActionPreference = "Stop"

Write-Host "Memasang WattGauge ke $Dest ..."

if (Test-Path $Dest) {
    Remove-Item -Recurse -Force $Dest
}
New-Item -ItemType Directory -Force -Path $Dest | Out-Null
Copy-Item -Path (Join-Path $Src "*") -Destination $Dest -Recurse -Force

$exe = Join-Path $Dest "python\pythonw.exe"
$app = Join-Path $Dest "app\main.py"
$icon = Join-Path $Dest "app\assets\icon.ico"

# uninstaller
Copy-Item -Path (Join-Path $PSScriptRoot "uninstall.ps1") -Destination (Join-Path $Dest "uninstall.ps1") -Force

function New-Shortcut([string]$Path) {
    $shell = New-Object -ComObject WScript.Shell
    $lnk = $shell.CreateShortcut($Path)
    $lnk.TargetPath = $exe
    $lnk.Arguments = "`"$app`""
    $lnk.WorkingDirectory = $Dest
    $lnk.IconLocation = $icon
    $lnk.Description = "WattGauge - PC power usage & PLN cost monitor"
    $lnk.Save()
}

$desktop = [Environment]::GetFolderPath("Desktop")
New-Shortcut (Join-Path $desktop "WattGauge.lnk")

$startMenu = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
New-Shortcut (Join-Path $startMenu "WattGauge.lnk")

# Add/Remove Programs entry
$uninstallKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\WattGauge"
New-Item -Path $uninstallKey -Force | Out-Null
Set-ItemProperty -Path $uninstallKey -Name "DisplayName" -Value "WattGauge"
Set-ItemProperty -Path $uninstallKey -Name "DisplayIcon" -Value $icon
Set-ItemProperty -Path $uninstallKey -Name "DisplayVersion" -Value "1.0.0"
Set-ItemProperty -Path $uninstallKey -Name "Publisher" -Value "Reza"
Set-ItemProperty -Path $uninstallKey -Name "InstallLocation" -Value $Dest
Set-ItemProperty -Path $uninstallKey -Name "UninstallString" `
    -Value "powershell -ExecutionPolicy Bypass -File `"$Dest\uninstall.ps1`""
Set-ItemProperty -Path $uninstallKey -Name "NoModify" -Value 1 -Type DWord
Set-ItemProperty -Path $uninstallKey -Name "NoRepair" -Value 1 -Type DWord

Write-Host "Selesai. Menjalankan WattGauge ..."
Start-Process -FilePath $exe -ArgumentList "`"$app`"" -WorkingDirectory $Dest