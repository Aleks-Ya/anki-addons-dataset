from unittest.mock import Mock, patch

from anki_addons_dataset.collector.ankiweb.page_downloader import PageDownloader
from anki_addons_dataset.common.data_types import HtmlStr, PageLoadTimeout, ElementWaitTimeout


def __make_page_downloader(driver: Mock, page_load_timeout: PageLoadTimeout,
                           element_wait_timeout: ElementWaitTimeout) -> PageDownloader:
    with patch("anki_addons_dataset.collector.ankiweb.page_downloader.webdriver.Chrome", return_value=driver):
        return PageDownloader(page_load_timeout, element_wait_timeout)


def test_configures_timeouts(page_load_timeout: PageLoadTimeout, element_wait_timeout: ElementWaitTimeout):
    driver: Mock = Mock()

    page_downloader: PageDownloader = __make_page_downloader(driver, page_load_timeout, element_wait_timeout)

    driver.set_page_load_timeout.assert_called_once_with(page_load_timeout)
    assert page_downloader is not None


def test_load_page_returns_page_source(page_load_timeout: PageLoadTimeout,
                                       element_wait_timeout: ElementWaitTimeout):
    driver: Mock = Mock()
    driver.page_source = "<html><body><div><main>Addon</main></div></body></html>"
    page_downloader: PageDownloader = __make_page_downloader(driver, page_load_timeout, element_wait_timeout)

    html: HtmlStr = page_downloader.load_page("https://ankiweb.net/shared/addons")

    driver.get.assert_called_once_with("https://ankiweb.net/shared/addons")
    assert html == driver.page_source
