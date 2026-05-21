"""Калибровка уверенности.

Сырая слитая оценка != вероятность правильности. Мы калибруем её против ИСТИНЫ,
которую получаем бесплатно: каждое восстановление в итоге верифицируется (проверка эффекта)
или ревьюится человеком. Логируем (raw_score, success_bool) и подгоняем монотонное
отображение raw -> p(верно).

Используем изотоническую регрессию (алгоритм Pool Adjacent Violators) на чистом Python —
без обязательных зависимостей. Пока данных мало, мягко откатываемся к identity.
"""
from __future__ import annotations

import bisect
import json
from dataclasses import dataclass, field


def _pav(xs: list[float], ys: list[float]) -> tuple[list[float], list[float]]:
    """Pool Adjacent Violators: возвращает (правые границы блоков, изотонические значения).

    Сначала агрегируем точки с ОДИНАКОВЫМ x (взвешенное среднее y) — иначе порядок внутри
    одного x создаёт ложные блоки и дубли границ, ломающие поиск. Затем накладываем
    монотонность с учётом весов.
    """
    # 1. агрегируем по уникальному x
    agg: dict[float, list[float]] = {}
    for x, y in zip(xs, ys):
        agg.setdefault(x, [0.0, 0.0])  # [sum_y, count]
        agg[x][0] += float(y)
        agg[x][1] += 1.0
    uniq = sorted(agg.items())
    gx = [x for x, _ in uniq]
    gy = [s / c for _, (s, c) in uniq]
    gw = [c for _, (_, c) in uniq]

    # 2. PAV: сливаем убывающие нарушения (с весами)
    sx: list[float] = []
    sy: list[float] = []
    sw: list[float] = []
    for x, y, w in zip(gx, gy, gw):
        sx.append(x); sy.append(y); sw.append(w)
        while len(sy) >= 2 and sy[-2] > sy[-1]:
            y2 = sy.pop(); w2 = sw.pop(); x2 = sx.pop()
            y1 = sy.pop(); w1 = sw.pop(); sx.pop()
            mw = w1 + w2
            sy.append((y1 * w1 + y2 * w2) / mw)
            sw.append(mw)
            sx.append(x2)            # блок представлен правой границей x
    return sx, sy


@dataclass
class Calibrator:
    min_samples: int = 30
    _xs: list[float] = field(default_factory=list)   # границы блоков (возрастают)
    _ys: list[float] = field(default_factory=list)   # калиброванные вероятности
    _n: int = 0
    fitted: bool = False

    def fit(self, raw_scores: list[float], successes: list[bool]) -> "Calibrator":
        self._n = len(raw_scores)
        if self._n < self.min_samples:
            self.fitted = False
            return self
        gx, gy = _pav(list(raw_scores), [1.0 if s else 0.0 for s in successes])
        self._xs, self._ys = gx, gy
        self.fitted = True
        return self

    def predict(self, raw: float) -> float:
        """Отображает сырую оценку в калиброванную вероятность.

        Изотоническая регрессия — кусочно-ПОСТОЯННАЯ ступенчатая функция: возвращаем
        значение первого блока, чья правая граница >= raw (стандартное поведение isotonic).
        Линейная интерполяция между блоками была бы неверна — она просаживала бы оценку,
        попавшую внутрь высокого блока, через «провал» к соседнему.

        Пока не обучен -> identity (консервативно: верь сырой оценке при высоком пороге).
        """
        if not self.fitted or not self._xs:
            return max(0.0, min(1.0, raw))
        i = bisect.bisect_left(self._xs, raw)
        if i >= len(self._ys):
            i = len(self._ys) - 1
        return max(0.0, min(1.0, self._ys[i]))

    # ---- персистентность ----
    def to_json(self) -> str:
        return json.dumps({"xs": self._xs, "ys": self._ys, "n": self._n,
                           "fitted": self.fitted, "min_samples": self.min_samples})

    @classmethod
    def from_json(cls, s: str) -> "Calibrator":
        d = json.loads(s)
        c = cls(min_samples=d.get("min_samples", 30))
        c._xs = list(d.get("xs", []))
        c._ys = list(d.get("ys", []))
        c._n = d.get("n", 0)
        c.fitted = d.get("fitted", False)
        return c
