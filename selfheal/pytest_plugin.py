"""Плагин pytest: фикстура `heal`, привязанная к `page` из pytest-playwright.

Подключение в conftest.py:
    pytest_plugins = ["selfheal.pytest_plugin"]

Использование в тесте:
    def test_login(page, heal):
        page.goto("https://example.com/login")
        heal.fill('#email', 'a@b.com', intent='поле email')
        heal.click('button[type=submit]', intent='кнопка входа')
"""
from __future__ import annotations

import os

try:
    import pytest
except Exception:  # pytest не обязателен для импорта пакета
    pytest = None  # type: ignore

from .config import Config
from .engine import HealEngine


if pytest is not None:

    @pytest.fixture
    def heal(page, request):  # noqa: ANN001
        cfg = Config(mode=os.environ.get("SELFHEAL_MODE", "propose"))
        test_id = request.node.nodeid.replace("::", "__")
        engine = HealEngine(page, test_id=test_id, cfg=cfg)
        yield engine
        # после теста: переобучить калибратор по накопленным исходам (дёшево, локально)
        try:
            engine.store.refit_calibrator()
        except Exception:
            pass
