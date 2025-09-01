import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver

from anki_addons_dataset.common.data_types import HtmlStr


class PageDownloader:
    def __init__(self, sleep_sec: int) -> None:
        options: Options = Options()
        options.add_argument('--headless')
        self.__driver: WebDriver = webdriver.Chrome(options=options)
        self.__sleep_sec: int = sleep_sec

    def __del__(self) -> None:
        self.__driver.quit()

    def load_page(self, url: str) -> HtmlStr:
        self.__driver.get(url)
        time.sleep(self.__sleep_sec)
        return HtmlStr(self.__driver.page_source)
