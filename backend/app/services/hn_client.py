import logging
from datetime import datetime, timezone
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search_by_date"
HN_ITEM_URL = "https://hn.algolia.com/api/v1/items"


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


async def fetch_stories_by_date_range(
    start_timestamp: int,
    end_timestamp: int,
    min_score: int = 10,
    max_comments_per_story: int = 20,
) -> list[HNStory]:
    """Fetch HN stories from Algolia API within a date range."""
    stories: list[HNStory] = []
    page = 0

    async with httpx.AsyncClient(timeout=30.0) as client:
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

            for hit in hits:
                story = HNStory(
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
                stories.append(story)

            page += 1
            if page >= data.get("nbPages", 0):
                break

    logger.info(f"Fetched {len(stories)} stories, now fetching comments...")

    for i, story in enumerate(stories):
        story.comments = await _fetch_top_comments(
            story.hn_id, max_comments_per_story
        )
        if (i + 1) % 50 == 0:
            logger.info(f"Fetched comments for {i + 1}/{len(stories)} stories")

    return stories


async def _fetch_top_comments(
    story_id: int, max_comments: int
) -> list[HNComment]:
    """Fetch top-level comments for a story via Algolia items endpoint."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
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
