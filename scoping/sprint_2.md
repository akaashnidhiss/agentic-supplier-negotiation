We have now completed the v1 of the product - built out the basic backend scaffolding and frontend setup.

this is the v1 iteration setup:

────────────────────────
PRODUCT ITERATION V1 – ARCHITECTURE OVERVIEW
────────────────────────

0.  Guiding Principles  
    • Memory-first: All events (messages, files, tasks, evaluations) are stored and indexed in Supabase immediately.
    • Evaluation-first: Agent outputs are auto-scored by an LLM judge before finalization.
    • Modular: Components are designed for easy replacement and improvement.

────────────────────────
1. MODULE MAP (CURRENT IMPLEMENTATION)
────────────────────────
1.  Ingestion / Indexing
2.  Memory & Retrieval
3.  Agent Orchestrator
4.  Evaluation / Guardrail
5.  Trigger & Scheduler
6.  Frontend Dashboard

────────────────────────
2. MODULE DETAILS
────────────────────────
2.1  Ingestion / Indexing  
     • PDF uploads via dashboard (manual upload).
     • Summarization and embedding planned (OpenAI, vector store integration).
     • Metadata enrichment: supplier_id, doc_type, version, date.
     • Data stored in Supabase `supplier_documents` table.

2.2  Memory & Retrieval  
     • Long-term memory: Supabase vector store (planned), keyed by supplier_id or "internal".
     • Episodic memory: Conversation objects stored in `supplier_conversations` (jsonb messages).
     • Retrieval API: To be implemented (LangChain, mem0).

2.3  Agent Orchestrator  
     • FastAPI backend with endpoints for suppliers, documents, conversations, evaluations.
     • Conversation state tracked (OPEN, WAITING_FOR_SUPPLIER, CLOSED).
     • Planning and skill layer (LangChain, mem0) to be integrated.

2.4  Evaluation / Guardrail  
     • Evaluation table (`supplier_evaluations`) for LLM judge scores and comments.
     • Evaluation logic: Drafts scored on accuracy, relevance, tone; threshold-based auto-send/flag.
     • Manual override via dashboard for failed evaluations.

2.5  Trigger & Scheduler  
     • Manual triggers: New conversation button on dashboard.
     • Automated triggers (planned): Inbound webhook, cron job for nudges.

2.6  Frontend Dashboard  
     • Next.js dashboard with Supabase auth.
     • Supplier list view: status, last contact, evaluation average.
     • Conversation thread view: messages, citations, evaluation scores.
     • Document tab: upload, search, preview (per supplier and internal docs).
     • Admin panel (planned): thresholds, auto-send toggle.

────────────────────────
3. SUPABASE SCHEMA (CURRENT)
────────────────────────
• suppliers_table(id, name, contact_email, status, last_contact, evaluation_average)
• supplier_documents(id, supplier_id, doc_type, version, date, summary, embedding, file_url)
• supplier_conversations(id, supplier_id, state, messages, last_updated)
• supplier_evaluations(id, conv_id, turn_id, judge_prompt_version, scores_json, comments, created_at)

────────────────────────
4. END-TO-END FLOW (CURRENT)
────────────────────────
1) Supplier uploads or sends document → dashboard/manual trigger.
2) Conversation Manager loads memory; agent (planned) will search docs and compose response.
3) Draft sent to Evaluation module; scored and logged.
4) Message auto-sent or flagged for manual review.
5) All artefacts stored; dashboard updates in real time.

────────────────────────
5. MINIMAL POC CHECKLIST (PROGRESS)
────────────────────────
[x] Supabase schema (tables created via SQL script)
[x] FastAPI backend with CRUD endpoints
[x] Next.js dashboard with forms/tables
[ ] PDF ingestion Lambda/Edge function (planned)
[ ] LangChain agent + mem0 memory (planned)
[ ] Evaluation call + threshold logic (partial)
[ ] File upload and preview (partial)

────────────────────────
6. FUTURE IMPROVEMENTS
────────────────────────
• Automated PDF ingestion and summarization
• Advanced retrieval and planning (LangChain, mem0)
• Multi-agent role separation
• RLHF and active learning on evaluation scores
• Supplier portal for two-way file upload

────────────────────────
This document summarizes the current architecture and implementation status of the AI-driven supplier communication & document exchange PoC as of Iteration V1.
"""


Now let's make the sprint_2 documentation that continues on from this architecture to meet the final deliverable of the MVP. I want to start building out the agentic logic starting first with the logic. We will think about what the agent logic will be using an initial DAG of the logical flow, then plan out the profiling of this part in detail. If the agents require additional backend development it should be clearly explained for our engineers to implement. Write a profile for each agent which will inform the prompt for the agent (system + user), how mem0 will be plugged in and how LLM as a judges will be created to evaluate the important sections specifically of the conversation traces - such as tool usage, grounding against the retrieved data from documents, multiple turn evaluation section that auto appends evals at each conversation step per supplier so that the evaluator can keep track of the trajectory of the agent's discussion. Let's also put up a parameter that directs the agent to either wait for evaluator to say "yes" before sending out agent response, or send out agent response regardless of evaluator judgement.


This is just profiling so no code needs to be implemented now.


──────────────────────────────────────────────
SPRINT 2 – “INTELLIGENT CORE” SPECIFICATION
──────────────────────────────────────────────
Goal: Ship the first end-to-end agentic loop (retrieve → reason → draft → judge → deliver) so that a real supplier conversation can be completed with 
• automatic grounding in uploaded PDFs,  
• continuous long-term memory (mem0 + Supabase), and  
• per-turn LLM evaluation stored in our DB.  

No production code is in this document—only the design/profiling that will guide engineering tickets.

────────────────────────
1. HIGH-LEVEL DAG
────────────────────────
(Text description – engineers can render in Mermaid)

TRIGGER  
└─► Load Context  
  (a) Long-term memory pull (mem0 / vector store)  
  (b) Episodic memory pull (conversation history)  
  (c) Input event (human question, webhook, cron nudge)  

└─► Planner Agent  
  • Decides next action(s) + tool list (retrieve, ask_clarifying, draft_reply, etc.)  

└─► Tool Executor  
  • Runs LangChain tools selected by planner  
  • Writes tool results back to mem0 short-term store  

└─► Drafting Agent  
  • Consumes planner rationale + tool outputs → crafts supplier message draft  

└─► LLM Judge  
  • Scores draft on Grounding, Relevance, Tone, Completeness  

└─► Delivery Gate  
  • If conversation_settings.send_policy = “WAIT”, pause & surface in dashboard  
  • If “AUTO” and score ≥ threshold, send via email/API & mark turn as SENT  
  • Else flag for human  

└─► Persist All Artifacts  
  (events, tool logs, evals) to Supabase  

└─► Schedule Next Step (if any) or END

────────────────────────
2. NEW / CHANGED BACKEND ENTITIES
────────────────────────
1. agent_runs  
   id, supplier_id, conv_id, dag_node, status, payload_jsonb, created_at  
2. tool_calls  
   id, run_id, tool_name, input_jsonb, output_jsonb, latency_ms  
3. conversation_turns  (rename from messages for clarity)  
   id, conv_id, role(enum: AGENT/SUPPLIER/HUMAN_OVERRIDE), content, sent_at  
4. evaluation_turns  
   id, turn_id, judge_version, grounding(0-10), relevance(0-10), tone(0-10), notes, pass(bool)  
5. conversation_settings  
   conv_id, send_policy(enum: AUTO / WAIT), auto_threshold numeric default 24  (sum of 3 subscores)

Existing tables remain; migrations will add FKs.

────────────────────────
3. MEMORY STRATEGY (mem0)
────────────────────────
mem0 will orchestrate multi-tier memory access inside each agent:
• Short-term scratchpad: tool outputs, planner notes (TTL = 1 run)  
• Episodic (conversation_turns) ← read/write every turn  
• Semantic store (vector) ← only read; write new embeddings when new docs ingested  
Bindings: mem0-supabase adapter (already OSS) with namespaces:  
   “conv:{conv_id}”, “supplier:{supplier_id}:docs”, “internal_docs”

────────────────────────
4. AGENT PROFILES & PROMPT SKELETONS
────────────────────────

4.1 Planner Agent
Purpose: Decide what the agent should do next, given conversation context & memories.

System prompt (abridged):
“You are Planner-Bot. Output a JSON plan with keys: thoughts, selected_tools[], arg_per_tool{}.
Use supplier documents and internal docs citations when necessary.”

User prompt assembly:
• Last 10 conversation turns (supplier + agent)  
• Any mem0 retrievals (top-k summaries)  
• Open tasks (if any)  

Output schema example:
{
  "thoughts": "Need to clarify delivery timeline; check latest contract.",
  "selected_tools": ["DocSearch", "DraftReply"],
  "arg_per_tool": {
      "DocSearch": {"query": "delivery terms", "scope": "supplier_docs"},
      "DraftReply": {"temperature": 0.2}
  }
}

mem0 usage:
read: conv namespace, supplier docs  
write: plan stored to mem0 scratch “run:{run_id}:plan”

4.2 Tool Executor (managed code, not LLM)  
Supabase function iterates selected_tools; posts results back to mem0.

4.3 Drafting Agent  
System prompt:
“You are Supplier-Comms-Writer. Draft a clear, professional message to the supplier. Incorporate factual grounding only from the ‘CONTEXT’ section. Cite like [doc#3]. Output only the message text.”

User prompt parts:
• Planner thoughts  
• Tool outputs (DocSearch passages, etc.)  
• Any constraints (tone guidelines, SLAs)  

mem0:
read: scratch plan + tool outputs  
write: draft message to mem0 scratch

4.4 LLM Judge (Evaluation Agent)  
System prompt:
“You are QA-Judge. Score the AGENT_DRAFT on:  
1. Grounding (0-10): Is every claim supported by CONTEXT?  
2. Relevance (0-10)  
3. Tone (0-10): Professional, courteous.  
Return JSON {grounding, relevance, tone, notes, pass} where pass = true if sum ≥ AUTO_THRESHOLD.”

User prompt:
• AGENT_DRAFT  
• CONTEXT (tool citations expanded)  

Writes directly to evaluation_turns.

────────────────────────
5. EVALUATION CONFIGURATION
────────────────────────
Parameter: conversation_settings.send_policy  
• AUTO  → if pass = true, back-end immediately sends email (existing SendGrid microservice)  
• WAIT  → system publishes “needs_human” state; dashboard shows Approve / Reject buttons  

Threshold logic: auto_threshold = numeric; default 24/30.  
Realtime websocket updates so frontend can display judge feedback instantly.

────────────────────────
6. TRIGGERS (RECAP)
────────────────────────
1. Manual: “New Message” button  
2. Inbound Email / Webhook: supplier replies → creates TURN role=SUPPLIER → DAG fires  
3. Cron Nudge: daily job checks OPEN conversations idle > N days → creates synthetic “REMINDER” event → DAG fires

Each trigger posts a message to queue “agent.run” with conv_id, event_payload.

────────────────────────
7. PROFILING & PERFORMANCE NOTES
────────────────────────
• latency budget per run: <12 s (Planner 3 s, Tools 4 s, Draft 3 s, Judge 2 s).  
• store token counts per turn in conversation_turns.meta for monitoring.  
• vector search top-k = 8, embedding dim 1536 (~24 kB/row).  
• Expected Supabase RPS increase ≈ +40% → add read replica.

────────────────────────
8. OPEN ENGINEERING TASKS FROM SPRINT 2
────────────────────────
A. DB migration files (new tables, enums)  
B. Queue consumer (agent.run → DAG executor)  
C. mem0 adapter wiring & caching layer  
D. Implement Planner & Drafting prompts in LangChain LLMChain  
E. Judge evaluator service with retry/back-off  
F. Dashboard updates: show judge scores, approve/deny, send-policy toggle  
G. Unit tests: prompt regression, evaluator pass/fail edge cases  
H. Load test with 1 000 synthetic docs / 50 suppliers

────────────────────────
9. DEFINITION OF DONE (MVP)
────────────────────────
• A supplier question + PDF set → agent answers, is auto-judged, either sent or waits for approval, all artifacts visible in UI.  
• 90% of judged turns pass on first try in internal test set.  
• Mean grounding score ≥ 8 on test harness of 20 queries.

────────────────────────
END OF SPRINT 2 SPECIFICATION
────────────────────────