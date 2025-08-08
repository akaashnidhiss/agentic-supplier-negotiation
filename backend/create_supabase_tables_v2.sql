-- Sprint 2: Updated Supabase Table Schema

CREATE TABLE IF NOT EXISTS suppliers_table (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    name text NOT NULL,
    contact_email text NOT NULL,
    status text NOT NULL,
    last_contact text,
    evaluation_average float
);

CREATE TABLE IF NOT EXISTS supplier_documents (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    supplier_id uuid REFERENCES suppliers_table(id),
    doc_type text NOT NULL,
    version text NOT NULL,
    date text NOT NULL,
    summary text,
    embedding jsonb,
    file_url text NOT NULL
);

CREATE TABLE IF NOT EXISTS supplier_conversations (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    supplier_id uuid REFERENCES suppliers_table(id),
    state text NOT NULL,
    conversation_turns jsonb NOT NULL,
    last_updated text NOT NULL
);

CREATE TABLE IF NOT EXISTS supplier_evaluations (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    conv_id uuid REFERENCES supplier_conversations(id),
    turn_id text NOT NULL,
    judge_prompt_version text NOT NULL,
    scores_json jsonb NOT NULL,
    comments text,
    created_at text NOT NULL
);

-- Sprint 2 Entities
CREATE TABLE IF NOT EXISTS agent_runs (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    supplier_id uuid REFERENCES suppliers_table(id),
    conv_id uuid REFERENCES supplier_conversations(id),
    dag_node text NOT NULL,
    status text NOT NULL,
    payload_jsonb jsonb NOT NULL,
    created_at text NOT NULL
);

CREATE TABLE IF NOT EXISTS tool_calls (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    run_id uuid REFERENCES agent_runs(id),
    tool_name text NOT NULL,
    input_jsonb jsonb NOT NULL,
    output_jsonb jsonb NOT NULL,
    latency_ms integer
);

CREATE TABLE IF NOT EXISTS conversation_turns (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    conv_id uuid REFERENCES supplier_conversations(id),
    role text NOT NULL, -- enum: AGENT/SUPPLIER/HUMAN_OVERRIDE
    content text NOT NULL,
    sent_at text NOT NULL,
    meta jsonb
);

CREATE TABLE IF NOT EXISTS evaluation_turns (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    turn_id uuid REFERENCES conversation_turns(id),
    judge_version text NOT NULL,
    grounding integer NOT NULL,
    relevance integer NOT NULL,
    tone integer NOT NULL,
    notes text,
    pass boolean NOT NULL
);

CREATE TABLE IF NOT EXISTS conversation_settings (
    conv_id uuid REFERENCES supplier_conversations(id) PRIMARY KEY,
    send_policy text NOT NULL, -- enum: AUTO / WAIT
    auto_threshold integer DEFAULT 24
);
