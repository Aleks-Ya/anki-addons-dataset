import pytest

from anki_addons_dataset.common.duration import format_duration


@pytest.mark.parametrize("seconds, expected", [
    (0.0, "0 seconds"),
    (0.42, "0.42 seconds"),
    (5, "5 seconds"),
    (12.34, "12.34 seconds"),
    (60, "1 minute"),
    (65, "1 minute and 5 seconds"),
    (125, "2 minutes and 5 seconds"),
    (3600, "1 hour"),
    (3661, "1 hour, 1 minute and 1 second"),
    (7325, "2 hours, 2 minutes and 5 seconds"),
])
def test_format_duration(seconds: float, expected: str):
    assert format_duration(seconds) == expected
