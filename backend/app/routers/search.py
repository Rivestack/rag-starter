import time

from fastapi import APIRouter

from app.schemas import SearchRequest, SearchResponse, SearchResultItem, PerformanceStats
from app.services.embeddings import generate_embedding
from app.services.vector_search import search_hn
from app.config import settings

router = APIRouter(prefix="/api", tags=["search"])


@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Semantic search over HN stories and comments."""
    total_start = time.time()

    # Generate embedding for query
    embed_start = time.time()
    query_embedding = await generate_embedding(request.query)
    embedding_time_ms = (time.time() - embed_start) * 1000

    # Search
    top_k = request.top_k or settings.top_k
    results, perf = await search_hn(
        query_embedding=query_embedding,
        top_k=top_k,
        threshold=settings.similarity_threshold,
    )

    total_time_ms = (time.time() - total_start) * 1000

    return SearchResponse(
        results=[
            SearchResultItem(
                story_title=r.story_title,
                story_url=r.story_url,
                story_author=r.story_author,
                story_score=r.story_score,
                story_hn_url=f"https://news.ycombinator.com/item?id={r.story_hn_id}",
                matched_content=r.matched_content,
                chunk_type=r.chunk_type,
                comment_author=r.comment_author,
                similarity_score=r.similarity_score,
                story_date=r.story_date,
            )
            for r in results
        ],
        performance=PerformanceStats(
            query_time_ms=round(perf.query_time_ms, 2),
            embedding_time_ms=round(embedding_time_ms, 2),
            total_time_ms=round(total_time_ms, 2),
            chunks_searched=perf.chunks_searched,
            results_found=len(results),
            index_type=perf.index_type,
            similarity_metric="cosine",
        ),
    )
