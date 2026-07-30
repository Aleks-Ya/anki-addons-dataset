from datetime import timedelta

import humanize


def format_duration(seconds: float) -> str:
    """Human-readable duration for monitoring, e.g. '0.42 seconds', '2 minutes and 5 seconds'."""
    return humanize.precisedelta(timedelta(seconds=seconds), minimum_unit="seconds", format="%0.2f")
