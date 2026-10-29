import time
import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Header, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Connector, Document, DocumentACL, Chunk, AuditLog, EvalRun
from app.api.auth import get_current_identity, IdentityContext, SEEDED_PERSONAS
from app.api.middleware import rate_limiter
from app.core.cache import get_cached_rag_response, set_cached_rag_response
from app.core.redis import cache_manager
from app.api.schemas import (
    QueryRequest,
    QueryResponse,
    QueryMeta,
    CitationItem,
    AgentRunRequest,
    AgentRunResponse,
    ConnectorCreateRequest,
    ConnectorResponse,
    AuditLogItem,
    PersonaInfo,
)
from app.retrieval.hybrid import search_hybrid
from app.retrieval.rerank import rerank_candidates
from app.retrieval.permissions import verify_answer_time_permissions, get_fresh_document_principals
from app.retrieval.rewrite import rewrite_query
from app.generation.prompts import build_generation_prompt, SYSTEM_PROMPT
from app.generation.citations import verify_and_extract_citations
from app.generation.llm_adapters.mock import MockLLMAdapter
from app.generation.llm_adapters.gemini import GeminiLLMAdapter
from app.agent.runner import AgentRunner
from app.audit.logger import record_audit_log, background_record_audit_log, get_audit_logs
from app.core.config import settings
from eval.run_security import run_security_suite
from eval.run_quality import run_quality_benchmarks
from eval.report import generate_evaluation_report

router = APIRouter()


@router.get("/personas", response_model=List[PersonaInfo])
def list_personas():
    """List available simulated personas for testing authorization boundaries."""
    result = []
    for p_key, p_val in SEEDED_PERSONAS.items():
        result.append(
            PersonaInfo(
                persona=p_key,
                user_id=p_val["user_id"],
                email=p_val["email"],
                display_name=p_val["display_name"],
                groups=p_val["groups"],
            )
        )
    return result


@router.post("/query", response_model=QueryResponse)
def execute_query(
    req: QueryRequest,
    background_tasks: BackgroundTasks,
    identity: IdentityContext = Depends(rate_limiter),
    db: Session = Depends(get_db),
):
    """
    Main permission-aware RAG query endpoint (G1, G2, G3, G4).
    Enforces authorization at retrieval time and again at answer time.
    High-concurrency optimized with permission-isolated caching and async audit logging.
    """
    start_time = time.time()
    cache_manager.track_metric("queries_total", 1)

    # 0. Check Permission-Isolated Response Cache (High QPS optimization for 1,000+ users)
    cached_data = get_cached_rag_response(identity.principals, req.question)
    if cached_data:
        cached_meta = cached_data.get("meta", {})
        cached_meta["latency_ms"] = round((time.time() - start_time) * 1000, 2)
        cached_meta["cached"] = True
        cached_data["meta"] = cached_meta

        # Persist audit record in current DB session
        record_audit_log(
            user_id=identity.user_id,
            query=req.question,
            rewritten_query=None,
            retrieved_ids=[c["chunk_ref"] for c in cached_data.get("citations", [])],
            removed_ids=[],
            model=cached_meta.get("model", settings.LLM_PROVIDER) + " (cached)",
            latency_ms=cached_meta["latency_ms"],
            tokens=len(req.question.split()),
            db=db,
        )
        return QueryResponse(**cached_data)

    # 1. Query Rewriting / expansion
    rewritten = rewrite_query(req.question)

    # 2. Retrieval-time permission-filtered search (pushed down to SQL)
    candidates = search_hybrid(
        query=rewritten,
        user_identity=identity,
        db=db,
        top_k=req.options.top_k,
    )

    # 3. Reranking
    if req.options.rerank and candidates:
        candidates = rerank_candidates(rewritten, candidates, top_k=req.options.top_k)

    # 4. Answer-time permission check (Second authorization layer)
    verified_candidates, removed_ids = verify_answer_time_permissions(
        candidates=candidates,
        user_identity=identity,
        db=db,
    )

    # 5. Prompt construction & Generation
    prompt = build_generation_prompt(req.question, verified_candidates)
    
    # Choose LLM adapter
    if settings.LLM_PROVIDER == "gemini":
        adapter = GeminiLLMAdapter()
    else:
        adapter = MockLLMAdapter()

    model_name = settings.LLM_PROVIDER
    raw_answer = adapter.generate(prompt, SYSTEM_PROMPT)

    # 6. Citation Verification
    clean_answer, raw_citations = verify_and_extract_citations(raw_answer, verified_candidates)

    latency_ms = (time.time() - start_time) * 1000

    # 7. Tamper-evident Audit Logging
    retrieved_chunk_ids = [c.chunk_id for c in verified_candidates]
    record_audit_log(
        user_id=identity.user_id,
        query=req.question,
        rewritten_query=rewritten if rewritten != req.question else None,
        retrieved_ids=retrieved_chunk_ids,
        removed_ids=removed_ids,
        model=model_name,
        latency_ms=round(latency_ms, 2),
        tokens=len(req.question.split()) + len(clean_answer.split()),
        db=db,
    )

    citations = [
        CitationItem(
            id=c["id"],
            title=c["title"],
            url=c["url"],
            chunk_ref=c["chunk_ref"],
            snippet=c["snippet"],
        )
        for c in raw_citations
    ]

    response_payload = QueryResponse(
        answer=clean_answer,
        citations=citations,
        meta=QueryMeta(
            latency_ms=round(latency_ms, 2),
            chunks_used=len(verified_candidates),
            filtered_out=len(removed_ids),
            persona=identity.persona,
            model=model_name,
            cached=False,
        ),
    )

    # Store in Permission-Isolated Response Cache
    set_cached_rag_response(
        principals=identity.principals,
        query=req.question,
        response_data=response_payload.model_dump(),
    )

    return response_payload


@router.post("/query/stream")
def execute_query_stream(
    req: QueryRequest,
    identity: IdentityContext = Depends(rate_limiter),
    db: Session = Depends(get_db),
):
    """
    Streaming query endpoint delivering tokens/chunks via Server-Sent Events (SSE)
    for low Time-To-First-Byte (TTFB) under high concurrency.
    """
    start_time = time.time()
    cache_manager.track_metric("queries_total", 1)

    rewritten = rewrite_query(req.question)
    candidates = search_hybrid(query=rewritten, user_identity=identity, db=db, top_k=req.options.top_k)
    if req.options.rerank and candidates:
        candidates = rerank_candidates(rewritten, candidates, top_k=req.options.top_k)
    verified_candidates, removed_ids = verify_answer_time_permissions(candidates, identity, db)

    prompt = build_generation_prompt(req.question, verified_candidates)
    adapter = MockLLMAdapter() if settings.LLM_PROVIDER == "mock" else GeminiLLMAdapter()
    raw_answer = adapter.generate(prompt, SYSTEM_PROMPT)
    clean_answer, raw_citations = verify_and_extract_citations(raw_answer, verified_candidates)

    def event_stream():
        # Stream answer in chunks of words for streaming effect
        words = clean_answer.split(" ")
        for i in range(0, len(words), 3):
            chunk = " ".join(words[i : i + 3]) + " "
            yield f"data: {json.dumps({'event': 'token', 'text': chunk})}\n\n"
            time.sleep(0.01)

        # Stream final citations & metadata
        yield f"data: {json.dumps({'event': 'done', 'citations': raw_citations, 'meta': {'chunks_used': len(verified_candidates), 'filtered_out': len(removed_ids), 'latency_ms': round((time.time() - start_time) * 1000, 2)}})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/documents/{doc_id}")
def get_document_by_id(
    doc_id: str,
    identity: IdentityContext = Depends(get_current_identity),
    db: Session = Depends(get_db),
):
    """
    Fetches document details and contents if authorized.
    Returns 404 / 403 identically to prevent leaking document existence.
    """
    allowed_principals, is_active = get_fresh_document_principals(doc_id, db)
    user_principals = set(identity.principals)

    if not is_active or user_principals.isdisjoint(allowed_principals):
        raise HTTPException(status_code=404, detail="Document not found or access denied")

    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or access denied")

    chunks = db.query(Chunk).filter(Chunk.document_id == doc_id).order_by(Chunk.ordinal).all()

    return {
        "id": doc.id,
        "title": doc.title,
        "url": doc.url,
        "sensitivity": doc.sensitivity,
        "chunks_count": len(chunks),
        "content_preview": chunks[0].text[:300] if chunks else "",
    }


@router.post("/agent/run", response_model=AgentRunResponse)
def run_agent_task(
    req: AgentRunRequest,
    identity: IdentityContext = Depends(get_current_identity),
    db: Session = Depends(get_db),
):
    """
    Runs permission-enforced tool-calling agent (FR-39, FR-40, FR-41, FR-42).
    """
    runner = AgentRunner(db=db)
    result = runner.run(
        instruction=req.instruction,
        identity=identity,
        confirmed_write=req.confirmed_write,
    )
    return AgentRunResponse(**result)


@router.get("/connectors", response_model=List[ConnectorResponse])
def list_connectors(
    identity: IdentityContext = Depends(get_current_identity),
    db: Session = Depends(get_db),
):
    """List registered connectors and sync status."""
    connectors = db.query(Connector).all()
    return [
        ConnectorResponse(
            id=c.id,
            type=c.type,
            name=c.name,
            status=c.status,
            last_sync_at=c.last_sync_at.isoformat() if c.last_sync_at else None,
        )
        for c in connectors
    ]


@router.post("/connectors", response_model=ConnectorResponse)
def register_connector(
    req: ConnectorCreateRequest,
    identity: IdentityContext = Depends(get_current_identity),
    db: Session = Depends(get_db),
):
    """Register a new source connector."""
    if "group:executives" not in identity.principals and identity.persona != "executive":
        raise HTTPException(status_code=403, detail="Administrator permissions required to register connectors")

    existing = db.query(Connector).filter(Connector.id == req.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Connector ID already exists")

    conn = Connector(
        id=req.id,
        type=req.type,
        name=req.name,
        config=req.config,
        status="active",
    )
    db.add(conn)
    db.commit()
    return ConnectorResponse(
        id=conn.id,
        type=conn.type,
        name=conn.name,
        status=conn.status,
        last_sync_at=None,
    )


@router.get("/audit", response_model=List[AuditLogItem])
def view_audit_logs(
    limit: int = 50,
    offset: int = 0,
    user_id: Optional[str] = None,
    identity: IdentityContext = Depends(get_current_identity),
    db: Session = Depends(get_db),
):
    """Admin endpoint to inspect tamper-evident audit logs (FR-44)."""
    logs = get_audit_logs(db=db, limit=limit, offset=offset, user_id=user_id)
    return [
        AuditLogItem(
            id=log.id,
            user_id=log.user_id,
            query=log.query,
            rewritten_query=log.rewritten_query,
            retrieved_ids=log.retrieved_ids or [],
            removed_ids=log.removed_ids or [],
            model=log.model,
            latency_ms=round(log.latency_ms, 2),
            created_at=log.created_at.isoformat(),
        )
        for log in logs
    ]


@router.post("/eval/run")
def trigger_eval_run(
    identity: IdentityContext = Depends(get_current_identity),
    db: Session = Depends(get_db),
):
    """
    Runs the full security red-team harness (S1-S10) and quality benchmark suite.
    """
    report = generate_evaluation_report()
    run_id = f"eval_{uuid.uuid4().hex[:8]}"
    eval_record = EvalRun(
        id=run_id,
        config_json={"harness": "S1-S10 + Quality"},
        finished_at=datetime.utcnow(),
        summary_json=report,
    )
    db.add(eval_record)
    db.commit()
    return {
        "run_id": run_id,
        "security_passed": report["security"]["zero_leakage_guarantee_met"],
        "security_score": f"{report['security']['passed_cases']}/{report['security']['total_cases']}",
        "recall_at_10": report["quality"]["recall_at_10"],
        "faithfulness": report["quality"]["faithfulness"],
        "summary": report,
    }
