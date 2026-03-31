import logging
import time

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from sqlalchemy import select, text as sql_text

from app.database import async_session
from app.models import Story, Chunk
from app.schemas import StoryDetail, StoryChunk, RelatedStory, RelatedStoriesResponse, StorySummary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["stories"])


@router.get("/stories/{slug}", response_model=StoryDetail)
async def get_story(slug: str):
    """Get a single story by slug with all its chunks."""
    async with async_session() as session:
        result = await session.execute(
            select(Story).where(Story.slug == slug)
        )
        story = result.scalar_one_or_none()
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")

        chunks_result = await session.execute(
            select(Chunk.content, Chunk.chunk_type, Chunk.author)
            .where(Chunk.story_id == story.id)
            .order_by(Chunk.created_at)
        )
        chunks = [
            StoryChunk(content=row.content, chunk_type=row.chunk_type, author=row.author)
            for row in chunks_result.fetchall()
        ]

        return StoryDetail(
            slug=story.slug,
            hn_id=story.hn_id,
            title=story.title,
            url=story.url,
            author=story.author,
            score=story.score,
            num_comments=story.num_comments,
            story_text=story.story_text,
            story_type=story.story_type,
            created_at=story.created_at.isoformat()[:10],
            chunks=chunks,
        )


@router.get("/stories/{slug}/related", response_model=RelatedStoriesResponse)
async def get_related_stories(slug: str, limit: int = 5):
    """Find related stories using pgvector similarity on the title chunk."""
    try:
        return await _get_related_stories(slug, limit)
    except Exception as e:
        logger.error(f"Related stories failed for {slug}: {type(e).__name__}: {e}")
        raise


async def _get_related_stories(slug: str, limit: int) -> RelatedStoriesResponse:
    async with async_session() as session:
        # Get the story
        result = await session.execute(
            select(Story).where(Story.slug == slug)
        )
        story = result.scalar_one_or_none()
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")

        # Count total title chunks searched
        count_result = await session.execute(
            sql_text("SELECT COUNT(*) FROM chunks WHERE chunk_type = 'title'")
        )
        chunks_searched = count_result.scalar() or 0

        # Find similar stories using a subquery for the embedding
        start = time.time()
        result = await session.execute(
            sql_text("""
                SELECT
                    s.slug,
                    s.title,
                    s.author,
                    s.score,
                    s.created_at,
                    1 - (c.embedding <=> ref.embedding) AS similarity_score
                FROM chunks c
                JOIN stories s ON c.story_id = s.id
                CROSS JOIN (
                    SELECT embedding FROM chunks
                    WHERE story_id = :story_id AND chunk_type = 'title'
                    LIMIT 1
                ) ref
                WHERE c.chunk_type = 'title'
                  AND s.id != :story_id
                  AND 1 - (c.embedding <=> ref.embedding) > 0.3
                ORDER BY c.embedding <=> ref.embedding
                LIMIT :limit
            """),
            {
                "story_id": str(story.id),
                "limit": limit,
            },
        )
        query_time_ms = (time.time() - start) * 1000

        stories = [
            RelatedStory(
                slug=row.slug,
                title=row.title,
                author=row.author,
                score=row.score,
                created_at=row.created_at.isoformat()[:10],
                similarity_score=round(float(row.similarity_score), 4),
            )
            for row in result.fetchall()
        ]

        return RelatedStoriesResponse(
            results=stories,
            query_time_ms=round(query_time_ms, 2),
            chunks_searched=chunks_searched,
        )


@router.get("/stories", response_model=list[StorySummary])
async def list_stories(offset: int = 0, limit: int = 100):
    """List all stories (paginated) for sitemap generation."""
    async with async_session() as session:
        result = await session.execute(
            select(Story.slug, Story.title, Story.created_at)
            .order_by(Story.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return [
            StorySummary(
                slug=row.slug,
                title=row.title,
                created_at=row.created_at.isoformat()[:10],
            )
            for row in result.fetchall()
        ]


@router.get("/sitemap.xml", response_class=Response)
async def sitemap():
    """Generate dynamic sitemap with all story pages."""
    async with async_session() as session:
        result = await session.execute(
            select(Story.slug, Story.created_at)
            .order_by(Story.created_at.desc())
        )
        stories = result.fetchall()

    base = "https://ask.rivestack.io"
    urls = [
        f'  <url>\n    <loc>{base}/</loc>\n    <changefreq>daily</changefreq>\n    <priority>1.0</priority>\n  </url>'
    ]
    for row in stories:
        urls.append(
            f'  <url>\n'
            f'    <loc>{base}/story/{row.slug}</loc>\n'
            f'    <lastmod>{row.created_at.isoformat()[:10]}</lastmod>\n'
            f'    <changefreq>monthly</changefreq>\n'
            f'    <priority>0.7</priority>\n'
            f'  </url>'
        )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + '\n'.join(urls) + '\n'
        '</urlset>\n'
    )
    return Response(content=xml, media_type="application/xml")
