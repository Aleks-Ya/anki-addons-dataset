from xlsxwriter import Workbook
from xlsxwriter.format import Format
from xlsxwriter.worksheet import Worksheet

from anki_addons_dataset.common.data_types import Aggregation, DatasetVersionMetadata, RawMetadata


class AggregationSheet:
    __title_row_top: int = 0
    __header_row: int = 2
    __property_col: int = 0
    __value_col: int = 1
    __c_col: int = 2
    __d_col: int = 3
    __e_col: int = 4
    __f_col: int = 5
    __h_col: int = 7
    __i_col: int = 8
    __j_col: int = 9
    __k_col: int = 10

    def __init__(self, workbook: Workbook):
        self.__workbook: Workbook = workbook

    def create_sheet(self, aggregation: Aggregation, dataset_version_metadata: DatasetVersionMetadata,
                     raw_metadata: RawMetadata) -> None:
        worksheet: Worksheet = self.__workbook.add_worksheet(name="Addons")
        self.__add_title(self.__workbook, worksheet, dataset_version_metadata, raw_metadata)
        self.__set_column_width(worksheet)
        self.__add_header(self.__workbook, worksheet)
        self.__add_rows(aggregation, worksheet)

    def __add_title(self, workbook: Workbook, worksheet: Worksheet,
                    dataset_version_metadata: DatasetVersionMetadata, raw_metadata: RawMetadata) -> None:
        title_format: Format = workbook.add_format({"bold": True, 'align': 'left', 'font_size': 18})
        property_name_format: Format = workbook.add_format({'align': 'right', 'valign': 'vcenter'})
        date_format: Format = workbook.add_format({'align': 'left', 'valign': 'vcenter', "num_format": "yyyy-mm-dd"})
        worksheet.merge_range(data="Anki Addons Dataset", cell_format=title_format,
                              first_row=self.__title_row_top, last_row=self.__title_row_top,
                              first_col=self.__property_col, last_col=self.__value_col)
        worksheet.merge_range(data="Data collected:", cell_format=property_name_format,
                              first_row=self.__title_row_top, last_row=self.__title_row_top,
                              first_col=self.__c_col, last_col=self.__d_col)
        if raw_metadata.start_timestamp:
            worksheet.merge_range(data=f"{raw_metadata.start_timestamp.date()}",
                                  cell_format=date_format,
                                  first_row=self.__title_row_top, last_row=self.__title_row_top,
                                  first_col=self.__e_col, last_col=self.__f_col)
        worksheet.merge_range(data="Report generated:", cell_format=property_name_format,
                              first_row=self.__title_row_top, last_row=self.__title_row_top,
                              first_col=self.__h_col, last_col=self.__i_col)
        worksheet.merge_range(data=f"{dataset_version_metadata.creation_date}",
                              cell_format=date_format,
                              first_row=self.__title_row_top, last_row=self.__title_row_top,
                              first_col=self.__j_col, last_col=self.__k_col)

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
