import datetime
import os

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# --- selfheal ---
from selfheal.config import Config
from selfheal.selenium_adapter import SeleniumHealEngine
from selfheal.engine import HealAbstained


class Base:
    def __init__(self, driver):
        self.driver = driver
        # один heal-движок на page-объект; test_id берём из текущего теста
        test_id = os.environ.get("PYTEST_CURRENT_TEST", "manual").split(" ")[0].replace("::", "__")
        mode = os.environ.get("SELFHEAL_MODE", "propose")     # propose | inline | off
        self._heal = SeleniumHealEngine(driver, test_id=test_id, cfg=Config(mode=mode))

    # ---------- heal-аware поиск ----------
    def find(self, xpath: str, intent: str, action: str = "click", timeout: float = 30.0):
        """Найти элемент по XPATH с самовосстановлением.

        intent  — человекочитаемое намерение (питает семантический матч и проверку идентичности).
        action  — readonly | navigate | fill | submit | destructive (влияет на порог доверия;
                  на счастливом пути не важен, срабатывает только при восстановлении).
        Если SELFHEAL_MODE=off — обычный WebDriverWait.
        """
        if os.environ.get("SELFHEAL_MODE", "propose") == "off":
            return WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((By.XPATH, xpath)))
        return self._heal.find(xpath, intent=intent, action=action, timeout=timeout)

    def scroll_to(self, element):
        """Прокрутить к элементу (вместо хрупких window.scrollTo с пиксельными константами)."""
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", element)

    def get_current_url(self):
        """Вернуть текущий URL (раньше только печатал, ничего не возвращая)."""
        url = self.driver.current_url
        print("Current url: " + url)
        return url

    def get_screenshot(self):
        now = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M.%S")
        screen_dir = os.path.join(os.getcwd(), "screen")
        os.makedirs(screen_dir, exist_ok=True)
        self.driver.save_screenshot(os.path.join(screen_dir, f"screenshot_{now}.png"))

    def assert_url(self, result):
        url = self.driver.current_url
        assert result in url, f"URL не совпал: ожидали подстроку '{result}', получили '{url}'"
        print("URL корректен")

    def assert_word(self, expected, actual):
        assert actual == expected, f"Текст не совпал: ожидали '{expected}', получили '{actual}'"
        print("Текст корректен")

    def cookies(self):
        try:
            self.find("//button[contains(text(),'ОК')]",
                      intent="кнопка принятия cookie-баннера",
                      action="navigate", timeout=10).click()
            print("Cookie-баннер закрыт")
        except (HealAbstained, TimeoutException):
            print("Cookie-баннер не появился или уже закрыт")
