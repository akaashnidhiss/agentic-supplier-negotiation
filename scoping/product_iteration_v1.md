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
