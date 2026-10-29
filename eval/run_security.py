import time
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, init_db
from app.db.models import Document
from app.connectors.gdrive import GoogleDriveConnector
from app.sync.worker import sync_connector_items
from eval.datasets.synthetic_corpus import get_synthetic_corpus
from eval.datasets.security_cases import SECURITY_TEST_CASES, SecurityTestCase
from app.core.identity import SEEDED_PERSONAS, IdentityContext
from app.retrieval.hybrid import search_hybrid
from app.retrieval.rerank import rerank_candidates
from app.retrieval.permissions import verify_answer_time_permissions
from app.generation.prompts import build_generation_prompt, SYSTEM_PROMPT
from app.generation.citations import verify_and_extract_citations
from app.generation.llm_adapters.mock import MockLLMAdapter


def seed_corpus_if_empty(db: Session):
    doc_count = db.query(Document).count()
    if doc_count > 0:
        return
    connector = GoogleDriveConnector("gdrive_main", "Corporate Google Drive", {})
    items = get_synthetic_corpus()
    for it in items:
        connector.seed_item(it)
    sync_connector_items(connector, db)


def run_security_suite(db: Session = None) -> Dict[str, Any]:
    """
    Executes the automated S1-S10 red-team security harness.
    Evaluates cross-user leakage, revoked permissions, prompt injection, and tool escalation.
    """
    should_close = False
    if db is None:
        init_db()
        db = SessionLocal()
        should_close = True

    seed_corpus_if_empty(db)
    llm = MockLLMAdapter()

    results: List[Dict[str, Any]] = []
    total_cases = len(SECURITY_TEST_CASES)
    passed_cases = 0
    leaked_cases = 0

    start_time = time.time()

    for tc in SECURITY_TEST_CASES:
        p_info = SEEDED_PERSONAS.get(tc.persona, SEEDED_PERSONAS["intern"])
        identity = IdentityContext(
            user_id=p_info["user_id"],
            email=p_info["email"],
            display_name=p_info["display_name"],
            persona=tc.persona,
            principals=p_info["principals"],
        )

        # 1. Retrieval
        candidates = search_hybrid(tc.question, identity, db, top_k=8)

        # 2. Rerank
        reranked = rerank_candidates(tc.question, candidates, top_k=5)

        # 3. Answer-time check
        verified, removed_ids = verify_answer_time_permissions(reranked, identity, db)

        # 4. Prompt & generation
        prompt = build_generation_prompt(tc.question, verified)
        raw_answer = llm.generate(prompt, SYSTEM_PROMPT)
        clean_answer, citations = verify_and_extract_citations(raw_answer, verified)

        # 5. Leakage check
        has_leakage = False
        leak_reasons = []

        # Check forbidden sources in citations
        for c in citations:
            for fs in tc.forbidden_sources:
                if fs in c.get("chunk_ref", "") or fs in c.get("title", ""):
                    has_leakage = True
                    leak_reasons.append(f"Forbidden source '{fs}' appeared in citation.")

        # Check forbidden terms in answer
        for ft in tc.forbidden_terms:
            if ft.lower() in clean_answer.lower():
                has_leakage = True
                leak_reasons.append(f"Forbidden term '{ft}' appeared in generated response.")

        # Check forbidden terms in retrieved context
        for v in verified:
            for ft in tc.forbidden_terms:
                if ft.lower() in v.text.lower():
                    has_leakage = True
                    leak_reasons.append(f"Forbidden term '{ft}' reached verified context block.")

        passed = not has_leakage
        if passed:
            passed_cases += 1
        else:
            leaked_cases += 1

        results.append({
            "id": tc.id,
            "category": tc.category,
            "persona": tc.persona,
            "question": tc.question,
            "passed": passed,
            "leak_reasons": leak_reasons,
            "answer_preview": clean_answer[:120],
            "citations_count": len(citations),
            "removed_ids_count": len(removed_ids),
        })

    duration_ms = (time.time() - start_time) * 1000

    summary = {
        "suite": "S1-S10 Red-Team Security Suite",
        "total_cases": total_cases,
        "passed_cases": passed_cases,
        "leaked_cases": leaked_cases,
        "pass_rate_pct": (passed_cases / total_cases) * 100.0 if total_cases > 0 else 0.0,
        "zero_leakage_guarantee_met": (leaked_cases == 0),
        "duration_ms": duration_ms,
        "cases": results,
    }

    if should_close:
        db.close()

    return summary


if __name__ == "__main__":
    summary = run_security_suite()
    print("========================================")
    print(f"SentinelRAG Red-Team Security Suite: {summary['passed_cases']}/{summary['total_cases']} PASSED")
    print(f"Zero Leakage Guarantee Met: {summary['zero_leakage_guarantee_met']}")
    print("========================================")
