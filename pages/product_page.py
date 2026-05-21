import time

import allure

from base.base_class import Base
from utilities.logger import Logger


class Product_page(Base):

    def __init__(self, driver):
        super().__init__(driver)
        self.driver = driver

    # Locators
    cart = "//a[@data-widget='headerIcon']"            # хороший локатор: data-widget стабилен
    button_add_to_cart = "//button[@class='pdp_a1f']"  # хеш-класс -> selfheal подстрахует

    def get_cart(self):
        return self.find(self.cart,
                         intent="иконка корзины в шапке", action="navigate")

    def get_button(self):
        return self.find(self.button_add_to_cart,
                         intent="кнопка 'Добавить в корзину' в карточке товара",
                         action="navigate")

    def click_button(self):
        el = self.get_button()
        self.scroll_to(el)
        el.click()
        print("Button click")

    def click_cart(self):
        self.get_cart().click()
        print("Cart click")

    """Methods"""

    def get_product_page(self):
        with allure.step("Get product page"):
            Logger.add_start_step(method="get_product_page")
            self.get_current_url()
            time.sleep(3)
            self.click_button()
            self.click_cart()
            self.get_screenshot()
            Logger.add_end_step(self.driver.current_url, method="get_product_page")
