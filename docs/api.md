# SentinelRAG: API Specification (v1)

## Endpoints

### 1. Health Check
`GET /healthz`
- Returns: `{"status": "ok", "app": "SentinelRAG", "version": "1.0.0"}`

### 2. Personas List
`GET /v1/personas`
- Returns array of supported simulated enterprise personas (`intern`, `engineer`, `hr_manager`, `finance_analyst`, `executive`).

### 3. Permission-Aware Query
`POST /v1/query`
- Headers: `X-Persona: <persona>` or `Authorization: Bearer <token>`
- Request Body:
```json
{
  "question": "What is our parental leave policy?",
  "conversation_id": "c1",
  "options": {
    "rerank": true,
    "top_k": 8
  }
}
```
- Response:
```json
{
  "answer": "All parents are eligible for 16 weeks of fully paid parental leave. [1]",
  "citations": [
    {
      "id": 1,
      "title": "Parental Leave and Health Insurance Policies",
      "url": "https://source.local/hr_002",
      "chunk_ref": "gdrive_main_hr_002_c0",
      "snippet": "All parents (birthing and non-birthing) are eligible..."
    }
  ],
  "meta": {
    "latency_ms": 142.5,
    "chunks_used": 1,
    "filtered_out": 0,
    "persona": "engineer",
    "model": "mock"
  }
}
```

### 4. Agent Execution
`POST /v1/agent/run`
- Request:
```json
{
  "instruction": "Fetch document doc_exec_001",
  "confirmed_write": false
}
```

### 5. Audit Log Explorer
`GET /v1/audit?limit=50&offset=0`

### 6. Security Evaluation Runner
`POST /v1/eval/run`
- Runs all 10 security attack categories (S1-S10) and quality metrics.
