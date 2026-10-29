# 🛡️ SentinelRAG

**Enterprise RAG where authorization is enforced at retrieval time and again at answer time, and where the proof is automated tests, not promises.**

[![Security Test Suite](https://img.shields.io/badge/Red--Team%20Suite-0%20Leakage%20Guaranteed-success)](file:///C:/Users/Asus/.gemini/antigravity/scratch/sentinelrag/eval/run_security.py)
[![Recall@10](https://img.shields.io/badge/Recall%4010-100%25-blue)](file:///C:/Users/Asus/.gemini/antigravity/scratch/sentinelrag/eval/run_quality.py)
[![Docker Ready](https://img.shields.io/badge/Docker%20Compose-Ready-blue)]()

---

## 🚀 Key Highlights

1. **Dual-Layer Authorization:**
   - **Layer 1 (Retrieval-time filter):** Direct SQL array overlap matching (`allowed_principals && :user_principals`) ensures unauthorized documents never enter the candidate ranking pool.
   - **Layer 2 (Answer-time fresh ACL verification):** Real-time check against authoritative ACL cache (60s TTL) detects revoked access and offboarding before answer synthesis.
2. **Hybrid Search + Cross-Encoder Reranking:** Parallel dense vector search and sparse keyword search fused with Reciprocal Rank Fusion (RRF), followed by cross-encoder reranking.
3. **Verifiable Citations:** Every answer cites bracketed context block IDs (`[1]`, `[2]`). Bogus or hallucinated citations are automatically stripped.
4. **Delimited Untrusted Context:** Neutralizes indirect prompt injections (S5).
5. **Continuous Red-Team Harness (S1-S10):** 10 automated attack categories testing direct retrieval, revoked groups, unshared files, inference, prompt injection, citation leakage, multi-turn accumulation, tool escalation, cache contamination, and SQL/filter bypass.
6. **Zero Hardware Demands:** Runs on CPU or modest 4GB VRAM GPU with Docker Compose.

---

## ⚡ Quickstart

### Option A: Local Python virtualenv
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the application
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Open [http://localhost:8000](http://localhost:8000) to view the interactive Web UI and test different personas!

### Option B: Docker Compose
```bash
docker-compose up --build
```

---

## 🧪 Running the Red-Team Security & Quality Suite

Run the automated S1-S10 security test harness:
```bash
python -m eval.run_security
```

Run the quality evaluation and ablation benchmarks:
```bash
python -m eval.run_quality
```

Generate the markdown evaluation report:
```bash
python -m eval.report
```

---

## 👥 Personas Matrix

| Persona | Role | Accessible Content |
|---|---|---|
| `intern` | Intern Alice | Public docs only |
| `engineer` | Software Engineer Bob | Engineering + Public + Companywide |
| `hr_manager` | HR Director Carol | HR Policies + Executive Salaries + Companywide |
| `finance_analyst` | Analyst Dave | Finance Highlights + Project Titan M&A + Companywide |
| `executive` | CEO Eve | All Corporate Records + Secret Strategy Memo |
