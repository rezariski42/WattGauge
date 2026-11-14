"""Qt-facing engine: owns the collector, history DB and cost projections."""
from __future__ import annotations

import sys
import time
from concurrent.futures import ThreadPoolExecutor

from PyQt6.QtCore import QObject, QTimer, pyqtProperty, pyqtSignal, pyqtSlot

import config
import history as history_mod
from telemetry import make_collector


class PowerEngine(QObject):
    dataChanged = pyqtSignal()
    configChanged = pyqtSignal()
    # Worker thread -> GUI thread hand-off. Emitted from the collector thread so
    # Qt delivers it queued: every field the UI reads is written on the GUI
    # thread, which keeps totalWatt and components from the same snapshot.
    snapshotReady = pyqtSignal(object)

    def __init__(self, cfg=None):
        super().__init__()
        self.cfg = cfg or config.Config()
        self.history = history_mod.History()
        self.collector = make_collector(self.cfg)
        self.pool = ThreadPoolExecutor(max_workers=1)
        self._busy = False

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
        self._assumed_hours = False
        self._weekday_stats: list[dict] = []
        self._last_tick = time.monotonic()
        self._cpu_name = ""
        self._gpu_summary = ""
        self._ram_total = 0.0
        self._disk_count = 0
        self._sensor_count = 0
        self._component_count = 0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.tick)
        self.snapshotReady.connect(self._apply_snapshot)
        self._timer.start(1000)
        self.tick()

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
        self._kwh_projected = round(self._total * self._selected_days * hours_per_day / 1000.0, 2)
        cost = round(self._kwh_projected * self._tariff)
        self._cost_formatted = "Rp {:,.0f}".format(cost).replace(",", ".")

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
    def costFormatted(self):
        return self._cost_formatted

    @pyqtProperty(str, notify=dataChanged)
    def costText(self):
        return self._cost_formatted

    @pyqtProperty(str, notify=dataChanged)
    def costPerHour(self):
        per_hour = round(self._total / 1000.0 * self._tariff)
        return "Rp {:,.0f}/jam".format(per_hour).replace(",", ".")

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
            return "ESTIMASI"
        if self._sensor_count == self._component_count:
            return "SENSOR REAL"
        return f"{self._sensor_count}/{self._component_count} SENSOR"

    @pyqtProperty(str, notify=dataChanged)
    def basisNote(self):
        if not self._use_smart:
            return "24 jam/hari"
        if self._assumed_hours:
            return "asumsi 8 jam/hari (data kurang)"
        return f"{self._avg_hours:.1f} jam/hari aktual"

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

    @pyqtProperty("QVariantMap", notify=configChanged)
    def settings(self):
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
        }

    # ---------------- slots ----------------
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
        displays[0]["max_watt"] = float(display1)
        displays[0]["enabled"] = True
        displays[0].setdefault("name", "Display 1")
        displays[1]["max_watt"] = float(display2)
        displays[1]["enabled"] = bool(display2_enabled)
        displays[1].setdefault("name", "Display 2")
        self.cfg.data["displays"] = displays
        self.cfg.save()
        self.configChanged.emit()
        self.dataChanged.emit()

    @pyqtSlot(int, float, bool, float, int, float, float)
    def savePlatform(self, fans, fan_watt, pump, pump_watt, leds, led_watt, mobo_base):
        self.cfg.set(int(fans), "fans", "count")
        self.cfg.set(float(fan_watt), "fans", "watt_each")
        self.cfg.set(bool(pump), "fans", "aio_pump")
        self.cfg.set(float(pump_watt), "fans", "pump_watt")
        self.cfg.set(int(leds), "rgb", "leds")
        self.cfg.set(float(led_watt), "rgb", "watt_each")
        self.cfg.set(float(mobo_base), "mobo", "base_watt")
        self.configChanged.emit()
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
        self.configChanged.emit()

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
        self.configChanged.emit()

    @pyqtSlot()
    def shutdown(self):
        self._timer.stop()
        self.history.close()
        self.pool.shutdown(wait=False)