"""ElementFingerprint — контракт между захватом (capture-time) и восстановлением (heal-time).

Захватывается на КАЖДОМ успешном ("зелёном") действии. В момент сбоя мы делаем
повторную идентификацию известной цели против этого отпечатка, а не угадываем с нуля.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class Intent:
    """Что тест на самом деле хотел сделать с элементом."""
    action: str                      # 'click' | 'fill' | 'check' | 'select' | ...
    role: str | None = None          # ARIA-роль
    accessible_name: str | None = None
    description: str | None = None    # человекочитаемое NL-описание (если задано в тесте)

    def to_text(self) -> str:
        """Нормализованная строка намерения для эмбеддинга/семантического матча."""
        parts = [self.role or "", self.accessible_name or "", self.description or ""]
        return " ".join(p.strip() for p in parts if p and p.strip()).lower()


@dataclass
class DomContext:
    tag: str = ""
    attrs: dict[str, str] = field(default_factory=dict)   # уже ОТФИЛЬТРОВАНЫ от волатильных
    text: str = ""
    rel_xpath: str = ""
    ancestor_roles: list[str] = field(default_factory=list)  # цепочка лендмарков: main>form>...
    sibling_signature: str = ""                              # хеш тегов+ролей соседей


@dataclass
class Visual:
    bbox: tuple[float, float, float, float] | None = None    # нормализовано к вьюпорту
    crop_ref: str | None = None                              # ссылка на сохранённый кроп
    embedding: list[float] | None = None                     # опц., лениво


@dataclass
class ElementFingerprint:
    test_id: str
    step_id: str
    intent: Intent
    locator_chain: list[str] = field(default_factory=list)   # [основной, ...запасные]
    dom: DomContext = field(default_factory=DomContext)
    a11y: dict[str, Any] = field(default_factory=dict)
    visual: Visual = field(default_factory=Visual)
    # стабильность на атрибут, выученная за N прогонов (0..1). Самый дешёвый "ML".
    stability: dict[str, float] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)

    # ---- сериализация ----
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ElementFingerprint":
        return cls(
            test_id=d["test_id"],
            step_id=d["step_id"],
            intent=Intent(**d["intent"]),
            locator_chain=list(d.get("locator_chain", [])),
            dom=DomContext(**d.get("dom", {})),
            a11y=dict(d.get("a11y", {})),
            visual=Visual(**d.get("visual", {})),
            stability=dict(d.get("stability", {})),
            provenance=dict(d.get("provenance", {})),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)

    @classmethod
    def from_json(cls, s: str) -> "ElementFingerprint":
        return cls.from_dict(json.loads(s))


def make_step_id(test_file: str, ordinal: int, primary_selector: str) -> str:
    """Стабильный идентификатор шага: один и тот же между прогонами, разный между шагами.

    Не зависит от текущей валидности селектора — поэтому переживает поломку.
    """
    raw = f"{test_file}::{ordinal}::{primary_selector}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def update_stability(prev: dict[str, float], current_attrs: dict[str, str],
                     last_attrs: dict[str, str], decay: float = 0.2) -> dict[str, float]:
    """Экспоненциально сглаженная стабильность на атрибут.

    Если атрибут совпал с предыдущим прогоном -> к 1.0, иначе -> к 0.0.
    Так мы ЭМПИРИЧЕСКИ узнаём, какие атрибуты надёжны на ЭТОМ приложении,
    вместо захардкоженного списка приоритетов.
    """
    out = dict(prev)
    keys = set(current_attrs) | set(last_attrs) | set(prev)
    for k in keys:
        matched = 1.0 if current_attrs.get(k) == last_attrs.get(k) and k in current_attrs else 0.0
        old = out.get(k, 0.5)
        out[k] = (1 - decay) * old + decay * matched
    return out
