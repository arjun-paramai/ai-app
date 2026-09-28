from io import BytesIO

import pytest
from docx import Document
from pypdf import PdfWriter

from app.ingestion import chunk_pages, extract_pages


def test_overlap_and_page_provenance():
    chunks = chunk_pages([(2, "one two three four five six"), (4, "seven eight")], size=4, overlap=1)
    assert chunks == [{"page": 2, "text": "one two three four"},
                      {"page": 2, "text": "four five six"}, {"page": 4, "text": "seven eight"}]


def test_bad_chunk_configuration():
    with pytest.raises(ValueError):
        chunk_pages([(1, "test")], size=3, overlap=3)


def test_bom_and_empty_document():
    assert extract_pages("a.txt", b"\xef\xbb\xbfAgreement") == [(1, "Agreement")]
    with pytest.raises(ValueError, match="No extractable text"):
        extract_pages("a.txt", b"  \n ")


def test_docx_includes_tables():
    doc = Document()
    doc.add_paragraph("Services Agreement")
    table = doc.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Notice period"
    table.cell(0, 1).text = "30 days"
    stream = BytesIO()
    doc.save(stream)
    assert "Notice period | 30 days" in extract_pages("a.docx", stream.getvalue())[0][1]


def test_scanned_pdf_rejected():
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    stream = BytesIO()
    writer.write(stream)
    with pytest.raises(ValueError, match="OCR"):
        extract_pages("scan.pdf", stream.getvalue())


def test_invalid_format_and_signature():
    for name in ["a.exe", "a.pdf"]:
        with pytest.raises(ValueError):
            extract_pages(name, b"not a pdf")
