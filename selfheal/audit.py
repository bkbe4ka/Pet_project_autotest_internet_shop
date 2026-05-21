"""Аудит и предложения.

Каждое решение восстановления логируется (JSONL) с кандидатами, оценками и вердиктом.
Воздержания (и опц. inline-восстановления) дополнительно сохраняются как ПРЕДЛОЖЕНИЯ,
которые CLI превращает в PR/карточки на ревью человеку.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict
from pathlib import Path

from .scoring.gate import Decision
from .strategies.base import Candidate
from .fingerprint import ElementFingerprint


def _cand_brief(c: Candidate) -> dict:
    return {
        "handle_id": c.element.handle_id,
        "tag": c.element.tag,
        "text": (c.element.text or "")[:60],
        "attrs": c.element.attrs,
        "signals": c.signals,
        "fused": c.fused,
        "calibrated": c.calibrated,
        "notes": c.notes,
    }


class Audit:
    def __init__(self, root: str = ".selfheal") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.log_path = self.root / "audit.jsonl"
        self.proposals_path = self.root / "proposals.jsonl"

    def record(self, fp: ElementFingerprint, ranked: list[Candidate],
               decision: Decision, healed_selector: str | None) -> None:
        rec = {
            "ts": time.time(),
            "test_id": fp.test_id,
            "step_id": fp.step_id,
            "intent": asdict(fp.intent),
            "decision": asdict(decision),
            "healed_selector": healed_selector,
            "candidates": [_cand_brief(c) for c in ranked[:5]],
        }
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")

    def propose(self, fp: ElementFingerprint, best: Candidate,
                proposed_selector: str, decision: Decision) -> None:
        rec = {
            "ts": time.time(),
            "test_id": fp.test_id,
            "step_id": fp.step_id,
            "old_locator": fp.locator_chain[0] if fp.locator_chain else None,
            "proposed_selector": proposed_selector,
            "reason": decision.reason,
            "calibrated": decision.calibrated,
            "margin": decision.margin,
            "candidate": _cand_brief(best),
            "status": "pending",
        }
        with self.proposals_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")

    def pending_proposals(self) -> list[dict]:
        if not self.proposals_path.exists():
            return []
        out = []
        for line in self.proposals_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                d = json.loads(line)
                if d.get("status") == "pending":
                    out.append(d)
        return out
