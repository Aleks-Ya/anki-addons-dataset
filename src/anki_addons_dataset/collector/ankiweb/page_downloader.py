from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from anki_addons_dataset.common.data_types import HtmlStr


class PageDownloader:
    def __init__(self) -> None:
        options: Options = Options()
        options.add_argument('--headless')
        self.__driver: WebDriver = webdriver.Chrome(options=options)
        self.__wait: WebDriverWait = WebDriverWait(self.__driver, 10)

    def __del__(self) -> None:
        self.__driver.quit()

    def load_page(self, url: str) -> HtmlStr:
        self.__driver.get(url)
        self.__wait.until(expected_conditions.presence_of_element_located((By.XPATH, "/html/body/div/main")))
        return HtmlStr(self.__driver.page_source)
