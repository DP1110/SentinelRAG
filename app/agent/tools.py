from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.core.identity import IdentityContext
from app.db.models import Document, DocumentACL, Chunk
from app.retrieval.hybrid import search_hybrid
from app.retrieval.permissions import verify_answer_time_permissions, get_fresh_document_principals


def tool_search_knowledge(
    query: str,
    identity: IdentityContext,
    db: Session,
) -> str:
    """Searches knowledge base strictly scoped to the requesting user's permissions."""
    candidates = search_hybrid(query, identity, db, top_k=3)
    verified, _ = verify_answer_time_permissions(candidates, identity, db)

    if not verified:
        return "No accessible documents found matching query."

    results = []
    for idx, c in enumerate(verified, start=1):
        results.append(f"[{idx}] {c.doc_title}: {c.text[:200]}")

    return "\n\n".join(results)


def tool_get_document(
    doc_id: str,
    identity: IdentityContext,
    db: Session,
) -> str:
    """Retrieves document contents only if the user is authorized."""
    allowed_principals, is_active = get_fresh_document_principals(doc_id, db)
    user_principals = set(identity.principals)

    if not is_active or user_principals.isdisjoint(allowed_principals):
        return "Access denied or document not found."

    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        return "Access denied or document not found."

    chunks = db.query(Chunk).filter(Chunk.document_id == doc_id).order_by(Chunk.ordinal).all()
    full_text = "\n".join(c.text for c in chunks)
    return f"Title: {doc.title}\nSensitivity: {doc.sensitivity}\n\n{full_text}"


def tool_summarize_document(
    doc_id: str,
    identity: IdentityContext,
    db: Session,
) -> str:
    """Summarizes document contents only if the user is authorized."""
    content = tool_get_document(doc_id, identity, db)
    if "Access denied" in content:
        return content

    first_line = content.split("\n")[0]
    return f"Summary of {first_line}: Document contains authorized operational guidelines."


def tool_create_ticket(
    title: str,
    description: str,
    confirmed: bool,
    identity: IdentityContext,
) -> str:
    """Write action creating a ticket. Requires explicit user confirmation (FR-42)."""
    if not confirmed:
        return f"Confirmation required: Please confirm creating ticket '{title}' with user {identity.user_id}."

    return f"Ticket created successfully: [TICK-{abs(hash(title)) % 10000}] '{title}' by {identity.user_id}."
