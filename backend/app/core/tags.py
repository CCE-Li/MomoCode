from __future__ import annotations

import re
from collections.abc import Iterable

MAX_TAGS = 12
MAX_TAG_LENGTH = 32


def normalize_tags(values: Iterable[str]) -> list[str]:
    """Normalize hashtag-style input into stable, de-duplicated tag strings.

    Accepts ``#二分``, ``二分``, ``#二分 #BFS`` and comma-separated strings.
    Case-insensitive de-duplication keeps the first spelling.
    """

    result: list[str] = []
    seen: set[str] = set()
    for raw in values:
        if not isinstance(raw, str):
            continue
        for piece in re.split(r"[\s,，]+", raw):
            tag = piece.strip().lstrip("#").strip()
            tag = re.sub(r"\s+", " ", tag)
            if not tag:
                continue
            key = tag.casefold()
            if key in seen:
                continue
            seen.add(key)
            result.append(tag[:MAX_TAG_LENGTH])
            if len(result) >= MAX_TAGS:
                return result
    return result
