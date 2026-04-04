set @col_exists := (
  select count(*)
  from information_schema.columns
  where table_schema = database()
    and table_name = 'students2025'
    and column_name = 'program_level'
);

set @ddl := if(
  @col_exists = 0,
  'alter table students2025 add column program_level varchar(20) default ''BTECH''',
  'select 1'
);

prepare stmt from @ddl;
execute stmt;
deallocate prepare stmt;

update students2025
set program_level = 'BTECH'
where program_level is null or program_level = '';
