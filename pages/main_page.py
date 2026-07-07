import time

import allure

from base.base_class import Base
from utilities.logger import Logger


class Main_page(Base):

    url = "https://www.ozon.ru/"

    def __init__(self, driver):
        super().__init__(driver)
        self.driver = driver

    # Locators
    burger_button = "//button[@class='b25_8_1-a4 b25_8_1-b6']"
    monitors = "//a[@href='/category/monitory-15738/']"

    # Return button (через self.find + intent)
    def choose_catalog(self):
        return self.find(self.burger_button,
                         intent="кнопка-бургер открытия каталога в шапке",
                         action="navigate")

    def get_monitor(self):
        return self.find(self.monitors,
                         intent="пункт 'Мониторы' в каталоге электроники",
                         action="navigate")

    # Action
    def click_catalog(self):
        el = self.choose_catalog()
        self.scroll_to(el)
        el.click()
        print("Catalog click")

    def click_monitor(self):
        el = self.get_monitor()
        self.scroll_to(el)
        el.click()
        print("Monitor click")

    """Methods"""

    def get_main_page(self):
        with allure.step("Get main page"):
            Logger.add_start_step(method="get_main_page")
            self.driver.get(self.url)
            time.sleep(3)
            self.get_current_url()
            self.cookies()                  # закрыть cookie-баннер, если есть
            self.click_catalog()
            self.click_monitor()
            Logger.add_end_step(self.driver.current_url, method="get_main_page")
