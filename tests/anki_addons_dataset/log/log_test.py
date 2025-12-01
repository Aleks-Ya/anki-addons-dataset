import logging
from logging import Logger

from _pytest.logging import LogCaptureFixture

from anki_addons_dataset.log.log import Log


def test_configure_logging(caplog: LogCaptureFixture):
    with caplog.at_level(logging.DEBUG):
        Log.configure_logging()
        logger: Logger = logging.getLogger('anki_addons_dataset')
        logger.debug("A message")
    assert "A message" in caplog.text
