import tiktoken
from collections import defaultdict
from dataclasses import dataclass, field

from app.services.pdf_parser import PageData


@dataclass
class ChunkResult:
    content: str
    page_number: int
    chunk_index: int
    bbox_data: list[dict] = field(default_factory=list)
    token_count: int = 0


def create_chunks(
    pages: list[PageData],
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> list[ChunkResult]:
    """
    Create page-aware chunks with bounding box metadata.

    Bounding boxes are stored as normalized [0,1] fractions of page dimensions
    so the frontend can use CSS percentage positioning at any scale.
    Word-level bboxes are merged into line-level rectangles for clean rendering.
    """
    enc = tiktoken.encoding_for_model("gpt-4o-mini")

    # Build unified text with page boundary tracking
    page_offsets: list[tuple[int, int, PageData]] = []
    full_text_parts = []
    offset = 0

    for page in pages:
        start = offset
        full_text_parts.append(page.full_text)
        offset += len(page.full_text)
        page_offsets.append((start, offset, page))
        full_text_parts.append("\n")
        offset += 1

    full_text = "".join(full_text_parts)
    tokens = enc.encode(full_text)

    chunks = []
    token_pos = 0
    chunk_idx = 0

    while token_pos < len(tokens):
        end_pos = min(token_pos + chunk_size, len(tokens))
        chunk_tokens = tokens[token_pos:end_pos]
        chunk_text = enc.decode(chunk_tokens)

        # Try to break at sentence boundaries for cleaner chunks
        if end_pos < len(tokens):
            search_zone = chunk_text[-100:]
            for delim in [". ", ".\n", "! ", "? "]:
                last_break = search_zone.rfind(delim)
                if last_break != -1:
                    actual_end = len(chunk_text) - len(search_zone) + last_break + len(delim)
                    chunk_text = chunk_text[:actual_end]
                    break

        # Map chunk back to global character offsets
        chunk_global_start = len(enc.decode(tokens[:token_pos]))
        chunk_global_end = chunk_global_start + len(chunk_text)

        # Collect bboxes from overlapping pages
        bbox_list = []
        primary_page = 1

        for page_start, page_end, page_data in page_offsets:
            overlap_start = max(chunk_global_start, page_start)
            overlap_end = min(chunk_global_end, page_end)

            if overlap_start >= overlap_end:
                continue

            if not bbox_list:
                primary_page = page_data.page_number

            local_start = overlap_start - page_start
            local_end = overlap_end - page_start

            for char_s, char_e, word_idx in page_data.char_to_word_map:
                if char_e > local_start and char_s < local_end:
                    w = page_data.words[word_idx]
                    bbox_list.append({
                        "x0": round(w.x0 / page_data.width, 6),
                        "y0": round(w.y0 / page_data.height, 6),
                        "x1": round(w.x1 / page_data.width, 6),
                        "y1": round(w.y1 / page_data.height, 6),
                        "page": page_data.page_number,
                    })

        bbox_list = _merge_line_bboxes(bbox_list)

        content = chunk_text.strip()
        if content:
            chunks.append(ChunkResult(
                content=content,
                page_number=primary_page,
                chunk_index=chunk_idx,
                bbox_data=bbox_list,
                token_count=len(enc.encode(content)),
            ))
            chunk_idx += 1

        actual_tokens_used = len(enc.encode(chunk_text))
        token_pos += max(actual_tokens_used - chunk_overlap, 1)

    return chunks


def _merge_line_bboxes(bboxes: list[dict]) -> list[dict]:
    """Merge word-level bboxes into line-level rectangles for clean rendering."""
    if not bboxes:
        return []

    groups: dict[tuple, list[dict]] = defaultdict(list)
    for b in bboxes:
        y_key = round(b["y0"] * 200) / 200
        groups[(b["page"], y_key)].append(b)

    merged = []
    for (page, _), group in sorted(groups.items()):
        merged.append({
            "x0": round(min(b["x0"] for b in group), 6),
            "y0": round(min(b["y0"] for b in group), 6),
            "x1": round(max(b["x1"] for b in group), 6),
            "y1": round(max(b["y1"] for b in group), 6),
            "page": page,
        })

    return merged
