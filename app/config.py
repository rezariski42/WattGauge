"""Config store: %%APPDATA%%/WattGauge/config.json (single source of truth)."""
from __future__ import annotations

import json
import os
import sys

APP_NAME = "WattGauge"
APP_VERSION = "1.2.0"
GITHUB_REPO = "rezariski42/WattGauge"

DEFAULTS = {
    "tariff_per_kwh": 1444.7,
    "displays": [
        {"name": "Display 1", "max_watt": 45.0, "enabled": True},
        {"name": "Display 2", "max_watt": 35.0, "enabled": False},
    ],
    "fans": {"count": 6, "watt_each": 1.5, "aio_pump": True, "pump_watt": 6.0},
    "rgb": {"leds": 24, "watt_each": 0.3},
    "mobo": {"base_watt": 18.0},
    "storage": {"watt_nvme_idle": 1.3, "watt_sata_idle": 0.6, "watt_hdd_idle": 4.0},
    "ram": {"ddr5_per_module": 1.2, "ddr4_per_module": 0.8},
    "history_days": 30,
    "use_smart_hours": True,
    "topbar": {"enabled": True, "always_on_top": True},
    "sensor_source": "auto",
    "ui": {"autostart": True, "window_width": 470, "window_height": 726,
           "language": "en", "close_to_tray": True},
}


def app_dir() -> str:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    d = os.path.join(base, APP_NAME)
    os.makedirs(d, exist_ok=True)
    return d


def config_path() -> str:
    return os.path.join(app_dir(), "config.json")


def db_path() -> str:
    return os.path.join(app_dir(), "history.db")


def _merge(defaults, current):
    if isinstance(defaults, dict):
        out = dict(defaults)
        if isinstance(current, dict):
            for k, v in current.items():
                out[k] = _merge(defaults.get(k, v), v)
        return out
    return current


class Config:
    def __init__(self):
        self.path = config_path()
        self.data = dict(DEFAULTS)
        self.load()

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                self.data = _merge(DEFAULTS, json.load(fh))
        except Exception:
            self.data = json.loads(json.dumps(DEFAULTS))
            self.save()

    def save(self):
        tmp = self.path + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(self.data, fh, indent=2)
            os.replace(tmp, self.path)
        except Exception:
            pass

    def get(self, *keys, default=None):
        cur = self.data
        for k in keys:
            if not isinstance(cur, dict) or k not in cur:
                return default
            cur = cur[k]
        return cur

    def set(self, value, *keys):
        cur = self.data
        for k in keys[:-1]:
            cur = cur.setdefault(k, {})
        cur[keys[-1]] = value
        self.save()