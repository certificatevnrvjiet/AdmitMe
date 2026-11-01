-- Gemini Batch API tracking for MySQL 8+

create table if not exists gemini_batch_jobs (
  id varchar(50) primary key,
  task_id varchar(100) not null,
  gemini_job_name text not null,
  input_file_name text,
  output_file_name text,
  model varchar(100),
  state varchar(50) not null default 'JOB_STATE_PENDING',
  total_students int default 0,
  total_documents int default 0,
  completed_documents int default 0,
  failed_documents int default 0,
  submitted_by varchar(255),
  error text,
  created_at datetime default current_timestamp,
  updated_at datetime default current_timestamp on update current_timestamp,
  submitted_at datetime,
  completed_at datetime
);

set @idx_exists := (
  select count(*) from information_schema.statistics
  where table_schema = database() and table_name = 'gemini_batch_jobs' and index_name = 'idx_gemini_batch_jobs_task_id'
);
set @sql := if(@idx_exists = 0, 'create index idx_gemini_batch_jobs_task_id on gemini_batch_jobs(task_id)', 'select 1');
prepare stmt from @sql; execute stmt; deallocate prepare stmt;

set @idx_exists := (
  select count(*) from information_schema.statistics
  where table_schema = database() and table_name = 'gemini_batch_jobs' and index_name = 'idx_gemini_batch_jobs_state'
);
set @sql := if(@idx_exists = 0, 'create index idx_gemini_batch_jobs_state on gemini_batch_jobs(state)', 'select 1');
prepare stmt from @sql; execute stmt; deallocate prepare stmt;

set @col_exists := (
  select count(*) from information_schema.columns
  where table_schema = database() and table_name = 'students2025' and column_name = 'extraction_status'
);
set @sql := if(@col_exists = 0, 'alter table students2025 add column extraction_status varchar(30) default ''pending''', 'select 1');
prepare stmt from @sql; execute stmt; deallocate prepare stmt;

set @col_exists := (
  select count(*) from information_schema.columns
  where table_schema = database() and table_name = 'extraction_runs' and column_name = 'batch_job_id'
);
set @sql := if(@col_exists = 0, 'alter table extraction_runs add column batch_job_id varchar(50)', 'select 1');
prepare stmt from @sql; execute stmt; deallocate prepare stmt;

set @col_exists := (
  select count(*) from information_schema.columns
  where table_schema = database() and table_name = 'extraction_runs' and column_name = 'batch_key'
);
set @sql := if(@col_exists = 0, 'alter table extraction_runs add column batch_key varchar(120)', 'select 1');
prepare stmt from @sql; execute stmt; deallocate prepare stmt;

set @idx_exists := (
  select count(*) from information_schema.statistics
  where table_schema = database() and table_name = 'extraction_runs' and index_name = 'idx_extraction_runs_batch_job_id'
);
set @sql := if(@idx_exists = 0, 'create index idx_extraction_runs_batch_job_id on extraction_runs(batch_job_id)', 'select 1');
prepare stmt from @sql; execute stmt; deallocate prepare stmt;

set @idx_exists := (
  select count(*) from information_schema.statistics
  where table_schema = database() and table_name = 'extraction_runs' and index_name = 'uq_extraction_runs_batch_key'
);
set @sql := if(@idx_exists = 0, 'create unique index uq_extraction_runs_batch_key on extraction_runs(batch_key)', 'select 1');
prepare stmt from @sql; execute stmt; deallocate prepare stmt;
