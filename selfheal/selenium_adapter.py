"""Selenium-адаптер для selfheal.

Мост между Selenium WebDriver и браузеро-независимым ядром (HealPlanner).
Ядро (стратегии/слияние/калибровка/гейт) переиспользуется как есть; здесь — только
извлечение кандидатов из живой страницы через driver.execute_script, захват отпечатка
на зелёном прогоне и исполнение решения (вернуть WebElement / воздержаться).

Извлекающий JS берётся из selfheal.extractor.EXTRACTOR_JS без изменений — это чистый DOM.

Зависит от selenium (ленивый импорт). Установка: pip install selenium
"""
from __future__ import annotations

import time
from typing import Any

from .attr_filter import filter_attrs
from .config import ActionClass, Config
from .extractor import EXTRACTOR_JS
from .fingerprint import (DomContext, ElementFingerprint, Intent, Visual,
                          make_step_id, update_stability)
from .planner import HealPlanner
from .store import Store
from .audit import Audit
from .strategies.base import ElementDescriptor
from .engine import HealAbstained   # переиспользуем то же исключение


# JS, описывающий ОДИН элемент (arguments[0]) теми же полями, что и экстрактор —
# нужно для захвата отпечатка известного-хорошего элемента.
_DESCRIBE_JS = r"""
const el = arguments[0];
const ROLE_LANDMARKS = ['main','navigation','form','search','banner','contentinfo','dialog','region'];
function roleOf(e){
  const r=e.getAttribute('role'); if(r) return r;
  const t=e.tagName.toLowerCase();
  if(t==='a'&&e.hasAttribute('href')) return 'link';
  if(t==='button') return 'button';
  if(t==='input'){const ty=(e.getAttribute('type')||'text').toLowerCase();
    if(['button','submit','reset'].includes(ty)) return 'button';
    if(ty==='checkbox') return 'checkbox'; if(ty==='radio') return 'radio'; return 'textbox';}
  if(t==='select') return 'combobox'; if(t==='textarea') return 'textbox'; return '';
}
function accName(e){
  const al=e.getAttribute('aria-label'); if(al) return al.trim();
  return (e.textContent||'').trim().slice(0,120);
}
function ancestorRoles(e){
  const out=[]; let n=e.parentElement;
  while(n&&out.length<8){const r=n.getAttribute('role')||''; const t=n.tagName.toLowerCase();
    if(ROLE_LANDMARKS.includes(r)) out.push(r);
    else if(['main','nav','form','header','footer','section','dialog'].includes(t)) out.push(t);
    n=n.parentElement;}
  return out.reverse();
}
function siblingSig(e){const p=e.parentElement; if(!p) return '';
  return Array.from(p.children).map(c=>c.tagName.toLowerCase()+':'+(roleOf(c)||'')).join('|');}
function relXPath(e){const parts=[]; let n=e;
  while(n&&n.nodeType===1&&parts.length<6){let i=1,s=n.previousElementSibling;
    while(s){if(s.tagName===n.tagName) i++; s=s.previousElementSibling;}
    parts.unshift(n.tagName.toLowerCase()+'['+i+']'); n=n.parentElement;}
  return '/'+parts.join('/');}
const attrs={}; for(const a of el.attributes){attrs[a.name]=a.value;}
const r=el.getBoundingClientRect();
return {tag: el.tagName.toLowerCase(), attrs, text:(el.textContent||'').trim().slice(0,120),
  role: roleOf(el), accessible_name: accName(el), rel_xpath: relXPath(el),
  ancestor_roles: ancestorRoles(el), sibling_signature: siblingSig(el),
  bbox:[r.x/innerWidth, r.y/innerHeight, r.width/innerWidth, r.height/innerHeight]};
"""


class SeleniumHealEngine:
    """Heal-движок поверх Selenium WebDriver.

    Использование (см. patch для Base): один экземпляр на драйвер/тест; метод find()
    возвращает WebElement (восстановленный при необходимости) или бросает HealAbstained.
    """

    def __init__(self, driver: Any, test_id: str, cfg: Config | None = None) -> None:
        self.driver = driver
        self.test_id = test_id
        self.cfg = cfg or Config()
        self.store = Store(self.cfg.storage_dir)
        self.audit = Audit(self.cfg.storage_dir)
        self.planner = HealPlanner(self.cfg, self.store.load_calibrator())
        self._ordinal = 0

    # ---------- публичный API ----------
    def find(self, xpath: str, intent: str, action: str = "click",
             timeout: float = 10.0):
        """Найти элемент по XPATH; при сбое — попытаться восстановить.

        Возвращает Selenium WebElement. Бросает HealAbstained, если не уверены.
        """
        from selenium.webdriver.common.by import By  # ленивый импорт

        self._ordinal += 1
        step_id = make_step_id(self.test_id, self._ordinal, xpath)

        # 1. счастливый путь: кэшированный локатор (если был восстановлен), затем оригинал
        cached = self.store.cache_get(step_id)
        attempts: list[tuple[Any, str]] = []
        if cached:
            by, val = _parse_cached(cached)
            attempts.append((by, val))
        attempts.append((By.XPATH, xpath))

        deadline = time.time() + timeout
        for by, val in attempts:
            el = self._find_one(by, val, deadline)
            if el is not None:
                self._capture(step_id, xpath, el, action, intent)
                return el

        # 2. путь восстановления
        fp = self.store.load_fingerprint(self.test_id, step_id)
        if fp is None:
            raise HealAbstained(
                f"шаг {step_id}: XPATH '{xpath}' не найден и нет отпечатка для восстановления")
        return self._heal(step_id, xpath, action, intent, fp)

    def click(self, xpath: str, intent: str, **kw):
        el = self.find(xpath, intent, action="click", **kw)
        el.click()
        return el

    # ---------- внутреннее ----------
    def _find_one(self, by: Any, value: str, deadline: float):
        """Вернуть элемент, только если он РОВНО ОДИН, видим и активен; иначе None."""
        while True:
            try:
                els = self.driver.find_elements(by, value)
                visible = [e for e in els if _safe(lambda: e.is_displayed())]
                if len(visible) == 1:
                    return visible[0]
                if len(els) == 1 and _safe(lambda: els[0].is_displayed()):
                    return els[0]
            except Exception:
                pass
            if time.time() >= deadline:
                return None
            time.sleep(0.25)

    def _heal(self, step_id: str, xpath: str, action: str, intent: str,
              fp: ElementFingerprint):
        descriptors = self._extract_candidates()

        # стратегия [1]: какие запасные локаторы из цепочки уникально разрешаются сейчас?
        fallback_hits: set[int] = set()
        for fb_by, fb_val, _ in _fallback_locators(fp):
            el = _safe(lambda: self.driver.find_elements(fb_by, fb_val))
            if el and len(el) == 1:
                hid = self._match_element_to_descriptor(el[0], descriptors)
                if hid is not None:
                    fallback_hits.add(hid)

        result = self.planner.plan(fp, descriptors, action, fallback_hits=fallback_hits)
        best, dec = result.best, result.decision
        healed = self._descriptor_to_locator(best.element) if best else None

        self.audit.record(fp, result.ranked, dec, str(healed) if dec.act else None)

        if dec.act and self.cfg.mode == "inline" and healed is not None:
            by, val = healed
            els = self.driver.find_elements(by, val)
            if len(els) == 1:
                self.store.cache_set(step_id, f"{_by_name(by)}::{val}")
                self.store.record_outcome(step_id, best.fused, True)
                return els[0]
            dec = type(dec)(False, "восстановленный локатор не уникален на странице",
                            dec.calibrated, dec.margin, dec.action_class)

        # воздержание -> предложение человеку
        if best and healed is not None:
            self.audit.propose(fp, best, f"{_by_name(healed[0])}::{healed[1]}", dec)
        raise HealAbstained(f"шаг {step_id}: {dec.reason}")

    def _capture(self, step_id: str, xpath: str, el: Any, action: str, intent: str):
        desc = _safe(lambda: self.driver.execute_script(_DESCRIBE_JS, el)) or {}
        last = self.store.load_fingerprint(self.test_id, step_id)
        attrs = filter_attrs(desc.get("attrs", {}))
        stability = update_stability(last.stability if last else {}, attrs,
                                     last.dom.attrs if last else {})
        fp = ElementFingerprint(
            test_id=self.test_id, step_id=step_id,
            intent=Intent(action=action, role=desc.get("role"),
                          accessible_name=desc.get("accessible_name"), description=intent),
            locator_chain=self._build_chain(xpath, desc),
            dom=DomContext(tag=desc.get("tag", ""), attrs=attrs,
                           text=desc.get("text", ""), rel_xpath=desc.get("rel_xpath", ""),
                           ancestor_roles=desc.get("ancestor_roles", []),
                           sibling_signature=desc.get("sibling_signature", "")),
            a11y={"role": desc.get("role", ""), "name": desc.get("accessible_name", "")},
            visual=Visual(bbox=tuple(desc["bbox"]) if desc.get("bbox") else None),
            stability=stability, provenance={"capturedAt": time.time(), "engine": "selenium"},
        )
        self.store.save_fingerprint(fp)

    def _build_chain(self, primary_xpath: str, desc: dict) -> list[str]:
        chain = [f"XPATH::{primary_xpath}"]
        a = desc.get("attrs", {})
        for key in ("data-testid", "data-test", "data-qa"):
            if a.get(key):
                chain.append(f'CSS::[{key}="{a[key]}"]')
        if a.get("id") and not _looks_hashed(a["id"]):
            chain.append(f'CSS::#{a["id"]}')
        if desc.get("text"):
            chain.append(f'XPATH::.//*[contains(text(),"{desc["text"][:40]}")]')
        seen, out = set(), []
        for c in chain:
            if c not in seen:
                seen.add(c); out.append(c)
        return out

    def _extract_candidates(self) -> list[ElementDescriptor]:
        raw = self.driver.execute_script("return (" + EXTRACTOR_JS + ")();") or []
        out = []
        for r in raw:
            out.append(ElementDescriptor(
                handle_id=r["handle_id"], tag=r.get("tag", ""),
                attrs=filter_attrs(r.get("attrs", {})), text=r.get("text", ""),
                role=r.get("role", ""), accessible_name=r.get("accessible_name", ""),
                rel_xpath=r.get("rel_xpath", ""), ancestor_roles=r.get("ancestor_roles", []),
                sibling_signature=r.get("sibling_signature", ""),
                bbox=tuple(r["bbox"]) if r.get("bbox") else None,
                visible=r.get("visible", True), enabled=r.get("enabled", True)))
        return out

    def _match_element_to_descriptor(self, el: Any, descs: list[ElementDescriptor]):
        box = _safe(lambda: self.driver.execute_script(
            "const r=arguments[0].getBoundingClientRect();"
            "return [r.x/innerWidth, r.y/innerHeight];", el))
        if not box:
            return None
        nx, ny = box
        best, bestd = None, 1e9
        for d in descs:
            if not d.bbox:
                continue
            dd = (d.bbox[0] - nx) ** 2 + (d.bbox[1] - ny) ** 2
            if dd < bestd:
                bestd, best = dd, d.handle_id
        return best if bestd < 0.001 else None

    def _descriptor_to_locator(self, el: ElementDescriptor):
        from selenium.webdriver.common.by import By
        a = el.attrs
        for key in ("data-testid", "data-test", "data-qa"):
            if a.get(key):
                return (By.CSS_SELECTOR, f'[{key}="{a[key]}"]')
        if a.get("id") and not _looks_hashed(a["id"]):
            return (By.CSS_SELECTOR, f'#{a["id"]}')
        if el.text:
            return (By.XPATH, f'.//*[normalize-space(text())="{el.text[:60]}"]')
        if el.rel_xpath:
            return (By.XPATH, el.rel_xpath)
        return None


# ---------- модульные хелперы ----------
def _safe(fn):
    try:
        return fn()
    except Exception:
        return None


def _looks_hashed(s: str) -> bool:
    from .attr_filter import is_volatile_token
    return is_volatile_token(s)


def _by_name(by: Any) -> str:
    return str(by).split(".")[-1] if by else "XPATH"


def _parse_cached(cached: str):
    from selenium.webdriver.common.by import By
    if "::" in cached:
        name, val = cached.split("::", 1)
        mapping = {"CSS": By.CSS_SELECTOR, "CSS_SELECTOR": By.CSS_SELECTOR,
                   "XPATH": By.XPATH, "ID": By.ID}
        return mapping.get(name, By.XPATH), val
    return By.XPATH, cached


def _fallback_locators(fp: ElementFingerprint):
    from selenium.webdriver.common.by import By
    for entry in fp.locator_chain[1:]:   # [0] — это сломавшийся оригинал
        if "::" in entry:
            name, val = entry.split("::", 1)
            by = By.CSS_SELECTOR if name.startswith("CSS") else By.XPATH
            yield by, val, entry
