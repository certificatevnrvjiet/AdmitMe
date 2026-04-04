-- Normalized document metadata table
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
