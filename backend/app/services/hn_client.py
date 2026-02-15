import asyncio
import logging
from datetime import datetime, timezone
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search_by_date"
HN_ITEM_URL = "https://hn.algolia.com/api/v1/items"

# Limit concurrent comment fetches to avoid rate limiting
_COMMENT_SEMAPHORE = asyncio.Semaphore(5)


@dataclass
class HNComment:
    author: str
    text: str


@dataclass
class HNStory:
    hn_id: int
    title: str
    url: str | None
    author: str
    score: int
    num_comments: int
    story_text: str | None
    story_type: str
    created_at: datetime
    comments: list[HNComment]


async def fetch_story_ids_in_range(
    client: httpx.AsyncClient,
    start_timestamp: int,
    end_timestamp: int,
    min_score: int = 10,
) -> list[dict]:
    """Fetch story metadata (without comments) from Algolia API."""
    all_hits: list[dict] = []
    page = 0

    while True:
        params = {
            "tags": "story",
            "numericFilters": f"created_at_i>{start_timestamp},created_at_i<{end_timestamp},points>{min_score}",
            "hitsPerPage": 100,
            "page": page,
        }
        response = await client.get(HN_SEARCH_URL, params=params)
        response.raise_for_status()
        data = response.json()

        hits = data.get("hits", [])
        if not hits:
            break

        all_hits.extend(hits)
        page += 1
        if page >= data.get("nbPages", 0):
            break

    return all_hits


def parse_story_from_hit(hit: dict) -> HNStory:
    """Parse an Algolia hit into an HNStory (without comments)."""
    return HNStory(
        hn_id=int(hit["objectID"]),
        title=hit.get("title", ""),
        url=hit.get("url"),
        author=hit.get("author", "unknown"),
        score=hit.get("points", 0),
        num_comments=hit.get("num_comments", 0),
        story_text=hit.get("story_text"),
        story_type=_classify_story(hit),
        created_at=datetime.fromtimestamp(
            hit["created_at_i"], tz=timezone.utc
        ),
        comments=[],
    )


async def fetch_comments_for_story(
    client: httpx.AsyncClient,
    story_id: int,
    max_comments: int,
) -> list[HNComment]:
    """Fetch top-level comments for a story via Algolia items endpoint."""
    async with _COMMENT_SEMAPHORE:
        try:
            response = await client.get(f"{HN_ITEM_URL}/{story_id}")
            response.raise_for_status()
            data = response.json()

            comments = []
            for child in (data.get("children") or [])[:max_comments]:
                text = child.get("text")
                author = child.get("author")
                if text and author:
                    comments.append(HNComment(author=author, text=text))

            return comments
        except Exception as e:
            logger.warning(f"Failed to fetch comments for story {story_id}: {e}")
            return []


def _classify_story(hit: dict) -> str:
    title = (hit.get("title") or "").lower()
    if title.startswith("ask hn"):
        return "ask_hn"
    elif title.startswith("show hn"):
        return "show_hn"
    return "story"
