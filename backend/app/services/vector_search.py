from dataclasses import dataclass
from sqlalchemy import text as sql_text

from app.database import async_session


@dataclass
class SearchResult:
    id: str
    content: str
    page_number: int
    bbox_data: list[dict]
    similarity_score: float


async def search_similar_chunks(
    document_id: str,
    query_embedding: list[float],
    top_k: int = 5,
    threshold: float = 0.3,
) -> list[SearchResult]:
    """Cosine similarity search using pgvector."""
    async with async_session() as session:
        query = sql_text("""
            SELECT
                id, content, page_number, bbox_data,
                1 - (embedding <=> :query_vec) AS similarity_score
            FROM chunks
            WHERE document_id = :doc_id
              AND 1 - (embedding <=> :query_vec) > :threshold
            ORDER BY embedding <=> :query_vec
            LIMIT :top_k
        """)

        result = await session.execute(query, {
            "query_vec": str(query_embedding),
            "doc_id": document_id,
            "threshold": threshold,
            "top_k": top_k,
        })

        return [
            SearchResult(
                id=str(row.id),
                content=row.content,
                page_number=row.page_number,
                bbox_data=row.bbox_data,
                similarity_score=float(row.similarity_score),
            )
            for row in result.fetchall()
        ]
