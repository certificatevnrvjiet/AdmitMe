-- Tracking and review records for Gemini document extraction.
create table if not exists public.extraction_runs (
  id uuid primary key default gen_random_uuid(),
  student_id text not null,
  document_id text,
  doc_type text,
  provider text,
  object_key text,
  status text not null default 'queued',
  raw_output jsonb,
  error text,
  batch_job_id text,
  batch_key text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
create index if not exists idx_extraction_runs_student_id on public.extraction_runs(student_id);
create index if not exists idx_extraction_runs_batch_job_id on public.extraction_runs(batch_job_id);
create unique index if not exists uq_extraction_runs_batch_key on public.extraction_runs(batch_key) where batch_key is not null;

create table if not exists public.parsed_extractions (
  id uuid primary key default gen_random_uuid(),
  extraction_run_id text,
  student_id text not null,
  doc_type text,
  parsed_fields jsonb not null default '{}'::jsonb,
  confidence jsonb not null default '{}'::jsonb,
  created_at timestamptz default now()
);
create index if not exists idx_parsed_extractions_student_id on public.parsed_extractions(student_id);

create table if not exists public.comparison_results (
  id uuid primary key default gen_random_uuid(),
  student_id text not null,
  field_name text not null,
  filled_value text,
  extracted_value text,
  match_status text not null,
  severity text not null default 'low',
  source_doc_type text,
  extraction_run_id text,
  reviewer_override boolean default false,
  reviewer_notes text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
create index if not exists idx_comparison_results_student_id on public.comparison_results(student_id);

create table if not exists public.gemini_batch_jobs (
  id text primary key,
  task_id text not null,
  gemini_job_name text not null,
  input_file_name text,
  output_file_name text,
  model text,
  state text not null default 'JOB_STATE_PENDING',
  total_students integer default 0,
  total_documents integer default 0,
  completed_documents integer default 0,
  failed_documents integer default 0,
  submitted_by text,
  error text,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  submitted_at timestamptz,
  completed_at timestamptz
);
create index if not exists idx_gemini_batch_jobs_state on public.gemini_batch_jobs(state);
