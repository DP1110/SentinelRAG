import pytest
from app.api.auth import SEEDED_PERSONAS, IdentityContext
from app.retrieval.hybrid import search_hybrid
from app.retrieval.permissions import verify_answer_time_permissions, get_fresh_document_principals
from app.sync.acl_sync import deactivate_document, update_document_acls


def test_retrieval_time_filter_blocks_restricted_chunks(db_session):
    intern_info = SEEDED_PERSONAS["intern"]
    intern_id = IdentityContext(
        user_id=intern_info["user_id"],
        email=intern_info["email"],
        display_name=intern_info["display_name"],
        persona="intern",
        principals=intern_info["principals"],
    )

    # Intern asks for executive salaries
    candidates = search_hybrid("CEO base salary and executive compensation", intern_id, db_session)
    # The confidential salary doc (doc_hr_sec_001) MUST NOT be in candidates
    for c in candidates:
        assert "hr_sec_001" not in c.document_id
        assert "$450,000" not in c.text


def test_answer_time_check_purges_revoked_permissions(db_session):
    eng_info = SEEDED_PERSONAS["engineer"]
    eng_id = IdentityContext(
        user_id=eng_info["user_id"],
        email=eng_info["email"],
        display_name=eng_info["display_name"],
        persona="engineer",
        principals=eng_info["principals"],
    )

    # First verify engineer can see engineering backend architecture
    candidates = search_hybrid("Backend architecture and microservices", eng_id, db_session)
    verified, removed = verify_answer_time_permissions(candidates, eng_id, db_session)
    assert len(verified) > 0

    # Now simulate unsharing or deactivating the document
    deactivate_document("gdrive_main_eng_001", db_session)

    # Re-running answer-time check MUST remove the candidate
    verified_after, removed_after = verify_answer_time_permissions(candidates, eng_id, db_session)
    for c in verified_after:
        assert c.document_id != "gdrive_main_eng_001"
    assert any("eng_001" in r_id for r_id in removed_after)

    # Restore active status so other tests have clean state
    from app.db.models import Document, Chunk
    from app.retrieval.permissions import invalidate_acl_cache
    doc = db_session.query(Document).filter(Document.id == "gdrive_main_eng_001").first()
    if doc:
        doc.is_active = True
        for ch in db_session.query(Chunk).filter(Chunk.document_id == "gdrive_main_eng_001").all():
            ch.is_active = True
        db_session.commit()
        invalidate_acl_cache()
