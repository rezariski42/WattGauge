@echo off
setlocal
set "SRC=%~dp0WattGauge"
set "DEST=%LOCALAPPDATA%\Programs\WattGauge"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" -Src "%SRC%" -Dest "%DEST%"
if errorlevel 1 (
  echo.
  echo Instalasi gagal. Tekan tombol apa saja untuk menutup.
  pause >nul
)
endlocal