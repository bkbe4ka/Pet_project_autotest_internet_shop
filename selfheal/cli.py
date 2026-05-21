"""CLI `selfheal`: ревью предложений восстановления и отчёт.

  selfheal review        — показать ожидающие предложения (старый -> предложенный локатор)
  selfheal report        — сводка прогона (восстановлено / воздержано / предложено)
  selfheal calibrate     — переобучить калибратор по накопленным исходам

Примечание: авто-применение к исходникам тестов намеренно НЕ реализовано в MVP —
человек одобряет (через PR). Это и есть гарантия безопасности «никогда молча неверно».
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .store import Store
from .audit import Audit
from .config import Config


def _review(root: str) -> int:
    audit = Audit(root)
    pend = audit.pending_proposals()
    if not pend:
        print("Нет ожидающих предложений (тесты либо зелёные, либо восстановлены inline).")
        return 0
    print(f"Ожидающих предложений: {len(pend)}\n")
    for i, p in enumerate(pend, 1):
        print(f"[{i}] тест: {p['test_id']}  шаг: {p['step_id']}")
        print(f"    старый локатор:     {p.get('old_locator')}")
        print(f"    предложенный:       {p.get('proposed_selector')}")
        print(f"    уверенность p={p.get('calibrated'):.2f}  маржа={p.get('margin'):.2f}")
        print(f"    причина воздержания: {p.get('reason')}")
        cand = p.get("candidate", {})
        print(f"    кандидат: <{cand.get('tag')}> текст='{cand.get('text')}' "
              f"сигналы={cand.get('signals')}\n")
    print("Одобрение -> внесите предложенный локатор в исходник теста и закоммитьте "
          "(в полной версии это делает GitHub App / codemod).")
    return 0


def _report(root: str) -> int:
    log = Path(root) / "audit.jsonl"
    if not log.exists():
        print("Аудит пуст.")
        return 0
    healed = abstained = 0
    for line in log.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("decision", {}).get("act"):
            healed += 1
        else:
            abstained += 1
    print(f"Сводка восстановлений: inline-восстановлено={healed}  воздержано/предложено={abstained}")
    if healed and (healed + abstained) and healed / (healed + abstained) > 0.3:
        print("⚠  Высокая доля восстановлений — возможен крупный редизайн. "
              "Пометьте прогон для массового ревью, не доверяйте по шагам.")
    return 0


def _calibrate(root: str) -> int:
    store = Store(root)
    cal = store.refit_calibrator()
    xs, _ = store.all_outcomes()
    print(f"Калибратор переобучен. Исходов: {len(xs)}. Обучен: {cal.fitted} "
          f"(нужно ≥{cal.min_samples}).")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="selfheal")
    ap.add_argument("command", choices=["review", "report", "calibrate"])
    ap.add_argument("--dir", default=Config().storage_dir)
    args = ap.parse_args(argv)
    return {"review": _review, "report": _report, "calibrate": _calibrate}[args.command](args.dir)


if __name__ == "__main__":
    sys.exit(main())
