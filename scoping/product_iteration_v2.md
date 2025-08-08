────────────────────────
PRODUCT ITERATION V2 – FUNCTIONALITY OVERVIEW
────────────────────────

0.  Guiding Principles
    • Modular, agentic architecture: Each step is isolated and replaceable.
    • Supabase as the single source of truth for all events and artifacts.
    • Stepwise agentic loop: Plan → Tool → Draft → Judge → Persist.

────────────────────────
1. TABLE SCHEMAS IN USE
────────────────────────

• suppliers_table(id, name, contact_email, status, last_contact, evaluation_average)
• supplier_documents(id, supplier_id, doc_type, version, date, summary, embedding, file_url)
• supplier_conversations(id, supplier_id, state, conversation_turns, last_updated)
• conversation_turns(id, conv_id, role, content, sent_at, meta)
• supplier_evaluations(id, conv_id, turn_id, judge_prompt_version, scores_json, comments, created_at)

────────────────────────
2. END-TO-END TURN-BY-TURN FLOW
────────────────────────

1. Dashboard displays all suppliers from `suppliers_table`.
2. User clicks 'Open Conversation' for a supplier, navigates to the conversation simulator page.
3. Supplier (user) types a message and submits a reply.
4. The reply is saved as a new turn in `conversation_turns` (role=SUPPLIER).
5. The agentic loop (`agentic_dag_run`) is triggered:
    a. Planner Agent: Plans next actions based on context.
    b. Tool Executor: Executes selected tools (simulated for now).
    c. Drafting Agent: Crafts agent's response using planner thoughts and tool outputs.
    d. LLM Judge: Evaluates the agent's draft for grounding, relevance, tone.
    e. Delivery Gate: If evaluation passes, marks as SENT; else, flags for review.
    f. Persist Artifacts: Agent's response and evaluation are saved as a new turn in `conversation_turns` (role=AGENT).
6. All conversation turns are displayed in order, showing both supplier and agent messages.

────────────────────────
3. CURRENT FUNCTIONALITY
────────────────────────

- Dashboard and supplier selection are fully implemented.
- Conversation simulator allows turn-by-turn interaction between supplier and agent.
- Agentic DAG runs end-to-end: plan, tool execution, draft, judge, persist.
- All events and artifacts are written to Supabase tables.
- Foreign key constraints are enforced: every turn is linked to a valid conversation.

────────────────────────
4. WHAT'S LEFT TO IMPLEMENT
────────────────────────

- True agentic E2E working: Replace simulated planner/tool/draft/judge logic with real agentic reasoning and LLM calls.
- mem0-based memory: Integrate mem0 for short-term, episodic, and semantic memory, following mem0 documentation.
- Advanced tool execution and retrieval.
- UI polish and real-time updates.

────────────────────────
5. NEXT STEPS
────────────────────────

Step 1: Finalize agentic_dag_run for true E2E agentic operation (without memory).

Agent will talk to suppliers on behalf of the clients. The client requirements will be put into their internal file storage DB (4o mini based caching will take place on this)
The agent will let the supplier upload their files (such as quotes and product specifications) and it will read both the client requirements & the user uploaded files and conversations to negotiate with the supplier, and provide updates to the client on the supplier's quotes details and let them know if it works for them or not.

First step will just be to do tool use. Implement it properly. It will just use the _read_available_file_descriptions() -> Dict, _retrieve_relevant_chunks(query: str) -> List.

Step 2: Integrate mem0 for memory-first agentic loop.
Step 3: Expand toolset, evaluation, and dashboard features as needed.

────────────────────────
This document summarizes the current architecture, table schemas, and end-to-end flow for Product Iteration V2. The next milestone is a fully working agentic loop, followed by memory integration.
