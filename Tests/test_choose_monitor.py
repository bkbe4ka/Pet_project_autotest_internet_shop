import time

import allure

from conftest import switch_to_new_tab
from pages.cart_page import Cart_final_page
from pages.main_page import Main_page
from pages.monitors_page import Monitor_filter_page
from pages.product_page import Product_page


@allure.description("Test select product")
def test_select_product(driver):
    # driver приходит из фикстуры (conftest.py) и закрывается в teardown — quit() больше не забыт
    mp = Main_page(driver)
    mp.get_main_page()

    # переход на новую вкладку — устойчиво, без жёсткого window_handles[1]
    switch_to_new_tab(driver)
    monitors_page = Monitor_filter_page(driver)
    monitors_page.get_monitor_page()

    switch_to_new_tab(driver)
    prp = Product_page(driver)
    prp.get_product_page()

    switch_to_new_tab(driver)
    cp = Cart_final_page(driver)
    cp.get_final_page()

    # хотя бы одна осмысленная проверка результата сценария
    assert "favorites" in driver.current_url, \
        f"Ожидали переход в избранное, текущий URL: {driver.current_url}"
