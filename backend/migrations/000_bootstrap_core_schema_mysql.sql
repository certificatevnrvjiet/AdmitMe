-- AdmitMe bootstrap schema for MySQL 8+
-- Run this on your local MySQL server for DB_PROVIDER=mysql

create database if not exists admitme;
use admitme;

create table if not exists users (
  id char(36) primary key default (uuid()),
  email varchar(255) not null unique,
  dept varchar(100) not null,
  rights varchar(100) not null default 'Read Only',
  password varchar(255) not null,
  created_at datetime default current_timestamp
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
  aadhaar_card_number varchar(20) primary key,
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
  program_level varchar(20) default 'BTECH',
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
  Time_updated datetime,
  verification_remarks text,
  reviewed_by text,
  reviewed_at datetime,
  application_reference text,
  created_at datetime default current_timestamp,
  updated_at datetime default current_timestamp on update current_timestamp
);

create index idx_students_branch_code on students2025(branch_code(50));
create index idx_students_degree_code on students2025(degree_code(50));
create index idx_students_status on students2025(status(50));
create index idx_students_name on students2025(student_name(100));

create table if not exists tasks (
  id varchar(100) primary key,
  status varchar(50) not null,
  params json,
  progress int default 0,
  result text,
  error text,
  created_at datetime default current_timestamp,
  updated_at datetime default current_timestamp on update current_timestamp
);

create table if not exists documents (
  id char(36) primary key default (uuid()),
  student_id varchar(50) not null,
  doc_type varchar(100) not null,
  provider varchar(30) not null,
  object_key text not null,
  mime_type varchar(120),
  size_bytes bigint,
  checksum varchar(128),
  status varchar(40) default 'submitted',
  created_at datetime default current_timestamp,
  updated_at datetime default current_timestamp on update current_timestamp,
  unique key uq_documents_student_doc_type (student_id, doc_type)
);

create index idx_documents_student_id on documents(student_id);
create index idx_documents_doc_type on documents(doc_type);

create or replace view degree_code_counts as
select
  coalesce(nullif(upper(branch_code), ''), upper(degree_code)) as branch_code,
  count(*) as student_count
from students2025
group by coalesce(nullif(upper(branch_code), ''), upper(degree_code));
