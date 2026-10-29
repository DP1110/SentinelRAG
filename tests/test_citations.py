import pytest
from app.generation.citations import verify_and_extract_citations
from app.retrieval.hybrid import RetrievalCandidate


def test_verify_valid_citations():
    candidate1 = RetrievalCandidate(
        chunk_id="c1",
        document_id="doc1",
        text="Parental leave is 16 weeks.",
        doc_title="Parental Leave Policy",
        doc_url="https://source.local/hr_002",
        score=1.0,
    )
    raw_answer = "Employees get 16 weeks of parental leave [1]."
    clean_ans, citations = verify_and_extract_citations(raw_answer, [candidate1])

    assert "[1]" in clean_ans
    assert len(citations) == 1
    assert citations[0]["id"] == 1
    assert citations[0]["title"] == "Parental Leave Policy"
    assert citations[0]["chunk_ref"] == "c1"


def test_strips_hallucinated_bogus_citations():
    candidate1 = RetrievalCandidate(
        chunk_id="c1",
        document_id="doc1",
        text="Parental leave is 16 weeks.",
        doc_title="Parental Leave Policy",
        doc_url="https://source.local/hr_002",
        score=1.0,
    )
    # The answer cites [1] (valid) and [99] (bogus/hallucinated)
    raw_answer = "Employees get 16 weeks [1] and another perk [99]."
    clean_ans, citations = verify_and_extract_citations(raw_answer, [candidate1])

    assert "[1]" in clean_ans
    assert "[99]" not in clean_ans
    assert len(citations) == 1
