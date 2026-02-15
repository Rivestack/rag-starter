from fastapi import APIRouter

from app.schemas import ChatRequest, ChatResponse
from app.services.rag import generate_rag_response

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message and get a RAG-powered response with source highlights."""
    result = await generate_rag_response(
        document_id=str(request.document_id),
        user_message=request.message,
        conversation_history=request.conversation_history,
    )
    return ChatResponse(**result)
