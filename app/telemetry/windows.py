"""Windows telemetry collector.

Source priority per metric:
  1. LibreHardwareMonitor WMI (real sensors: CPU package power, GPU power,
     fan RPM) when the user runs LHM with "Enable WMI provider" (optional).
  2. nvidia-smi power.draw (real NVIDIA GPU power, ships with the driver).
  3. Vendor modelled estimate from live load + TDP table (labelled "estimate").
"""
from __future__ import annotations

import os
import re
import time

import psutil

from .base import Component, Snapshot, powershell_json, run, as_list, short_cpu, short_gpu

GPU_TDP = [
    (r"rtx\s*50\d0", 250.0), (r"rtx\s*40\d0", 145.0), (r"rtx\s*30\d0", 170.0),
    (r"rtx\s*20\d0", 175.0), (r"gtx\s*16\d0", 125.0), (r"gtx\s*10\d0", 120.0),
    (r"rx\s*9\d{3}", 175.0), (r"rx\s*7\d{3}", 165.0), (r"rx\s*6\d{3}", 150.0),
    (r"rx\s*5\d{3}", 130.0), (r"arc\s*a\d{3}", 150.0), (r"arc\s*b\d{3}", 190.0),
]
CPU_TDP = [
    (r"i9[- ]1[0-9]{3,}", 125.0), (r"i7[- ]1[0-9]{3,}", 125.0), (r"i5[- ]1[0-9]{3,}", 95.0),
    (r"i3[- ]1[0-9]{3,}", 65.0), (r"i[0-9][- ]1[0-9]{3,}", 65.0),
    (r"ryzen\s*9\s*9[0-9]{3}", 170.0), (r"ryzen\s*7\s*9[0-9]{3}", 140.0),
    (r"ryzen\s*9\s*7[0-9]{3}", 120.0), (r"ryzen\s*7\s*7[0-9]{3}", 105.0),
    (r"ryzen\s*5\s*7[0-9]{3}", 95.0), (r"ryzen\s*9\s*5[0-9]{3}", 105.0),
    (r"ryzen\s*7\s*5[0-9]{3}", 95.0), (r"ryzen\s*5\s*5[0-9]{3}", 85.0),
    (r"ryzen\s*3\s*5[0-9]{3}", 65.0), (r"ryzen\s*[3579]\s*[0-9]{4}", 95.0),
]
SKIP_GPU = re.compile(r"basic display|remote|virtualbox|vmware|citrix|parsec|hyper-v|microsoft", re.I)


def _match(table, text, default):
    low = (text or "").lower().replace("®", "").replace("™", "")
    for pattern, tdp in table:
        if re.search(pattern, low):
            return tdp
    return default


class WindowsCollector:
    def __init__(self, cfg):
        self.cfg = cfg
        self._cache = {}
        self._lhm_ok = None
        self._lhm_misses = 0
        self._lhm_off_until = 0.0
        self._last_disk_bytes = None
        self._last_disk_ts = None

    # ---------------- cached inventory ----------------
    def _cached(self, key, ttl, producer):
        now = time.time()
        hit = self._cache.get(key)
        if hit and (now - hit[0]) < ttl:
            return hit[1]
        value = producer()
        self._cache[key] = (now, value)
        return value

    def _cpu_name(self):
        def read():
            try:
                import winreg
                k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                   r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
                val, _ = winreg.QueryValueEx(k, "ProcessorNameString")
                return " ".join(val.split())
            except Exception:
                pass
            try:
                data = powershell_json("Get-CimInstance Win32_Processor | Select-Object -First 1 -Property Name")
                rows = as_list(data)
                return (rows[0] or {}).get("Name", "") if rows else ""
            except Exception:
                return ""
        return self._cached("cpu_name", 3600, read)

    def _lhm_sensors(self):
        """LibreHardwareMonitor WMI sensors (Power + Fan). Empty when absent."""
        if time.time() < self._lhm_off_until:
            return []
        def read():
            script = (
                "Get-CimInstance -Namespace root/LibreHardwareMonitor -ClassName Sensor "
                "-ErrorAction SilentlyContinue | "
                "Select-Object Identifier,Name,SensorType,Value"
            )
            data = powershell_json(script, timeout=10)
            rows = [r for r in as_list(data) if isinstance(r, dict) and r.get("SensorType")]
            if not rows:
                self._lhm_misses += 1
                if self._lhm_misses >= 3:
                    self._lhm_off_until = time.time() + 600
            else:
                self._lhm_ok = True
                self._lhm_misses = 0
            return rows
        return self._cached("lhm", 5, read)

    def _ram_info(self):
        def read():
            data = powershell_json(
                "Get-CimInstance Win32_PhysicalMemory | "
                "Select-Object Capacity,SMBIOSMemoryType,Speed,ConfiguredClockSpeed"
            )
            rows = as_list(data)
            return [r for r in rows if isinstance(r, dict) and r.get("Capacity")]
        return self._cached("ram", 3600, read)

    def _gpu_adapters(self):
        def read():
            data = powershell_json(
                "Get-CimInstance Win32_VideoController | "
                "Select-Object Name,AdapterRAM,DriverVersion"
            )
            rows = [r for r in as_list(data) if isinstance(r, dict) and r.get("Name")]
            return [r for r in rows if not SKIP_GPU.search(r["Name"] or "")]
        return self._cached("gpu_adapters", 600, read)

    def _physical_disks(self):
        def read():
            data = powershell_json(
                "Get-PhysicalDisk -ErrorAction SilentlyContinue | "
                "Select-Object FriendlyName,MediaType,BusType,Size"
            )
            rows = [r for r in as_list(data) if isinstance(r, dict) and r.get("FriendlyName")]
            if rows:
                return rows
            data = powershell_json(
                "Get-CimInstance Win32_DiskDrive | Select-Object Model,MediaType,InterfaceType,Size"
            )
            return [r for r in as_list(data) if isinstance(r, dict) and r.get("Model")]
        return self._cached("disks", 600, read)

    def _brightness(self):
        def read():
            data = powershell_json(
                "Get-CimInstance -Namespace root/wmi -ClassName WmiMonitorBrightness "
                "-ErrorAction SilentlyContinue | Select-Object CurrentBrightness"
            )
            rows = as_list(data)
            vals = [float(r.get("CurrentBrightness") or 0) for r in rows if isinstance(r, dict)]
            return (sum(vals) / len(vals) / 100.0) if vals else None
        return self._cached("brightness", 20, read)

    # ---------------- live sensors ----------------
    def _nvidia_smi(self):
        out = run([
            "nvidia-smi",
            "--query-gpu=name,power.draw,utilization.gpu,memory.total",
            "--format=csv,noheader,nounits",
        ], timeout=3.0)
        if not out:
            for candidate in (
                r"C:\Windows\System32\nvidia-smi.exe",
                r"C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe",
            ):
                out = run([candidate, "--query-gpu=name,power.draw,utilization.gpu,memory.total",
                           "--format=csv,noheader,nounits"], timeout=3.0)
                if out:
                    break
        gpus = []
        if not out:
            return gpus
        for line in out.strip().splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 3:
                continue
            name = parts[0]
            try:
                power = float(parts[1])
            except Exception:
                power = None
            try:
                util = float(parts[2])
            except Exception:
                util = None
            mem = parts[3] if len(parts) > 3 else ""
            gpus.append({"name": name, "power": power, "util": util, "mem": mem})
        return gpus

    def _gpu_util_amd_intel(self):
        """Sum 3D engine utilisation via GPU performance counters (Win10+)."""
        script = (
            "(Get-Counter '\\GPU Engine(*engtype_3D)\\Utilization Percentage' "
            "-ErrorAction SilentlyContinue).CounterSamples | "
            "Measure-Object -Property CookedValue -Sum | Select-Object -Property Sum"
        )
        data = powershell_json(script, timeout=6)
        rows = as_list(data)
        val = (rows[0] or {}).get("Sum") if rows else 0
        try:
            return min(100.0, float(val))
        except Exception:
            return 0.0

    def _lhm_value(self, sensors, kind, name_contains=None, ident_contains=None):
        for s in sensors:
            if s.get("SensorType") != kind:
                continue
            name = (s.get("Name") or "").lower()
            ident = (s.get("Identifier") or "").lower()
            if name_contains and name_contains.lower() not in name:
                continue
            if ident_contains and ident_contains.lower() not in ident:
                continue
            try:
                return float(s.get("Value"))
            except Exception:
                continue
        return None

    def _disk_io_rate(self):
        try:
            io = psutil.disk_io_counters(perdisk=False)
        except Exception:
            return 0.0, 0.0
        if io is None:
            return 0.0, 0.0
        now = time.time()
        total = io.read_bytes + io.write_bytes
        rate = 0.0
        if self._last_disk_ts is not None and now > self._last_disk_ts:
            dt = max(0.5, now - self._last_disk_ts)
            delta = max(0, total - (self._last_disk_bytes or total))
            rate = delta / (1024 * 1024) / dt
        self._last_disk_bytes = total
        self._last_disk_ts = now
        read_mb = io.read_bytes / (1024 * 1024)
        return rate, read_mb

    # ---------------- main ----------------
    def collect(self) -> Snapshot:
        snap = Snapshot()
        sensors = self._lhm_sensors()

        cpu_load = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        snap.cpu_load = cpu_load
        snap.ram_used_pct = mem.percent
        snap.ram_total_gb = round(mem.total / (1024 ** 3), 1)
        snap.uptime_sec = int(time.time() - psutil.boot_time())

        # ---- CPU ----
        cpu_name = self._cpu_name() or "CPU"
        snap.cpu_name = cpu_name
        tdp = _match(CPU_TDP, cpu_name, 95.0)
        cpu_power = self._lhm_value(sensors, "Power", "package")
        if cpu_power is None:
            cpu_power = self._lhm_value(sensors, "Power", "cpu package")
        if cpu_power is None:
            cpu_power = self._lhm_value(sensors, "Power", ident_contains="/cpu/")
        if cpu_power is not None and cpu_power > 0:
            cpu_watt, cpu_source = cpu_power, "sensor"
        else:
            ceiling = tdp * 1.15
            idle = max(6.0, ceiling * 0.12)
            load = min(1.0, max(0.0, cpu_load / 100.0))
            cpu_watt = idle + (ceiling - idle) * (load ** 1.15)
            cpu_source = "estimate"
        snap.components.append(Component(
            "cpu", "⚡", short_cpu(cpu_name), cpu_watt,
            cpu_source, f"load {cpu_load:.0f}% · TDP {tdp:.0f} W",
        ))

        # ---- GPU(s) ----
        nv = self._nvidia_smi()
        gpu_amdgpu_sensors = [s for s in sensors if s.get("SensorType") == "Power"
                              and ("gpu" in (s.get("Identifier") or "").lower()
                                   or "gpu" in (s.get("Name") or "").lower())]
        gpu_cards = []
        for g in nv:
            watt = g["power"]
            source = "sensor"
            if watt is None or watt <= 0:
                model_tdp = _match(GPU_TDP, g["name"], 130.0)
                util = g["util"] or 0.0
                watt = 12.0 + (model_tdp - 12.0) * (util / 100.0)
                source = "estimate"
            gpu_cards.append({
                "name": g["name"], "watt": watt, "source": source,
                "detail": f"load {g['util'] or 0:.0f}% · {g['mem']} MB" if g.get("mem") else "",
                "real": source == "sensor",
            })

        others = [a["Name"] for a in self._gpu_adapters()
                  if not re.search(r"nvidia", a["Name"], re.I)]
        if others:
            util = self._gpu_util_amd_intel()
            for idx, name in enumerate(others):
                model_tdp = _match(GPU_TDP, name, 110.0)
                watt = None
                if idx == 0:
                    watt = self._lhm_value(sensors, "Power", "gpu")
                if watt and watt > 0:
                    source = "sensor"
                else:
                    l = min(100.0, max(0.0, util)) / 100.0
                    watt = 10.0 + (model_tdp - 10.0) * l
                    source = "estimate"
                gpu_cards.append({
                    "name": name, "watt": watt, "source": source,
                    "detail": f"load {util:.0f}%" if util else "", "real": source == "sensor",
                })

        # No adapter detected (e.g. a VM with a basic display): add no GPU row at
        # all instead of a phantom 0 W tile.

        snap.gpu_names = [g["name"] for g in gpu_cards]
        snap.gpu_load = nv[0]["util"] if nv and nv[0].get("util") is not None else 0.0
        for i, g in enumerate(gpu_cards, start=1):
            label = g["name"]
            if len(gpu_cards) > 1:
                label = f"{g['name']}"
            snap.components.append(Component(
                f"gpu{i}", "🎮", short_gpu(label), g["watt"], g["source"], g.get("detail", ""),
            ))

        # ---- RAM ----
        modules = self._ram_info()
        smbios = [int(m.get("SMBIOSMemoryType") or 0) for m in modules]
        if 34 in smbios or 35 in smbios:
            ram_type, per_module = "DDR5", float(self.cfg.get("ram", "ddr5_per_module", default=1.2))
        elif 26 in smbios or 27 in smbios:
            ram_type, per_module = "DDR4", float(self.cfg.get("ram", "ddr4_per_module", default=0.8))
        else:
            ram_type = "DDR4"
            per_module = float(self.cfg.get("ram", "ddr4_per_module", default=0.8))
        module_count = max(1, len(modules)) if modules else max(1, int(round(snap.ram_total_gb / 16.0)))
        load = snap.ram_used_pct / 100.0
        span = 6.0 if ram_type == "DDR4" else 10.0
        ram_watt = module_count * per_module + span * load
        snap.ram_type = ram_type
        snap.components.append(Component(
            "ram", "💾", f"RAM {ram_type} {snap.ram_total_gb:.0f} GB", ram_watt,
            "estimate", f"{module_count} modul · {snap.ram_used_pct:.0f}% pakai",
        ))

        # ---- Displays (user-set max watt) ----
        brightness = self._brightness()
        for idx, disp in enumerate(self.cfg.get("displays", default=[]), start=1):
            if not isinstance(disp, dict) or not disp.get("enabled", True):
                continue
            max_watt = float(disp.get("max_watt") or 45.0)
            factor = brightness if brightness is not None else 0.92
            watt = max_watt * (0.72 + 0.28 * factor)
            snap.components.append(Component(
                f"display{idx}", "🖥️", disp.get("name") or f"Display {idx}",
                watt, "config", f"max {max_watt:.0f} W",
            ))

        # ---- Mobo / fans / RGB ----
        fans = self.cfg.get("fans", default={}) or {}
        rgb = self.cfg.get("rgb", default={}) or {}
        def clamp(v, lo, hi):
            try:
                return max(lo, min(hi, float(v)))
            except (TypeError, ValueError):
                return lo

        fan_count = int(clamp(fans.get("count", 6), 0, 16))
        fan_watt = clamp(fans.get("watt_each", 1.5), 0.0, 5.0)
        pump_watt = clamp(fans.get("pump_watt", 6.0), 0.0, 25.0) if fans.get("aio_pump", True) else 0.0
        led_count = int(clamp(rgb.get("leds", 24), 0, 150))
        led_watt = clamp(rgb.get("watt_each", 0.3), 0.0, 1.0)
        base = clamp(self.cfg.get("mobo", "base_watt", default=18.0), 0.0, 40.0)
        platform_watt = base + fan_count * fan_watt + pump_watt + led_count * led_watt
        platform_watt += 2.5 * min(1.0, cpu_load / 100.0)
        snap.components.append(Component(
            "platform", "⚙️", "Mobo · Fans · RGB", platform_watt, "config",
            f"{fan_count} fan · {led_count} LED" + (" · pump" if pump_watt else ""),
        ))

        # ---- Storage ----
        disks = self._physical_disks()
        io_rate, _ = self._disk_io_rate()
        nvme_idle = float(self.cfg.get("storage", "watt_nvme_idle", default=1.3))
        sata_idle = float(self.cfg.get("storage", "watt_sata_idle", default=0.6))
        hdd_idle = float(self.cfg.get("storage", "watt_hdd_idle", default=4.0))
        if disks:
            total = 0.0
            kinds = []
            for d in disks:
                bus = (d.get("BusType") or d.get("InterfaceType") or "").upper()
                media = (d.get("MediaType") or "").upper()
                if "NVME" in bus:
                    total += nvme_idle
                    kinds.append("NVMe")
                elif "HDD" in media or "FIXED HARD" in media:
                    total += hdd_idle
                    kinds.append("HDD")
                else:
                    total += sata_idle
                    kinds.append("SATA")
            io_factor = min(1.0, io_rate / 250.0)
            total += 4.0 * io_factor
            snap.disk_count = len(disks)
            label = f"Storage · {len(disks)} disk"
            detail = f"{', '.join(kinds[:3])}{'…' if len(kinds) > 3 else ''} · {io_rate:.1f} MB/s"
        else:
            total = nvme_idle
            label = "Storage"
            detail = f"{io_rate:.1f} MB/s"
        snap.components.append(Component("storage", "🗄️", label, total, "estimate", detail))

        return snap