from pydantic import BaseModel
from typing import List, Optional

class Supplier(BaseModel):
    id: Optional[str] = None
    name: str
    contact_email: str
    status: str
    last_contact: Optional[str] = None
    evaluation_average: Optional[float] = None

class Document(BaseModel):
    id: str
    supplier_id: Optional[str]
    doc_type: str
    version: str
    date: str
    summary: str
    embedding: Optional[List[float]]
    file_url: str

class Conversation(BaseModel):
    id: str
    supplier_id: str
    state: str
    conversation_turns: List[dict]
    last_updated: str

class Evaluation(BaseModel):
    id: str
    conv_id: str
    turn_id: str
    judge_prompt_version: str
    scores_json: dict
    comments: Optional[str]
    created_at: str

# Sprint 2 Entities
class AgentRun(BaseModel):
    id: str
    supplier_id: str
    conv_id: str
    dag_node: str
    status: str
    payload_jsonb: dict
    created_at: str

class ToolCall(BaseModel):
    id: str
    run_id: str
    tool_name: str
    input_jsonb: dict
    output_jsonb: dict
    latency_ms: Optional[int]

class ConversationTurn(BaseModel):
    id: str
    conv_id: str
    role: str  # enum: AGENT/SUPPLIER/HUMAN_OVERRIDE
    content: str
    sent_at: str
    meta: Optional[dict] = None

class EvaluationTurn(BaseModel):
    id: str
    turn_id: str
    judge_version: str
    grounding: int
    relevance: int
    tone: int
    notes: Optional[str]
    pass_: bool

class ConversationSettings(BaseModel):
    conv_id: str
    send_policy: str  # enum: AUTO / WAIT
    auto_threshold: int = 24
