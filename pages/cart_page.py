import time

import allure
from selenium.webdriver.common.action_chains import ActionChains

from base.base_class import Base
from utilities.logger import Logger


class Cart_final_page(Base):

    def __init__(self, driver):
        super().__init__(driver)
        self.driver = driver

    # Locators
    cart = "//div[@class='checkout_m1 checkout_m2']"
    favourites = "//div[@class='ea5_3_21-a checkout_q7']"
    delete = "//button[@class='checkout_q7 ag5_9_1-a0 ag5_9_1-a2']"
    final_delete = "//div[text()='Удалить']"
    my_favourite = "//a[@href='/my/favorites']"
    favourite_word = "//div[contains(text(), 'Избранное')]"

    def return_text(self):
        return self.find(self.cart, intent="заголовок корзины", action="readonly").text

    def get_favourites(self):
        return self.find(self.favourites,
                         intent="кнопка 'В избранное' у товара в корзине", action="navigate")

    def get_delete_button(self):
        return self.find(self.delete,
                         intent="кнопка удаления товара из корзины", action="destructive")

    def get_final_delete_button(self):
        return self.find(self.final_delete,
                         intent="подтверждение 'Удалить' в диалоге", action="destructive")

    def get_favourite_button(self):
        return self.find(self.my_favourite,
                         intent="ссылка перехода в раздел 'Избранное'", action="navigate")

    def get_favourite_word(self):
        return self.find(self.favourite_word,
                         intent="заголовок раздела 'Избранное'", action="readonly")

    def add_to_favourites(self):
        self.get_favourites().click()
        print("Add to favourites")

    def delete_product(self):
        self.get_delete_button().click()
        print("Click to delete")

    def final_delete_product(self):
        el = self.get_final_delete_button()
        ActionChains(self.driver).move_to_element(el).click().perform()
        print("Final delete")

    def favourite_product(self):
        self.get_favourite_button().click()
        print("Click to my favourite")

    """Methods"""

    def get_final_page(self):
        with allure.step("Get final page"):
            Logger.add_start_step(method="get_final_page")
            self.get_current_url()
            time.sleep(3)
            self.assert_url("https://www.ozon.ru/cart")
            self.assert_word("Корзина", self.return_text())
            self.add_to_favourites()
            self.delete_product()
            self.final_delete_product()
            self.favourite_product()
            self.assert_url("/my/favorites")
            Logger.add_end_step(self.driver.current_url, method="get_final_page")
