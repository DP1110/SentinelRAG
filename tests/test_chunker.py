import pytest
from app.ingestion.cleaner import clean_text
from app.ingestion.chunker import chunk_document


def test_clean_text_removes_zero_width_chars():
    dirty_text = "System\u200b \u200cClean\ufeff"
    cleaned = clean_text(dirty_text)
    assert "\u200b" not in cleaned
    assert "\u200c" not in cleaned
    assert "\ufeff" not in cleaned
    assert "System Clean" == cleaned


def test_clean_text_normalizes_whitespace():
    text = "Hello   world!\r\n\r\n\r\n\r\nNew line here."
    cleaned = clean_text(text)
    assert "Hello world!" in cleaned
    assert "\r" not in cleaned
    assert "\n\n\n" not in cleaned


def test_chunk_document_structure_aware():
    markdown_doc = """# Document Title
Introductory paragraph explaining overview.

## Section 1: Architecture
Detailed architecture description.
FastAPI and PostgreSQL with pgvector.

## Section 2: Security
Dual layer authorization is enforced here."""

    chunks = chunk_document(markdown_doc, doc_id="doc1", doc_title="Test Document", target_chars=200)
    assert len(chunks) >= 2
    assert chunks[0].ordinal == 0
    assert chunks[0].metadata["doc_id"] == "doc1"
    assert chunks[0].metadata["doc_title"] == "Test Document"
