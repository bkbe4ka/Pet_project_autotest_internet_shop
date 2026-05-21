"""Конфигурация: классы действий, пороги уверенности, веса слияния.

Это «ручки» бюджета доверия. Пороги — НА КАЛИБРОВАННЫХ вероятностях (см. scoring/calibrate.py),
а не на сырых оценках.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ActionClass(str, Enum):
    """Стоимость ошибки растёт сверху вниз -> порог тоже."""
    READONLY = "readonly"          # assert/hover/read
    NAVIGATE = "navigate"          # click по неразрушающему
    INPUT = "input"                # fill/select/check
    SUBMIT = "submit"              # submit/confirm (по умолчанию только-предложение)
    DESTRUCTIVE = "destructive"    # delete/pay/необратимое (НИКОГДА не авто)


# Какому классу принадлежит действие. Можно переопределить на уровне шага.
DEFAULT_ACTION_CLASS: dict[str, ActionClass] = {
    "assert": ActionClass.READONLY,
    "hover": ActionClass.READONLY,
    "get_text": ActionClass.READONLY,
    "click": ActionClass.NAVIGATE,
    "fill": ActionClass.INPUT,
    "select": ActionClass.INPUT,
    "check": ActionClass.INPUT,
    "submit": ActionClass.SUBMIT,
    "delete": ActionClass.DESTRUCTIVE,
    "pay": ActionClass.DESTRUCTIVE,
}


@dataclass
class GateConfig:
    # минимальная КАЛИБРОВАННАЯ p(верно) для inline авто-восстановления, на класс действия
    thresholds: dict[ActionClass, float] = field(default_factory=lambda: {
        ActionClass.READONLY: 0.70,
        ActionClass.NAVIGATE: 0.85,
        ActionClass.INPUT: 0.88,
        ActionClass.SUBMIT: 0.97,        # очень высокий; включается флагом
        ActionClass.DESTRUCTIVE: 1.01,   # >1 => НЕДОСТИЖИМО => всегда человек
    })
    # минимальный разрыв между кандидатом №1 и №2 (маржа уникальности)
    min_uniqueness_margin: float = 0.12
    # разрешать ли вообще inline-восстановление SUBMIT (по умолчанию нет — только предложение)
    allow_inline_submit: bool = False


@dataclass
class FuseWeights:
    """Начальные веса слияния сигналов (заменяются обученной логистикой по исходам)."""
    fallback_hit: float = 3.0      # запасной локатор уникально разрешился — сильнейший дешёвый сигнал
    attr_score: float = 1.6
    structural_score: float = 1.2
    embedding_score: float = 1.0
    bias: float = -2.2             # смещение: по умолчанию НЕ уверены


@dataclass
class Config:
    mode: str = "propose"          # 'inline' | 'propose' | 'off'
    storage_dir: str = ".selfheal"
    gate: GateConfig = field(default_factory=GateConfig)
    weights: FuseWeights = field(default_factory=FuseWeights)
    # таймаут счастливого пути (мс) до попытки восстановления
    happy_path_timeout_ms: int = 4000
    # доля от таймаута, отведённая встроенному восстановлению (см. бюджет задержки)
    inline_heal_budget_ms: int = 1500
