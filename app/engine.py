"""Qt-facing engine: owns the collector, history DB and cost projections."""
from __future__ import annotations

import sys
import time
from concurrent.futures import ThreadPoolExecutor

from PyQt6.QtCore import QObject, QTimer, pyqtProperty, pyqtSignal, pyqtSlot

import config
import history as history_mod
from telemetry import make_collector

TEXT = {
    "en": {
        "hours_assumed": "8 h/day assumed",
        "hours_active": "{v} h/day active",
        "basis_24": "24 h/day",
        "basis_assumed": "8 h/day assumed, low data",
        "basis_actual": "{v} h/day actual",
        "src_estimate": "ESTIMATE",
        "src_real": "REAL SENSOR",
        "src_partial": "{n}/{m} SENSOR",
        "per_hour": "Rp {v}/hr",
        "session": "{kwh} kWh session",
        "waiting": "waiting for data",
        "checking": "Checking...",
        "up_to_date": "You are on the latest version",
        "update_available": "New version {v} available",
        "update_failed": "Update check failed",
    },
    "id": {
        "hours_assumed": "asumsi 8 j/hari",
        "hours_active": "{v} j/hari aktif",
        "basis_24": "24 jam/hari",
        "basis_assumed": "asumsi 8 jam/hari, data kurang",
        "basis_actual": "{v} jam/hari aktual",
        "src_estimate": "ESTIMASI",
        "src_real": "SENSOR REAL",
        "src_partial": "{n}/{m} SENSOR",
        "per_hour": "Rp {v}/jam",
        "session": "{kwh} kWh sesi",
        "waiting": "menunggu data",
        "checking": "Memeriksa...",
        "up_to_date": "Sudah versi terbaru",
        "update_available": "Versi baru {v} tersedia",
        "update_failed": "Gagal cek update",
    },
}


class PowerEngine(QObject):
    dataChanged = pyqtSignal()
    configChanged = pyqtSignal()
    # Worker thread -> GUI thread hand-off. Emitted from the collector thread so
    # Qt delivers it queued: every field the UI reads is written on the GUI
    # thread, which keeps totalWatt and components from the same snapshot.
    snapshotReady = pyqtSignal(object)
    updateReady = pyqtSignal(object)

    def __init__(self, cfg=None):
        super().__init__()
        self.cfg = cfg or config.Config()
        self.history = history_mod.History()
        self.collector = make_collector(self.cfg)
        self.pool = ThreadPoolExecutor(max_workers=1)
        self._busy = False

        self._sanitize_config()
        lang = str(self.cfg.get("ui", "language", default="en") or "en").lower()
        self._language = lang if lang in ("en", "id") else "en"
        self._settings_cache = {}
        self._update_status = ""
        self._update_checking = False
        self.updateReady.connect(self._apply_update)
        self._snapshot = None
        self._components: list[dict] = []
        self._total = 0.0
        self._session_kwh = 0.0
        self._selected_days = int(self.cfg.get("history_days", default=30) or 30)
        self._use_smart = bool(self.cfg.get("use_smart_hours", default=True))
        self._tariff = float(self.cfg.get("tariff_per_kwh", default=1444.7) or 1444.7)
        self._cost_formatted = "Rp 0"
        self._kwh_projected = 0.0
        self._avg_hours = 0.0
        self._hours_per_day = 0.0
        self._estimated_hours = 0.0
        self._active_days = 0
        self._assumed_hours = False
        self._weekday_stats: list[dict] = []
        self._last_tick = time.monotonic()
        self._cpu_name = ""
        self._gpu_summary = ""
        self._ram_total = 0.0
        self._disk_count = 0
        self._sensor_count = 0
        self._component_count = 0

        self._settings_cache = self._build_settings()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.tick)
        self.snapshotReady.connect(self._apply_snapshot)
        self._timer.start(1000)
        self.tick()

    def _sanitize_config(self):
        """Clamp hand-edited/corrupt config values to plausible ranges."""
        d = self.cfg.data
        limits = (
            ("fans", "count", 0, 16, int),
            ("fans", "watt_each", 0.0, 5.0, float),
            ("fans", "pump_watt", 0.0, 25.0, float),
            ("rgb", "leds", 0, 150, int),
            ("rgb", "watt_each", 0.0, 1.0, float),
            ("mobo", "base_watt", 0.0, 40.0, float),
        )
        changed = False
        # Schema bump: older builds wrote locale-mangled values (1.5 -> 15).
        if d.get("settings_schema") != 2:
            for section, key, lo, hi, cast in limits:
                block = d.get(section)
                if not isinstance(block, dict):
                    block = {}
                    d[section] = block
                block[key] = cast(config.DEFAULTS.get(section, {}).get(key, lo))
            d["settings_schema"] = 2
            changed = True
        for section, key, lo, hi, cast in limits:
            block = d.get(section)
            if not isinstance(block, dict):
                block = {}
                d[section] = block
                changed = True
            default = cast(config.DEFAULTS.get(section, {}).get(key, lo))
            try:
                raw = cast(block.get(key, default))
            except (TypeError, ValueError):
                raw = default
            if key not in block:
                block[key] = default
                changed = True
            elif not (lo <= raw <= hi):
                block[key] = default
                changed = True
        if changed:
            try:
                self.cfg.save()
            except Exception:
                pass

    # ---------------- scheduling ----------------
    def tick(self):
        now = time.monotonic()
        dt = max(0.0, min(5.0, now - self._last_tick))
        self._last_tick = now
        if self._snapshot is not None and dt > 0:
            self._session_kwh += self._total * dt / 3_600_000.0
            self.history.add_sample(self._total, dt)
        self._refresh_async()
        self._recompute()
        self.dataChanged.emit()

    def _refresh_async(self):
        if self._busy:
            return
        self._busy = True

        def work():
            try:
                return self.collector.collect()
            except Exception:
                return None

        fut = self.pool.submit(work)

        def deliver(done):
            try:
                self.snapshotReady.emit(done)
            except RuntimeError:
                pass  # engine already torn down at exit

        fut.add_done_callback(deliver)

    def _apply_snapshot(self, fut):
        try:
            snap = fut.result()
        except Exception:
            snap = None
        if snap is not None:
            self._snapshot = snap
            self._components = [c.as_dict() for c in snap.components]
            self._total = snap.total_watt
            self._cpu_name = snap.cpu_name
            self._ram_total = snap.ram_total_gb
            self._disk_count = snap.disk_count
            self._component_count = len(snap.components)
            self._sensor_count = sum(1 for c in snap.components if c.source == "sensor")
            if snap.gpu_names:
                self._gpu_summary = " + ".join(
                    n.split("(")[0].strip() for n in snap.gpu_names[:2])
            else:
                self._gpu_summary = ""
            self.dataChanged.emit()
        self._busy = False

    def _recompute(self):
        raw_avg = self.history.avg_daily_hours(7)
        self._avg_hours = raw_avg if raw_avg >= 0.5 else 0.0
        self._weekday_stats = self.history.weekday_stats()
        hours_per_day = self._avg_hours if self._use_smart else 24.0
        self._assumed_hours = False
        if self._use_smart and hours_per_day <= 0:
            hours_per_day = 8.0
            self._assumed_hours = True
        self._hours_per_day = hours_per_day
        self._active_days = int(self.history.active_days(7))
        self._estimated_hours = round(self._selected_days * hours_per_day, 1)
        self._kwh_projected = round(self._total * self._selected_days * hours_per_day / 1000.0, 2)
        cost = round(self._kwh_projected * self._tariff)
        self._cost_formatted = self._rp(cost)

    # ---------------- properties ----------------
    @pyqtProperty(float, notify=dataChanged)
    def totalWatt(self):
        return self._total

    @pyqtProperty("QVariantList", notify=dataChanged)
    def components(self):
        return self._components

    @pyqtProperty("QVariantList", notify=dataChanged)
    def weekdayStats(self):
        return self._weekday_stats

    @pyqtProperty(float, notify=dataChanged)
    def avgDailyHours(self):
        return round(self._avg_hours, 1)

    @pyqtProperty(float, notify=dataChanged)
    def hoursPerDay(self):
        return float(self._hours_per_day)

    @pyqtProperty(float, notify=dataChanged)
    def estimatedHours(self):
        return float(self._estimated_hours)

    @pyqtProperty(int, notify=dataChanged)
    def activeDays(self):
        return int(self._active_days)

    # ---------------- i18n helpers ----------------
    def _t(self, key, **kw):
        table = TEXT.get(self._language, TEXT["en"])
        text = table.get(key, TEXT["en"].get(key, key))
        return text.format(**kw) if kw else text

    def _rp(self, value):
        txt = "{:,.0f}".format(value)
        return "Rp " + (txt.replace(",", ".") if self._language == "id" else txt)

    @pyqtProperty(str, notify=dataChanged)
    def hoursLabel(self):
        # Always describes the average-hours estimate, independent of which
        # mode is selected (the 24h button has its own fixed subtitle).
        if self._assumed_hours:
            return self._t("hours_assumed")
        return self._t("hours_active", v="{:.1f}".format(self._avg_hours))

    @pyqtProperty(str, notify=dataChanged)
    def avgNote(self):
        if not self._use_smart:
            return self._t("basis_24") + " · " + str(self._selected_days)
        if self._assumed_hours:
            return self._t("basis_assumed")
        return self._t("basis_actual", v="{:.1f}".format(self._avg_hours))

    @pyqtProperty(float, notify=dataChanged)
    def costFormatted(self):
        return self._cost_formatted

    @pyqtProperty(str, notify=dataChanged)
    def costText(self):
        return self._cost_formatted

    @pyqtProperty(str, notify=dataChanged)
    def costPerHour(self):
        per_hour = round(self._total / 1000.0 * self._tariff)
        return self._t("per_hour", v="{:,.0f}".format(per_hour).replace(",", "." if self._language == "id" else ","))

    @pyqtProperty(str, notify=dataChanged)
    def taskbarText(self):
        return "WattGauge · {:.0f} W · {}".format(self._total, self.costPerHour)

    @pyqtProperty(float, notify=dataChanged)
    def kwhProjected(self):
        return self._kwh_projected

    @pyqtProperty(float, notify=dataChanged)
    def kwhSession(self):
        return round(self._session_kwh, 3)

    @pyqtProperty(float, notify=dataChanged)
    def tariff(self):
        return self._tariff

    @pyqtProperty(int, notify=dataChanged)
    def selectedDays(self):
        return self._selected_days

    @pyqtProperty(bool, notify=dataChanged)
    def useSmartHours(self):
        return self._use_smart

    @pyqtProperty(str, notify=dataChanged)
    def uptimeText(self):
        sec = 0
        if self._snapshot is not None:
            sec = self._snapshot.uptime_sec
        return f"{sec // 3600}h {(sec % 3600) // 60:02d}m"

    @pyqtProperty(str, notify=dataChanged)
    def cpuName(self):
        return self._cpu_name

    @pyqtProperty(str, notify=dataChanged)
    def gpuSummary(self):
        return self._gpu_summary

    @pyqtProperty(float, notify=dataChanged)
    def ramTotal(self):
        return self._ram_total

    @pyqtProperty(int, notify=dataChanged)
    def diskCount(self):
        return self._disk_count

    @pyqtProperty(int, notify=dataChanged)
    def sensorCount(self):
        return self._sensor_count

    @pyqtProperty(int, notify=dataChanged)
    def componentCount(self):
        return self._component_count

    @pyqtProperty(str, notify=dataChanged)
    def sourceLabel(self):
        if self._sensor_count == 0:
            return self._t("src_estimate")
        if self._sensor_count == self._component_count:
            return self._t("src_real")
        return self._t("src_partial", n=self._sensor_count, m=self._component_count)

    @pyqtProperty(str, notify=dataChanged)
    def basisNote(self):
        if not self._use_smart:
            return self._t("basis_24")
        if self._assumed_hours:
            return self._t("basis_assumed")
        return self._t("basis_actual", v="{:.1f}".format(self._avg_hours))

    @pyqtProperty(str, notify=dataChanged)
    def modeLabel(self):
        return "Mode: Rata-rata Jam" if self._use_smart else "Mode: 24 Jam Non-Stop"

    @pyqtProperty(str, notify=dataChanged)
    def summaryChips(self):
        chips = []
        if self._gpu_summary:
            chips.append(self._gpu_summary)
        if self._ram_total:
            chips.append(f"{self._ram_total:.0f} GB RAM")
        if self._disk_count:
            chips.append(f"{self._disk_count} Disk")
        return " · ".join(chips)

    def _build_settings(self):
        cfg = self.cfg.data
        return {
            "tariff": float(cfg.get("tariff_per_kwh", 1444.7)),
            "display1": float(cfg.get("displays", [{}])[0].get("max_watt", 45.0)),
            "display2": float(cfg.get("displays", [{}, {}])[1].get("max_watt", 35.0)),
            "display2Enabled": bool(cfg.get("displays", [{}, {}])[1].get("enabled", False)),
            "fans": int(cfg.get("fans", {}).get("count", 6)),
            "fanWatt": float(cfg.get("fans", {}).get("watt_each", 1.5)),
            "pump": bool(cfg.get("fans", {}).get("aio_pump", True)),
            "pumpWatt": float(cfg.get("fans", {}).get("pump_watt", 6.0)),
            "leds": int(cfg.get("rgb", {}).get("leds", 24)),
            "ledWatt": float(cfg.get("rgb", {}).get("watt_each", 0.3)),
            "autostart": self.autostart,
            "topbar": bool(cfg.get("topbar", {}).get("enabled", True)),
            "language": self._language,
            "closeToTray": bool(cfg.get("ui", {}).get("close_to_tray", True)),
            "tariffPreset": str(cfg.get("tariff_preset", "") or ""),
            "version": config.APP_VERSION,
        }

    def _emit_config(self):
        # Rebuild the map first: handing out a fresh QVariantMap per access
        # crashes when the UI reads it from more than one binding.
        try:
            self._settings_cache = self._build_settings()
        except Exception:
            pass
        self.configChanged.emit()

    @pyqtProperty("QVariantMap", notify=configChanged)
    def settings(self):
        return self._settings_cache

    @pyqtProperty(str, notify=configChanged)
    def language(self):
        return self._language

    @pyqtProperty(str, notify=configChanged)
    def appVersion(self):
        return config.APP_VERSION

    @pyqtProperty(str, notify=configChanged)
    def githubUrl(self):
        return "https://github.com/" + config.GITHUB_REPO

    @pyqtProperty(str, notify=configChanged)
    def releasesUrl(self):
        return "https://github.com/" + config.GITHUB_REPO + "/releases/latest"

    @pyqtProperty(str, notify=configChanged)
    def tariffPresetName(self):
        return str(self.cfg.get("tariff_preset", default="") or "")

    @pyqtProperty(str, notify=configChanged)
    def updateStatus(self):
        return self._update_status

    @pyqtSlot(str, result=str)
    def label(self, key):
        return self._t(str(key))

    # ---------------- slots ----------------
    @pyqtSlot(str)
    def setLanguage(self, lang):
        lang = str(lang).lower()
        if lang not in ("en", "id") or lang == self._language:
            return
        self._language = lang
        self.cfg.set(lang, "ui", "language")
        self._recompute()
        self._emit_config()
        self.dataChanged.emit()

    @pyqtSlot(bool)
    def saveCloseToTray(self, enabled):
        self.cfg.set(bool(enabled), "ui", "close_to_tray")
        self._emit_config()

    @pyqtSlot(str, float)
    def setTariffPreset(self, name, price):
        self.cfg.set(str(name), "tariff_preset")
        self.setTariff(float(price))
        self._emit_config()

    @pyqtSlot(str)
    def openUrl(self, url):
        url = str(url)
        if not url.startswith("https://github.com/"):
            return
        import webbrowser
        try:
            webbrowser.open(url)
        except Exception:
            pass

    @pyqtSlot()
    def checkUpdate(self):
        if self._update_checking:
            return
        self._update_checking = True
        self._update_status = self._t("checking")
        self._emit_config()

        def work():
            import json
            import urllib.request
            url = "https://api.github.com/repos/" + config.GITHUB_REPO + "/releases/latest"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "WattGauge"})
                with urllib.request.urlopen(req, timeout=6) as resp:
                    tag = json.load(resp).get("tag_name", "").lstrip("vV")
                return {"ok": True, "latest": tag}
            except Exception:
                return {"ok": False, "latest": ""}

        fut = self.pool.submit(work)
        fut.add_done_callback(lambda f: self.updateReady.emit(f.result() if not f.exception() else {"ok": False, "latest": ""}))

    @staticmethod
    def _version_tuple(text):
        parts = []
        for chunk in str(text).split("."):
            digits = ""
            for ch in chunk:
                if ch.isdigit():
                    digits += ch
                else:
                    break
            parts.append(int(digits or 0))
        return tuple(parts)

    def _apply_update(self, info):
        self._update_checking = False
        if not isinstance(info, dict) or not info.get("ok"):
            self._update_status = self._t("update_failed")
        else:
            latest = (info.get("latest") or "").strip()
            if latest and self._version_tuple(latest) > self._version_tuple(config.APP_VERSION):
                self._update_status = self._t("update_available", v=latest)
            else:
                self._update_status = self._t("up_to_date")
        self._emit_config()

    @pyqtSlot(int)
    def setSelectedDays(self, days):
        if days in (1, 7, 14, 30):
            self._selected_days = days
            self.cfg.set(days, "history_days")
            self._recompute()
            self.dataChanged.emit()

    @pyqtSlot(bool)
    def setUseSmartHours(self, smart):
        self._use_smart = bool(smart)
        self.cfg.set(self._use_smart, "use_smart_hours")
        self._recompute()
        self.dataChanged.emit()

    @pyqtSlot(float)
    def setTariff(self, value):
        if value > 0:
            self._tariff = float(value)
            self.cfg.set(self._tariff, "tariff_per_kwh")
            self._recompute()
            self.dataChanged.emit()

    @pyqtSlot(float, float, bool)
    def saveDisplays(self, display1, display2, display2_enabled):
        displays = self.cfg.data.get("displays", [{}, {}])
        while len(displays) < 2:
            displays.append({})
        def disp(v, fallback):
            try:
                return max(5.0, min(400.0, float(v)))
            except (TypeError, ValueError):
                return fallback

        displays[0]["max_watt"] = disp(display1, 45.0)
        displays[0]["enabled"] = True
        displays[0].setdefault("name", "Display 1")
        displays[1]["max_watt"] = disp(display2, 35.0)
        displays[1]["enabled"] = bool(display2_enabled)
        displays[1].setdefault("name", "Display 2")
        self.cfg.data["displays"] = displays
        self.cfg.save()
        self._emit_config()
        self.dataChanged.emit()

    @pyqtSlot(int, float, bool, float, int, float, float)
    def savePlatform(self, fans, fan_watt, pump, pump_watt, leds, led_watt, mobo_base):
        def clamp(v, lo, hi, cast):
            try:
                return cast(max(lo, min(hi, float(v))))
            except (TypeError, ValueError):
                return cast(lo)

        self.cfg.set(clamp(fans, 0, 16, int), "fans", "count")
        self.cfg.set(clamp(fan_watt, 0.0, 5.0, float), "fans", "watt_each")
        self.cfg.set(bool(pump), "fans", "aio_pump")
        self.cfg.set(clamp(pump_watt, 0.0, 25.0, float), "fans", "pump_watt")
        self.cfg.set(clamp(leds, 0, 150, int), "rgb", "leds")
        self.cfg.set(clamp(led_watt, 0.0, 1.0, float), "rgb", "watt_each")
        self.cfg.set(clamp(mobo_base, 0.0, 40.0, float), "mobo", "base_watt")
        self._emit_config()
        self.dataChanged.emit()

    @pyqtSlot(bool)
    def saveAutostart(self, enabled):
        r"""Register/unregister the app in HKCU\...\Run (no admin needed)."""
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE,
            )
            if enabled:
                winreg.SetValueEx(key, "WattGauge", 0, winreg.REG_SZ, self._autostart_cmd())
            else:
                try:
                    winreg.DeleteValue(key, "WattGauge")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception:
            pass
        self.cfg.set(bool(enabled), "ui", "autostart")
        self._emit_config()

    def _autostart_key(self):
        import winreg
        return winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE,
        )

    @pyqtSlot()
    def ensureAutostart(self):
        """First run / every start: keep the Run key in sync with the setting.

        Default is on, so a fresh install starts with Windows right away until
        the user unticks it in Settings.
        """
        want = bool(self.cfg.get("ui", "autostart", default=True))
        try:
            import winreg
            key = self._autostart_key()
            try:
                current, _ = winreg.QueryValueEx(key, "WattGauge")
            except FileNotFoundError:
                current = None
            cmd = self._autostart_cmd()
            if want and current != cmd:
                winreg.SetValueEx(key, "WattGauge", 0, winreg.REG_SZ, cmd)
            elif not want and current is not None:
                try:
                    winreg.DeleteValue(key, "WattGauge")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception:
            pass

    def _autostart_cmd(self):
        import os
        import sys
        exe = sys.executable
        if exe.lower().endswith("python.exe"):
            alt = exe[: -len("python.exe")] + "pythonw.exe"
            if os.path.exists(alt):
                exe = alt
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
        return f'"{exe}" "{script}"'

    @pyqtProperty(bool, notify=configChanged)
    def autostart(self):
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
            )
            winreg.QueryValueEx(key, "WattGauge")
            winreg.CloseKey(key)
            return True
        except Exception:
            return bool(self.cfg.get("ui", "autostart", default=True)) if sys.platform != "win32" else False

    @pyqtProperty(int, notify=configChanged)
    def windowWidth(self):
        return int(self.cfg.get("ui", "window_width", default=470) or 470)

    @pyqtProperty(int, notify=configChanged)
    def windowHeight(self):
        return int(self.cfg.get("ui", "window_height", default=726) or 726)

    @pyqtSlot(int, int)
    def saveWindowSize(self, width, height):
        width = max(330, min(1400, int(width)))
        height = max(510, min(1800, int(height)))
        if (width, height) == (self.windowWidth, self.windowHeight):
            return
        self.cfg.set(width, "ui", "window_width")
        self.cfg.set(height, "ui", "window_height")

    @pyqtSlot(bool)
    def saveTopbar(self, enabled):
        self.cfg.set(bool(enabled), "topbar", "enabled")
        self._emit_config()

    @pyqtSlot()
    def shutdown(self):
        self._timer.stop()
        self.history.close()
        self.pool.shutdown(wait=False)