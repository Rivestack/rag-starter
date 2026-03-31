from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database import engine
from app.models import Base
from app.routers import search, ingest, stats, stories
from app.services.embeddings import generate_embedding


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        # One-time migration: if chunks table exists with old schema (document_id), wipe and recreate
        result = await conn.execute(text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.columns "
            "  WHERE table_name = 'chunks' AND column_name = 'story_id'"
            ")"
        ))
        has_correct_schema = result.scalar()
        if not has_correct_schema:
            await conn.execute(text("DROP TABLE IF EXISTS chunks CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS documents CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS stories CASCADE"))
        # Migration: add slug column if missing
        slug_exists = await conn.execute(text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.columns "
            "  WHERE table_name = 'stories' AND column_name = 'slug'"
            ")"
        ))
        if not slug_exists.scalar():
            await conn.execute(text(
                "ALTER TABLE stories ADD COLUMN slug VARCHAR(300)"
            ))
            # Backfill slugs for existing stories
            rows = await conn.execute(text("SELECT id, title, hn_id FROM stories"))
            for row in rows.fetchall():
                from app.models import generate_slug
                slug = generate_slug(row.title, row.hn_id)
                await conn.execute(text(
                    "UPDATE stories SET slug = :slug WHERE id = :id"
                ), {"slug": slug, "id": row.id})
            await conn.execute(text(
                "ALTER TABLE stories ALTER COLUMN slug SET NOT NULL"
            ))
            await conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_stories_slug ON stories (slug)"
            ))
        await conn.run_sync(Base.metadata.create_all)
        # Create HNSW index for cosine similarity
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw
            ON chunks USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64)
        """))
    # Warm up OpenAI connection so first search is fast
    await generate_embedding("warmup")
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
    max_age=3600,
)

app.include_router(search.router)
app.include_router(ingest.router)
app.include_router(stats.router)
app.include_router(stories.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
