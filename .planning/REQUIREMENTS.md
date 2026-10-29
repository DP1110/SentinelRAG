# Requirements: SentinelRAG

**Defined:** 29 Oct 2026  
**Core Value:** Zero cross-user data leakage enforced at retrieval time and verified again at answer time, backed by an automated red-team test harness.

## v1 Requirements

### Authentication & Identity
- [ ] **AUTH-01**: System verifies OAuth2 / OIDC tokens and extracts user ID, email, and group memberships.
- [ ] **AUTH-02**: System provides a seeded directory simulating 5 enterprise personas (Intern, Engineer, HR Manager, Finance Analyst, Executive).
- [ ] **AUTH-03**: System computes the user's complete principal set (`user:<id>`, `group:<id>`, `domain:<domain>`, `public`).
- [ ] **AUTH-04**: Anonymous or unauthorized requests are rejected with HTTP 401.

### Ingestion & Connectors
- [ ] **INGEST-01**: Base connector interface handles item listing, content extraction, native ACL retrieval, and change detection.
- [ ] **INGEST-02**: Google Drive connector extracts files, folder inheritance, and permissions.
- [ ] **INGEST-03**: GitHub connector extracts repo contents and team/collaborator access.
- [ ] **INGEST-04**: Structure-aware chunker splits text by headings, paragraphs, and code blocks (default 512 tokens, 64 overlap).
- [ ] **INGEST-05**: Prompt injection risk scorer detects malicious instruction patterns and assigns a risk score.
- [ ] **INGEST-06**: Chunks are stored in Postgres with dense embeddings (384-d), TSV full-text search, and `allowed_principals` text array.

### Search & Retrieval
- [ ] **SEARCH-01**: Vector search filters chunks directly via `allowed_principals && :user_principals` array overlap.
- [ ] **SEARCH-02**: Keyword search filters chunks with identical permission criteria in parallel.
- [ ] **SEARCH-03**: Reciprocal Rank Fusion (RRF) combines vector and keyword results.
- [ ] **SEARCH-04**: Cross-encoder reranks top 50 candidates down to top 8.
- [ ] **SEARCH-05**: Superseded and inactive chunks are strictly excluded.

### Authorization & Generation
- [ ] **AUTHZ-01**: Answer-time permission check re-verifies each candidate against fresh/cached ACL before synthesis.
- [ ] **AUTHZ-02**: Fail-closed: missing or revoked permissions remove candidate; if no candidates remain, system returns generic empty message without leaking document existence.
- [ ] **GEN-01**: Prompt isolates context inside `<context_block id="...">` untrusted tags.
- [ ] **GEN-02**: System prompt instructs model to answer only from context and abstain when context is insufficient.
- [ ] **GEN-03**: Citation verifier validates all `[N]` references against supplied context blocks, removing invalid citations.

### Operations, Agent & Evaluation
- [ ] **SYNC-01**: Sync worker handles document updates, deactivations, and ACL modifications without re-embedding.
- [ ] **AGENT-01**: Tool-calling agent executes tools (`search_knowledge`, `get_document`, `summarize_document`, `create_ticket`) strictly under requesting user's identity.
- [ ] **AUDIT-01**: System records tamper-evident audit logs with query, user ID, retrieved chunk IDs, removed chunk IDs, and latency.
- [ ] **EVAL-01**: Red-team test harness runs 10 attack categories (S1-S10) and asserts 0 cross-user leakage.
- [ ] **EVAL-02**: Quality metrics (Recall@k, Faithfulness, Abstention) and ablation experiments are generated in a report.
- [ ] **UI-01**: Web UI provides persona switcher, grounded chat with citations, admin audit viewer, and red-team runner.

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 to AUTH-04 | Phase 1 | Pending |
| INGEST-01 to INGEST-06 | Phase 2 | Pending |
| SEARCH-01 to SEARCH-05 | Phase 3 | Pending |
| AUTHZ-01 to AUTHZ-02, GEN-01 to GEN-03 | Phase 4 | Pending |
| SYNC-01, AGENT-01, AUDIT-01 | Phase 5 | Pending |
| EVAL-01, EVAL-02, UI-01 | Phase 6 | Pending |
