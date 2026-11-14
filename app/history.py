"""Persistent activity history in SQLite.

Rows are keyed by local calendar date. While the app runs it accumulates
active seconds and kWh for the current date, so Monday..Sunday history
survives restarts and app upgrades.
"""
from __future__ import annotations

import datetime
import sqlite3

import config

DDL = """
CREATE TABLE IF NOT EXISTS days (
    date        TEXT PRIMARY KEY,
    active_sec  INTEGER NOT NULL DEFAULT 0,
    kwh         REAL    NOT NULL DEFAULT 0.0,
    watt_sum    REAL    NOT NULL DEFAULT 0.0,
    samples     INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_days_date ON days(date);
"""

WEEKDAYS = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]


class History:
    def __init__(self, path: str | None = None):
        self.path = path or config.db_path()
        self._conn = sqlite3.connect(self.path)
        self._conn.executescript(DDL)
        self._conn.commit()

    def add_sample(self, watts: float, seconds: float):
        if seconds <= 0:
            return
        day = datetime.date.today().isoformat()
        kwh = watts * seconds / 3_600_000.0
        self._conn.execute(
            """INSERT INTO days(date, active_sec, kwh, watt_sum, samples)
               VALUES(?,?,?,?,1)
               ON CONFLICT(date) DO UPDATE SET
                 active_sec = active_sec + excluded.active_sec,
                 kwh        = kwh + excluded.kwh,
                 watt_sum   = watt_sum + excluded.watt_sum,
                 samples    = samples + 1""",
            (day, int(round(seconds)), kwh, watts),
        )
        self._conn.commit()

    def day(self, date_obj: datetime.date):
        row = self._conn.execute(
            "SELECT active_sec, kwh, watt_sum, samples FROM days WHERE date=?",
            (date_obj.isoformat(),),
        ).fetchone()
        if not row:
            return {"active_sec": 0, "kwh": 0.0, "avg_watt": 0.0, "samples": 0}
        active, kwh, watt_sum, samples = row
        return {
            "active_sec": active,
            "kwh": kwh,
            "avg_watt": (watt_sum / samples) if samples else 0.0,
            "samples": samples,
        }

    def last_days(self, count: int):
        today = datetime.date.today()
        return [self.day(today - datetime.timedelta(days=i)) for i in range(count - 1, -1, -1)]

    def weekday_stats(self):
        """Average active hours per weekday (Sen..Min) over all recorded weeks."""
        rows = self._conn.execute("SELECT date, active_sec FROM days WHERE active_sec > 0").fetchall()
        buckets = {i: [] for i in range(7)}
        for date_str, active in rows:
            try:
                d = datetime.date.fromisoformat(date_str)
            except Exception:
                continue
            buckets[d.weekday()].append(active / 3600.0)
        out = []
        for idx, label in enumerate(WEEKDAYS):
            vals = buckets[idx]
            out.append({
                "day": label,
                "idx": idx,
                "hours": round(sum(vals) / len(vals), 1) if vals else 0.0,
                "days": len(vals),
            })
        return out

    def avg_daily_hours(self, window_days: int = 7):
        today = datetime.date.today()
        total = 0.0
        seen = 0
        for i in range(window_days):
            d = self.day(today - datetime.timedelta(days=i))
            if d["active_sec"] > 0:
                total += d["active_sec"] / 3600.0
                seen += 1
        if seen == 0:
            return 0.0
        return total / seen

    def active_days(self, window_days: int = 7) -> int:
        today = datetime.date.today()
        seen = 0
        for i in range(window_days):
            if self.day(today - datetime.timedelta(days=i))["active_sec"] > 0:
                seen += 1
        return seen

    def total_kwh(self):
        row = self._conn.execute("SELECT COALESCE(SUM(kwh),0) FROM days").fetchone()
        return float(row[0] or 0.0)

    def close(self):
        try:
            self._conn.close()
        except Exception:
            pass