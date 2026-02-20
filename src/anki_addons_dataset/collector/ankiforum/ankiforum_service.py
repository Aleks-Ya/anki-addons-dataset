import logging
import re
from datetime import datetime, timezone
from logging import Logger
from pathlib import Path
from re import Match
from typing import Optional

from pydiscourse import DiscourseClient

from anki_addons_dataset.common.data_types import URL, TopicId, TopicSlug, LastPostedAt
from anki_addons_dataset.common.working_dir import VersionDir

log: Logger = logging.getLogger(__name__)


class AnkiForumService:
    __url_pattern: re.Pattern = re.compile(r'^https://forums\.ankiweb\.net/t/([^/]+)/(\d+)')

    def __init__(self, discourse_client: DiscourseClient, version_dir: VersionDir, offline: bool):
        self.__discourse_client: DiscourseClient = discourse_client
        self.__raw_dir: Path = version_dir.get_raw_dir() / "3-forum"
        self.__raw_dir.mkdir(parents=True, exist_ok=True)
        self.__offline: bool = offline

    def extract_topic_slug(self, topic_url: Optional[URL]) -> Optional[TopicSlug]:
        if topic_url is None:
            return None
        match: Match[str] = re.search(self.__url_pattern, topic_url)
        if match:
            topic_slug_str: str = match.group(1)
            return TopicSlug(topic_slug_str)
        else:
            raise ValueError(f"Cannot extract Topic Slug from Anki Forum Topic URL: '{topic_url}'")

    def extract_topic_id(self, topic_url: Optional[URL]) -> Optional[TopicId]:
        if topic_url is None:
            return None
        match: Match[str] = re.search(self.__url_pattern, topic_url)
        if match:
            topic_id_str: str = match.group(2)
            return TopicId(int(topic_id_str))
        else:
            raise ValueError(f"Cannot extract Topic ID from Anki Forum Topic URL: '{topic_url}'")

    def get_last_posted_at(self, topic_slug: TopicSlug, topic_id: TopicId) -> Optional[LastPostedAt]:
        raw_file: Path = self.__raw_dir / f"{topic_id}.json"
        if raw_file.exists():
            last_posted_at_str: str = raw_file.read_text()
            if last_posted_at_str == "None":
                return None
        else:
            if self.__offline:
                log.debug(f"Offline mode is enabled. Skip fetching last_posted_at for topic '{topic_slug}/{topic_id}'")
                return None
            topic: dict = self.__discourse_client.topic(
                topic_slug, topic_id, override_request_kwargs={"allow_redirects": True})
            if topic is None:
                raw_file.write_text("None")
                return None
            last_posted_at_str: str = topic['last_posted_at']
            raw_file.write_text(last_posted_at_str)
        last_posted_at: datetime = datetime.strptime(last_posted_at_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(
            tzinfo=timezone.utc)
        return LastPostedAt(last_posted_at)
