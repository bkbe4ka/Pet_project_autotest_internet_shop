import time

import allure

from base.base_class import Base
from utilities.logger import Logger


class Monitor_filter_page(Base):

    def __init__(self, driver):
        super().__init__(driver)
        self.driver = driver

    # Locators
    radio_button = "//div[@class='x1b_7'][5]"          # хеш-класс + позиционный индекс -> хрупко
    original_brand = "//span[contains(text(), 'Оригинальный товар')]"
    hdmi_button = "//span[contains(text(), 'HDMI')]"
    game_button = "//span[contains(text(), 'Для игр')]"
    mat = "//span[contains(text(), 'Матовое')]"
    menu = "//*[@id='layoutPage']/div[1]/div/div/div/div[2]/div[2]/div[1]/div/div/div/div/div/div[1]/input"
    rating = "//span[contains(text(), 'С высоким рейтингом')]"
    cart = "//a[@href='/cart']"
    product = "//span[contains(text(), 'LOBOTi')]"

    # Return button (через self.find + intent)
    def choose_radio(self):
        return self.find(self.radio_button,
                         intent="радио-выбор раздела мониторов в каталоге", action="navigate")

    def get_original(self):
        return self.find(self.original_brand,
                         intent="фильтр 'Оригинальный товар'", action="navigate")

    def get_hdmi(self):
        return self.find(self.hdmi_button,
                         intent="фильтр 'HDMI' в характеристиках монитора", action="navigate")

    def get_game(self):
        return self.find(self.game_button,
                         intent="фильтр 'Для игр'", action="navigate")

    def get_mat(self):
        return self.find(self.mat,
                         intent="фильтр покрытия экрана 'Матовое'", action="navigate")

    def get_menu(self):
        return self.find(self.menu,
                         intent="поле ввода в панели фильтров", action="fill")

    def get_rating(self):
        return self.find(self.rating,
                         intent="сортировка 'С высоким рейтингом'", action="navigate")

    def get_cart(self):
        return self.find(self.cart,
                         intent="иконка перехода в корзину", action="navigate")

    def get_product(self):
        return self.find(self.product,
                         intent="карточка товара LOBOTi в выдаче", action="navigate")

    # Action — каждый клик: найти -> прокрутить к элементу -> кликнуть
    def _click(self, getter):
        el = getter()
        self.scroll_to(el)
        el.click()

    def click_radio(self):
        self._click(self.choose_radio); print("Radio-button click")

    def click_original(self):
        self._click(self.get_original); print("Original brand click")

    def click_hdmi(self):
        self._click(self.get_hdmi); print("HDMI click")

    def click_game(self):
        self._click(self.get_game); print("Game click")

    def click_mat(self):
        self._click(self.get_mat); print("Mat click")

    def click_menu(self):
        self._click(self.get_menu); print("Menu click")

    def click_rating(self):
        self._click(self.get_rating); print("High rating click")

    def click_product(self):
        self._click(self.get_product); print("Product click")

    """Methods"""

    def get_monitor_page(self):
        with allure.step("Get monitor page"):
            Logger.add_start_step(method="get_monitor_page")
            self.get_current_url()
            time.sleep(3)
            self.click_radio()
            self.click_original()
            self.click_hdmi()
            self.click_game()
            self.click_mat()
            self.click_menu()
            self.click_rating()
            self.click_product()
            Logger.add_end_step(self.driver.current_url, method="get_monitor_page")
