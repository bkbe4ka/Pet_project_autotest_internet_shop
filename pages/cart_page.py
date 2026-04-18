import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains


from base.base_class import Base


class Cart_final_page(Base):

    def __init__(self, driver):
        super().__init__(driver)
        self.driver = driver

    #Locators

    cart = "//div[@class='checkout_m1 checkout_m2']"

    #Return button

    def return_text(self):
        words = WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, self.cart)))
        return words.text


    """Methods"""

    def get_final_page(self):
        self.get_current_url()
        time.sleep(3)
        self.assert_url('https://www.ozon.ru/cart')
        self.assert_word("Корзина", self.return_text())


