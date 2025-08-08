-- Run this SQL script in your Supabase SQL editor to create all required tables and columns

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
    messages jsonb NOT NULL,
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
