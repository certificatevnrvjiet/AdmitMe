-- AdmitMe bootstrap schema for Supabase/PostgreSQL
-- Run this in Supabase SQL Editor (safe with IF NOT EXISTS)

create extension if not exists pgcrypto;

create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  dept text not null,
  rights text not null default 'Read Only',
  password text not null,
  created_at timestamptz default now()
);

create table if not exists students2025 (
  degree_code text,
  ht_no text,
  student_name text,
  father_name text,
  mother_name text,
  date_of_birth text,
  gender text,
  identification_mark_1 text,
  identification_mark_2 text,
  tenth_board_name text,
  tenth_school_name text,
  tenth_district_code text,
  tenth_ht_no text,
  tenth_maximum_marks text,
  tenth_total_marks_cgpa text,
  tenth_percentage text,
  tenth_month_year text,
  twelfth_board_name text,
  twelfth_college_name text,
  twelfth_district_code text,
  twelfth_ht_no text,
  twelfth_maximum_marks text,
  twelfth_total_marks text,
  twelfth_percentage text,
  m1 text,
  m2 text,
  m3 text,
  m4 text,
  p1 text,
  p2 text,
  ch1 text,
  ch2 text,
  plab text,
  chlab text,
  total text,
  twelfth_groups_percentage text,
  twelfth_month_year text,
  eapcet_ht_no text,
  eapcet_rank text,
  jee_ht_no text,
  jee_mains_rank text,
  aadhaar_card_number text primary key,
  mother_tongue text,
  student_phone text,
  parent_phone text,
  parent_email text,
  father_phone text,
  mother_phone text,
  student_passport_no text,
  father_passport_no text,
  mother_passport_no text,
  vnr_email text,
  student_email text,
  father_email text,
  mother_email text,
  father_profession_and_designation text,
  mother_profession_and_designation text,
  reservation text,
  category_name text,
  caste_as_per_tc text,
  ebc_status text,
  ews_status text,
  income text,
  blood_group text,
  nationality text,
  religion text,
  minority text,
  address_dno text,
  address_street text,
  address_village_town text,
  address_mandal text,
  address_district text,
  address_state text,
  address_pincode text,
  rural_urban text,
  admission_category text,
  program_level text default 'BTECH',
  section text,
  branch_code text,
  college_code text,
  ph_status text,
  scribe text,
  status text,
  candidate_pic text,
  allotment_order text,
  joining_report text,
  aadhaar_link text,
  transfer_certificate_link text,
  tenth_memo_link text,
  twelfth_memo_link text,
  jee_rank_card_link text,
  eapcet_rank_card_link text,
  student_type text,
  Time_updated timestamptz,
  verification_remarks text,
  reviewed_by text,
  reviewed_at timestamptz,
  application_reference text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);


create index if not exists idx_students_branch_code on students2025(branch_code);
create index if not exists idx_students_degree_code on students2025(degree_code);
create index if not exists idx_students_status on students2025(status);
create index if not exists idx_students_name on students2025(student_name);

create table if not exists tasks (
  id text primary key,
  status text not null,
  params jsonb,
  progress integer default 0,
  result text,
  error text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists documents (
  id uuid primary key default gen_random_uuid(),
  student_id text not null,
  doc_type text not null,
  provider text not null,
  object_key text not null,
  mime_type text,
  size_bytes bigint,
  checksum text,
  status text default 'submitted',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create index if not exists idx_documents_student_id on documents(student_id);
create index if not exists idx_documents_doc_type on documents(doc_type);
create unique index if not exists uq_documents_student_doc_type on documents(student_id, doc_type);

create or replace view degree_code_counts as
select
  coalesce(nullif(upper(branch_code), ''), upper(degree_code)) as branch_code,
  count(*)::int as student_count
from students2025
group by coalesce(nullif(upper(branch_code), ''), upper(degree_code));
