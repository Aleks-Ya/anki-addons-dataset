import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver

from anki_addons_dataset.collector.ankiweb.addon_page_parser import AddonPageParser
from anki_addons_dataset.collector.ankiweb.addons_page_parser import AddonsPageParser
from anki_addons_dataset.common.data_types import AddonId, AddonInfo, AddonHeader
from anki_addons_dataset.common.json_helper import JsonHelper


class AnkiWebService:
    def __init__(self, raw_dir: Path, addon_page_parser: AddonPageParser) -> None:
        self.__addon_page_parser: AddonPageParser = addon_page_parser
        options: Options = Options()
        options.add_argument('--headless')
        self.__driver: WebDriver = webdriver.Chrome(options=options)
        raw_ankiweb_dir: Path = raw_dir / "1-anki-web"
        self.__raw_html_dir: Path = raw_ankiweb_dir / "html"
        self.__raw_json_dir: Path = raw_ankiweb_dir / "json"

    def __del__(self) -> None:
        self.__driver.quit()

    def load_addon_infos(self) -> list[AddonInfo]:
        addon_headers: list[AddonHeader] = self.__get_headers()
        addon_infos: list[AddonInfo] = self.__get_addon_infos(addon_headers)
        print(f"Addon number: {len(addon_infos)}")
        return addon_infos

    def __get_headers(self) -> list[AddonHeader]:
        html: str = self.__load_addons_page()
        addon_headers: list[AddonHeader] = AddonsPageParser.parse_addons_page(html)
        return addon_headers

    def __get_addon_infos(self, addon_headers: list[AddonHeader]) -> list[AddonInfo]:
        addon_infos: list[AddonInfo] = []
        for i, addon_header in enumerate(addon_headers):
            print(f"Parsing addon page: {addon_header.id} ({i}/{len(addon_headers)})")
            html: str = self.__load_addon_page(addon_header.id)
            addon_info: AddonInfo = self.__addon_page_parser.parse_addon_page(addon_header, html)
            addon_json_file: Path = self.__raw_json_dir / "addon" / f"{addon_header.id}.json"
            JsonHelper.write_addon_info_to_file(addon_info, addon_json_file)
            addon_infos.append(addon_info)
        return addon_infos

    def __load_addons_page(self) -> str:
        raw_file: Path = self.__raw_html_dir / "addons_page.html"
        if not raw_file.exists():
            print(f"Downloading addons page to {raw_file}")
            raw_file.parent.mkdir(parents=True, exist_ok=True)
            html: str = self.__load_page("https://ankiweb.net/shared/addons")
            raw_file.write_text(html)
        print(f"Reading addons page from {raw_file}")
        return raw_file.read_text()

    def __load_addon_page(self, addon_id: AddonId) -> str:
        raw_file: Path = self.__raw_html_dir / "addon" / f"{addon_id}.html"
        if not raw_file.exists():
            print(f"Downloading addon page to {raw_file}")
            raw_file.parent.mkdir(parents=True, exist_ok=True)
            html: str = self.__load_page(f"https://ankiweb.net/shared/info/{addon_id}")
            raw_file.write_text(html)
        return raw_file.read_text()

    def __load_page(self, url: str) -> str:
        self.__driver.get(url)
        time.sleep(3)
        return self.__driver.page_source
