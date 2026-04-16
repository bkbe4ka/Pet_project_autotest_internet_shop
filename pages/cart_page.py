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



    #Return button




    """Methods"""

    def get_final_page(self):
        self.driver.maximize_window()
        self.get_current_url()
        time.sleep(3)
        self.assert_url('https://www.ozon.ru/cart')


