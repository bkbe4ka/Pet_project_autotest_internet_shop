import datetime
import os


class Base():
    def __init__(self, driver):
        self.driver = driver

    """Get current url"""

    def get_current_url(self):
        get_url = self.driver.current_url
        print("Current url: " + get_url)

    """Get screen"""



    """Assert url"""

    def assert_url(self, result):
        get_url = self.driver.current_url
        assert get_url == result
        print("Get correct result")

    """Assert word"""
    def assert_word(self, word, xpath_word):
        self.word = word
        self.xpath_word = xpath_word
        assert xpath_word == word
        print("Correct word")

