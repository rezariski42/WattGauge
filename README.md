# WattGauge

Monitor daya PC real-time + estimasi biaya listrik PLN untuk Windows 10/11.

**[⬇ Download WattGauge 1.1.0 (Windows 64-bit, 64 MB)](https://github.com/rezariski42/WattGauge/releases/download/v1.1.0/WattGauge-1.1.0-win64.zip)** — ekstrak zip, jalankan `WattGauge-Setup-1.1.0.exe`. Tidak perlu install Python.
Python + PyQt6 (QML UI), dikemas jadi installer yang **tidak butuh Python terpasang** —
runtime Python 3.12 + PyQt6 sudah dibundel di dalam installer.

## Fitur

- Total konsumsi watt real-time, dijabarkan per komponen (CPU, RAM, GPU/Display, mobo, fan, RGB, storage).
- CPU watt dibaca dari sensor (LibreHardwareMonitor / RAPL via LHM); kalau sensor tidak ada,
  nilai dihitung dari load x TDP dan diberi label *estimasi*.
- GPU terdeteksi otomatis lewat `nvidia-smi` (tidak ada GPU = tile GPU tidak ditampilkan).
- Riwayat jam aktif PC per hari (Senin–Minggu) tersimpan permanen di SQLite `%APPDATA%\WattGauge\history.db`.
- Estimasi kWh dan biaya Rp (tarif PLN bisa diubah di Pengaturan).
- Top bar mini selalu di atas (pojok kanan bawah, di atas taskbar) berisi watt + Rp/jam.
- Tray icon + tooltip + judul window menampilkan watt berjalan.
- Jendela bisa di-resize/di-scale (ukuran terakhir diingat).
- **Autostart default ON**: aplikasi otomatis jalan saat Windows booting, bisa dimatikan di Pengaturan.
- Riwayat jam PC, rata-rata harian otomatis, mode "24 Jam Non-Stop" atau rata-rata.

## Instalasi

1. Unduh `dist/WattGauge-Setup-1.1.0.exe`.
2. Jalankan (per-user, tidak perlu admin).
3. Wizard: Next → Install → Finish (aplikasi langsung terbuka).

Install ke `%LOCALAPPDATA%\Programs\WattGauge`, membuat shortcut Desktop + Start Menu,
entri uninstall di *Apps & features*, dan entri autostart di
`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`.

Autostart bisa dimatikan kapan saja: buka Pengaturan (ikon gear atau `Ctrl+,`)
→ bagian STARTUP → hilangkan centang "Autostart saat Windows nyala" → SIMPAN.

## Pintasan

| Tombol | Aksi |
| --- | --- |
| `Ctrl+,` | Buka Pengaturan |
| `Ctrl+Q` | Keluar |
| Tarik sudut kanan bawah | Resize / scale UI |

## Build dari source

Butuh Linux atau Windows dengan NSIS 3.x. Runtime Windows diambil dari paket NuGet `python`
(portable Python 3.12.8), plus wheel PyQt6/psutil win_amd64.

```bash
cd build
# stage payload: build/stage/WattGauge/{python,app}
NSISDIR=$PWD/nsis/usr/share/nsis ./nsis/usr/bin/makensis installer/installer.nsi
```

Hasil: `build/WattGauge-Setup.exe`.

## Struktur

```
app/
  main.py                 entry point, tray, top bar, --selftest
  engine.py               sampler thread, snapshot, biaya, autostart, window size
  config.py               config JSON di %APPDATA%\WattGauge
  history.py              SQLite riwayat harian + rata-rata
  telemetry/windows.py    collector Windows (LHM WMI, nvidia-smi, CIM)
  telemetry/linux.py      collector Linux (RAPL, nvidia-smi) untuk dev
  qml/Main.qml            dashboard
  qml/Settings.qml        pengaturan
  qml/TopBar.qml          mini bar always-on-top
build/installer/installer.nsi
dist/WattGauge-Setup-1.1.0.exe
```

## Catatan akurasi

Di VM tanpa GPU/passthrough, watt bersifat estimasi. Angka sensor asli (CPU package power,
GPU power draw) hanya muncul saat dijalankan langsung di PC fisik dengan
LibreHardwareMonitor (WMI) atau driver NVIDIA.