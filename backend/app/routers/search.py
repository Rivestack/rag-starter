import logging
import time

from fastapi import APIRouter, HTTPException
from openai import OpenAIError, RateLimitError

from app.schemas import SearchRequest, SearchResponse, SearchResultItem, PerformanceStats
from app.services.embeddings import generate_embedding
from app.services.vector_search import search_hn
from app.config import settings

router = APIRouter(prefix="/api", tags=["search"])
logger = logging.getLogger(__name__)


@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Semantic search over HN stories and comments."""
    total_start = time.time()

    # Generate embedding for query.
    #
    # Embedding failures are the provider being unavailable, not a bad request:
    # letting them escape returned a bare 500 with no body, so the UI could only
    # report a generic failure and in practice showed nothing at all. Answer with
    # a 503 and a reason the page can display.
    embed_start = time.time()
    try:
        query_embedding = await generate_embedding(request.query)
    except RateLimitError:
        logger.exception("embedding quota exhausted; search unavailable")
        raise HTTPException(
            status_code=503,
            detail="Search is temporarily unavailable: the embedding quota is exhausted. Browsing still works.",
        )
    except OpenAIError:
        logger.exception("embedding provider error; search unavailable")
        raise HTTPException(
            status_code=503,
            detail="Search is temporarily unavailable: the embedding provider did not respond.",
        )
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
                story_slug=r.story_slug,
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
