-- Engines and admin-created admission forms for Supabase/PostgreSQL

create table if not exists extraction_runs (
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

create index if not exists idx_extraction_runs_student_id on extraction_runs(student_id);
create index if not exists idx_extraction_runs_doc_type on extraction_runs(doc_type);
create index if not exists idx_extraction_runs_batch_job_id on extraction_runs(batch_job_id);
create unique index if not exists uq_extraction_runs_batch_key on extraction_runs(batch_key) where batch_key is not null;

create table if not exists parsed_extractions (
  id uuid primary key default gen_random_uuid(),
  extraction_run_id text,
  student_id text not null,
  doc_type text,
  parsed_fields jsonb not null default '{}'::jsonb,
  confidence jsonb not null default '{}'::jsonb,
  created_at timestamptz default now()
);

create index if not exists idx_parsed_extractions_student_id on parsed_extractions(student_id);

create table if not exists comparison_results (
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

create index if not exists idx_comparison_results_student_id on comparison_results(student_id);
create index if not exists idx_comparison_results_match_status on comparison_results(match_status);

create table if not exists admission_forms (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  description text,
  slug text not null unique,
  status text not null default 'draft',
  created_by text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists admission_form_fields (
  id uuid primary key default gen_random_uuid(),
  form_id text not null,
  section text not null default 'General',
  field_key text not null,
  label text not null,
  field_type text not null default 'text',
  required boolean default false,
  options jsonb not null default '[]'::jsonb,
  help_text text,
  sort_order integer default 0,
  maps_to_student_field boolean default true,
  created_at timestamptz default now()
);

create index if not exists idx_admission_form_fields_form_id on admission_form_fields(form_id);

create table if not exists form_responses (
  id uuid primary key default gen_random_uuid(),
  form_id text not null,
  student_id text not null,
  submitted_by text,
  response_data jsonb not null default '{}'::jsonb,
  status text not null default 'submitted',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create index if not exists idx_form_responses_form_id on form_responses(form_id);
create index if not exists idx_form_responses_student_id on form_responses(student_id);
