-- Canonical provenance for records entering the 2026 admissions workflow.
alter table students2025 add column if not exists source_system text;
alter table students2025 add column if not exists source_spreadsheet_id text;
alter table students2025 add column if not exists source_sheet_tab text;
alter table students2025 add column if not exists source_response_timestamp text;
alter table students2025 add column if not exists source_response_email text;
alter table students2025 add column if not exists consent text;

create index if not exists idx_students_source_system on students2025(source_system);
create index if not exists idx_students_source_sheet_tab on students2025(source_sheet_tab);
