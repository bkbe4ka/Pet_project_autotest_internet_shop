"""Стратегия [2]: переподбор по взвешенным атрибутам.

Оценка по взвешенному пересечению атрибутов кандидата с отпечатком, где веса —
это ВЫУЧЕННАЯ стабильность на атрибут (fp.stability). Учитывает уникальность на уровне
движка слияния (маржа), здесь же — чистая схожесть.
"""
from __future__ import annotations

from ..fingerprint import ElementFingerprint
from .base import ElementDescriptor

# Запасной приоритет атрибутов, пока не накоплена выученная стабильность.
_FALLBACK_PRIORITY = {
    "data-testid": 1.0, "data-test": 1.0, "data-cy": 1.0, "data-qa": 1.0,
    "id": 0.9, "name": 0.85, "role": 0.8, "type": 0.6,
    "aria-label": 0.8, "placeholder": 0.7, "href": 0.6, "alt": 0.6,
    "title": 0.5, "class": 0.25,
}


def _weight_for(attr: str, fp: ElementFingerprint) -> float:
    if attr in fp.stability:
        # выученная стабильность доминирует, когда есть
        return fp.stability[attr]
    if attr.startswith("data-"):
        return 0.9
    if attr.startswith("aria-"):
        return 0.75
    return _FALLBACK_PRIORITY.get(attr, 0.3)


class AttrWeightedStrategy:
    name = "attr"

    def score(self, fp: ElementFingerprint,
              candidates: list[ElementDescriptor]) -> dict[int, float]:
        target = fp.dom.attrs
        target_text = (fp.dom.text or "").strip().lower()
        out: dict[int, float] = {}
        for el in candidates:
            num = 0.0
            den = 0.0
            for attr, tval in target.items():
                w = _weight_for(attr, fp)
                den += w
                cval = el.attrs.get(attr)
                if cval is None:
                    continue
                if cval == tval:
                    num += w
                elif _soft_equal(cval, tval):
                    num += 0.6 * w
            # тег — слабый, но полезный сигнал
            if fp.dom.tag and el.tag:
                den += 0.3
                if el.tag == fp.dom.tag:
                    num += 0.3
            # совпадение видимого текста — сильный сигнал
            if target_text:
                den += 0.7
                el_text = (el.text or "").strip().lower()
                if el_text == target_text:
                    num += 0.7
                elif target_text in el_text or el_text in target_text:
                    num += 0.4
            score = num / den if den > 0 else 0.0
            if score > 0:
                out[el.handle_id] = round(score, 4)
        return out


def _soft_equal(a: str, b: str) -> bool:
    """Толерантность к мелкой нормализации (регистр, пробелы)."""
    return a.strip().lower() == b.strip().lower()
