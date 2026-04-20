import datetime
import os

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class Base():
    def __init__(self, driver):
        self.driver = driver

    """Get current url"""

    def get_current_url(self):
        get_url = self.driver.current_url
        print("Current url: " + get_url)

    """Get screen"""

    def get_screenshot(self):
        self.now_date = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M.%S")
        self.driver.save_screenshot(self.now_date + ".png")

    """Assert url"""

    def assert_url(self, result):
        get_url = self.driver.current_url
        assert get_url == result
        print("Get correct result")

    """Assert word"""
    def assert_word(self, word, xpath_word):
        try:
            self.word = word
            self.xpath_word = xpath_word
            assert xpath_word == word
            print("Correct word")
        except AssertionError:
            print(f"Word {word} != {xpath_word}")

    """Close cookie"""

    def cookies(self):
        try:
            cookie_accept_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'ОК')]"))
            )
            cookie_accept_button.click()
            print("Cookie-баннер закрыт")
        except:
            print("Cookie-баннер не появился или уже закрыт")
