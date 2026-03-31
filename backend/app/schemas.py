from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str
    top_k: int = 10


class SearchResultItem(BaseModel):
    story_title: str
    story_slug: str
    story_url: str | None
    story_author: str
    story_score: int
    story_hn_url: str
    matched_content: str
    chunk_type: str
    comment_author: str | None = None
    similarity_score: float
    story_date: str


class PerformanceStats(BaseModel):
    query_time_ms: float
    embedding_time_ms: float
    total_time_ms: float
    chunks_searched: int
    results_found: int
    index_type: str
    similarity_metric: str


class SearchResponse(BaseModel):
    results: list[SearchResultItem]
    performance: PerformanceStats


class DbStats(BaseModel):
    total_stories: int
    total_chunks: int
    oldest_story: str | None
    newest_story: str | None
    index_type: str


class IngestResponse(BaseModel):
    stories_fetched: int
    chunks_created: int
    duration_seconds: float


class StoryChunk(BaseModel):
    content: str
    chunk_type: str
    author: str | None = None


class StoryDetail(BaseModel):
    slug: str
    hn_id: int
    title: str
    url: str | None
    author: str
    score: int
    num_comments: int
    story_text: str | None
    story_type: str
    created_at: str
    chunks: list[StoryChunk]


class RelatedStory(BaseModel):
    slug: str
    title: str
    author: str
    score: int
    created_at: str
    similarity_score: float


class StorySummary(BaseModel):
    slug: str
    title: str
    created_at: str
