from typing import List, Dict
from sqlalchemy.orm import Session
from app.db.models import Document, DocumentACL, Chunk
from app.retrieval.permissions import invalidate_acl_cache


def update_document_acls(
    document_id: str,
    new_acls: List[Dict[str, str]],
    db: Session,
):
    """
    Updates document ACLs and updates allowed_principals on all chunks
    WITHOUT re-embedding the chunks (FR-37).
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise ValueError(f"Document {document_id} not found")

    # 1. Clear old ACLs
    db.query(DocumentACL).filter(DocumentACL.document_id == document_id).delete()

    # 2. Add new ACLs and compile allowed principals list
    principals = set()
    for acl in new_acls:
        p_type = acl.get("principal_type") or acl.get("type", "user")
        p_id = acl.get("principal_id") or acl.get("id", "")
        role = acl.get("role", "reader")

        db_acl = DocumentACL(
            document_id=document_id,
            principal_type=p_type,
            principal_id=p_id,
            role=role,
        )
        db.add(db_acl)

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

    allowed_list = sorted(list(principals))

    # 3. Denormalize onto chunks directly without re-embedding
    chunks = db.query(Chunk).filter(Chunk.document_id == document_id).all()
    for chunk in chunks:
        chunk.allowed_principals = allowed_list

    db.commit()

    # 4. Invalidate cache
    invalidate_acl_cache(document_id)


def deactivate_document(document_id: str, db: Session):
    """
    Marks a document and all its chunks inactive (deactivated / unshared / deleted).
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if doc:
        doc.is_active = False
        chunks = db.query(Chunk).filter(Chunk.document_id == document_id).all()
        for chunk in chunks:
            chunk.is_active = False
        db.commit()
        invalidate_acl_cache(document_id)
