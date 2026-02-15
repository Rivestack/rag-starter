export interface Document {
  id: string
  filename: string
  file_size: number
  page_count: number
  upload_status: 'processing' | 'ready' | 'error'
  created_at: string
}

export interface BboxRect {
  x0: number
  y0: number
  x1: number
  y1: number
  page: number
}

export interface SourceChunk {
  chunk_id: string
  content: string
  page_number: number
  bbox_data: BboxRect[]
  similarity_score: number
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: SourceChunk[]
  timestamp: Date
}

export interface UploadProgress {
  stage: 'parsing' | 'chunking' | 'embedding' | 'storing'
  percent: number
  message: string
}
