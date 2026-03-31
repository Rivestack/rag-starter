from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from sqlalchemy import select, func, text as sql_text

from app.database import async_session
from app.models import Story, Chunk
from app.schemas import StoryDetail, StoryChunk, RelatedStory, StorySummary
from app.services.embeddings import generate_embedding

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


@router.get("/stories/{slug}/related", response_model=list[RelatedStory])
async def get_related_stories(slug: str, limit: int = 5):
    """Find related stories using pgvector similarity on the title chunk."""
    async with async_session() as session:
        # Get the story and its title chunk embedding
        result = await session.execute(
            select(Story).where(Story.slug == slug)
        )
        story = result.scalar_one_or_none()
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")

        # Get the title chunk's embedding for this story
        title_chunk = await session.execute(
            select(Chunk.embedding)
            .where(Chunk.story_id == story.id, Chunk.chunk_type == "title")
            .limit(1)
        )
        embedding_row = title_chunk.scalar_one_or_none()
        if embedding_row is None:
            return []

        # Find similar stories by their title chunks, excluding self
        query = sql_text("""
            SELECT DISTINCT ON (s.id)
                s.slug,
                s.title,
                s.author,
                s.score,
                s.created_at,
                1 - (c.embedding <=> :query_vec) AS similarity_score
            FROM chunks c
            JOIN stories s ON c.story_id = s.id
            WHERE c.chunk_type = 'title'
              AND s.id != :story_id
              AND 1 - (c.embedding <=> :query_vec) > 0.3
            ORDER BY s.id, c.embedding <=> :query_vec
        """)

        # Wrap to sort and limit
        wrapped = sql_text(f"""
            SELECT * FROM ({query.text}) sub
            ORDER BY similarity_score DESC
            LIMIT :limit
        """)

        result = await session.execute(wrapped, {
            "query_vec": str(list(embedding_row)),
            "story_id": str(story.id),
            "limit": limit,
        })

        return [
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
