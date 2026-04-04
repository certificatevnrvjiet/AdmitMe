alter table if exists students2025
add column if not exists program_level text default 'BTECH';

update students2025
set program_level = 'BTECH'
where coalesce(program_level, '') = '';
