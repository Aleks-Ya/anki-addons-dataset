from bs4 import ResultSet, Tag, BeautifulSoup

from anki_addons_dataset.common.data_types import AddonHeader, AddonId, HtmlStr


class AddonsPageParser:

    @staticmethod
    def parse_addons_page(html: HtmlStr) -> list[AddonHeader]:
        soup: BeautifulSoup = BeautifulSoup(html, 'html.parser')
        addon_rows: list[AddonHeader] = []
        table_rows: ResultSet[Tag] = soup.find("main").find("table").find_all("tr")
        table_rows.pop(0)  # remove header
        for row in table_rows:
            cells: ResultSet[Tag] = row.find_all("td")
            addon_name: str = cells[0].text
            addon_page: str = f"""https://ankiweb.net{cells[0].find("a")["href"]}"""
            addon_id: AddonId = AddonId(int(addon_page.split("/")[-1]))
            rating: int = int(cells[1].text)
            update_date: str = cells[2].text
            versions: str = cells[3].text
            addon_header: AddonHeader = AddonHeader(addon_id, addon_name, addon_page, rating, update_date, versions)
            addon_rows.append(addon_header)
        return sorted(addon_rows, key=lambda header: header.id)
