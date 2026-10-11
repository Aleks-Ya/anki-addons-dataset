from xlsxwriter import Workbook
from xlsxwriter.format import Format
from xlsxwriter.worksheet import Worksheet

from anki_addons_dataset.common.data_types import AiTagDefinition


class TagsSheet:
    __header_row: int = 0
    __name_col: int = 0
    __group_col: int = 1
    __description_col: int = 2

    def __init__(self, workbook: Workbook):
        self.__workbook: Workbook = workbook

    def create_sheet(self, tags: list[AiTagDefinition]) -> None:
        worksheet: Worksheet = self.__workbook.add_worksheet(name="Tags")
        self.__set_column_width(worksheet)
        self.__add_header(self.__workbook, worksheet)
        self.__add_rows(tags, worksheet)

    def __set_column_width(self, worksheet: Worksheet) -> None:
        worksheet.set_column(self.__name_col, self.__name_col, 20)
        worksheet.set_column(self.__group_col, self.__group_col, 10)
        worksheet.set_column(self.__description_col, self.__description_col, 100)

    def __add_header(self, workbook: Workbook, worksheet: Worksheet) -> None:
        header_format: Format = workbook.add_format({"bold": True, 'align': 'center'})
        worksheet.write_string(self.__header_row, self.__name_col, "Name", header_format)
        worksheet.write_string(self.__header_row, self.__group_col, "Group", header_format)
        worksheet.write_string(self.__header_row, self.__description_col, "Description", header_format)
        worksheet.freeze_panes(self.__header_row + 1, 0)

    def __add_rows(self, tags: list[AiTagDefinition], worksheet: Worksheet) -> None:
        for i, tag in enumerate(tags):
            row: int = self.__header_row + i + 1
            worksheet.write_string(row, self.__name_col, tag.name)
            worksheet.write_string(row, self.__group_col, tag.group)
            worksheet.write_string(row, self.__description_col, tag.description)
