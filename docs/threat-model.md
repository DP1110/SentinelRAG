# SentinelRAG: Threat Model & Security Mitigations

## Threat Matrix

| Threat ID | Threat Vector | Attack Description | Mitigation Mechanism |
|---|---|---|---|
| **T1** | Direct Cross-User Retrieval | Low-privilege user queries confidential documents (e.g. Intern querying Executive salaries) | Layer 1 retrieval-time filter (`allowed_principals && :user_principals`) ensures unauthorized chunks never enter candidate ranking |
| **T2** | Stale Permissions / Permission Drift | User's group membership was revoked after index time | Layer 2 answer-time check verifies against authoritative `document_acl` with 60s TTL cache; purged prior to generation |
| **T3** | Indirect Prompt Injection | Ingested document contains instructions to override system prompt and dump secrets | Delimited `<context_block>` untrusted tags, prompt injection risk scoring, strict system prompt constraints |
| **T4** | Over-privileged Agent Escalation | User asks AI agent tool to fetch or summarize restricted files | Tools execute strictly under requesting user's `IdentityContext`, never elevated service accounts |
| **T5** | Metadata / Snippet Leakage | System reveals titles, paths, or snippets of restricted files in error messages or citations | Error and empty responses are completely identical regardless of document existence; citation verifier strips non-surfaced IDs |
| **T6** | SQL / Filter Injection | User injects `' OR '1'='1` in search query to bypass principal check | Parameterized ORM queries; array overlap operations are strictly typed |
| **T7** | Multi-Turn Context Accumulation | Privileged context persists into non-privileged user chat session | Chat context and caching is keyed by `user_id` and complete `principals` set |
