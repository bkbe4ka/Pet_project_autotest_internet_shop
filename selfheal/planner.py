"""HealPlanner — алгоритмическое ядро, НЕ зависящее от браузера.

На вход: отпечаток (последний-известный-хороший) + список ElementDescriptor'ов,
извлечённых из текущей (изменившейся) страницы. На выход: ранжированные кандидаты + Decision.

Не зависит от Playwright -> полностью тестируется офлайн. Движок (engine.py) лишь
поставляет дескрипторы из живой страницы и исполняет решение.
"""
from __future__ import annotations

from dataclasses import dataclass

from .config import ActionClass, Config
from .fingerprint import ElementFingerprint
from .scoring.calibrate import Calibrator
from .scoring.fuse import fuse_all, uniqueness_margin
from .scoring.gate import Decision, gate
from .strategies.base import Candidate, ElementDescriptor
from .strategies.attr_weighted import AttrWeightedStrategy
from .strategies.structural import StructuralStrategy
from .strategies.embedding_match import EmbeddingStrategy


@dataclass
class HealResult:
    ranked: list[Candidate]
    decision: Decision
    best: Candidate | None


class HealPlanner:
    def __init__(self, cfg: Config | None = None,
                 calibrator: Calibrator | None = None) -> None:
        self.cfg = cfg or Config()
        self.calibrator = calibrator or Calibrator()
        self.strategies = [
            AttrWeightedStrategy(),
            StructuralStrategy(),
            EmbeddingStrategy(),
        ]

    def plan(self, fp: ElementFingerprint,
             candidates: list[ElementDescriptor],
             action: str,
             fallback_hits: set[int] | None = None,
             action_class_override: ActionClass | None = None) -> HealResult:
        """fallback_hits: handle_id'ы, для которых запасной локатор уникально разрешился
        (стратегия [1], проверяется движком против живой страницы)."""
        fallback_hits = fallback_hits or set()

        # 1. собрать сигналы со всех стратегий
        by_id: dict[int, Candidate] = {
            el.handle_id: Candidate(element=el) for el in candidates
        }
        for el in candidates:
            if el.handle_id in fallback_hits:
                by_id[el.handle_id].signals["fallback"] = 1.0

        for strat in self.strategies:
            scores = strat.score(fp, candidates)
            for hid, sc in scores.items():
                if hid in by_id:
                    by_id[hid].signals[strat.name] = sc

        cand_list = list(by_id.values())

        # 2. слить -> сырая оценка; отсортировать
        ranked = fuse_all(cand_list, self.cfg.weights)

        # 3. калибровать -> p(верно)
        for c in ranked:
            c.calibrated = round(self.calibrator.predict(c.fused), 4)

        # 4. маржа уникальности + гейт
        margin = uniqueness_margin(ranked)
        best = ranked[0] if ranked else None
        if best is None:
            dec = Decision(False, "нет кандидатов", 0.0, 0.0, ActionClass.NAVIGATE)
            return HealResult([], dec, None)

        dec = gate(best, ranked, margin, action, fp, self.cfg.gate,
                   action_class_override=action_class_override,
                   allow_inline_submit=self.cfg.gate.allow_inline_submit)
        return HealResult(ranked, dec, best)
