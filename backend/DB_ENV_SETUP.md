# AdmitMe DB + ENV Setup (Detailed)

## 1) Create Supabase Project
1. Go to Supabase and create a new project.
2. Copy these values from Project Settings:
- `Project URL` -> `SUPABASE_URL`
- `service_role` key -> `SUPABASE_KEY`

Important: use `service_role` key on backend only (never in frontend).

## 2) Run Bootstrap SQL
In Supabase SQL Editor, run:
- `/Users/gouthamlingoju/Projects/AdmitMe/backend/migrations/000_bootstrap_core_schema.sql`

This creates:
- `users`
- `students2025`
- `tasks`
- `documents`
- `degree_code_counts` (view)

Optional (if not already done):
- `/Users/gouthamlingoju/Projects/AdmitMe/backend/migrations/001_create_documents_table.sql`

## 3) Create Backend ENV
1. Copy:
- `backend/.env.example` -> `backend/.env`
2. Fill required values in `backend/.env`:
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `GOOGLE_API_KEY`
- `SPREADSHEET_ID`
- `GOOGLE_CREDENTIALS` (single-line JSON)
- `FRONTEND_URL`
- `SECRET_KEY`

## 4) Storage Mode Setup
### A) Local storage (recommended first)
Set:
- `STORAGE_PROVIDER=local`
- `LOCAL_STORAGE_ROOT=./data/admitme` (or absolute path)

Create and permissions:
```bash
mkdir -p backend/data/admitme
```

### B) S3 storage (when ready)
Set:
- `STORAGE_PROVIDER=s3`
- `S3_BUCKET`
- `AWS_REGION`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- optional: `S3_ENDPOINT_URL` (for non-AWS S3-compatible services)

Also ensure bucket policy/IAM allow:
- `s3:PutObject`
- `s3:GetObject`
- `s3:DeleteObject`
- `s3:HeadObject`
for the bucket path used by AdmitMe.

## 5) Frontend ENV
1. Copy:
- `frontend/.env.example` -> `frontend/.env`
2. Set:
- `VITE_API_BASE_URL=http://127.0.0.1:8000`

## 6) Seed First Admin User
Backend expects bcrypt-hashed password in `users.password`.

Generate bcrypt hash:
```bash
python3 - <<'PY'
import bcrypt
pwd = "ChangeMe@123".encode("utf-8")
print(bcrypt.hashpw(pwd, bcrypt.gensalt()).decode("utf-8"))
PY
```

Insert user (replace hash):
```sql
insert into users (email, dept, rights, password)
values ('admin@admitme.local', 'admin', 'Full Access', 'PASTE_BCRYPT_HASH_HERE')
on conflict (email) do update
set dept = excluded.dept,
    rights = excluded.rights,
    password = excluded.password;
```

## 7) Install + Run
Backend:
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

## 8) Smoke Test Checklist
1. Open `http://localhost:5173/student-portal`
2. Submit application + required files.
3. Login from `/` with admin user.
4. Open dashboard and verify student appears.
5. Open student modal and verify document preview works.

## 9) If You Switch to S3
1. Update backend `.env` with S3 variables.
2. Restart backend.
3. Upload a new student document.
4. Verify row in `documents` has `provider = 's3'`.

## 10) Common Issues
- `SUPABASE_KEY` wrong: auth and DB operations fail immediately.
- `GOOGLE_CREDENTIALS` malformed: sync/extractor startup fails.
- Missing `documents` table: new upload endpoints fail.
- Wrong S3 IAM: upload/download fail with permission errors.
