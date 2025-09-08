-- sql/create_supabase_tables.sql
create table if not exists suppliers (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  category text not null,
  email text not null
);

create table if not exists sessions (
  id uuid primary key default gen_random_uuid(),
  created_at timestamp with time zone default now(),
  mode text default 'demo'
);

create table if not exists bids (
  id uuid primary key default gen_random_uuid(),
  session_id uuid references sessions(id),
  supplier_id uuid references suppliers(id),
  sku_id text not null,
  raw_reply text,
  normalized_json jsonb
);
