"""Shared telemetry types and helpers."""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field


@dataclass
class Component:
    key: str
    icon: str
    name: str
    watt: float
    source: str = "estimate"   # "sensor" | "estimate" | "config"
    detail: str = ""

    def as_dict(self):
        return {
            "key": self.key,
            "icon": self.icon,
            "name": self.name,
            "watt": round(self.watt, 1),
            "source": self.source,
            "detail": self.detail,
        }


@dataclass
class Snapshot:
    components: list[Component] = field(default_factory=list)
    cpu_load: float = 0.0
    gpu_load: float = 0.0
    cpu_name: str = ""
    gpu_names: list[str] = field(default_factory=list)
    ram_total_gb: float = 0.0
    ram_used_pct: float = 0.0
    ram_type: str = ""
    disk_count: int = 0
    uptime_sec: int = 0

    @property
    def total_watt(self) -> float:
        return round(sum(c.watt for c in self.components), 1)


def run(cmd, timeout=4.0, env=None):
    try:
        p = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, env=env,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if p.returncode != 0:
            return None
        return p.stdout
    except Exception:
        return None


def powershell_json(script: str, timeout=8.0):
    out = run([
        "powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
        "-Command", script + " | ConvertTo-Json -Compress -Depth 4",
    ], timeout=timeout)
    if not out:
        return None
    out = out.strip()
    if not out:
        return None
    try:
        data = json.loads(out)
    except Exception:
        return None
    return data


def as_list(obj):
    if obj is None:
        return []
    if isinstance(obj, list):
        return obj
    return [obj]

import re as _re


def short_cpu(name: str) -> str:
    s = (name or "").replace("(R)", "").replace("(TM)", "").replace(" CPU", "")
    s = _re.sub(r"\s*@\s*[0-9.]+\s*GHz", "", s, flags=_re.I)
    s = _re.sub(r"\s+\d+-Core Processor", "", s, flags=_re.I)
    s = s.replace("Intel Core", "Core").replace("AMD Ryzen", "Ryzen")
    s = s.replace("Genuine Intel", "Core")
    return " ".join(s.split())


def short_gpu(name: str) -> str:
    s = (name or "").replace("NVIDIA ", "").replace("AMD ", "").replace("Radeon RX", "RX")
    s = _re.sub(r"\s+Laptop GPU.*$", "", s, flags=_re.I)
    return " ".join(s.split())
