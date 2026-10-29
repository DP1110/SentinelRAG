from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class QueryOptions(BaseModel):
    rerank: bool = True
    top_k: int = 8
    stream: bool = False


class QueryRequest(BaseModel):
    question: str = Field(..., description="The user question to ask")
    conversation_id: Optional[str] = Field(None, description="Optional conversation session ID")
    options: QueryOptions = Field(default_factory=QueryOptions)


class CitationItem(BaseModel):
    id: int
    title: str
    url: str
    chunk_ref: str
    snippet: str


class QueryMeta(BaseModel):
    latency_ms: float
    chunks_used: int
    filtered_out: int
    persona: str
    model: str
    cached: bool = False


class QueryResponse(BaseModel):
    answer: str
    citations: List[CitationItem]
    meta: QueryMeta


class AgentRunRequest(BaseModel):
    instruction: str
    confirmed_write: bool = False


class AgentRunResponse(BaseModel):
    instruction: str
    steps_count: int
    final_answer: str
    trace: List[Dict[str, Any]]
    identity_used: str


class ConnectorCreateRequest(BaseModel):
    id: str
    type: str  # 'gdrive', 'github'
    name: str
    config: Dict[str, Any] = Field(default_factory=dict)


class ConnectorResponse(BaseModel):
    id: str
    type: str
    name: str
    status: str
    last_sync_at: Optional[str] = None


class AuditLogItem(BaseModel):
    id: int
    user_id: str
    query: str
    rewritten_query: Optional[str]
    retrieved_ids: List[str]
    removed_ids: List[str]
    model: str
    latency_ms: float
    created_at: str


class PersonaInfo(BaseModel):
    persona: str
    user_id: str
    email: str
    display_name: str
    groups: List[str]
