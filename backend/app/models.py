import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, Text, ForeignKey, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass


class Story(Base):
    __tablename__ = "stories"
    __table_args__ = (
        Index("idx_stories_hn_id", "hn_id", unique=True),
        Index("idx_stories_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    hn_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    author: Mapped[str] = mapped_column(String(200), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    num_comments: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    story_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    story_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="story"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="story", cascade="all, delete-orphan"
    )


class Chunk(Base):
    __tablename__ = "chunks"
    __table_args__ = (
        Index("idx_chunks_story_id", "story_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    story_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stories.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )
    author: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    embedding = mapped_column(Vector(1536), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    story: Mapped["Story"] = relationship(back_populates="chunks")
