export interface SearchResultItem {
  story_title: string
  story_slug: string
  story_url: string | null
  story_author: string
  story_score: number
  story_hn_url: string
  matched_content: string
  chunk_type: 'title' | 'story_text' | 'comment'
  comment_author: string | null
  similarity_score: number
  story_date: string
}

export interface StoryDetail {
  slug: string
  hn_id: number
  title: string
  url: string | null
  author: string
  score: number
  num_comments: number
  story_text: string | null
  story_type: string
  created_at: string
  chunks: StoryChunk[]
}

export interface StoryChunk {
  content: string
  chunk_type: string
  author: string | null
}

export interface RelatedStory {
  slug: string
  title: string
  author: string
  score: number
  created_at: string
  similarity_score: number
}

export interface PerformanceStats {
  query_time_ms: number
  embedding_time_ms: number
  total_time_ms: number
  chunks_searched: number
  results_found: number
  index_type: string
  similarity_metric: string
}

export interface SearchResponse {
  results: SearchResultItem[]
  performance: PerformanceStats
}

export interface DbStats {
  total_stories: number
  total_chunks: number
  oldest_story: string | null
  newest_story: string | null
  index_type: string
}
