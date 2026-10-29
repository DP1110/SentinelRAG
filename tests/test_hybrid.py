import pytest
from app.api.auth import SEEDED_PERSONAS, IdentityContext
from app.retrieval.hybrid import search_hybrid, compute_keyword_score
from app.retrieval.rerank import rerank_candidates


def test_keyword_scoring():
    query = "paid time off PTO"
    text1 = "Full time employees receive 25 days of paid time off (PTO) annually."
    text2 = "Kubernetes clusters deploy in us-west-2."
    
    score1 = compute_keyword_score(query, text1)
    score2 = compute_keyword_score(query, text2)
    assert score1 > score2
    assert score2 == 0.0


def test_hybrid_search_and_rerank(db_session):
    eng_info = SEEDED_PERSONAS["engineer"]
    eng_id = IdentityContext(
        user_id=eng_info["user_id"],
        email=eng_info["email"],
        display_name=eng_info["display_name"],
        persona="engineer",
        principals=eng_info["principals"],
    )

    candidates = search_hybrid("paid time off benefits", eng_id, db_session, top_k=5)
    assert len(candidates) > 0
    assert any("hr_001" in c.document_id for c in candidates)

    # Reranking
    reranked = rerank_candidates("paid time off benefits", candidates, top_k=3)
    assert len(reranked) <= 3
    assert reranked[0].score > 0
