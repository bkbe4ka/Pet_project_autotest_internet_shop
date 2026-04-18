import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains


from base.base_class import Base


class Product_page(Base):

    def __init__(self, driver):
        super().__init__(driver)
        self.driver = driver

    #Locators

    cart = "//a[@data-widget='headerIcon']"
    button_add_to_cart = "//button[@style='background-color: var(--bgActionPrimary); border-radius: 16px;']"

    #Return button


    def get_cart(self):
        return WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, self.cart)))

    def get_button(self):
        return WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, self.button_add_to_cart)))

    def click_button(self):
        self.driver.execute_script("window.scrollTo(0, 300);")
        self.get_button().click()
        print("Button click")

    def click_cart(self):
        self.get_cart().click()
        print("Cart click")


    """Methods"""

    def get_product_page(self):
        self.get_current_url()
        time.sleep(3)
        self.click_button()
        self.click_cart()


