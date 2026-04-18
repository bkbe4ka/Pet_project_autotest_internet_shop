import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains


from base.base_class import Base


class Monitor_filter_page(Base):

    def __init__(self, driver):
        super().__init__(driver)
        self.driver = driver

    #Locators

    radio_button = "//div[@class='x1b_7'][5]"
    original_brand = "//span[contains(text(), 'Оригинальный товар')]"
    hdmi_button = "//span[contains(text(), 'HDMI')]"
    game_button = "//span[contains(text(), 'Для игр')]"
    mat = "//span[contains(text(), 'Матовое')]"
    menu = "//*[@id='layoutPage']/div[1]/div/div/div/div[2]/div[2]/div[1]/div/div/div/div/div/div[1]/input"
    rating = "//span[contains(text(), 'С высоким рейтингом')]"
    cart = "//a[@href='/cart']"
    product = "//span[contains(text(), 'LOBOTi')]"
    assert_word = "//div[@class='checkout_m1 checkout_m2']"


    #Return button

    def scroll(self):
        self.driver.execute_script("window.scrollTo(0, 1200);")
        time.sleep(3)

    def choose_radio(self):
        return WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, self.radio_button)))


    def get_original(self):
        return WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, self.original_brand)))


    def get_hdmi(self):
        return WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, self.hdmi_button)))


    def get_game(self):
        return WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, self.game_button)))

    def get_mat(self):
        return WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, self.mat)))


    def get_menu(self):
        return WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, self.menu)))

    def get_rating(self):
        return WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, self.rating)))

    def get_cart(self):
        return WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, self.cart)))

    def get_product(self):
        return WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, self.product)))


    #Action

    def click_radio(self):
        self.driver.execute_script("window.scrollTo(0, 400);")
        self.choose_radio().click()
        print("Radio-button click")

    def click_original(self):
        self.scroll()
        self.get_original().click()
        print("Original brand click")

    def click_hdmi(self):
        self.scroll()
        self.get_hdmi().click()
        print("HDMI click")

    def click_game(self):
        self.scroll()
        self.get_game().click()
        print("Game click")

    def click_mat(self):
        self.scroll()
        self.get_mat().click()
        print("Mat click")

    def click_menu(self):
        self.driver.execute_script("window.scrollTo(0, -1200);")
        self.get_menu().click()
        print("Menu click")

    def click_rating(self):
        self.get_rating().click()
        print("High rating click")

    def click_product(self):
        self.driver.execute_script("window.scrollTo(0, 400);")
        self.get_product().click()
        print("Product click")


    """Methods"""

    def get_monitor_page(self):
        self.get_current_url()
        time.sleep(5)
        self.click_radio()
        time.sleep(3)
        self.click_original()
        self.click_hdmi()
        self.click_game()
        self.click_mat()
        self.click_menu()
        self.click_rating()
        self.click_product()
