-- Canonical provenance for records entering the 2026 admissions workflow.
alter table students2025 add column source_system varchar(50) null;
alter table students2025 add column source_spreadsheet_id varchar(255) null;
alter table students2025 add column source_sheet_tab varchar(255) null;
alter table students2025 add column source_response_timestamp varchar(100) null;
alter table students2025 add column source_response_email varchar(320) null;
alter table students2025 add column consent text null;
