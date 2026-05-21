"""Стратегия [5]: семантический матч по эмбеддингам.

Эмбеддим нормализованную строку намерения (role + accessible_name + ближний текст)
и берём косинус против эмбеддинга отпечатка. Полезно, когда метки/текст переформулировали,
а атрибуты сменились.

Эмбеддер ПЛАГИННЫЙ:
  - если установлен sentence-transformers -> используем настоящую модель (локально, без сети);
  - иначе -> детерминированный fallback на хешированных символьных n-граммах.
Fallback слабее, но позволяет демо и тестам работать офлайн без зависимостей.
"""
from __future__ import annotations

import hashlib
import math
from functools import lru_cache

from ..fingerprint import ElementFingerprint
from .base import ElementDescriptor

_DIM = 256


def _ngrams(s: str, n: int = 3) -> list[str]:
    s = f"  {s.lower().strip()}  "
    return [s[i:i + n] for i in range(len(s) - n + 1)]


@lru_cache(maxsize=4096)
def _fallback_embed(text: str) -> tuple[float, ...]:
    """Детерминированный bag-of-char-ngrams -> хешированный вектор -> L2-норма."""
    vec = [0.0] * _DIM
    for g in _ngrams(text):
        h = int(hashlib.md5(g.encode("utf-8")).hexdigest(), 16)
        idx = h % _DIM
        sign = 1.0 if (h >> 8) & 1 else -1.0
        vec[idx] += sign
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return tuple(v / norm for v in vec)


class _Embedder:
    def __init__(self) -> None:
        self._model = None
        try:  # настоящая модель, если доступна — но никогда не обязательна
            from sentence_transformers import SentenceTransformer  # type: ignore
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            self._model = None

    def embed(self, text: str) -> list[float]:
        if not text:
            return [0.0] * _DIM
        if self._model is not None:
            return list(self._model.encode(text, normalize_embeddings=True))
        return list(_fallback_embed(text))

    @property
    def backend(self) -> str:
        return "sentence-transformers" if self._model is not None else "hashed-ngram-fallback"


_EMBEDDER: _Embedder | None = None


def get_embedder() -> _Embedder:
    global _EMBEDDER
    if _EMBEDDER is None:
        _EMBEDDER = _Embedder()
    return _EMBEDDER


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    # векторы уже нормализованы -> dot == cosine; клипуем в [0,1]
    return max(0.0, min(1.0, dot))


def _candidate_intent_text(el: ElementDescriptor) -> str:
    parts = [el.role or "", el.accessible_name or "", (el.text or "")[:80]]
    return " ".join(p.strip() for p in parts if p.strip()).lower()


class EmbeddingStrategy:
    name = "embedding"

    def score(self, fp: ElementFingerprint,
              candidates: list[ElementDescriptor]) -> dict[int, float]:
        emb = get_embedder()
        target_text = fp.intent.to_text() or fp.dom.text or ""
        if not target_text:
            return {}
        target_vec = fp.visual.embedding or emb.embed(target_text)
        out: dict[int, float] = {}
        for el in candidates:
            ctext = _candidate_intent_text(el)
            if not ctext:
                continue
            sim = _cosine(target_vec, emb.embed(ctext))
            if sim > 0:
                out[el.handle_id] = round(sim, 4)
        return out
