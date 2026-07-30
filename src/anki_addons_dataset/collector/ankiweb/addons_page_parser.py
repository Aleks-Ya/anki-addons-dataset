from typing import Optional

from bs4 import ResultSet, Tag, BeautifulSoup

from anki_addons_dataset.common.data_types import AddonHeader, AddonId, HtmlStr, AnkiVersion, URL, Rating


class AddonsPageParser:

    @staticmethod
    def parse_addons_page(html: HtmlStr) -> list[AddonHeader]:
        soup: BeautifulSoup = BeautifulSoup(html, 'html.parser')
        addon_rows: list[AddonHeader] = []
        main: Optional[Tag] = soup.find("main")
        if main is None:
            return addon_rows
        table: Optional[Tag] = main.find("table")
        if table is None:
            return addon_rows
        table_rows: ResultSet[Tag] = table.find_all("tr")
        table_rows.pop(0)  # remove header
        for row in table_rows:
            cells: ResultSet[Tag] = row.find_all("td")
            addon_name: str = cells[0].text
            addon_page: URL = URL(f"""https://ankiweb.net{cells[0].find("a")["href"]}""")
            addon_id: AddonId = AddonId(int(addon_page.split("/")[-1]))
            rating: Rating = Rating(int(cells[1].text))
            update_date: str = cells[2].text
            branches: AnkiVersion = AnkiVersion(cells[3].text)
            addon_header: AddonHeader = AddonHeader(addon_id, addon_name, addon_page, rating, update_date, branches)
            addon_rows.append(addon_header)
        return sorted(addon_rows, key=lambda header: header.id)
