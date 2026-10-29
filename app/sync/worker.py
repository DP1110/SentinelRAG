import hashlib
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.db.models import Connector, Document, DocumentACL, Chunk, SyncEvent
from app.connectors.base import BaseConnector, ConnectorItem
from app.ingestion.chunker import chunk_document
from app.retrieval.embeddings import get_embedding
from app.sync.acl_sync import update_document_acls, deactivate_document


def sync_connector_items(
    connector: BaseConnector,
    db: Session,
) -> Dict[str, Any]:
    """
    Syncs items from a connector into the PostgreSQL/database index.
    Detects new documents, modifies updated ones, and updates ACLs.
    """
    start_time = datetime.utcnow()
    items = connector.list_items()
    synced_count = 0
    errors = []

    for item in items:
        try:
            content_hash = hashlib.sha256(item.content.encode("utf-8")).hexdigest()
            existing_doc = (
                db.query(Document)
                .filter(
                    Document.connector_id == connector.connector_id,
                    Document.source_id == item.source_id,
                )
                .first()
            )

            allowed_principals = item.get_allowed_principals()

            if not existing_doc:
                # 1. New document
                doc = Document(
                    id=f"{connector.connector_id}_{item.source_id}",
                    connector_id=connector.connector_id,
                    source_id=item.source_id,
                    title=item.title,
                    url=item.url,
                    path=item.path,
                    version=item.version,
                    content_hash=content_hash,
                    sensitivity=item.sensitivity,
                    is_active=True,
                    modified_at=item.modified_at,
                )
                db.add(doc)
                db.flush()

                # Add ACLs
                for acl in item.acls:
                    doc_acl = DocumentACL(
                        document_id=doc.id,
                        principal_type=acl.get("type", "user"),
                        principal_id=acl.get("id", ""),
                        role=acl.get("role", "reader"),
                    )
                    db.add(doc_acl)

                # Chunk and embed
                chunk_items = chunk_document(item.content, doc.id, doc.title)
                for ci in chunk_items:
                    emb = get_embedding(ci.text)
                    c = Chunk(
                        id=f"{doc.id}_c{ci.ordinal}",
                        document_id=doc.id,
                        ordinal=ci.ordinal,
                        text=ci.text,
                        embedding=emb,
                        tsv=ci.text.lower(),
                        metadata_json=ci.metadata,
                        allowed_principals=allowed_principals,
                        risk_score=ci.risk_score,
                        is_active=True,
                    )
                    db.add(c)

                synced_count += 1
            else:
                # 2. Existing document - check if content or ACLs changed
                if existing_doc.content_hash != content_hash:
                    # Content updated: re-chunk and re-embed
                    existing_doc.title = item.title
                    existing_doc.url = item.url
                    existing_doc.content_hash = content_hash
                    existing_doc.version = item.version
                    existing_doc.modified_at = item.modified_at
                    existing_doc.is_active = True

                    # Delete old chunks
                    db.query(Chunk).filter(Chunk.document_id == existing_doc.id).delete()

                    chunk_items = chunk_document(item.content, existing_doc.id, existing_doc.title)
                    for ci in chunk_items:
                        emb = get_embedding(ci.text)
                        c = Chunk(
                            id=f"{existing_doc.id}_c{ci.ordinal}",
                            document_id=existing_doc.id,
                            ordinal=ci.ordinal,
                            text=ci.text,
                            embedding=emb,
                            tsv=ci.text.lower(),
                            metadata_json=ci.metadata,
                            allowed_principals=allowed_principals,
                            risk_score=ci.risk_score,
                            is_active=True,
                        )
                        db.add(c)
                    synced_count += 1
                else:
                    # Check if ACLs changed
                    update_document_acls(existing_doc.id, item.acls, db)

        except Exception as e:
            db.rollback()
            errors.append(str(e))

    db.commit()

    # Record sync event
    status = "failed" if errors and synced_count == 0 else "success"
    event = SyncEvent(
        connector_id=connector.connector_id,
        event_type="sync_all",
        status=status,
        error="; ".join(errors) if errors else None,
    )
    db.add(event)
    db.commit()

    return {
        "connector_id": connector.connector_id,
        "synced_count": synced_count,
        "errors": errors,
        "duration_ms": (datetime.utcnow() - start_time).total_seconds() * 1000,
    }
