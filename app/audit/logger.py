from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.db.models import AuditLog


def record_audit_log(
    user_id: str,
    query: str,
    rewritten_query: Optional[str],
    retrieved_ids: List[str],
    removed_ids: List[str],
    model: str,
    latency_ms: float,
    tokens: int,
    db: Session,
) -> AuditLog:
    """
    Persists tamper-evident query audit record (FR-43).
    """
    log_entry = AuditLog(
        user_id=user_id,
        query=query,
        rewritten_query=rewritten_query,
        retrieved_ids=retrieved_ids,
        removed_ids=removed_ids,
        model=model,
        latency_ms=latency_ms,
        tokens=tokens,
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry


def get_audit_logs(
    db: Session,
    limit: int = 50,
    offset: int = 0,
    user_id: Optional[str] = None,
) -> List[AuditLog]:
    """Retrieves paginated audit logs for administrators (FR-44)."""
    q = db.query(AuditLog)
    if user_id:
        q = q.filter(AuditLog.user_id == user_id)
    return q.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
