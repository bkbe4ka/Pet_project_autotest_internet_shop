"""Корневой conftest.py.

Лежит В КОРНЕ проекта (а не в utilities/), иначе pytest не видит фикстуры из Tests/.
Содержит фикстуру драйвера с teardown (driver.quit()), которой раньше не было.
"""
import pytest
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait


@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    drv = webdriver.Chrome(options=options)
    drv.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    drv.maximize_window()
    yield drv
    drv.quit()                      # <-- teardown: браузер больше не висит после прогона


def switch_to_new_tab(driver, timeout: int = 15):
    """Переключиться на последнюю открытую вкладку (устойчиво вместо window_handles[N]).

    Ждём, пока вкладок станет больше, затем берём самую новую. Не ломается от
    лишнего popup и не зависит от жёсткого индекса.
    """
    current = len(driver.window_handles)
    WebDriverWait(driver, timeout).until(lambda d: len(d.window_handles) >= current)
    driver.switch_to.window(driver.window_handles[-1])
    return driver.current_window_handle
