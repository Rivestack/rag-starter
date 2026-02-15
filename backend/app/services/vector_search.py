import time
from dataclasses import dataclass

from sqlalchemy import text as sql_text

from app.database import async_session


@dataclass
class HNSearchResult:
    story_title: str
    story_url: str | None
    story_author: str
    story_score: int
    story_hn_id: int
    matched_content: str
    chunk_type: str
    comment_author: str | None
    similarity_score: float
    story_date: str


@dataclass
class SearchPerformance:
    query_time_ms: float
    chunks_searched: int
    index_type: str


async def search_hn(
    query_embedding: list[float],
    top_k: int = 10,
    threshold: float = 0.1,
) -> tuple[list[HNSearchResult], SearchPerformance]:
    """Semantic search across all HN chunks, returning results with story metadata."""
    async with async_session() as session:
        count_result = await session.execute(
            sql_text("SELECT COUNT(*) FROM chunks")
        )
        total_chunks = count_result.scalar()

        start = time.time()

        query = sql_text("""
            SELECT
                s.title AS story_title,
                s.url AS story_url,
                s.author AS story_author,
                s.score AS story_score,
                s.hn_id AS story_hn_id,
                c.content AS matched_content,
                c.chunk_type,
                c.author AS comment_author,
                1 - (c.embedding <=> :query_vec) AS similarity_score,
                s.created_at AS story_date
            FROM chunks c
            JOIN stories s ON c.story_id = s.id
            WHERE 1 - (c.embedding <=> :query_vec) > :threshold
            ORDER BY c.embedding <=> :query_vec
            LIMIT :top_k
        """)

        result = await session.execute(query, {
            "query_vec": str(query_embedding),
            "threshold": threshold,
            "top_k": top_k,
        })

        query_time = (time.time() - start) * 1000

        results = [
            HNSearchResult(
                story_title=row.story_title,
                story_url=row.story_url,
                story_author=row.story_author,
                story_score=row.story_score,
                story_hn_id=row.story_hn_id,
                matched_content=row.matched_content,
                chunk_type=row.chunk_type,
                comment_author=row.comment_author,
                similarity_score=round(float(row.similarity_score), 4),
                story_date=row.story_date.isoformat()[:10],
            )
            for row in result.fetchall()
        ]

        perf = SearchPerformance(
            query_time_ms=round(query_time, 2),
            chunks_searched=total_chunks or 0,
            index_type="hnsw",
        )

        return results, perf
