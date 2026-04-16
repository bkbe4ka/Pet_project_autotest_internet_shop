import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


from base.base_class import Base


class Main_page(Base):

    url = 'https://www.ozon.ru/'

    def __init__(self, driver):
        super().__init__(driver)
        self.driver = driver

    #Locators

    burger_button = "//button[@class='b25_8_1-a4 b25_8_1-b6']"
    monitors = "//a[@href='/category/monitory-15738/']"

    #Return button

    def choose_catalog(self):
        return WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, self.burger_button)))

    def get_monitor(self):
        return WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, self.monitors)))

    #Action

    def click_catalog(self):
        self.choose_catalog().click()
        print("Catalog click")

    def click_monitor(self):
        self.get_monitor().click()
        print("Monitor click")

    """Methods"""

    def get_main_page(self):
        self.driver.get(self.url)
        self.driver.maximize_window()
        time.sleep(3)
        self.get_current_url()
        self.click_catalog()
        self.click_monitor()