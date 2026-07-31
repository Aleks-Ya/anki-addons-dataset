from typing import Any


class TreeReader:
    """Shared reader for a cached `tree.json` (`GET /git/trees/HEAD?recursive=1`) response.

    Reused by the tests counter and the manifest/dependency lookup so the repo tree is downloaded once.
    Truncated trees (very large repos) yield an empty list rather than raising, so best-effort lookups
    (manifest/dependencies) degrade gracefully.
    """

    @staticmethod
    def extract_file_paths(content_obj: dict[str, Any]) -> list[str]:
        if content_obj.get("truncated") or "tree" not in content_obj:
            return []
        return [entry["path"] for entry in content_obj["tree"] if "path" in entry]
