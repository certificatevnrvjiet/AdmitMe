-- Gemini Batch API tracking for Supabase/PostgreSQL

create table if not exists gemini_batch_jobs (
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

create index if not exists idx_gemini_batch_jobs_task_id on gemini_batch_jobs(task_id);
create index if not exists idx_gemini_batch_jobs_state on gemini_batch_jobs(state);

alter table extraction_runs add column if not exists batch_job_id text;
alter table extraction_runs add column if not exists batch_key text;
alter table students2025 add column if not exists extraction_status text default 'pending';

create index if not exists idx_extraction_runs_batch_job_id on extraction_runs(batch_job_id);
create unique index if not exists uq_extraction_runs_batch_key on extraction_runs(batch_key) where batch_key is not null;
