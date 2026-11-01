-- Engines and admin-created admission forms for MySQL 8+

create table if not exists extraction_runs (
  id char(36) primary key default (uuid()),
  student_id varchar(50) not null,
  document_id varchar(50),
  doc_type varchar(100),
  provider varchar(30),
  object_key text,
  status varchar(50) not null default 'queued',
  raw_output json,
  error text,
  batch_job_id varchar(50),
  batch_key varchar(120),
  created_at datetime default current_timestamp,
  updated_at datetime default current_timestamp on update current_timestamp
);

create index idx_extraction_runs_student_id on extraction_runs(student_id);
create index idx_extraction_runs_doc_type on extraction_runs(doc_type);
create index idx_extraction_runs_batch_job_id on extraction_runs(batch_job_id);
create unique index uq_extraction_runs_batch_key on extraction_runs(batch_key);

create table if not exists parsed_extractions (
  id char(36) primary key default (uuid()),
  extraction_run_id varchar(50),
  student_id varchar(50) not null,
  doc_type varchar(100),
  parsed_fields json not null,
  confidence json not null,
  created_at datetime default current_timestamp
);

create index idx_parsed_extractions_student_id on parsed_extractions(student_id);

create table if not exists comparison_results (
  id char(36) primary key default (uuid()),
  student_id varchar(50) not null,
  field_name varchar(120) not null,
  filled_value text,
  extracted_value text,
  match_status varchar(50) not null,
  severity varchar(30) not null default 'low',
  source_doc_type varchar(100),
  extraction_run_id varchar(50),
  reviewer_override boolean default false,
  reviewer_notes text,
  created_at datetime default current_timestamp,
  updated_at datetime default current_timestamp on update current_timestamp
);

create index idx_comparison_results_student_id on comparison_results(student_id);
create index idx_comparison_results_match_status on comparison_results(match_status);

create table if not exists admission_forms (
  id char(36) primary key default (uuid()),
  title text not null,
  description text,
  slug varchar(150) not null unique,
  status varchar(50) not null default 'draft',
  created_by text,
  created_at datetime default current_timestamp,
  updated_at datetime default current_timestamp on update current_timestamp
);

create table if not exists admission_form_fields (
  id char(36) primary key default (uuid()),
  form_id varchar(50) not null,
  section text not null,
  field_key varchar(120) not null,
  label text not null,
  field_type varchar(50) not null default 'text',
  required boolean default false,
  options json not null,
  help_text text,
  sort_order int default 0,
  maps_to_student_field boolean default true,
  created_at datetime default current_timestamp
);

create index idx_admission_form_fields_form_id on admission_form_fields(form_id);

create table if not exists form_responses (
  id char(36) primary key default (uuid()),
  form_id varchar(50) not null,
  student_id varchar(50) not null,
  submitted_by text,
  response_data json not null,
  status varchar(50) not null default 'submitted',
  created_at datetime default current_timestamp,
  updated_at datetime default current_timestamp on update current_timestamp
);

create index idx_form_responses_form_id on form_responses(form_id);
create index idx_form_responses_student_id on form_responses(student_id);
