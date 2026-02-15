from openai import AsyncOpenAI
from app.config import settings
from app.services.embeddings import generate_embedding
from app.services.vector_search import search_similar_chunks

client = AsyncOpenAI(api_key=settings.openai_api_key)

SYSTEM_PROMPT = """You are a helpful assistant that answers questions about a PDF document.
You MUST answer based ONLY on the provided context excerpts from the document.
If the context doesn't contain enough information to answer, say so clearly.

When referencing information, mention which part of the document it comes from
(e.g., "According to page 3..." or "The document states...").

Be concise and accurate. Do not make up information not present in the context."""


async def generate_rag_response(
    document_id: str,
    user_message: str,
    conversation_history: list[dict] | None = None,
) -> dict:
    """Full RAG pipeline: embed query -> vector search -> LLM with context -> answer + sources."""

    # 1. Embed the query
    query_embedding = await generate_embedding(user_message)

    # 2. Search for similar chunks
    results = await search_similar_chunks(
        document_id=document_id,
        query_embedding=query_embedding,
        top_k=settings.top_k,
        threshold=settings.similarity_threshold,
    )

    # 3. Build context
    context_parts = []
    for i, chunk in enumerate(results):
        context_parts.append(
            f"[Excerpt {i + 1}, Page {chunk.page_number}]:\n{chunk.content}"
        )
    context = "\n\n---\n\n".join(context_parts)

    # 4. Build messages
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if conversation_history:
        messages.extend(conversation_history[-6:])

    messages.append({
        "role": "user",
        "content": f"Context from the document:\n\n{context}\n\n---\n\nQuestion: {user_message}",
    })

    # 5. Call LLM
    response = await client.chat.completions.create(
        model=settings.chat_model,
        messages=messages,
        temperature=0.3,
        max_tokens=1024,
    )

    answer = response.choices[0].message.content

    # 6. Format sources
    sources = [
        {
            "chunk_id": chunk.id,
            "content": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
            "page_number": chunk.page_number,
            "bbox_data": chunk.bbox_data,
            "similarity_score": round(chunk.similarity_score, 4),
        }
        for chunk in results
    ]

    return {"answer": answer, "sources": sources, "model": settings.chat_model}
