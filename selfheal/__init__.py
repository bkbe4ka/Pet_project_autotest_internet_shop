"""selfheal — самовосстанавливающийся слой локаторов для Playwright (Python).

Публичный API:
    from selfheal import HealEngine, Config, HealPlanner
    from selfheal.fingerprint import ElementFingerprint, Intent
    from selfheal.strategies import ElementDescriptor
"""
from .config import Config, ActionClass
from .engine import HealEngine, HealAbstained
from .planner import HealPlanner, HealResult
from .fingerprint import ElementFingerprint, Intent, DomContext, Visual, make_step_id

__version__ = "0.1.0"

__all__ = [
    "Config", "ActionClass",
    "HealEngine", "HealAbstained",
    "HealPlanner", "HealResult",
    "ElementFingerprint", "Intent", "DomContext", "Visual", "make_step_id",
]
