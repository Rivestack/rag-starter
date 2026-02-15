from fastapi import APIRouter
from sqlalchemy import select, func

from app.database import async_session
from app.models import Story, Chunk
from app.schemas import DbStats

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/stats", response_model=DbStats)
async def get_stats():
    """Get database statistics."""
    async with async_session() as session:
        story_count = (await session.execute(
            select(func.count(Story.id))
        )).scalar() or 0

        chunk_count = (await session.execute(
            select(func.count(Chunk.id))
        )).scalar() or 0

        oldest = (await session.execute(
            select(func.min(Story.created_at))
        )).scalar()

        newest = (await session.execute(
            select(func.max(Story.created_at))
        )).scalar()

        return DbStats(
            total_stories=story_count,
            total_chunks=chunk_count,
            oldest_story=oldest.isoformat()[:10] if oldest else None,
            newest_story=newest.isoformat()[:10] if newest else None,
            index_type="hnsw",
        )
