"""Гейт бюджета доверия.

Решает: ДЕЙСТВОВАТЬ inline, или ВОЗДЕРЖАТЬСЯ (и предложить человеку).
По умолчанию — воздержание. Громкий сбой предпочтительнее молчаливого неверного действия.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..config import ActionClass, GateConfig, DEFAULT_ACTION_CLASS
from ..strategies.base import Candidate
from ..fingerprint import ElementFingerprint


@dataclass
class Decision:
    act: bool
    reason: str
    calibrated: float
    margin: float
    action_class: ActionClass


def classify_action(action: str, override: ActionClass | None = None) -> ActionClass:
    if override is not None:
        return override
    return DEFAULT_ACTION_CLASS.get(action, ActionClass.NAVIGATE)


def identity_consistent(best: Candidate, fp: ElementFingerprint) -> bool:
    """Семантическая согласованность: 'Delete'-отпечаток не должен лечиться в 'Save'.

    Если у отпечатка есть роль/имя и у кандидата они есть и явно конфликтуют — запрет.
    """
    el = best.element
    want_role = (fp.intent.role or fp.a11y.get("role") or "").strip().lower()
    if want_role and el.role and el.role.strip().lower() != want_role:
        # роль конфликтует — но допускаем близкие пары (button/link часто взаимозаменяемы)
        interchangeable = {("button", "link"), ("link", "button")}
        if (want_role, el.role.strip().lower()) not in interchangeable:
            return False
    want_name = (fp.intent.accessible_name or "").strip().lower()
    if want_name and el.accessible_name:
        a = want_name
        b = el.accessible_name.strip().lower()
        if a != b and a not in b and b not in a:
            # имена явно расходятся — подозрительно, но не жёсткий запрет (текст мог смениться)
            best.notes.append(f"имя расходится: хотели '{a}', нашли '{b}'")
    return True


def gate(best: Candidate, sorted_candidates: list[Candidate], margin: float,
         action: str, fp: ElementFingerprint, cfg: GateConfig,
         action_class_override: ActionClass | None = None,
         allow_inline_submit: bool = False) -> Decision:
    ac = classify_action(action, action_class_override)
    threshold = cfg.thresholds[ac]

    # необратимое — никогда не авто
    if ac == ActionClass.DESTRUCTIVE:
        return Decision(False, "разрушающее действие — только человек", best.calibrated, margin, ac)
    if ac == ActionClass.SUBMIT and not (allow_inline_submit or cfg.allow_inline_submit):
        return Decision(False, "submit по умолчанию только-предложение", best.calibrated, margin, ac)

    if not identity_consistent(best, fp):
        return Decision(False, "конфликт идентичности (роль)", best.calibrated, margin, ac)

    if margin < cfg.min_uniqueness_margin:
        return Decision(False, f"неоднозначно: маржа {margin:.2f} < {cfg.min_uniqueness_margin:.2f}",
                        best.calibrated, margin, ac)

    if best.calibrated < threshold:
        return Decision(False, f"низкая уверенность {best.calibrated:.2f} < порог {threshold:.2f}",
                        best.calibrated, margin, ac)

    if not best.element.visible or not best.element.enabled:
        return Decision(False, "элемент не видим/не активен", best.calibrated, margin, ac)

    return Decision(True, f"восстановлено: p={best.calibrated:.2f}, маржа={margin:.2f}",
                    best.calibrated, margin, ac)
