import re
from re import Match
from typing import Optional

from anki_addons_dataset.common.data_types import URL, TopicId, TopicSlug


class AnkiForumTopic:
    __url_pattern: re.Pattern = re.compile(r'^https://forums\.ankiweb\.net/t/([^/]+)/(\d+)')

    @staticmethod
    def extract_topic_slug(topic_url: Optional[URL]) -> Optional[TopicSlug]:
        if topic_url is None:
            return None
        match: Match[str] = re.search(AnkiForumTopic.__url_pattern, topic_url)
        if match:
            topic_slug_str: str = match.group(1)
            return TopicSlug(topic_slug_str)
        else:
            raise ValueError(f"Cannot extract Topic Slug from Anki Forum Topic URL: '{topic_url}'")

    @staticmethod
    def extract_topic_id(topic_url: Optional[URL]) -> Optional[TopicId]:
        if topic_url is None:
            return None
        match: Match[str] = re.search(AnkiForumTopic.__url_pattern, topic_url)
        if match:
            topic_id_str: str = match.group(2)
            return TopicId(int(topic_id_str))
        else:
            raise ValueError(f"Cannot extract Topic ID from Anki Forum Topic URL: '{topic_url}'")
