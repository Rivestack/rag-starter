from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database import engine
from app.models import Base
from app.routers import search, ingest, stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        # Drop old DocChat tables (one-time migration)
        await conn.execute(text("DROP TABLE IF EXISTS documents CASCADE"))
        await conn.run_sync(Base.metadata.create_all)
        # Create HNSW index for cosine similarity
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw
            ON chunks USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64)
        """))
    yield
    await engine.dispose()


app = FastAPI(
    title="HN Search API",
    description="Semantic search over Hacker News — powered by Rivestack pgvector",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router)
app.include_router(ingest.router)
app.include_router(stats.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
