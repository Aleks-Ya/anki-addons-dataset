import dataclasses
from datetime import date
from pathlib import Path
from typing import Optional

import pytest
from huggingface_hub import HfApi
from pydiscourse import DiscourseClient

from anki_addons_dataset.collector.ankiweb.page_downloader import PageDownloader
from anki_addons_dataset.collector.github.github_rest_client import GithubRestClient
from anki_addons_dataset.common.data_types import AddonId, ElementWaitTimeout, GithubRepo, GithubRepoName, \
    GithubUserName, PageLoadTimeout, SnapshotDate, TopicId, TopicSlug
from anki_addons_dataset.common.working_dir import SnapshotDir, WorkingDir
from anki_addons_dataset.config.app_config import AppConfig
from anki_addons_dataset.huggingface.hugging_face_client import HuggingFaceClient

__ANKI_FORUM_HOST: str = "https://forums.ankiweb.net"
__MIN_GITHUB_REQUESTS_REMAINING: int = 50


@pytest.fixture(scope="session")
def page_load_timeout() -> PageLoadTimeout:
    return PageLoadTimeout(120)


@pytest.fixture(scope="session")
def element_wait_timeout() -> ElementWaitTimeout:
    return ElementWaitTimeout(30)


@pytest.fixture(scope="session")
def snapshot_date() -> SnapshotDate:
    return SnapshotDate(date(2026, 1, 1))


@pytest.fixture(scope="session")
def known_addon_id() -> AddonId:
    return AddonId(1188705668)


@pytest.fixture(scope="session")
def known_github_repo() -> GithubRepo:
    return GithubRepo(GithubUserName("Aleks-Ya"), GithubRepoName("note-size-anki-addon"))


@pytest.fixture(scope="session")
def known_topic_slug() -> TopicSlug:
    return TopicSlug("note-size-addon-support")


@pytest.fixture(scope="session")
def known_topic_id() -> TopicId:
    return TopicId(46001)


@pytest.fixture(scope="session")
def contents_github_repo() -> GithubRepo:
    return GithubRepo(GithubUserName("ankitects"), GithubRepoName("anki-addons"))


@pytest.fixture(scope="session")
def missing_github_repo() -> GithubRepo:
    return GithubRepo(GithubUserName("Aleks-Ya"), GithubRepoName("no-such-repo-anki-addons-dataset-integration-test"))


@pytest.fixture(scope="session")
def missing_topic_slug() -> TopicSlug:
    return TopicSlug("no-such-topic-anki-addons-dataset-integration-test")


@pytest.fixture(scope="session")
def missing_topic_id() -> TopicId:
    return TopicId(999999999)


@pytest.fixture
def integration_config(tmp_path: Path) -> AppConfig:
    return dataclasses.replace(AppConfig.defaults(), working_dir=tmp_path)


@pytest.fixture
def working_dir(tmp_path: Path) -> WorkingDir:
    return WorkingDir(tmp_path)


@pytest.fixture
def snapshot_dir(tmp_path: Path, snapshot_date: SnapshotDate) -> SnapshotDir:
    return SnapshotDir(tmp_path / "history" / snapshot_date.isoformat()).create()


@pytest.fixture(scope="session")
def page_downloader(page_load_timeout: PageLoadTimeout, element_wait_timeout: ElementWaitTimeout) -> PageDownloader:
    return PageDownloader(page_load_timeout, element_wait_timeout)


@pytest.fixture
def github_rest_client(integration_config: AppConfig) -> GithubRestClient:
    return GithubRestClient(offline=False, token_file=integration_config.github.token_file)


@pytest.fixture
def github_rate_limit_guard(github_rest_client: GithubRestClient) -> int:
    remaining: Optional[int] = github_rest_client.verify_token()
    if remaining is not None and remaining < __MIN_GITHUB_REQUESTS_REMAINING:
        pytest.fail(f"GitHub rate limit nearly exhausted ({remaining} requests remaining). "
                    f"Wait for the reset instead of letting the tests block on it.")
    return remaining if remaining is not None else 0


@pytest.fixture
def discourse_client() -> DiscourseClient:
    return DiscourseClient(host=__ANKI_FORUM_HOST, api_username=None, api_key=None)


@pytest.fixture
def hugging_face_client(integration_config: AppConfig) -> HuggingFaceClient:
    return HuggingFaceClient(HfApi(), integration_config.huggingface)
