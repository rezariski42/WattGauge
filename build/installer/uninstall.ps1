$ErrorActionPreference = "SilentlyContinue"

$dest = Split-Path -Parent $PSCommandPath

Get-Process pythonw -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -and $_.Path.StartsWith($dest)
} | Stop-Process -Force

Remove-Item -Force (Join-Path ([Environment]::GetFolderPath("Desktop")) "WattGauge.lnk")
Remove-Item -Force (Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\WattGauge.lnk")
Remove-Item -Recurse -Force "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\WattGauge"

$appData = Join-Path $env:APPDATA "WattGauge"
if (Test-Path $appData) {
    Remove-Item -Recurse -Force $appData
}

Set-Location $env:TEMP
Remove-Item -Recurse -Force $dest