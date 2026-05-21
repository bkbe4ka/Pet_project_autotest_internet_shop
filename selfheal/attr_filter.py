"""Фильтрация волатильных атрибутов.

Хеш-классы Webpack/Vite (css-1a2b3c), CSRF-nonce, рантайм-id отравляют сопоставление.
Удаляем их ДО сохранения отпечатка. Один этот фильтр резко снижает ложные срабатывания.
"""
from __future__ import annotations

import math
import re

# Атрибуты, которые почти всегда стабильны и осмысленны -> всегда оставляем.
STABLE_ATTRS = {
    "data-testid", "data-test", "data-cy", "data-qa", "name", "type",
    "role", "placeholder", "alt", "title", "href", "for", "aria-label",
}

# Явные паттерны сгенерированных/хешевых токенов в значениях класса.
_HASHY_CLASS_PATTERNS = [
    re.compile(r"^css-[a-z0-9]{5,}$", re.I),        # emotion / styled
    re.compile(r"^sc-[a-zA-Z0-9]{5,}$"),            # styled-components
    re.compile(r"^jss\d+$"),                         # JSS
    re.compile(r"^[A-Za-z]+-(?=[a-z0-9]*\d)[a-z0-9]{5,}$"),  # Mui-abc123 (суффикс ДОЛЖЕН содержать цифру)
    re.compile(r"^_[a-z0-9]{5,}$", re.I),            # CSS-modules _1a2b3
]


def _shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    counts: dict[str, int] = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def is_volatile_token(token: str) -> bool:
    """Эвристика: токен похож на сгенерированный машиной (хеш/nonce)?"""
    if not token:
        return False
    for pat in _HASHY_CLASS_PATTERNS:
        if pat.match(token):
            return True
    # высокая энтропия + смесь букв/цифр + длина -> вероятно хеш
    has_digit = any(c.isdigit() for c in token)
    has_alpha = any(c.isalpha() for c in token)
    if len(token) >= 8 and has_digit and has_alpha and _shannon_entropy(token) > 3.0:
        return True
    # чистый длинный hex
    if len(token) >= 8 and re.fullmatch(r"[0-9a-f]+", token, re.I):
        return True
    return False


def filter_class_value(class_value: str) -> str:
    """Оставляем только стабильные токены классов."""
    tokens = class_value.split()
    kept = [t for t in tokens if not is_volatile_token(t)]
    return " ".join(kept)


def filter_attrs(attrs: dict[str, str]) -> dict[str, str]:
    """Возвращает отфильтрованную копию атрибутов, пригодную для сопоставления."""
    out: dict[str, str] = {}
    for k, v in attrs.items():
        kl = k.lower()
        if kl == "class":
            cleaned = filter_class_value(v)
            if cleaned:
                out["class"] = cleaned
            continue
        if kl in STABLE_ATTRS or kl.startswith("aria-") or kl.startswith("data-"):
            # data-* в основном осмысленны; но если ЗНАЧЕНИЕ хешевое — отбрасываем
            if not is_volatile_token(v):
                out[kl] = v
            continue
        if kl == "id":
            if not is_volatile_token(v):
                out["id"] = v
            continue
        # прочие атрибуты оставляем, только если значение не выглядит сгенерированным
        if v and not is_volatile_token(v):
            out[kl] = v
    return out
