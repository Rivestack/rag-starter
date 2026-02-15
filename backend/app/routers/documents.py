import json
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.database import get_session, async_session
from app.models import Document, Chunk
from app.schemas import DocumentResponse, DocumentListResponse
from app.services.pdf_parser import extract_pages
from app.services.chunker import create_chunks
from app.services.embeddings import generate_embeddings
from app.config import settings

router = APIRouter(prefix="/api/documents", tags=["documents"])

UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a PDF and process it with real-time SSE progress updates."""

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    async def event_generator():
        doc_id = uuid.uuid4()
        try:
            # 1. Read file
            pdf_bytes = await file.read()
            file_size = len(pdf_bytes)

            if file_size > settings.max_file_size_mb * 1024 * 1024:
                yield {
                    "event": "error",
                    "data": json.dumps({"message": f"File exceeds {settings.max_file_size_mb}MB limit"}),
                }
                return

            yield {
                "event": "progress",
                "data": json.dumps({"stage": "parsing", "percent": 10, "message": "Extracting text from PDF..."}),
            }

            # 2. Parse PDF
            pages = extract_pages(pdf_bytes)
            if not pages:
                yield {"event": "error", "data": json.dumps({"message": "Could not extract text from PDF"})}
                return

            yield {
                "event": "progress",
                "data": json.dumps({"stage": "parsing", "percent": 25, "message": f"Parsed {len(pages)} pages"}),
            }

            # 3. Create chunks
            chunks = create_chunks(pages, settings.chunk_size, settings.chunk_overlap)
            yield {
                "event": "progress",
                "data": json.dumps({"stage": "chunking", "percent": 35, "message": f"Created {len(chunks)} chunks"}),
            }

            # 4. Generate embeddings in batches
            batch_size = 20
            all_embeddings: list[list[float]] = []
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i : i + batch_size]
                embeddings = await generate_embeddings([c.content for c in batch])
                all_embeddings.extend(embeddings)
                progress = 35 + int((i + len(batch)) / len(chunks) * 55)
                yield {
                    "event": "progress",
                    "data": json.dumps({
                        "stage": "embedding",
                        "percent": min(progress, 90),
                        "message": f"Generating embeddings ({i + len(batch)}/{len(chunks)})",
                    }),
                }

            yield {
                "event": "progress",
                "data": json.dumps({"stage": "storing", "percent": 92, "message": "Storing vectors in Rivestack..."}),
            }

            # 5. Save PDF to disk
            pdf_path = UPLOAD_DIR / f"{doc_id}.pdf"
            pdf_path.write_bytes(pdf_bytes)

            # 6. Store document and chunks in database
            async with async_session() as session:
                doc = Document(
                    id=doc_id,
                    filename=file.filename,
                    file_size=file_size,
                    page_count=len(pages),
                    upload_status="ready",
                )
                session.add(doc)

                for idx, chunk in enumerate(chunks):
                    db_chunk = Chunk(
                        document_id=doc_id,
                        chunk_index=idx,
                        content=chunk.content,
                        page_number=chunk.page_number,
                        bbox_data=chunk.bbox_data,
                        token_count=chunk.token_count,
                        embedding=all_embeddings[idx],
                    )
                    session.add(db_chunk)

                await session.commit()

            yield {
                "event": "complete",
                "data": json.dumps({
                    "document_id": str(doc_id),
                    "filename": file.filename,
                    "page_count": len(pages),
                    "chunk_count": len(chunks),
                    "file_size": file_size,
                }),
            }

        except Exception as e:
            yield {"event": "error", "data": json.dumps({"message": str(e)})}

    return EventSourceResponse(event_generator())


@router.get("", response_model=DocumentListResponse)
async def list_documents(session: AsyncSession = Depends(get_session)):
    """List all uploaded documents."""
    result = await session.execute(
        select(Document).order_by(Document.created_at.desc())
    )
    docs = result.scalars().all()
    return DocumentListResponse(documents=[DocumentResponse.model_validate(d) for d in docs])


@router.get("/{document_id}/pdf")
async def serve_pdf(document_id: uuid.UUID):
    """Serve the original PDF file."""
    pdf_path = UPLOAD_DIR / f"{document_id}.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found")
    return FileResponse(pdf_path, media_type="application/pdf")


@router.delete("/{document_id}", status_code=204)
async def delete_document(document_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    """Delete a document and all its chunks."""
    result = await session.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    await session.delete(doc)
    await session.commit()

    # Remove PDF file
    pdf_path = UPLOAD_DIR / f"{document_id}.pdf"
    if pdf_path.exists():
        pdf_path.unlink()
