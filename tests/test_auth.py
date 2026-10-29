import pytest
from app.api.auth import SEEDED_PERSONAS, get_current_identity, IdentityContext


def test_seeded_personas_exist():
    assert "intern" in SEEDED_PERSONAS
    assert "engineer" in SEEDED_PERSONAS
    assert "hr_manager" in SEEDED_PERSONAS
    assert "finance_analyst" in SEEDED_PERSONAS
    assert "executive" in SEEDED_PERSONAS


def test_intern_principals_scoping():
    intern = SEEDED_PERSONAS["intern"]
    principals = intern["principals"]
    assert "public" in principals
    assert "group:interns" in principals
    assert "group:executives" not in principals
    assert "group:engineering" not in principals
    assert "group:finance" not in principals


def test_executive_principals_scoping():
    exec_p = SEEDED_PERSONAS["executive"]
    principals = exec_p["principals"]
    assert "public" in principals
    assert "group:executives" in principals
    assert "group:engineering" in principals
    assert "group:hr" in principals
    assert "group:finance" in principals


def test_identity_context_resolution(db_session):
    identity = get_current_identity(x_persona="intern", authorization=None, db=db_session)
    assert identity.persona == "intern"
    assert identity.user_id == "intern_alice"
    assert "public" in identity.principals
