import json
import logging
from datetime import datetime, timezone
from logging import Logger
from pathlib import Path
from typing import Optional

from pydiscourse import DiscourseClient

from anki_addons_dataset.common.data_types import TopicId, TopicSlug, LastPostedAt
from anki_addons_dataset.common.working_dir import VersionDir

log: Logger = logging.getLogger(__name__)


class AnkiForumService:

    def __init__(self, discourse_client: DiscourseClient, version_dir: VersionDir, offline: bool):
        self.__discourse_client: DiscourseClient = discourse_client
        self.__raw_dir: Path = version_dir.get_raw_dir() / "3-forum"
        self.__topic = self.__raw_dir / "topic"
        self.__topic.mkdir(parents=True, exist_ok=True)
        self.__offline: bool = offline

    def get_last_posted_at(self, topic_slug: TopicSlug, topic_id: TopicId) -> Optional[LastPostedAt]:
        topic_dict: Optional[dict] = self.__read_topic_json(topic_slug, topic_id)
        if not topic_dict:
            return None
        last_posted_at_str: str = topic_dict['last_posted_at']
        last_posted_at: datetime = datetime.strptime(last_posted_at_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(
            tzinfo=timezone.utc)
        return LastPostedAt(last_posted_at)

    def get_post_number(self, topic_slug: TopicSlug, topic_id: TopicId) -> Optional[int]:
        topic_dict: Optional[dict] = self.__read_topic_json(topic_slug, topic_id)
        return topic_dict['posts_count'] if not topic_dict else None

    def __read_topic_json(self, topic_slug: TopicSlug, topic_id: TopicId) -> Optional[dict]:
        json_file: Path = self.__topic / f"{topic_id}.json"
        if json_file.exists():
            json_str: str = json_file.read_text()
            if json_str == "None":
                return None
            topic_dict: dict = json.loads(json_str)
        else:
            if self.__offline:
                log.debug(f"Offline mode is enabled. Skip fetching last_posted_at for topic '{topic_slug}/{topic_id}'")
                return None
            topic_dict: dict = self.__discourse_client.topic(
                topic_slug, topic_id, override_request_kwargs={"allow_redirects": True})
            if topic_dict is None:
                json_file.write_text("None")
                return None
            topic_json: str = json.dumps(topic_dict, indent=2)
            json_file.write_text(topic_json)
        return topic_dict
