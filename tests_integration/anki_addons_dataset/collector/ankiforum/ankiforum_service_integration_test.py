from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydiscourse import DiscourseClient
from pydiscourse.exceptions import DiscourseClientError

from anki_addons_dataset.collector.ankiforum.ankiforum_service import AnkiForumService
from anki_addons_dataset.common.data_types import LastPostedAt, PostsCount, TopicId, TopicSlug
from anki_addons_dataset.common.working_dir import SnapshotDir


@pytest.fixture
def anki_forum_service(discourse_client: DiscourseClient, snapshot_dir: SnapshotDir) -> AnkiForumService:
    return AnkiForumService(discourse_client, snapshot_dir, offline=False)


def test_known_topic(anki_forum_service: AnkiForumService, snapshot_dir: SnapshotDir,
                     known_topic_slug: TopicSlug, known_topic_id: TopicId) -> None:
    posts_count: PostsCount = anki_forum_service.get_posts_count(known_topic_slug, known_topic_id)
    assert posts_count is not None
    assert posts_count > 0

    last_posted_at: LastPostedAt = anki_forum_service.get_last_posted_at(known_topic_slug, known_topic_id)
    assert last_posted_at is not None
    assert last_posted_at.tzinfo == timezone.utc
    assert last_posted_at < datetime.now(timezone.utc)

    raw_file: Path = snapshot_dir.get_raw_dir() / "3-forum" / "topic" / f"{known_topic_id}.json"
    assert raw_file.exists()
    assert raw_file.stat().st_size > 0


def test_missing_topic(anki_forum_service: AnkiForumService, snapshot_dir: SnapshotDir,
                       missing_topic_slug: TopicSlug, missing_topic_id: TopicId) -> None:
    with pytest.raises(DiscourseClientError):
        anki_forum_service.get_posts_count(missing_topic_slug, missing_topic_id)
    assert not (snapshot_dir.get_raw_dir() / "3-forum" / "topic" / f"{missing_topic_id}.json").exists()
