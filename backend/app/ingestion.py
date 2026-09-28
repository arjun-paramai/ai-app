from io import BytesIO
import re
from zipfile import ZipFile


def extract_pages(name: str, data: bytes) -> list[tuple[int, str]]:
    suffix = name.lower().rsplit(".", 1)[-1]
    if suffix == "pdf":
        from pypdf import PdfReader
        if not data.startswith(b"%PDF-"):
            raise ValueError("Invalid PDF signature.")
        reader = PdfReader(BytesIO(data))
        if reader.is_encrypted:
            raise ValueError("Encrypted PDFs are not supported.")
        if len(reader.pages) > 100:
            raise ValueError("Maximum 100 pages per document.")
        pages = [(i + 1, p.extract_text() or "") for i, p in enumerate(reader.pages)]
    elif suffix == "docx":
        from docx import Document
        with ZipFile(BytesIO(data)) as archive:
            if sum(f.file_size for f in archive.infolist()) > 30_000_000:
                raise ValueError("Expanded DOCX exceeds 30 MB.")
        doc = Document(BytesIO(data))
        text = "\n".join(p.text for p in doc.paragraphs)
        text += "\n" + "\n".join(" | ".join(c.text for c in row.cells) for table in doc.tables for row in table.rows)
        # DOCX has no reliable page boundaries; 1 denotes the extracted text section.
        pages = [(1, text)]
    elif suffix == "txt":
        pages = [(1, data.decode("utf-8-sig"))]
    else:
        raise ValueError("Upload PDF, DOCX, or UTF-8 TXT.")
    if sum(len(text) for _, text in pages) > 300_000:
        raise ValueError("Maximum 300,000 extracted characters.")
    if not any(text.strip() for _, text in pages):
        raise ValueError("No extractable text. Scanned PDFs need OCR before upload.")
    return pages


def chunk_pages(pages: list[tuple[int, str]], size: int = 180, overlap: int = 30) -> list[dict]:
    if size <= overlap or overlap < 0:
        raise ValueError("Chunk size must be greater than overlap.")
    result = []
    for page, text in pages:
        words = re.findall(r"\S+", text.replace("\x00", ""))
        for start in range(0, len(words), size - overlap):
            result.append({"page": page, "text": " ".join(words[start:start + size])})
            if start + size >= len(words):
                break
    return result
