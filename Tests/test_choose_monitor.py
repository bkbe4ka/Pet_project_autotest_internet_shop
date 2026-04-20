import time

from selenium import webdriver

from pages.cart_page import Cart_final_page
from pages.main_page import Main_page
from pages.monitors_page import Monitor_filter_page
from pages.product_page import Product_page


def test_select_product():
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    print("Start test")


    mp = Main_page(driver)
    mp.get_main_page()

    driver.switch_to.window(driver.window_handles[1])

    monitors_page = Monitor_filter_page(driver)
    monitors_page.get_monitor_page()

    driver.switch_to.window(driver.window_handles[2])
    prp = Product_page(driver)
    prp.get_product_page()

    driver.switch_to.window(driver.window_handles[3])
    cp = Cart_final_page(driver)
    cp.get_final_page()




    time.sleep(4)