from dataclasses import replace
from unittest.mock import Mock

import pytest
from _pytest.logging import LogCaptureFixture

from anki_addons_dataset.addon_catalog import _upload_free
from anki_addons_dataset.argument.script_arguments import Operation
from anki_addons_dataset.config.app_config import AppConfig, SampleConfig


def __arguments(explicit_upload: bool) -> Mock:
    arguments: Mock = Mock()
    arguments.has_explicit_operation.return_value = explicit_upload
    return arguments


def __sampled(app_config: AppConfig) -> AppConfig:
    return replace(app_config, sample=SampleConfig(addons=20))


def test_upload_runs_when_nothing_is_sampled(app_config: AppConfig):
    operations: list[Operation] = list(Operation)
    assert _upload_free(operations, __arguments(False), app_config) == operations


def test_an_explicit_upload_of_a_sampled_run_is_rejected(app_config: AppConfig):
    arguments: Mock = __arguments(True)
    sampled: AppConfig = __sampled(app_config)

    with pytest.raises(ValueError, match="must not be uploaded"):
        _upload_free([Operation.BUNDLE, Operation.UPLOAD], arguments, sampled)


def test_all_drops_upload_from_a_sampled_run(app_config: AppConfig, caplog: LogCaptureFixture):
    operations: list[Operation] = _upload_free(list(Operation), __arguments(False), __sampled(app_config))
    assert Operation.UPLOAD not in operations
    assert Operation.BUNDLE in operations
    assert "Skipping the 'upload' step" in caplog.text


def test_a_sampled_run_without_upload_is_untouched(app_config: AppConfig):
    operations: list[Operation] = [Operation.PARSE, Operation.REPORT]
    assert _upload_free(operations, __arguments(False), __sampled(app_config)) == operations
