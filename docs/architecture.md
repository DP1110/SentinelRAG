# SentinelRAG: Architecture & Technical Design

## 1. High-Level Architecture Overview

```
Enterprise Apps (Google Drive, GitHub, Slack)
   │
   ▼
Connectors (BaseConnector, GDrive, GitHub)
   │ (extract content, folder hierarchy, native ACLs)
   ▼
Ingestion Pipeline
   ├── Cleaner (Unicode normalizer, zero-width char stripper)
   ├── Structure-Aware Chunker (Headings, code blocks, paragraphs)
   ├── Risk Scorer (Indirect prompt injection pattern detection)
   └── Embeddings Generator (bge-small-en-v1.5 / 384-d normalized vectors)
   │
   ▼
PostgreSQL 16 + pgvector
   ├── chunks (embedding vector, TSV full-text search, allowed_principals array)
   ├── documents & document_acl (source-of-truth ACLs)
   └── audit_log (tamper-evident query tracking)

User Query -> FastAPI -> Identity Context Resolver (OAuth / OIDC / Persona)
   │
   ▼
Dual-Layer Authorization Retrieval
   ├── Layer 1: Query-Time Filter (Vector + FTS filtered by allowed_principals)
   ├── Reciprocal Rank Fusion (RRF) -> Candidate Pool
   ├── Cross-Encoder Reranker -> Top Candidates
   └── Layer 2: Answer-Time Fresh ACL Re-Verification (Short-TTL cache)
         └── Fail-Closed Guard (If revoked, candidate is purged immediately)
   │
   ▼
Grounded Generation
   ├── Delimited Untrusted Context (<context_block>)
   ├── Prompt Injection Shielding & Abstention Rules
   ├── LLM Adapter (Gemini / Mock / Local)
   └── Citation Verifier (Bracketed citation check & URL mapping)
   │
   ▼
Response & Audit Log Record
```

## 2. Core Security Invariants

1. **Relevance is NOT Authorization:** Chunks are never ranked or surfaced if the user is not in the chunk's `allowed_principals`.
2. **Freshness Invariant:** Permissions revoked after indexing are blocked in real-time by the answer-time check (Layer 2).
3. **Fail-Closed Principle:** Any error or ambiguity in permission resolution results in document exclusion.
4. **No Existence Leaks:** Unauthorized documents return identical messages to nonexistent documents.
