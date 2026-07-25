-- Apply in Supabase SQL Editor before enabling /api/v1/research-runs.
create table if not exists public.research_workflows (
    id uuid primary key,
    topic text not null,
    lifecycle text not null,
    state jsonb not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.research_workflow_events (
    id bigint generated always as identity primary key,
    research_workflow_id uuid not null references public.research_workflows(id) on delete cascade,
    event jsonb not null,
    created_at timestamptz not null default now()
);

create index if not exists research_workflows_lifecycle_idx on public.research_workflows(lifecycle);
create index if not exists research_workflow_events_run_idx on public.research_workflow_events(research_workflow_id);

alter table public.research_workflows enable row level security;
alter table public.research_workflow_events enable row level security;

-- The backend uses the service-role key; add authenticated-user policies when auth is introduced.
