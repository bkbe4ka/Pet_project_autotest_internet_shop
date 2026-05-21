"""Хранилище.

- Отпечатки -> JSON под .selfheal/fingerprints/<test>/<step_id>.json (КОММИТЯТСЯ в git:
  бесплатное версионирование, история аудита, диффы локаторов видны в PR).
- Исходы восстановления, кэш шага, калибратор -> локальный SQLite (.selfheal/state.db).
"""
from __future__ import annotations

import os
import re
import sqlite3
import time
from pathlib import Path

from .fingerprint import ElementFingerprint
from .scoring.calibrate import Calibrator

_SAFE = re.compile(r"[^A-Za-z0-9_.-]+")


def _safe(name: str) -> str:
    return _SAFE.sub("_", name)[:120]


class Store:
    def __init__(self, root: str = ".selfheal") -> None:
        self.root = Path(root)
        self.fp_dir = self.root / "fingerprints"
        self.fp_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / "state.db"
        self._db = sqlite3.connect(self.db_path)
        self._db.execute("""CREATE TABLE IF NOT EXISTS outcomes(
            step_id TEXT, raw_score REAL, success INTEGER, ts REAL)""")
        self._db.execute("""CREATE TABLE IF NOT EXISTS step_cache(
            step_id TEXT PRIMARY KEY, selector TEXT, ts REAL)""")
        self._db.execute("""CREATE TABLE IF NOT EXISTS kv(k TEXT PRIMARY KEY, v TEXT)""")
        self._db.commit()

    # ---- отпечатки ----
    def save_fingerprint(self, fp: ElementFingerprint) -> Path:
        d = self.fp_dir / _safe(fp.test_id)
        d.mkdir(parents=True, exist_ok=True)
        path = d / f"{fp.step_id}.json"
        path.write_text(fp.to_json(), encoding="utf-8")
        return path

    def load_fingerprint(self, test_id: str, step_id: str) -> ElementFingerprint | None:
        path = self.fp_dir / _safe(test_id) / f"{step_id}.json"
        if not path.exists():
            return None
        return ElementFingerprint.from_json(path.read_text(encoding="utf-8"))

    # ---- кэш шага ----
    def cache_get(self, step_id: str) -> str | None:
        row = self._db.execute(
            "SELECT selector FROM step_cache WHERE step_id=?", (step_id,)).fetchone()
        return row[0] if row else None

    def cache_set(self, step_id: str, selector: str) -> None:
        self._db.execute(
            "INSERT OR REPLACE INTO step_cache VALUES(?,?,?)",
            (step_id, selector, time.time()))
        self._db.commit()

    def cache_evict(self, step_id: str) -> None:
        self._db.execute("DELETE FROM step_cache WHERE step_id=?", (step_id,))
        self._db.commit()

    # ---- исходы (для калибровки) ----
    def record_outcome(self, step_id: str, raw_score: float, success: bool) -> None:
        self._db.execute("INSERT INTO outcomes VALUES(?,?,?,?)",
                         (step_id, raw_score, 1 if success else 0, time.time()))
        self._db.commit()

    def all_outcomes(self) -> tuple[list[float], list[bool]]:
        rows = self._db.execute("SELECT raw_score, success FROM outcomes").fetchall()
        return [r[0] for r in rows], [bool(r[1]) for r in rows]

    # ---- калибратор ----
    def save_calibrator(self, cal: Calibrator) -> None:
        self._db.execute("INSERT OR REPLACE INTO kv VALUES('calibrator', ?)", (cal.to_json(),))
        self._db.commit()

    def load_calibrator(self) -> Calibrator:
        row = self._db.execute("SELECT v FROM kv WHERE k='calibrator'").fetchone()
        if row:
            return Calibrator.from_json(row[0])
        return Calibrator()

    def refit_calibrator(self) -> Calibrator:
        xs, ys = self.all_outcomes()
        cal = Calibrator().fit(xs, ys)
        self.save_calibrator(cal)
        return cal
