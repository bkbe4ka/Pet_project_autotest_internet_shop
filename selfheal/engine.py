"""HealEngine — рантайм поверх Playwright.

Это единственное место, зависящее от Playwright. Тонкое: вся логика ранжирования живёт
в planner.py. Движок отвечает за:
  - счастливый путь (разрешить локатор) + захват отпечатка на успехе;
  - путь восстановления при сбое: извлечь кандидатов -> planner.plan -> верификация -> действие/воздержание;
  - кэш шага, аудит, предложения.

Импорт Playwright — отложенный, чтобы остальной пакет работал без него.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable

from .attr_filter import filter_attrs
from .config import ActionClass, Config
from .extractor import EXTRACTOR_JS
from .fingerprint import (DomContext, ElementFingerprint, Intent, Visual,
                          make_step_id, update_stability)
from .planner import HealPlanner
from .store import Store
from .audit import Audit
from .strategies.base import ElementDescriptor


class HealAbstained(Exception):
    """Бросается, когда восстановление не прошло гейт. Громкий сбой, не молчаливое неверное действие."""


@dataclass
class _StepCtx:
    test_id: str
    step_id: str
    ordinal: int


class HealEngine:
    def __init__(self, page: Any, test_id: str, cfg: Config | None = None) -> None:
        self.page = page
        self.test_id = test_id
        self.cfg = cfg or Config()
        self.store = Store(self.cfg.storage_dir)
        self.audit = Audit(self.cfg.storage_dir)
        self.planner = HealPlanner(self.cfg, self.store.load_calibrator())
        self._ordinal = 0

    # ---------- публичные обёртки действий ----------
    def click(self, selector: str, intent: str, **kw):
        return self._act("click", selector, intent, lambda loc: loc.click(**kw))

    def fill(self, selector: str, value: str, intent: str, **kw):
        return self._act("fill", selector, intent, lambda loc: loc.fill(value, **kw))

    def check(self, selector: str, intent: str, **kw):
        return self._act("check", selector, intent, lambda loc: loc.check(**kw))

    def locator(self, selector: str, intent: str):
        """Вернуть разрешённый (при необходимости восстановленный) локатор без действия."""
        return self._resolve("locate", selector, intent)

    # ---------- ядро ----------
    def _act(self, action: str, selector: str, intent: str,
             do: Callable[[Any], None], expect: Callable[[], bool] | None = None):
        loc = self._resolve(action, selector, intent)
        do(loc)
        if expect is not None and not expect():
            # верификация эффекта провалена -> вытесняем кэш, не считаем зелёным
            sid = make_step_id(self.test_id, self._ordinal, selector)
            self.store.cache_evict(sid)
            raise HealAbstained(f"эффект не подтверждён для шага {sid}")
        return loc

    def _resolve(self, action: str, selector: str, intent: str):
        self._ordinal += 1
        step_id = make_step_id(self.test_id, self._ordinal, selector)

        # кэш шага: уже восстановленный селектор воспроизводим на нативной скорости
        cached = self.store.cache_get(step_id)
        candidates_sel = [cached] if cached else []
        candidates_sel.append(selector)

        # 1. счастливый путь
        for sel in candidates_sel:
            try:
                loc = self._locator_from(sel)
                loc.wait_for(state="attached", timeout=self.cfg.happy_path_timeout_ms)
                self._capture(step_id, sel, loc, action, intent)
                return loc
            except Exception:
                continue

        # 2. путь восстановления
        fp = self.store.load_fingerprint(self.test_id, step_id)
        if fp is None:
            raise HealAbstained(
                f"шаг {step_id}: локатор '{selector}' не разрешился и нет отпечатка для восстановления")
        return self._heal(step_id, selector, action, intent, fp)

    def _heal(self, step_id: str, selector: str, action: str, intent: str,
              fp: ElementFingerprint):
        descriptors = self._extract_candidates()

        # стратегия [1]: какие запасные локаторы уникально разрешаются прямо сейчас?
        fallback_hits: set[int] = set()
        for fb in fp.locator_chain:
            try:
                loc = self._locator_from(fb)
                if loc.count() == 1:
                    # сопоставляем разрешённый элемент с дескриптором по bbox (приближённо)
                    hid = self._match_locator_to_descriptor(loc, descriptors)
                    if hid is not None:
                        fallback_hits.add(hid)
            except Exception:
                continue

        result = self.planner.plan(fp, descriptors, action, fallback_hits=fallback_hits)
        best = result.best
        dec = result.decision
        healed_selector = self._descriptor_to_selector(best.element) if best else None

        self.audit.record(fp, result.ranked, dec, healed_selector if dec.act else None)

        if dec.act and self.cfg.mode == "inline" and healed_selector:
            loc = self._locator_from(healed_selector)
            self.store.cache_set(step_id, healed_selector)
            # исход записываем оптимистично; верификация эффекта обновит при провале
            self.store.record_outcome(step_id, best.fused, True)
            return loc

        # воздержание -> предложение для человека
        if best and healed_selector:
            self.audit.propose(fp, best, healed_selector, dec)
        raise HealAbstained(f"шаг {step_id}: {dec.reason}")

    # ---------- захват ----------
    def _capture(self, step_id: str, selector: str, loc: Any, action: str, intent: str):
        try:
            desc = self._describe_locator(loc)
        except Exception:
            desc = None
        last = self.store.load_fingerprint(self.test_id, step_id)
        attrs = filter_attrs(desc.get("attrs", {})) if desc else {}
        stability = update_stability(
            last.stability if last else {},
            attrs,
            last.dom.attrs if last else {},
        )
        fp = ElementFingerprint(
            test_id=self.test_id,
            step_id=step_id,
            intent=Intent(action=action,
                          role=(desc or {}).get("role"),
                          accessible_name=(desc or {}).get("accessible_name"),
                          description=intent),
            locator_chain=self._build_locator_chain(selector, desc),
            dom=DomContext(
                tag=(desc or {}).get("tag", ""),
                attrs=attrs,
                text=(desc or {}).get("text", ""),
                rel_xpath=(desc or {}).get("rel_xpath", ""),
                ancestor_roles=(desc or {}).get("ancestor_roles", []),
                sibling_signature=(desc or {}).get("sibling_signature", ""),
            ),
            a11y={"role": (desc or {}).get("role", ""),
                  "name": (desc or {}).get("accessible_name", "")},
            visual=Visual(bbox=tuple((desc or {}).get("bbox")) if desc and desc.get("bbox") else None),
            stability=stability,
            provenance={"capturedAt": time.time()},
        )
        self.store.save_fingerprint(fp)

    def _build_locator_chain(self, primary: str, desc: dict | None) -> list[str]:
        chain = [primary]
        if not desc:
            return chain
        a = desc.get("attrs", {})
        if a.get("data-testid"):
            chain.append(f'[data-testid="{a["data-testid"]}"]')
        if desc.get("role") and desc.get("accessible_name"):
            chain.append(f'role={desc["role"]}[name="{desc["accessible_name"]}"]')
        if desc.get("text"):
            chain.append(f'text="{desc["text"][:40]}"')
        # уникализируем, сохраняя порядок
        seen, out = set(), []
        for c in chain:
            if c not in seen:
                seen.add(c); out.append(c)
        return out

    # ---------- мосты к Playwright (отделены, чтобы можно было мокать) ----------
    def _locator_from(self, selector: str):
        # поддержка псевдо-синтаксиса getByRole/getByTestId опускается для краткости;
        # реальная реализация маршрутизирует на page.get_by_* / page.locator
        return self.page.locator(selector)

    def _extract_candidates(self) -> list[ElementDescriptor]:
        raw = self.page.evaluate(EXTRACTOR_JS)
        out = []
        for r in raw:
            out.append(ElementDescriptor(
                handle_id=r["handle_id"],
                tag=r.get("tag", ""),
                attrs=filter_attrs(r.get("attrs", {})),
                text=r.get("text", ""),
                role=r.get("role", ""),
                accessible_name=r.get("accessible_name", ""),
                rel_xpath=r.get("rel_xpath", ""),
                ancestor_roles=r.get("ancestor_roles", []),
                sibling_signature=r.get("sibling_signature", ""),
                bbox=tuple(r["bbox"]) if r.get("bbox") else None,
                visible=r.get("visible", True),
                enabled=r.get("enabled", True),
            ))
        return out

    def _describe_locator(self, loc: Any) -> dict:
        return loc.evaluate("""el => {
            const attrs={}; for(const a of el.attributes){attrs[a.name]=a.value;}
            return {tag: el.tagName.toLowerCase(), attrs,
                    text:(el.textContent||'').trim().slice(0,120),
                    role: el.getAttribute('role')||'',
                    accessible_name:(el.getAttribute('aria-label')||el.textContent||'').trim().slice(0,120)};
        }""")

    def _match_locator_to_descriptor(self, loc: Any, descs: list[ElementDescriptor]) -> int | None:
        try:
            box = loc.bounding_box()
        except Exception:
            return None
        if not box:
            return None
        vw = self.page.viewport_size or {"width": 1280, "height": 720}
        nx, ny = box["x"] / vw["width"], box["y"] / vw["height"]
        best, bestd = None, 1e9
        for d in descs:
            if not d.bbox:
                continue
            dd = (d.bbox[0] - nx) ** 2 + (d.bbox[1] - ny) ** 2
            if dd < bestd:
                bestd, best = dd, d.handle_id
        return best if bestd < 0.001 else None

    def _descriptor_to_selector(self, el: ElementDescriptor) -> str:
        a = el.attrs
        if a.get("data-testid"):
            return f'[data-testid="{a["data-testid"]}"]'
        if a.get("id"):
            return f'#{a["id"]}'
        if el.role and el.accessible_name:
            return f'role={el.role}[name="{el.accessible_name}"]'
        if el.text:
            return f'text="{el.text[:40]}"'
        return f'xpath={el.rel_xpath}'
