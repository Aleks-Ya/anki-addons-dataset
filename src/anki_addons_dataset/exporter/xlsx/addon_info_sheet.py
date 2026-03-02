from xlsxwriter import Workbook
from xlsxwriter.format import Format
from xlsxwriter.worksheet import Worksheet

from anki_addons_dataset.common.data_types import AddonInfos


class AddonInfoSheet:
    __header_row_top: int = 0
    __header_row_bottom: int = 1

    __id_col: int = 0
    __name_col: int = 1
    __updated_col: int = 2
    __versions_col: int = 3
    __rating_col: int = 4
    __likes_col: int = 5
    __dislikes_col: int = 6
    __anki_web_url_col: int = 7
    __anki_forum_url_col: int = 8
    __anki_forum_posts_count_col: int = 9
    __anki_forum_last_posted_at_col: int = 10
    __github_url_col: int = 11
    __stars_col: int = 12
    __last_commit_col: int = 13
    __languages_col: int = 14
    __actions_count_col: int = 15
    __tests_count_col: int = 16

    def __init__(self, workbook: Workbook):
        self.__workbook: Workbook = workbook

    def create_sheet(self, addon_infos: AddonInfos) -> None:
        worksheet: Worksheet = self.__workbook.add_worksheet(name="Addons")
        self.__set_column_width(worksheet)
        self.__add_header(self.__workbook, worksheet)
        self.__add_rows(addon_infos, worksheet)

    def __set_column_width(self, worksheet: Worksheet) -> None:
        worksheet.set_column(self.__id_col, self.__id_col, 12)
        worksheet.set_column(self.__name_col, self.__name_col, 80)
        worksheet.set_column(self.__updated_col, self.__updated_col, 10)
        worksheet.set_column(self.__versions_col, self.__versions_col, 10)
        worksheet.set_column(self.__rating_col, self.__rating_col, 6)
        worksheet.set_column(self.__likes_col, self.__likes_col, 6)
        worksheet.set_column(self.__dislikes_col, self.__dislikes_col, 7)
        worksheet.set_column(self.__anki_web_url_col, self.__anki_web_url_col, 8)
        worksheet.set_column(self.__anki_forum_url_col, self.__anki_forum_url_col, 8)
        worksheet.set_column(self.__anki_forum_posts_count_col, self.__anki_forum_posts_count_col, 8)
        worksheet.set_column(self.__anki_forum_last_posted_at_col, self.__anki_forum_last_posted_at_col, 10)
        worksheet.set_column(self.__github_url_col, self.__github_url_col, 8)
        worksheet.set_column(self.__stars_col, self.__stars_col, 8)
        worksheet.set_column(self.__last_commit_col, self.__last_commit_col, 13)
        worksheet.set_column(self.__languages_col, self.__languages_col, 50)
        worksheet.set_column(self.__actions_count_col, self.__actions_count_col, 10)
        worksheet.set_column(self.__tests_count_col, self.__tests_count_col, 8)

    def __add_header(self, workbook: Workbook, worksheet: Worksheet) -> None:
        header_format: Format = workbook.add_format({"bold": True, 'align': 'center'})
        row1: int = self.__header_row_top
        row2: int = self.__header_row_bottom

        worksheet.merge_range(data="Anki Web", cell_format=header_format,
                              first_row=row1, last_row=row1,
                              first_col=self.__id_col, last_col=self.__anki_web_url_col)
        worksheet.write_string(row2, self.__id_col, "ID", header_format)
        worksheet.write_string(row2, self.__name_col, "Name", header_format)
        worksheet.write_string(row2, self.__updated_col, "Updated", header_format)
        worksheet.write_string(row2, self.__versions_col, "Versions", header_format)
        worksheet.write_string(row2, self.__rating_col, "Rating", header_format)
        worksheet.write_string(row2, self.__likes_col, "Likes", header_format)
        worksheet.write_string(row2, self.__dislikes_col, "Dislikes", header_format)
        worksheet.write_string(row2, self.__anki_web_url_col, "Page", header_format)

        worksheet.merge_range(data="Anki Forum", cell_format=header_format,
                              first_row=row1, last_row=row1,
                              first_col=self.__anki_forum_url_col, last_col=self.__anki_forum_last_posted_at_col)
        worksheet.write_string(row2, self.__anki_forum_url_col, "Page", header_format)
        worksheet.write_string(row2, self.__anki_forum_posts_count_col, "Posts Count", header_format)
        worksheet.write_string(row2, self.__anki_forum_last_posted_at_col, "Last post", header_format)

        worksheet.merge_range(data="GitHub", cell_format=header_format,
                              first_row=row1, last_row=row1,
                              first_col=self.__github_url_col, last_col=self.__tests_count_col)
        worksheet.write_string(row2, self.__github_url_col, "Repo", header_format)
        worksheet.write_string(row2, self.__stars_col, "Stars", header_format)
        worksheet.write_string(row2, self.__last_commit_col, "Last commit", header_format)
        worksheet.write_string(row2, self.__languages_col, "Languages", header_format)
        worksheet.write_string(row2, self.__actions_count_col, "Actions", header_format)
        worksheet.write_comment(row2, self.__actions_count_col, "Number of GitHub Actions in the repo")
        worksheet.write_string(row2, self.__tests_count_col, "Tests", header_format)
        worksheet.write_comment(row2, self.__tests_count_col, "Number of unit-tests in the repo")

        worksheet.freeze_panes(row2 + 1, self.__id_col)
        worksheet.autofilter(first_row=row2, last_row=row2,
                             first_col=self.__id_col, last_col=self.__tests_count_col)

    def __add_rows(self, addon_infos: AddonInfos, worksheet: Worksheet) -> None:
        for i, addon in enumerate(addon_infos):
            self.__add_row(addon, i, worksheet)

    def __add_row(self, addon, i: int, worksheet: Worksheet):
        row: int = i + self.__header_row_bottom + 1
        worksheet.write_number(row, self.__id_col, addon.header.id)
        worksheet.write_string(row, self.__name_col, addon.header.name)
        worksheet.write_string(row, self.__updated_col, addon.header.update_date)
        worksheet.write_string(row, self.__versions_col, addon.header.versions)
        worksheet.write_number(row, self.__rating_col, addon.header.rating)
        worksheet.write_number(row, self.__likes_col, addon.page.like_number)
        worksheet.write_number(row, self.__dislikes_col, addon.page.dislike_number)
        worksheet.write_url(row, self.__anki_web_url_col, addon.header.addon_page, string='link')
        if addon.forum.anki_forum_url:
            worksheet.write_url(row, self.__anki_forum_url_col, addon.forum.anki_forum_url, string='link')
        last_posted_at_str: str = addon.forum.last_posted_at.strftime("%Y-%m-%d") \
            if addon.forum and addon.forum.last_posted_at else ""
        worksheet.write_number(row, self.__anki_forum_posts_count_col, addon.forum.posts_count)
        worksheet.write_string(row, self.__anki_forum_last_posted_at_col, last_posted_at_str)
        if addon.github.github_repo:
            worksheet.write_url(row, self.__github_url_col, addon.github.github_repo.get_url(), string='link')
        if addon.github.stars:
            worksheet.write_number(row, self.__stars_col, addon.github.stars)
        commit_str: str = addon.github.last_commit.strftime("%Y-%m-%d") if addon.github.last_commit else ""
        worksheet.write_string(row, self.__last_commit_col, commit_str)
        languages_str: str = ", ".join(addon.github.languages)
        worksheet.write_string(row, self.__languages_col, languages_str)
        if addon.github.action_count:
            worksheet.write_number(row, self.__actions_count_col, addon.github.action_count)
        if addon.github.tests_count:
            worksheet.write_number(row, self.__tests_count_col, addon.github.tests_count)
