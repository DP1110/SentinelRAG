# Roadmap: SentinelRAG

## Phase 1: Foundation, Database & Identity (Days 1-3)
- Docker Compose setup (Postgres 16 with pgvector + Redis)
- SQLAlchemy database schema and models
- Identity service, OAuth/OIDC validator, and seeded 5-persona directory

## Phase 2: Ingestion, Connectors & Indexing (Days 4-7)
- Connector framework (Google Drive, GitHub mock & live adapters)
- Multi-format document parsing and structural chunking
- Prompt injection risk scorer
- Dense embeddings + PostgreSQL TSV indexing with `allowed_principals` text array

## Phase 3: Hybrid Retrieval & Cross-Encoder Reranking (Days 8-12)
- Query-time permission-filtered vector search (array overlap)
- Parallel full-text search with identical permission filters
- Reciprocal Rank Fusion (RRF)
- Cross-encoder reranker with graceful fallback

## Phase 4: Answer-Time ACL Check & Grounded Generation (Days 13-16)
- Answer-time ACL verification against short-TTL cache
- Fail-closed candidate pruner and non-existence privacy enforcement
- Delimited prompt synthesis and provider-agnostic LLM adapter
- Post-synthesis citation verifier and reference formatter

## Phase 5: Incremental Sync, Scoped Agent & Audit Logging (Days 17-21)
- Incremental sync worker with ACL update and deactivation
- User-scoped tool-calling agent (`search_knowledge`, `get_document`, `summarize_document`, `create_ticket`)
- Audit logging service with query and latency tracing

## Phase 6: Red-Team Evaluation Harness & Web UI (Days 22-28)
- Synthetic 4-department corpus and gold question sets
- Automated S1-S10 security red-team harness with zero-leakage validation
- Quality benchmarks (Recall@k, Faithfulness, Abstention) and ablation reporter
- Interactive Web UI with persona switcher, citation inspector, and admin panel
