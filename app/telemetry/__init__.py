from __future__ import annotations

import sys

from .base import Component, Snapshot

__all__ = ["Component", "Snapshot", "make_collector"]


def make_collector(cfg):
    if sys.platform == "win32":
        from .windows import WindowsCollector
        return WindowsCollector(cfg)
    from .linux import LinuxCollector
    return LinuxCollector(cfg)