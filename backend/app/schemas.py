from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class DocumentResponse(BaseModel):
    id: UUID
    filename: str
    file_size: int
    page_count: int
    upload_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]


class ChatRequest(BaseModel):
    document_id: UUID
    message: str
    conversation_history: list[dict] | None = None


class SourceChunk(BaseModel):
    chunk_id: UUID
    content: str
    page_number: int
    bbox_data: list[dict]
    similarity_score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    model: str
