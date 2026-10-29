# SentinelRAG: Product Requirements Document

**Version:** 1.0  
**Author:** Dipak Mane  
**Date:** 29 Oct 2026  
**Status:** Approved / Ready to build  
**Feature Branch:** `ralph/sentinel-rag`

---

## 1. Introduction & Overview

SentinelRAG is a permission-aware enterprise Retrieval-Augmented Generation (RAG) platform. It ingests content from connected corporate tools (Google Drive, GitHub, and Slack), provides accurate conversational answers with verifiable citations, and strictly guarantees that each user only receives information they are authorized to see.

Traditional RAG systems rank documents purely by semantic relevance, ignoring enterprise authorization boundaries. SentinelRAG solves the "relevance is not authorization" problem by enforcing identity access filters at retrieval time and re-verifying documents at answer time against live/cached Access Control Lists (ACLs). Furthermore, SentinelRAG ships with a built-in automated red-team security harness that tests against cross-user leakage, indirect prompt injection, and stale permission drift on every build.

---

## 2. Goals & Non-Goals

### Goals
- **G1 (Zero Leakage):** 0 cross-user data leakage across the automated security test suite (categories S1–S10).
- **G2 (Dual-Layer Authorization):** Enforce ACL filters at retrieval time and re-verify at answer time before LLM context synthesis.
- **G3 (Hybrid Retrieval + Reranking):** Parallel BM25/FTS keyword search and vector dense retrieval with Reciprocal Rank Fusion (RRF) and cross-encoder reranking.
- **G4 (Audit & Citations):** Every answer cites authoritative chunk IDs; every query logs a complete, tamper-evident audit record.
- **G5 (Pluggable Connectors):** Clean connector abstraction for Google Drive, GitHub, and Slack with incremental sync and ACL capture.
- **G6 (Continuous Red-Team Harness):** Automated red-team test harness producing quality metrics and leakage reports.
- **G7 (Lean & Portable):** Runs completely with Docker Compose on CPU or modest 4GB VRAM GPU.

### Non-Goals (v1)
- Multi-region geo-distributed cluster.
- SAML/SCIM enterprise single sign-on (OAuth 2.0 / OIDC and seeded directory are supported for v1).
- Proprietary LLM fine-tuning.
- Multi-modal image/audio/video retrieval.

---

## 3. User Stories

### US-001: Project Foundation & Database Schema
**Description:** As a platform engineer, I want a containerized PostgreSQL database with pgvector, FTS, and relational schema so that chunks, vectors, ACLs, and audit logs are securely stored in one place.
**Acceptance Criteria:**
- [ ] Docker Compose defines Postgres 16 with `pgvector` extension and Redis.
- [ ] SQLAlchemy / SQL schemas create `users`, `groups`, `group_members`, `connectors`, `documents`, `document_acl`, `chunks`, `audit_log`, and `eval_runs` tables.
- [ ] HNSW index on `chunks.embedding` and GIN indexes on `chunks.tsv` and `chunks.allowed_principals`.
- [ ] Health check endpoint `GET /healthz` returns `{"status": "ok"}`.
- [ ] Unit tests for database connection and schema initialization pass.

### US-002: Identity & Authentication Context
**Description:** As an enterprise user, I want my authenticated identity and group memberships resolved on every query so that the system enforces my exact permissions.
**Acceptance Criteria:**
- [ ] OAuth2 / OIDC token bearer authentication provider implemented.
- [ ] Seeded directory provider allows simulating 5 personas: `intern`, `engineer`, `hr_manager`, `finance_analyst`, and `executive`.
- [ ] Identity resolver builds principal set: `user:<id>`, `group:<id>`, `domain:<domain>`, and `public`.
- [ ] Unauthorized or anonymous requests return HTTP 401.
- [ ] Unit tests for identity resolution and persona switching pass.

### US-003: Connector Framework & Source Connectors
**Description:** As an administrator, I want modular connectors for Google Drive and GitHub so that corporate documents and repositories can be ingested with native ACL metadata.
**Acceptance Criteria:**
- [ ] Base `Connector` interface defined with `list_items()`, `fetch_content()`, `fetch_acl()`, and `detect_changes()`.
- [ ] Google Drive connector extracts files, folder hierarchy, and permissions (user, group, domain, anyone).
- [ ] GitHub connector extracts repositories, markdown/code files, and team/collaborator permissions.
- [ ] Connector secrets are securely loaded from environment variables and never logged.
- [ ] Unit tests for Google Drive and GitHub connector parsers pass.

### US-004: Ingestion Pipeline & Text Processing
**Description:** As a data engineer, I want documents parsed, cleaned, chunked with structural awareness, and scanned for prompt injection so that high-quality, safe chunks enter the index.
**Acceptance Criteria:**
- [ ] Parsers handle Markdown, Text, PDF, DOCX, and Code files.
- [ ] Text cleaner strips zero-width characters, normalizes whitespace, and strips boilerplate.
- [ ] Chunker performs structure-aware splitting (headings, paragraphs, code blocks) targeting 512 tokens with 64 overlap.
- [ ] Chunks retain rich metadata (doc ID, title, URL, author, sensitivity, department).
- [ ] Prompt injection risk scorer flags instruction-like patterns and stores a `risk_score`.
- [ ] Unit tests for chunking, cleaning, and prompt injection detection pass.

### US-005: Embeddings & PGVector Indexing
**Description:** As a search engineer, I want chunks converted to dense vectors and indexed alongside full-text search vectors and allowed principals so that they are ready for hybrid search.
**Acceptance Criteria:**
- [ ] Embedding adapter supports `bge-small-en-v1.5` (or sentence-transformers fallback) with configurable dimensions.
- [ ] Chunks are stored with dense vector, postgres TSV, and `allowed_principals` text array.
- [ ] Superseded chunks are marked `is_active = false`.
- [ ] Deduplication drops identical content hashes.
- [ ] Unit tests for embedding generation and storage pass.

### US-006: Retrieval-Time Permission-Aware Hybrid Search
**Description:** As a user, I want hybrid keyword and semantic search that filters out inaccessible documents at the query level so that unauthorized chunks never enter candidate pools.
**Acceptance Criteria:**
- [ ] Vector search applies `allowed_principals && :user_principals` array overlap directly in the SQL query.
- [ ] Full-text search applies the same `allowed_principals` filter in parallel.
- [ ] Reciprocal Rank Fusion (RRF) merges keyword and vector candidate lists.
- [ ] Inactive and superseded chunks are strictly excluded.
- [ ] Unit tests confirm restricted documents are never returned in candidate rankings.

### US-007: Cross-Encoder Reranking
**Description:** As a search engineer, I want candidates reranked by a cross-encoder model so that answer precision is maximized within the authorized subset.
**Acceptance Criteria:**
- [ ] Cross-encoder reranker scores top candidates (e.g. top 50 to top 8).
- [ ] Reranking gracefully falls back to RRF score if model is not loaded.
- [ ] Reranking toggle (`options.rerank`) is configurable per request.
- [ ] Unit tests verify reranking score ordering and fallback behavior.

### US-008: Answer-Time Permission Verification & Fail-Closed Guard
**Description:** As a security auditor, I want candidates re-verified against live/cached ACLs right before LLM synthesis so that stale permissions never cause data leakage.
**Acceptance Criteria:**
- [ ] Short-TTL ACL cache (60s) validates whether the user still has access to each document ID.
- [ ] Any candidate document failing the re-check is purged from the context.
- [ ] If all candidates are removed, returns a generic "No accessible information found" message without hinting at document existence.
- [ ] Chunks removed by answer-time check are logged in the audit record (`removed_ids`).
- [ ] Unit tests confirm revoked permissions block synthesis even if chunk was in the index.

### US-009: Grounded Generation & Citation Verification
**Description:** As a knowledge worker, I want answers synthesized strictly from authorized chunks with bracketed citations so that I can verify facts and avoid hallucinations.
**Acceptance Criteria:**
- [ ] Prompt template isolates context in delimited untrusted tags (`<context_block id="...">`).
- [ ] System prompt instructs the model to abstain if the context lacks information.
- [ ] Citation verifier parses `[1]`, `[2]` citations and confirms they map to actual chunks in context.
- [ ] Invalid or hallucinated citations are stripped before returning to user.
- [ ] Response includes structured `citations` list with doc title, URL, and chunk ID.
- [ ] Unit tests verify citation validation and abstention behavior.

### US-010: Sync Worker & Freshness Engine
**Description:** As an administrator, I want document edits, deletions, and ACL modifications synced automatically so that search results remain up to date.
**Acceptance Criteria:**
- [ ] Sync worker detects modified documents and updates chunks/embeddings.
- [ ] Deleted or unshared documents are immediately marked `is_active = false`.
- [ ] Permission changes update `document_acl` and chunk `allowed_principals` without re-embedding.
- [ ] Sync event log tracks operations, latency, and errors.
- [ ] Unit tests verify incremental sync, ACL updates, and deactivation.

### US-011: Permission-Enforced Agent & Tool Calling
**Description:** As an employee, I want an AI agent that can search documents, summarize files, and draft tickets while strictly enforcing my permissions on every tool execution.
**Acceptance Criteria:**
- [ ] Agent runner supports tools: `search_knowledge`, `get_document`, `create_ticket`, and `summarize_document`.
- [ ] Every tool receives the requesting user's identity context and fails if unauthorized.
- [ ] Write tools (`create_ticket`) require explicit user confirmation.
- [ ] Agent respects maximum step count (default 5 steps).
- [ ] Unit tests verify tool authorization and step limits.

### US-012: Comprehensive Audit Logging & Metrics
**Description:** As a compliance officer, I want complete audit logs of all queries, user identities, retrieved chunks, and latency metrics so that all enterprise access is traceable.
**Acceptance Criteria:**
- [ ] `audit_log` records: `user_id`, `query`, `retrieved_ids`, `removed_ids`, `model`, `latency_ms`, `tokens`, timestamp.
- [ ] Sensitive content in queries is protected, and PII is not leaked into logs.
- [ ] Admin endpoint `GET /v1/audit` returns paginated audit records.
- [ ] Unit tests verify audit log creation and query filtering.

### US-013: Red-Team Security & Quality Evaluation Harness
**Description:** As a security reviewer, I want an automated test suite evaluating retrieval quality and testing 10 security attack categories (S1-S10) so that zero-leakage compliance is verified.
**Acceptance Criteria:**
- [ ] Synthetic corpus with 4 departments (Engineering, HR, Finance, Executive) and 5 personas.
- [ ] Security test cases covering S1 to S10 (cross-user retrieval, revoked access, indirect prompt injection, tool escalation, etc.).
- [ ] Harness executes test cases and asserts 0 security leakage.
- [ ] Quality evaluation computes Recall@k, Faithfulness, and Abstention accuracy.
- [ ] CLI and API endpoint `POST /v1/eval/run` generates a comprehensive Markdown/JSON report.
- [ ] Unit tests for evaluation harness pass.

### US-014: Interactive Web UI & Live Demo Dashboard
**Description:** As a user and administrator, I want an interactive web UI with a persona switcher, chat interface, citation inspector, and audit/security dashboards.
**Acceptance Criteria:**
- [ ] Clean single-page application served directly by FastAPI.
- [ ] Persona selector allows testing queries as Intern, Engineer, HR Manager, Finance Analyst, or Executive.
- [ ] Chat UI displays streamed or structured answers with interactive citation pills.
- [ ] Admin panel displays connectors, audit logs, and one-click security evaluation runner with visual leakage scorecards.
- [ ] Visual verification of UI routes and components passes.

---

## 4. Functional Requirements Summary

- **FR-1 to FR-3:** Authentication, group syncing, verified identity headers.
- **FR-4 to FR-7:** Connector interface, ACL extraction, credential encryption, fault-tolerant sync.
- **FR-8 to FR-13:** Multi-format ingestion, structure-aware chunking, metadata extraction, prompt injection scoring.
- **FR-14 to FR-16:** Embeddings, pgvector HNSW indexing, full-text search indexing, allowed principals arrays.
- **FR-17 to FR-22:** Query rewriting, parallel keyword + vector search, RRF merge, cross-encoder reranking.
- **FR-23 to FR-27:** Retrieval-time filtering, answer-time ACL re-verification, fail-closed handling, cache isolation.
- **FR-28 to FR-33:** Delimited prompt synthesis, citation verification, provider-agnostic LLM adapter, streaming.
- **FR-34 to FR-38:** Incremental sync worker, deactivation, lightweight ACL update.
- **FR-39 to FR-42:** Permission-scoped agent tool execution, write confirmations, step boundaries.
- **FR-43 to FR-45:** Tamper-evident audit logging and performance metrics.
- **FR-46 to FR-50:** Multi-persona synthetic corpus, S1-S10 security test suite, CI failure gates, markdown reports.

---

## 5. Non-Functional Requirements & Security Guarantees

- **Zero Data Leakage:** 0 forbidden chunks or citations leaked across all S1-S10 tests.
- **Performance:** End-to-end query latency p95 < 6.0s; retrieval latency < 800ms.
- **Reliability:** Fail-closed on any permission resolution error.
- **Portability:** 100% self-contained runnable via `docker-compose up` or local Python virtual environment.
