"""Стратегия [3]: структурное сопоставление.

Матч по цепочке ролей предков, сигнатуре соседей и относительной позиции.
Ловит «компонент переехал / добавлены div-обёртки», когда атрибуты бесполезны.
"""
from __future__ import annotations

from ..fingerprint import ElementFingerprint
from .base import ElementDescriptor


def _trail_similarity(a: list[str], b: list[str]) -> float:
    """Похожесть двух цепочек лендмарков по самому длинному общему суффиксу.

    Суффикс (ближайшие предки) важнее корня — добавление обёрток у корня не должно ломать матч.
    """
    if not a or not b:
        return 0.0
    a_r, b_r = list(reversed(a)), list(reversed(b))
    common = 0
    for x, y in zip(a_r, b_r):
        if x == y:
            common += 1
        else:
            break
    return common / max(len(a), len(b))


class StructuralStrategy:
    name = "structural"

    def score(self, fp: ElementFingerprint,
              candidates: list[ElementDescriptor]) -> dict[int, float]:
        t_roles = fp.dom.ancestor_roles
        t_sig = fp.dom.sibling_signature
        t_tag = fp.dom.tag
        out: dict[int, float] = {}
        for el in candidates:
            score = 0.0
            weight = 0.0

            weight += 0.5
            score += 0.5 * _trail_similarity(t_roles, el.ancestor_roles)

            if t_sig:
                weight += 0.3
                if el.sibling_signature == t_sig:
                    score += 0.3
                elif _sig_overlap(t_sig, el.sibling_signature) > 0.5:
                    score += 0.18

            if t_tag:
                weight += 0.2
                if el.tag == t_tag:
                    score += 0.2

            final = score / weight if weight > 0 else 0.0
            if final > 0:
                out[el.handle_id] = round(final, 4)
        return out


def _sig_overlap(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    sa, sb = set(a.split("|")), set(b.split("|"))
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)
