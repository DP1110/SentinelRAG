from typing import List, Dict, Any, Set
from sqlalchemy.orm import Session
from app.db.models import Chunk, Document
from app.core.identity import IdentityContext
from app.retrieval.embeddings import get_embedding, cosine_similarity
from app.core.config import settings
import re


class RetrievalCandidate:
    def __init__(
        self,
        chunk_id: str,
        document_id: str,
        text: str,
        doc_title: str,
        doc_url: str,
        score: float,
        dense_rank: int = -1,
        sparse_rank: int = -1,
        risk_score: float = 0.0,
        metadata: Dict[str, Any] = None,
    ):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.text = text
        self.doc_title = doc_title
        self.doc_url = doc_url
        self.score = score
        self.dense_rank = dense_rank
        self.sparse_rank = sparse_rank
        self.risk_score = risk_score
        self.metadata = metadata or {}


def compute_keyword_score(query: str, text: str) -> float:
    """Computes BM25-like token overlap score."""
    q_tokens = set(re.findall(r"\w+", query.lower()))
    if not q_tokens:
        return 0.0
    text_lower = text.lower()
    score = 0.0
    for tok in q_tokens:
        matches = len(re.findall(r"\b" + re.escape(tok) + r"\b", text_lower))
        if matches > 0:
            score += 1.0 + (matches * 0.2)
    return score


def search_hybrid(
    query: str,
    user_identity: IdentityContext,
    db: Session,
    top_k: int = settings.DEFAULT_TOP_K,
    candidate_pool_size: int = settings.DEFAULT_RERANK_TOP_K,
    rrf_k: int = settings.RRF_K,
) -> List[RetrievalCandidate]:
    """
    Executes permission-aware hybrid search (vector dense + keyword sparse)
    with Reciprocal Rank Fusion (RRF).
    Only returns chunks matching the user's allowed principals.
    """
    user_principals_set: Set[str] = set(user_identity.principals)

    # 1. Fetch active chunks and filter by allowed_principals
    active_chunks = (
        db.query(Chunk, Document)
        .join(Document, Chunk.document_id == Document.id)
        .filter(Chunk.is_active == True, Document.is_active == True)
        .all()
    )

    allowed_chunks = []
    for chunk, doc in active_chunks:
        principals = chunk.allowed_principals
        if isinstance(principals, list):
            chunk_principals = set(principals)
        else:
            chunk_principals = set()

        # Enforce RETRIEVAL-TIME access filter: set intersection must be non-empty
        if not user_principals_set.isdisjoint(chunk_principals):
            allowed_chunks.append((chunk, doc))

    if not allowed_chunks:
        return []

    # 2. Vector search (Dense)
    query_emb = get_embedding(query)
    dense_scored = []
    for chunk, doc in allowed_chunks:
        if chunk.embedding:
            sim = cosine_similarity(query_emb, chunk.embedding)
        else:
            sim = 0.0
        dense_scored.append((chunk, doc, sim))

    # Sort descending by cosine similarity
    dense_scored.sort(key=lambda x: x[2], reverse=True)
    dense_ranks = {item[0].id: rank + 1 for rank, item in enumerate(dense_scored)}

    # 3. Keyword search (Sparse)
    sparse_scored = []
    for chunk, doc in allowed_chunks:
        kw_score = compute_keyword_score(query, chunk.text)
        sparse_scored.append((chunk, doc, kw_score))

    sparse_scored.sort(key=lambda x: x[2], reverse=True)
    sparse_ranks = {item[0].id: rank + 1 for rank, item in enumerate(sparse_scored)}

    # 4. Reciprocal Rank Fusion (RRF)
    # RRF score = 1/(k + dense_rank) + 1/(k + sparse_rank)
    rrf_candidates = {}
    for chunk, doc in allowed_chunks:
        c_id = chunk.id
        d_rank = dense_ranks.get(c_id, 9999)
        s_rank = sparse_ranks.get(c_id, 9999)

        rrf_score = (1.0 / (rrf_k + d_rank)) + (1.0 / (rrf_k + s_rank))
        rrf_candidates[c_id] = RetrievalCandidate(
            chunk_id=c_id,
            document_id=doc.id,
            text=chunk.text,
            doc_title=doc.title,
            doc_url=doc.url or "",
            score=rrf_score,
            dense_rank=d_rank,
            sparse_rank=s_rank,
            risk_score=chunk.risk_score or 0.0,
            metadata=chunk.metadata_json or {},
        )

    # Sort descending by RRF score
    sorted_candidates = sorted(rrf_candidates.values(), key=lambda c: c.score, reverse=True)
    return sorted_candidates[:candidate_pool_size]
