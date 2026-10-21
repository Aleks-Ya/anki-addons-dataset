from xlsxwriter import Workbook
from xlsxwriter.format import Format
from xlsxwriter.worksheet import Worksheet

from anki_addons_dataset.common.data_types import AnkiRelease


class AnkiVersionsSheet:
    __header_row: int = 0
    __version_col: int = 0
    __point_version_col: int = 1

    def __init__(self, workbook: Workbook):
        self.__workbook: Workbook = workbook

    def create_sheet(self, anki_versions: list[AnkiRelease]) -> None:
        worksheet: Worksheet = self.__workbook.add_worksheet(name="Anki versions")
        self.__set_column_width(worksheet)
        self.__add_header(self.__workbook, worksheet)
        self.__add_rows(anki_versions, worksheet)

    def __set_column_width(self, worksheet: Worksheet) -> None:
        worksheet.set_column(self.__version_col, self.__version_col, 12)
        worksheet.set_column(self.__point_version_col, self.__point_version_col, 14)

    def __add_header(self, workbook: Workbook, worksheet: Worksheet) -> None:
        header_format: Format = workbook.add_format({"bold": True, 'align': 'center'})
        worksheet.write_string(self.__header_row, self.__version_col, "Version", header_format)
        worksheet.write_string(self.__header_row, self.__point_version_col, "Point version", header_format)
        worksheet.freeze_panes(self.__header_row + 1, 0)

    def __add_rows(self, anki_versions: list[AnkiRelease], worksheet: Worksheet) -> None:
        for i, anki_version in enumerate(anki_versions):
            row: int = self.__header_row + i + 1
            worksheet.write_string(row, self.__version_col, anki_version.version)
            worksheet.write_number(row, self.__point_version_col, anki_version.point_version)
