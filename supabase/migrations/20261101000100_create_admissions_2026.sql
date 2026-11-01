-- B.Tech Admissions 2026: canonical application record and immutable source ledger.
create table if not exists public.admissions_2026 (
  id uuid primary key default gen_random_uuid(),
  admission_year smallint not null default 2026 check (admission_year = 2026),
  branch text not null check (branch in ('AID', 'AUT', 'BIO', 'CIV', 'CSB', 'CSC', 'CSD', 'CSE', 'CSM', 'CSO', 'ECE', 'EEE', 'EIE', 'EVL', 'INF', 'MEC', 'RAI')),
  admission_category text,
  application_reference text,
  student_name text not null, father_name text, mother_name text, date_of_birth text, gender text,
  aadhaar_card_number text not null,
  eapcet_ht_no text, eapcet_rank text, jee_ht_no text, jee_mains_rank text,
  mother_tongue text, religion text, nationality text,
  student_phone text, father_phone text, mother_phone text, parent_phone text,
  student_email text, father_email text, mother_email text, parent_email text,
  father_profession_and_designation text, mother_profession_and_designation text,
  address_dno text, address_street text, address_village_town text, address_mandal text,
  address_district text, address_state text, address_pincode text, rural_urban text,
  ews_status text, category_name text, caste_as_per_tc text, ebc_status text, income text,
  minority text, blood_group text, ph_status text, scribe text,
  tenth_board_name text, twelfth_board_name text,
  candidate_pic text, allotment_order text, joining_report text, aadhaar_link text,
  transfer_certificate_link text, tenth_memo_link text, twelfth_memo_link text,
  jee_rank_card_link text, eapcet_rank_card_link text, consent text,
  status text not null default 'submitted', verification_remarks text, reviewed_by text, reviewed_at timestamptz,
  extraction_status text not null default 'pending',
  source_system text not null, source_spreadsheet_id text, source_sheet_tab text,
  source_response_timestamp text, source_response_email text,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
  unique (admission_year, aadhaar_card_number)
);

create index if not exists idx_admissions_2026_branch on public.admissions_2026(branch);
create index if not exists idx_admissions_2026_status on public.admissions_2026(status);

create table if not exists public.admissions_2026_responses (
  id uuid primary key default gen_random_uuid(),
  admission_id uuid references public.admissions_2026(id) on delete set null,
  source_spreadsheet_id text not null, source_sheet_tab text not null,
  source_response_timestamp text, source_response_email text, aadhaar_card_number text,
  response_fingerprint text not null unique, raw_response jsonb not null,
  imported_at timestamptz not null default now()
);

create index if not exists idx_admissions_2026_responses_admission on public.admissions_2026_responses(admission_id);
