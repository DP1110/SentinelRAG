from typing import List
from app.retrieval.hybrid import RetrievalCandidate, compute_keyword_score
from app.core.config import settings

_CROSS_ENCODER = None
_CE_FAILED = False


def _get_cross_encoder():
    global _CROSS_ENCODER, _CE_FAILED
    if _CROSS_ENCODER is None and not _CE_FAILED:
        try:
            from sentence_transformers import CrossEncoder
            _CROSS_ENCODER = CrossEncoder(settings.RERANKER_MODEL, local_files_only=True)
        except Exception:
            _CE_FAILED = True
    return _CROSS_ENCODER


def rerank_candidates(
    query: str,
    candidates: List[RetrievalCandidate],
    top_k: int = settings.DEFAULT_TOP_K,
) -> List[RetrievalCandidate]:
    """
    Reranks candidates using a cross-encoder model or enhanced relevance scoring.
    """
    if not candidates:
        return []

    ce = _get_cross_encoder()
    if ce is not None:
        try:
            pairs = [[query, c.text] for c in candidates]
            scores = ce.predict(pairs)
            for c, s in zip(candidates, scores):
                c.score = float(s)
            candidates.sort(key=lambda x: x.score, reverse=True)
            return candidates[:top_k]
        except Exception:
            pass

    # Fallback reranking: boost candidates that have high RRF score + keyword density
    for c in candidates:
        kw = compute_keyword_score(query, c.text)
        # Combine RRF score with keyword exact match weight
        c.score = c.score * 10.0 + (kw * 0.5)

    candidates.sort(key=lambda x: x.score, reverse=True)
    return candidates[:top_k]
