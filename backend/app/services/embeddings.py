from openai import AsyncOpenAI
from app.config import settings

client = AsyncOpenAI(api_key=settings.openai_api_key)


async def generate_embedding(text: str) -> list[float]:
    """Generate embedding for a single text."""
    response = await client.embeddings.create(
        input=text,
        model=settings.embedding_model,
    )
    return response.data[0].embedding


async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a batch of texts."""
    response = await client.embeddings.create(
        input=texts,
        model=settings.embedding_model,
    )
    sorted_data = sorted(response.data, key=lambda x: x.index)
    return [item.embedding for item in sorted_data]
