import asyncio
import re
import logging
import time
from datetime import datetime, timezone, timedelta

import httpx
from sqlalchemy import select, delete

from app.database import async_session
from app.models import Story, Chunk
from app.services.hn_client import (
    fetch_story_ids_in_range,
    parse_story_from_hit,
    fetch_comments_for_story,
    HNStory,
)
from app.services.embeddings import generate_embeddings
from app.config import settings

logger = logging.getLogger(__name__)

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    clean = _HTML_TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", clean).strip()


def _create_chunks_for_story(story: HNStory) -> list[dict]:
    """Create chunk dicts (content, chunk_type, author) for a story."""
    chunks = []

    # Title + URL chunk
    title_content = story.title
    if story.url:
        title_content += f"\n{story.url}"
    chunks.append({
        "content": title_content,
        "chunk_type": "title",
        "author": None,
    })

    # Story text chunk (for Ask HN / Show HN)
    if story.story_text and story.story_text.strip():
        clean_text = _strip_html(story.story_text)
        if clean_text:
            chunks.append({
                "content": clean_text,
                "chunk_type": "story_text",
                "author": None,
            })

    # Comment chunks
    for comment in story.comments:
        clean_text = _strip_html(comment.text)
        if clean_text and len(clean_text) > 10:
            chunks.append({
                "content": clean_text,
                "chunk_type": "comment",
                "author": comment.author,
            })

    return chunks


async def _get_existing_hn_ids(hn_ids: list[int]) -> set[int]:
    """Check which hn_ids already exist in the database."""
    if not hn_ids:
        return set()
    async with async_session() as session:
        result = await session.execute(
            select(Story.hn_id).where(Story.hn_id.in_(hn_ids))
        )
        return set(result.scalars().all())


async def ingest_one_day(day_start: datetime, day_end: datetime) -> dict:
    """Ingest stories for a single day. Returns counts."""
    start_time = time.time()

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Fetch story metadata (fast, no comments)
        hits = await fetch_story_ids_in_range(
            client,
            start_timestamp=int(day_start.timestamp()),
            end_timestamp=int(day_end.timestamp()),
            min_score=settings.hn_min_score,
        )
        logger.info(f"Day {day_start.date()}: found {len(hits)} stories from API")

        if not hits:
            return {"stories_fetched": 0, "chunks_created": 0}

        # 2. Parse stories and filter out existing ones
        parsed = [parse_story_from_hit(h) for h in hits]
        hn_ids = [s.hn_id for s in parsed]
        existing_ids = await _get_existing_hn_ids(hn_ids)
        new_stories = [s for s in parsed if s.hn_id not in existing_ids]

        logger.info(f"Day {day_start.date()}: {len(new_stories)} new stories (skipping {len(existing_ids)} existing)")

        if not new_stories:
            return {"stories_fetched": 0, "chunks_created": 0}

        # 3. Fetch comments concurrently (only for new stories)
        comment_tasks = [
            fetch_comments_for_story(client, s.hn_id, settings.hn_max_comments_per_story)
            for s in new_stories
        ]
        all_comments = await asyncio.gather(*comment_tasks)
        for story, comments in zip(new_stories, all_comments):
            story.comments = comments

    # 4. Store stories and generate embeddings
    stories_created = 0
    chunks_created = 0

    async with async_session() as session:
        for story in new_stories:
            db_story = Story(
                hn_id=story.hn_id,
                title=story.title,
                url=story.url,
                author=story.author,
                score=story.score,
                num_comments=story.num_comments,
                story_text=story.story_text,
                story_type=story.story_type,
                created_at=story.created_at,
            )
            session.add(db_story)
            await session.flush()

            chunk_defs = _create_chunks_for_story(story)
            if not chunk_defs:
                continue

            # Generate embeddings in batches
            texts = [c["content"] for c in chunk_defs]
            all_embeddings: list[list[float]] = []
            batch_size = settings.embedding_batch_size
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                embeddings = await generate_embeddings(batch)
                all_embeddings.extend(embeddings)

            for idx, chunk_def in enumerate(chunk_defs):
                db_chunk = Chunk(
                    story_id=db_story.id,
                    content=chunk_def["content"],
                    chunk_type=chunk_def["chunk_type"],
                    author=chunk_def["author"],
                    embedding=all_embeddings[idx],
                )
                session.add(db_chunk)

            stories_created += 1
            chunks_created += len(chunk_defs)

            if stories_created % 25 == 0:
                await session.commit()
                logger.info(f"Day {day_start.date()}: committed {stories_created} stories, {chunks_created} chunks")

        await session.commit()

    duration = time.time() - start_time
    logger.info(f"Day {day_start.date()}: done — {stories_created} stories, {chunks_created} chunks in {duration:.1f}s")
    return {"stories_fetched": stories_created, "chunks_created": chunks_created}


async def ingest_initial():
    """Fetch 30 days of stories, one day at a time."""
    total_stories = 0
    total_chunks = 0
    start_time = time.time()

    end_dt = datetime.now(timezone.utc)
    start_dt = end_dt - timedelta(days=settings.hn_days_to_keep)

    # Process day by day (most recent first)
    current = end_dt
    while current > start_dt:
        day_start = max(current - timedelta(days=1), start_dt)
        day_end = current

        result = await ingest_one_day(day_start, day_end)
        total_stories += result["stories_fetched"]
        total_chunks += result["chunks_created"]

        current = day_start

    duration = time.time() - start_time
    logger.info(f"Initial ingest complete: {total_stories} stories, {total_chunks} chunks in {duration:.1f}s")
    return {
        "stories_fetched": total_stories,
        "chunks_created": total_chunks,
        "duration_seconds": round(duration, 2),
    }


async def ingest_daily():
    """Fetch last 24 hours and delete stories older than 30 days."""
    end_dt = datetime.now(timezone.utc)
    start_dt = end_dt - timedelta(hours=25)  # 25h overlap for safety

    result = await ingest_one_day(start_dt, end_dt)

    # Clean up old stories (cascade deletes chunks)
    cutoff = end_dt - timedelta(days=settings.hn_days_to_keep)
    async with async_session() as session:
        deleted = await session.execute(
            delete(Story).where(Story.created_at < cutoff)
        )
        await session.commit()
        logger.info(f"Pruned {deleted.rowcount} stories older than {cutoff.date()}")

    return {
        "stories_fetched": result["stories_fetched"],
        "chunks_created": result["chunks_created"],
        "duration_seconds": 0,
    }
