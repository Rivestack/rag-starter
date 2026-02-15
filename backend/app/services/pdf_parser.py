import fitz  # PyMuPDF
from dataclasses import dataclass, field


@dataclass
class WordInfo:
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    page_number: int
    block_no: int
    line_no: int
    word_no: int


@dataclass
class PageData:
    page_number: int
    width: float
    height: float
    words: list[WordInfo] = field(default_factory=list)
    full_text: str = ""
    char_to_word_map: list[tuple[int, int, int]] = field(default_factory=list)


def extract_pages(pdf_bytes: bytes) -> list[PageData]:
    """Extract all pages with word-level position data for highlight mapping."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        page_number = page_idx + 1
        rect = page.rect

        raw_words = page.get_text("words")

        words = []
        text_parts = []
        char_to_word_map = []
        current_offset = 0

        for i, w in enumerate(raw_words):
            word_text = w[4]
            word_info = WordInfo(
                text=word_text,
                x0=w[0], y0=w[1], x1=w[2], y1=w[3],
                page_number=page_number,
                block_no=w[5], line_no=w[6], word_no=w[7],
            )
            words.append(word_info)

            if i > 0:
                text_parts.append(" ")
                current_offset += 1

            start = current_offset
            end = current_offset + len(word_text)
            char_to_word_map.append((start, end, i))
            text_parts.append(word_text)
            current_offset = end

        pages.append(PageData(
            page_number=page_number,
            width=rect.width,
            height=rect.height,
            words=words,
            full_text="".join(text_parts),
            char_to_word_map=char_to_word_map,
        ))

    doc.close()
    return pages
