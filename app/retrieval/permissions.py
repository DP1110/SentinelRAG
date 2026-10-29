import time
from typing import List, Tuple, Dict, Set, Optional
from sqlalchemy.orm import Session
from app.core.identity import IdentityContext
from app.db.models import Document, DocumentACL
from app.retrieval.hybrid import RetrievalCandidate
from app.core.config import settings

# Short-TTL ACL Cache: { doc_id: (timestamp, set_of_principals, is_active) }
_ACL_CACHE: Dict[str, Tuple[float, Set[str], bool]] = {}


def get_fresh_document_principals(doc_id: str, db: Session) -> Tuple[Set[str], bool]:
    """
    Fetches the freshest ACL principals for a document, utilizing a 60-second TTL cache.
    """
    now = time.time()
    if doc_id in _ACL_CACHE:
        cached_time, principals, is_active = _ACL_CACHE[doc_id]
        if now - cached_time < settings.ACL_CACHE_TTL_SECONDS:
            return principals, is_active

    # Fetch from database
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        _ACL_CACHE[doc_id] = (now, set(), False)
        return set(), False

    acls = db.query(DocumentACL).filter(DocumentACL.document_id == doc_id).all()
    principals = set()
    for acl in acls:
        p_type = acl.principal_type
        p_id = acl.principal_id
        if p_type in ["public", "anyone"] or p_id in ["public", "anyone"]:
            principals.add("public")
        elif p_type == "domain":
            principals.add(f"domain:{p_id}")
        elif p_type == "group":
            principals.add(f"group:{p_id}")
        elif p_type == "user":
            principals.add(f"user:{p_id}")
        else:
            principals.add(f"{p_type}:{p_id}")

    _ACL_CACHE[doc_id] = (now, principals, doc.is_active)
    return principals, doc.is_active


def invalidate_acl_cache(doc_id: Optional[str] = None):
    """Invalidates the ACL cache for a document or globally."""
    global _ACL_CACHE
    if doc_id:
        _ACL_CACHE.pop(doc_id, None)
    else:
        _ACL_CACHE.clear()


def verify_answer_time_permissions(
    candidates: List[RetrievalCandidate],
    user_identity: IdentityContext,
    db: Session,
) -> Tuple[List[RetrievalCandidate], List[str]]:
    """
    Secondary authorization gate (Answer-time check).
    Re-verifies each candidate document against the freshest ACLs.
    Returns: (verified_candidates, list_of_removed_chunk_ids)
    """
    user_principals = set(user_identity.principals)
    verified: List[RetrievalCandidate] = []
    removed_ids: List[str] = []

    for c in candidates:
        try:
            allowed_principals, is_active = get_fresh_document_principals(c.document_id, db)
            # If document is inactive or unshared, or user's identity does not overlap allowed principals
            if not is_active or user_principals.isdisjoint(allowed_principals):
                removed_ids.append(c.chunk_id)
            else:
                verified.append(c)
        except Exception:
            # Fail closed on error
            if settings.FAIL_CLOSED_ON_ACL_ERROR:
                removed_ids.append(c.chunk_id)

    return verified, removed_ids
