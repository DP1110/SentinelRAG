import pytest


def test_healthz_endpoint(client):
    res = client.get("/healthz")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"


def test_personas_endpoint(client):
    res = client.get("/v1/personas")
    assert res.status_code == 200
    personas = res.json()
    assert len(personas) >= 5
    assert any(p["persona"] == "intern" for p in personas)
    assert any(p["persona"] == "engineer" for p in personas)


def test_query_endpoint_as_engineer(client):
    res = client.post(
        "/v1/query",
        headers={"X-Persona": "engineer"},
        json={"question": "What is our paid time off (PTO) policy?"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
    assert len(data["citations"]) > 0
    assert data["meta"]["persona"] == "engineer"


def test_query_endpoint_blocks_intern_leakage(client):
    res = client.post(
        "/v1/query",
        headers={"X-Persona": "intern"},
        json={"question": "What is the CEO salary?"},
    )
    assert res.status_code == 200
    data = res.json()
    # Salary must not be in answer or citations
    assert "$450,000" not in data["answer"]
    for c in data["citations"]:
        assert "hr_sec_001" not in c["chunk_ref"]


def test_document_forbidden_access_returns_404(client):
    # Intern tries to access secret executive memo
    res = client.get("/v1/documents/gdrive_main_exec_001", headers={"X-Persona": "intern"})
    assert res.status_code == 404
    assert "access denied" in res.json()["detail"].lower()


def test_audit_logs_endpoint(client):
    # Make a query first
    client.post(
        "/v1/query",
        headers={"X-Persona": "engineer"},
        json={"question": "What is our company mission?"},
    )
    res = client.get("/v1/audit?limit=10", headers={"X-Persona": "engineer"})
    assert res.status_code == 200
    logs = res.json()
    assert len(logs) > 0
    assert logs[0]["user_id"] == "bob_eng"


def test_unauthenticated_query_returns_401(client):
    res = client.post("/v1/query", json={"question": "What is our company mission?"})
    assert res.status_code == 401
    assert "Authentication required" in res.json()["detail"]
