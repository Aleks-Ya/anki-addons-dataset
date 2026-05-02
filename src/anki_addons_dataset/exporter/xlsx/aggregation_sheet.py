from xlsxwriter import Workbook
from xlsxwriter.format import Format
from xlsxwriter.worksheet import Worksheet

from anki_addons_dataset.common.data_types import Aggregation


class AggregationSheet:
    __title_row_top: int = 0
    __header_row: int = 2
    __property_col: int = 0
    __value_col: int = 1

    def __init__(self, workbook: Workbook):
        self.__workbook: Workbook = workbook

    def create_sheet(self, aggregation: Aggregation) -> None:
        worksheet: Worksheet = self.__workbook.add_worksheet(name="Addons")
        self.__add_title(self.__workbook, worksheet)
        self.__set_column_width(worksheet)
        self.__add_header(self.__workbook, worksheet)
        self.__add_rows(aggregation, worksheet)

    def __add_title(self, workbook: Workbook, worksheet: Worksheet) -> None:
        title_format: Format = workbook.add_format({"bold": True, 'align': 'left', 'font_size': 18})
        worksheet.merge_range(data="Anki Addons Dataset", cell_format=title_format,
                              first_row=self.__title_row_top, last_row=self.__title_row_top,
                              first_col=self.__property_col, last_col=self.__value_col)

    def __set_column_width(self, worksheet: Worksheet) -> None:
        worksheet.set_column(self.__property_col, self.__property_col, 40)
        worksheet.set_column(self.__value_col, self.__value_col, 20)

    def __add_header(self, workbook: Workbook, worksheet: Worksheet) -> None:
        header_format: Format = workbook.add_format({"bold": True, 'align': 'center'})
        worksheet.write_string(self.__header_row, self.__property_col, "Property", header_format)
        worksheet.write_string(self.__header_row, self.__value_col, "Value", header_format)

    def __add_rows(self, aggregation: Aggregation, worksheet: Worksheet) -> None:
        values: dict[str, int] = {
            "Addon number": aggregation.addon_number,
            "Addon with GitHub number": aggregation.addon_with_github_number,
            "Addon with Anki forum page number": aggregation.addon_with_anki_forum_page_number,
            "Addon with unit-tests number": aggregation.addon_with_unit_tests_number
        }
        for i, (name, value) in enumerate(values.items()):
            row: int = self.__header_row + i + 1
            worksheet.write_string(row, self.__property_col, name)
            worksheet.write_number(row, self.__value_col, value)
