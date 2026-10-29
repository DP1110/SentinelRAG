# SentinelRAG

## What This Is

SentinelRAG is a permission-aware enterprise RAG platform. It ingests documents and code from connected corporate sources (Google Drive, GitHub, and Slack), answers questions with verifiable source citations, and strictly guarantees that each user only receives information they are authorized to see.

## Core Value

Zero cross-user data leakage enforced at retrieval time and verified again at answer time, backed by an automated red-team test harness.

## Requirements

### Validated

(None yet — initial build)

### Active

- [ ] Dual-layer authorization: retrieval query filter + answer-time fresh ACL verification
- [ ] Connectors for Google Drive and GitHub with native ACL extraction
- [ ] Structure-aware chunking and prompt injection risk scoring
- [ ] Hybrid search (pgvector dense search + PostgreSQL full-text search) with Reciprocal Rank Fusion (RRF)
- [ ] Cross-encoder reranking
- [ ] Grounded response synthesis with bracketed citations and post-processing verification
- [ ] Incremental sync worker with soft-deletion and ACL update without re-embedding
- [ ] Permission-enforced tool-calling agent
- [ ] Comprehensive audit logging
- [ ] Red-team security evaluation harness with 10 attack categories (S1-S10) and 0-leakage assertion
- [ ] Interactive Web UI with persona switcher (Intern, Engineer, HR Manager, Finance Analyst, Executive)

### Out of Scope

- Multi-region or high-availability clustering (v1 scope is single-instance Docker Compose)
- Full enterprise SAML/SCIM SSO (OAuth 2.0 / OIDC and seeded directory are used)
- Multi-modal image/video retrieval (text, pdf, docx, code only)

## Context

Most RAG systems fail in enterprise deployments because semantic relevance ranks above access permissions, and indexing snapshots cause permission drift. SentinelRAG solves this by denormalizing allowed principals onto chunks for direct query filtering, maintaining an ACL cache for answer-time verification, and providing a continuous security test harness.

## Constraints

- **Language**: Python 3.11+
- **Database**: PostgreSQL 16 with pgvector extension and Redis
- **Models**: Small, CPU/4GB VRAM friendly (e.g. bge-small-en-v1.5 and cross-encoder / lightweight fallback)
- **Deployment**: Docker Compose
- **Zero Leakage**: 100% pass rate across S1-S10 security test suite

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| PostgreSQL + pgvector | Single database for vectors, full-text search, relational data, and ACLs | ✓ Good |
| Denormalized `allowed_principals` on chunks | Enables fast SQL-level array overlap filtering (`allowed_principals && :user_principals`) | ✓ Good |
| Dual-layer authorization | Retrieval filter eliminates unauthorized chunks; answer-time check catches stale permissions | ✓ Good |
| Delimited untrusted context | Neutralizes indirect prompt injection in retrieved chunks | ✓ Good |
| Built-in Red-Team Harness | Quantifiable proof of security and retrieval quality | ✓ Good |

---
*Last updated: 29 Oct 2026 after project initialization*
