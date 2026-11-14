"""Linux collector (used for local development and the Linux build)."""
from __future__ import annotations

import glob
import os
import platform
import re
import subprocess
import time

import psutil

from .base import Component, Snapshot, run, short_cpu, short_gpu
from .windows import GPU_TDP, CPU_TDP, _match, SKIP_GPU

RAPL = "/sys/class/powercap/intel-rapl:0/energy_uj"


class LinuxCollector:
    def __init__(self, cfg):
        self.cfg = cfg
        self._last_rapl = None
        self._last_rapl_ts = None
        self._last_disk_bytes = None
        self._last_disk_ts = None
        self._cpu_name = self._read_cpu_name()

    def _read_cpu_name(self):
        try:
            with open("/proc/cpuinfo", "r", encoding="utf-8") as fh:
                for line in fh:
                    if line.lower().startswith("model name"):
                        return line.split(":", 1)[1].strip()
        except Exception:
            pass
        return platform.processor() or "CPU"

    def _cpu_power(self):
        if not os.path.exists(RAPL):
            return None
        now = time.time()
        try:
            with open(RAPL, "r") as fh:
                energy = int(fh.read().strip())
        except Exception:
            return None
        watt = None
        if self._last_rapl is not None and now > self._last_rapl_ts:
            dt = now - self._last_rapl_ts
            if dt > 0.2 and energy >= self._last_rapl:
                watt = (energy - self._last_rapl) / 1e6 / dt
        self._last_rapl = energy
        self._last_rapl_ts = now
        return watt

    def _brightness(self):
        try:
            for path in glob.glob("/sys/class/backlight/*/brightness"):
                cur = int(open(path).read())
                maxp = int(open(os.path.join(os.path.dirname(path), "max_brightness")).read())
                if maxp:
                    return cur / maxp
        except Exception:
            pass
        return None

    def _nvidia(self):
        out = run(["nvidia-smi", "--query-gpu=name,power.draw,utilization.gpu,memory.total",
                   "--format=csv,noheader,nounits"], timeout=3.0)
        cards = []
        if not out:
            return cards
        for line in out.strip().splitlines():
            p = [x.strip() for x in line.split(",")]
            if len(p) < 3:
                continue
            try:
                power = float(p[1])
            except Exception:
                power = None
            try:
                util = float(p[2])
            except Exception:
                util = None
            cards.append({"name": p[0], "power": power, "util": util,
                          "mem": p[3] if len(p) > 3 else ""})
        return cards

    def _gpus(self):
        cards = []
        for g in self._nvidia():
            watt, source = g["power"], "sensor"
            if watt is None or watt <= 0:
                tdp = _match(GPU_TDP, g["name"], 130.0)
                watt = 12.0 + (tdp - 12.0) * ((g["util"] or 0) / 100.0)
                source = "estimate"
            cards.append({"name": g["name"], "watt": watt, "source": source,
                          "detail": f"load {g['util'] or 0:.0f}%"})
        others = []
        try:
            out = run(["lspci", "-nn"], timeout=2.0) or ""
            for line in out.splitlines():
                if re.search(r"vga compatible|3d controller", line, re.I):
                    name = line.split(": ", 1)[-1]
                    name = re.sub(r"\[[0-9a-f]{4}:[0-9a-f]{4}\]", "", name).strip()
                    if re.search(r"nvidia", name, re.I) or SKIP_GPU.search(name):
                        continue
                    others.append(name)
        except Exception:
            pass
        for name in others:
            tdp = _match(GPU_TDP, name, 110.0)
            cards.append({"name": name, "watt": tdp * 0.18, "source": "estimate", "detail": "idle"})
        return cards

    def _ram(self):
        mem = psutil.virtual_memory()
        total_gb = round(mem.total / 1024 ** 3, 1)
        modules = 2
        load = mem.percent / 100.0
        watt = modules * 0.8 + 6.0 * load
        return total_gb, mem.percent, "DDR4", modules, watt

    def _disks(self):
        kinds = []
        try:
            for path in glob.glob("/sys/block/*/device"):
                dev = path.split("/")[3]
                if dev.startswith(("loop", "ram", "zram", "sr")):
                    continue
                kinds.append(dev)
        except Exception:
            pass
        return kinds

    def _disk_io_rate(self):
        try:
            io = psutil.disk_io_counters(perdisk=False)
        except Exception:
            return 0.0
        if io is None:
            return 0.0
        now = time.time()
        total = io.read_bytes + io.write_bytes
        rate = 0.0
        if self._last_disk_ts and now > self._last_disk_ts:
            dt = max(0.5, now - self._last_disk_ts)
            rate = max(0, total - (self._last_disk_bytes or total)) / (1024 * 1024) / dt
        self._last_disk_bytes = total
        self._last_disk_ts = now
        return rate

    def collect(self) -> Snapshot:
        snap = Snapshot()
        cpu_load = psutil.cpu_percent(interval=None)
        snap.cpu_load = cpu_load
        snap.cpu_name = self._cpu_name
        snap.uptime_sec = int(time.time() - psutil.boot_time())

        cpu_watt = self._cpu_power()
        if cpu_watt and cpu_watt > 0:
            source = "sensor"
        else:
            tdp = _match(CPU_TDP, self._cpu_name, 95.0)
            idle = max(6.0, tdp * 0.12)
            cpu_watt = idle + (tdp * 1.15 - idle) * ((cpu_load / 100.0) ** 1.15)
            source = "estimate"
        snap.components.append(Component("cpu", "⚡", short_cpu(self._cpu_name), cpu_watt, source,
                                         f"load {cpu_load:.0f}%"))

        gpus = self._gpus()
        if not gpus:
            gpus = [{"name": "GPU (not detected)", "watt": 0.0, "source": "estimate", "detail": ""}]
        snap.gpu_names = [g["name"] for g in gpus]
        snap.gpu_load = 0.0
        for i, g in enumerate(gpus, start=1):
            snap.components.append(Component(f"gpu{i}", "🎮", short_gpu(g["name"]), g["watt"],
                                             g["source"], g.get("detail", "")))

        total_gb, used, ram_type, modules, ram_watt = self._ram()
        snap.ram_total_gb, snap.ram_used_pct, snap.ram_type = total_gb, used, ram_type
        snap.components.append(Component("ram", "💾", f"RAM {ram_type} {total_gb:.0f} GB",
                                         ram_watt, "estimate",
                                         f"{modules} modul · {used:.0f}% pakai"))

        brightness = self._brightness()
        for idx, disp in enumerate(self.cfg.get("displays", default=[]), start=1):
            if not isinstance(disp, dict) or not disp.get("enabled", True):
                continue
            max_watt = float(disp.get("max_watt") or 45.0)
            factor = brightness if brightness is not None else 0.92
            snap.components.append(Component(f"display{idx}", "🖥️",
                                             disp.get("name") or f"Display {idx}",
                                             max_watt * (0.72 + 0.28 * factor), "config",
                                             f"max {max_watt:.0f} W"))

        fans = self.cfg.get("fans", default={}) or {}
        rgb = self.cfg.get("rgb", default={}) or {}
        fan_count = int(fans.get("count") or 0)
        platform = (float(self.cfg.get("mobo", "base_watt", default=18.0) or 18.0)
                    + fan_count * float(fans.get("watt_each") or 1.5)
                    + (float(fans.get("pump_watt") or 6.0) if fans.get("aio_pump", True) else 0.0)
                    + int(rgb.get("leds") or 0) * float(rgb.get("watt_each") or 0.3))
        platform += 2.5 * min(1.0, cpu_load / 100.0)
        snap.components.append(Component(
            "platform", "⚙️", "Mobo · Fans · RGB", platform, "config",
            f"{fan_count} fan · {int(rgb.get('leds') or 0)} LED"))

        disks = self._disks()
        io_rate = self._disk_io_rate()
        nvme = sum(1 for d in disks if d.startswith("nvme"))
        sata = len(disks) - nvme
        storage_watt = nvme * 1.3 + sata * 0.6 + 4.0 * min(1.0, io_rate / 250.0)
        snap.disk_count = len(disks)
        snap.components.append(Component(
            "storage", "🗄️", f"Storage · {len(disks)} disk", storage_watt, "estimate",
            f"{nvme} NVMe · {sata} SATA · {io_rate:.1f} MB/s"))
        return snap