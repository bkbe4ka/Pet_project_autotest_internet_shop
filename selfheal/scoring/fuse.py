"""Слияние сигналов.

Берёт сырые оценки на стратегию для каждого кандидата и сливает их в одну сырую оценку
через логистическую модель. Изначально веса заданы вручную (config.FuseWeights);
позже заменяются весами, обученными на накопленных исходах восстановления.

КЛЮЧЕВОЙ выход помимо оценки — МАРЖА УНИКАЛЬНОСТИ: разрыв между кандидатом №1 и №2.
Это самый предсказательный одиночный признак: высокая оценка с малым разрывом = неоднозначность = воздержаться.
"""
from __future__ import annotations

import math

from ..config import FuseWeights
from ..strategies.base import Candidate


def _sigmoid(x: float) -> float:
    if x < -60:
        return 0.0
    if x > 60:
        return 1.0
    return 1.0 / (1.0 + math.exp(-x))


def fuse_candidate(c: Candidate, w: FuseWeights) -> float:
    s = c.signals
    z = (
        w.bias
        + w.fallback_hit * s.get("fallback", 0.0)
        + w.attr_score * s.get("attr", 0.0)
        + w.structural_score * s.get("structural", 0.0)
        + w.embedding_score * s.get("embedding", 0.0)
    )
    return _sigmoid(z)


def fuse_all(candidates: list[Candidate], w: FuseWeights) -> list[Candidate]:
    """Проставляет .fused каждому кандидату и сортирует по убыванию."""
    for c in candidates:
        c.fused = round(fuse_candidate(c, w), 4)
    candidates.sort(key=lambda c: c.fused, reverse=True)
    return candidates


def uniqueness_margin(sorted_candidates: list[Candidate]) -> float:
    """Разрыв между лучшим и вторым (по слитой оценке). 1.0, если кандидат один."""
    if not sorted_candidates:
        return 0.0
    if len(sorted_candidates) == 1:
        return 1.0
    return round(sorted_candidates[0].fused - sorted_candidates[1].fused, 4)
