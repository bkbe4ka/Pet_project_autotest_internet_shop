"""Базовые типы стратегий восстановления.

Ядро стратегий работает с ПЛОСКИМИ словарями (ElementDescriptor), извлечёнными из
живой страницы. Это значит, что вся логика ранжирования тестируется БЕЗ браузера —
именно так офлайн-демо доказывает, что healing-движок работает.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from ..fingerprint import ElementFingerprint


@dataclass
class ElementDescriptor:
    """Снимок ОДНОГО элемента-кандидата на текущей (возможно изменившейся) странице."""
    handle_id: int                       # как адресовать элемент обратно в адаптере
    tag: str = ""
    attrs: dict[str, str] = field(default_factory=dict)   # уже отфильтрованы
    text: str = ""
    role: str = ""
    accessible_name: str = ""
    rel_xpath: str = ""
    ancestor_roles: list[str] = field(default_factory=list)
    sibling_signature: str = ""
    bbox: tuple[float, float, float, float] | None = None
    visible: bool = True
    enabled: bool = True


@dataclass
class Candidate:
    element: ElementDescriptor
    # сырые оценки на стратегию (0..1); отсутствующие = 0
    signals: dict[str, float] = field(default_factory=dict)
    fused: float = 0.0                   # слитая сырая оценка (см. scoring/fuse)
    calibrated: float = 0.0              # калиброванная p(верно)
    notes: list[str] = field(default_factory=list)


class Strategy(Protocol):
    name: str

    def score(self, fp: ElementFingerprint,
              candidates: list[ElementDescriptor]) -> dict[int, float]:
        """Вернуть {handle_id: оценка 0..1} для элементов, которые стратегия считает совпадением."""
        ...
