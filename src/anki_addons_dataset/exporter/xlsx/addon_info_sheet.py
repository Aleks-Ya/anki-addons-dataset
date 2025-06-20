from xlsxwriter import Workbook
from xlsxwriter.format import Format
from xlsxwriter.worksheet import Worksheet

from anki_addons_dataset.common.data_types import AddonInfo


class AddonInfoSheet:
    __header_row_top: int = 0
    __header_row_bottom: int = 1

    __id_col: int = 0
    __name_col: int = 1
    __versions_col: int = 2
    __rating_col: int = 3
    __likes_col: int = 4
    __dislikes_col: int = 5
    __anki_web_url_col: int = 6
    __anki_forum_url_col: int = 7
    __stars_col: int = 8
    __updated_col: int = 9
    __last_commit_col: int = 10
    __github_url_col: int = 11
    __languages_col: int = 12
    __actions_count_col: int = 13
    __tests_count_col: int = 14

    @staticmethod
    def create_sheet(workbook: Workbook, addon_infos: list[AddonInfo]) -> None:
        worksheet: Worksheet = workbook.add_worksheet(name="Addons")
        AddonInfoSheet.__set_column_width(worksheet)
        AddonInfoSheet.__add_header(workbook, worksheet)
        AddonInfoSheet.__add_rows(addon_infos, worksheet)

    @staticmethod
    def __set_column_width(worksheet: Worksheet) -> None:
        worksheet.set_column(AddonInfoSheet.__id_col, AddonInfoSheet.__id_col, 12)
        worksheet.set_column(AddonInfoSheet.__name_col, AddonInfoSheet.__name_col, 80)
        worksheet.set_column(AddonInfoSheet.__versions_col, AddonInfoSheet.__versions_col, 10)
        worksheet.set_column(AddonInfoSheet.__rating_col, AddonInfoSheet.__rating_col, 6)
        worksheet.set_column(AddonInfoSheet.__likes_col, AddonInfoSheet.__likes_col, 6)
        worksheet.set_column(AddonInfoSheet.__dislikes_col, AddonInfoSheet.__dislikes_col, 7)
        worksheet.set_column(AddonInfoSheet.__anki_web_url_col, AddonInfoSheet.__anki_web_url_col, 8)
        worksheet.set_column(AddonInfoSheet.__anki_forum_url_col, AddonInfoSheet.__anki_forum_url_col, 10)
        worksheet.set_column(AddonInfoSheet.__stars_col, AddonInfoSheet.__stars_col, 8)
        worksheet.set_column(AddonInfoSheet.__updated_col, AddonInfoSheet.__updated_col, 10)
        worksheet.set_column(AddonInfoSheet.__last_commit_col, AddonInfoSheet.__last_commit_col, 13)
        worksheet.set_column(AddonInfoSheet.__github_url_col, AddonInfoSheet.__github_url_col, 8)
        worksheet.set_column(AddonInfoSheet.__languages_col, AddonInfoSheet.__languages_col, 50)
        worksheet.set_column(AddonInfoSheet.__actions_count_col, AddonInfoSheet.__actions_count_col, 10)
        worksheet.set_column(AddonInfoSheet.__tests_count_col, AddonInfoSheet.__tests_count_col, 8)

    @staticmethod
    def __add_header(workbook: Workbook, worksheet: Worksheet) -> None:
        header_format: Format = workbook.add_format({"bold": True, 'align': 'center'})

        worksheet.merge_range(data="Anki Web", cell_format=header_format,
                              first_row=AddonInfoSheet.__header_row_top, last_row=AddonInfoSheet.__header_row_top,
                              first_col=AddonInfoSheet.__id_col, last_col=AddonInfoSheet.__anki_web_url_col)
        worksheet.write_string(AddonInfoSheet.__header_row_bottom, AddonInfoSheet.__id_col, "ID", header_format)
        worksheet.write_string(AddonInfoSheet.__header_row_bottom, AddonInfoSheet.__name_col, "Name", header_format)
        worksheet.write_string(AddonInfoSheet.__header_row_bottom, AddonInfoSheet.__versions_col, "Versions",
                               header_format)
        worksheet.write_string(AddonInfoSheet.__header_row_bottom, AddonInfoSheet.__rating_col, "Rating", header_format)
        worksheet.write_string(AddonInfoSheet.__header_row_bottom, AddonInfoSheet.__likes_col, "Likes", header_format)
        worksheet.write_string(AddonInfoSheet.__header_row_bottom, AddonInfoSheet.__dislikes_col, "Dislikes",
                               header_format)
        worksheet.write_string(AddonInfoSheet.__header_row_bottom, AddonInfoSheet.__anki_web_url_col, "Page",
                               header_format)

        worksheet.write_string(AddonInfoSheet.__header_row_top, AddonInfoSheet.__anki_forum_url_col,
                               "Anki Forum", header_format)
        worksheet.write_string(AddonInfoSheet.__header_row_bottom, AddonInfoSheet.__anki_forum_url_col,
                               "Page", header_format)

        worksheet.merge_range(data="GitHub", cell_format=header_format,
                              first_row=AddonInfoSheet.__header_row_top, last_row=AddonInfoSheet.__header_row_top,
                              first_col=AddonInfoSheet.__stars_col, last_col=AddonInfoSheet.__languages_col)
        worksheet.write_string(AddonInfoSheet.__header_row_bottom, AddonInfoSheet.__stars_col, "Stars",
                               header_format)
        worksheet.write_string(AddonInfoSheet.__header_row_bottom, AddonInfoSheet.__updated_col, "Updated",
                               header_format)
        worksheet.write_string(AddonInfoSheet.__header_row_bottom, AddonInfoSheet.__last_commit_col,
                               "Last commit", header_format)
        worksheet.write_string(AddonInfoSheet.__header_row_bottom, AddonInfoSheet.__github_url_col, "Repo",
                               header_format)
        worksheet.write_string(AddonInfoSheet.__header_row_bottom, AddonInfoSheet.__languages_col, "Languages",
                               header_format)
        worksheet.write_string(AddonInfoSheet.__header_row_bottom, AddonInfoSheet.__actions_count_col, "Actions",
                               header_format)
        worksheet.write_string(AddonInfoSheet.__header_row_bottom, AddonInfoSheet.__tests_count_col, "Tests",
                               header_format)

        worksheet.freeze_panes(AddonInfoSheet.__header_row_bottom + 1, AddonInfoSheet.__id_col)
        worksheet.autofilter(first_row=AddonInfoSheet.__header_row_bottom, last_row=AddonInfoSheet.__header_row_bottom,
                             first_col=AddonInfoSheet.__id_col, last_col=AddonInfoSheet.__tests_count_col)

    @staticmethod
    def __add_rows(addon_infos: list[AddonInfo], worksheet: Worksheet) -> None:
        for i, addon in enumerate(addon_infos):
            row: int = i + AddonInfoSheet.__header_row_bottom + 1
            worksheet.write_number(row, AddonInfoSheet.__id_col, addon.header.id)
            worksheet.write_string(row, AddonInfoSheet.__name_col, addon.header.name)
            worksheet.write_string(row, AddonInfoSheet.__versions_col, addon.header.versions)
            worksheet.write_number(row, AddonInfoSheet.__rating_col, addon.header.rating)
            worksheet.write_number(row, AddonInfoSheet.__likes_col, addon.page.like_number)
            worksheet.write_number(row, AddonInfoSheet.__dislikes_col, addon.page.dislike_number)
            worksheet.write_url(row, AddonInfoSheet.__anki_web_url_col, addon.header.addon_page, string='link')
            if addon.page.anki_forum_url:
                worksheet.write_url(row, AddonInfoSheet.__anki_forum_url_col, addon.page.anki_forum_url, string='link')
            if addon.github.stars:
                worksheet.write_number(row, AddonInfoSheet.__stars_col, addon.github.stars)
            worksheet.write_string(row, AddonInfoSheet.__updated_col, addon.header.update_date)
            worksheet.write_string(row, AddonInfoSheet.__last_commit_col,
                                   addon.github.last_commit.strftime("%Y-%m-%d") if addon.github.last_commit else "")
            if addon.github.github_repo:
                worksheet.write_url(row, AddonInfoSheet.__github_url_col, addon.github.github_repo.get_url(),
                                    string='link')
            languages_str: str = ", ".join(addon.github.languages)
            worksheet.write_string(row, AddonInfoSheet.__languages_col, languages_str)
            if addon.github.action_count:
                worksheet.write_number(row, AddonInfoSheet.__actions_count_col, addon.github.action_count)
            if addon.github.tests_count:
                worksheet.write_number(row, AddonInfoSheet.__tests_count_col, addon.github.tests_count)
