import time

import allure
from selenium.common import ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains


from base.base_class import Base
from utilities.logger import Logger


class Cart_final_page(Base):

    def __init__(self, driver):
        super().__init__(driver)
        self.driver = driver

    #Locators

    cart = "//div[@class='checkout_m1 checkout_m2']"
    favourites = "//div[@class='ea5_3_21-a checkout_q7']"
    delete = "//button[@class='checkout_q7 ag5_9_1-a0 ag5_9_1-a2']"
    final_delete = "//div[text()='Удалить']"
    my_favourite = "//a[@href='/my/favorites']"
    favourite_word = "//div[contains(text(), 'Избранное')]"

    #Return button

    def return_text(self):
        words = WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, self.cart)))
        return words.text

    def get_favourites(self):
        return WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, self.favourites)))

    def get_delete_button(self):
        return WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, self.delete)))

    def get_final_delete_button(self):
        return WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, self.final_delete)))

    def get_favourite_button(self):
        return WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, self.my_favourite)))

    def get_favourite_word(self):
        return WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, self.my_favourite)))

    def add_to_favourites(self):
        self.get_favourites().click()
        print("Add to favourites")

    def delete_product(self):
        self.get_delete_button().click()
        print("Click to delete")

    def final_delete_product(self):
        self.action = ActionChains(self.driver)
        self.action.move_to_element(self.get_final_delete_button()).click().perform()
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
            self.assert_url('https://www.ozon.ru/cart')
            self.assert_word("Корзина", self.return_text())
            self.add_to_favourites()
            self.delete_product()
            self.final_delete_product()
            self.favourite_product()
            self.assert_url('https://www.ozon.ru/my/favorites')
            Logger.add_end_step(self.driver.current_url, method="get_final_page")


