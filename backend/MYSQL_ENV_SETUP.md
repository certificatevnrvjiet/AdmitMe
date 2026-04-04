# AdmitMe MySQL + ENV Setup

## 1) Start MySQL
Make sure local MySQL is running and listening on `127.0.0.1:3306`.

## 2) Bootstrap schema
Run:
```bash
mysql --protocol=TCP -h 127.0.0.1 -P 3306 -u root -p < /Users/gouthamlingoju/Projects/AdmitMe/backend/migrations/000_bootstrap_core_schema_mysql.sql
```

## 3) Create app DB user (do not use root in app)
Run as root:
```sql
CREATE USER IF NOT EXISTS 'admitme_app'@'127.0.0.1' IDENTIFIED BY 'CHANGE_ME_STRONG_PASSWORD';
GRANT ALL PRIVILEGES ON admitme.* TO 'admitme_app'@'127.0.0.1';
FLUSH PRIVILEGES;
```

## 4) Configure backend env
```bash
cp /Users/gouthamlingoju/Projects/AdmitMe/backend/.env.example /Users/gouthamlingoju/Projects/AdmitMe/backend/.env
```

Set in `backend/.env`:
```env
DB_PROVIDER=mysql
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DB=admitme
MYSQL_USER=admitme_app
MYSQL_PASSWORD=CHANGE_ME_STRONG_PASSWORD

STORAGE_PROVIDER=local
LOCAL_STORAGE_ROOT=./data/admitme
```

Create storage path:
```bash
mkdir -p /Users/gouthamlingoju/Projects/AdmitMe/backend/data/admitme
```

## 5) Install backend deps in venv
```bash
cd /Users/gouthamlingoju/Projects/AdmitMe/backend
source venv/bin/activate
pip install -r requirements.txt
```

Important: `cryptography` must be installed in this same `venv` (required by PyMySQL with MySQL 9 default auth).

## 6) Seed admin user
Generate hash:
```bash
python3 - <<'PY'
import bcrypt
pwd = "adminpass".encode("utf-8")
print(bcrypt.hashpw(pwd, bcrypt.gensalt()).decode("utf-8"))
PY
```

Insert:
```sql
USE admitme;
INSERT INTO users (id, email, dept, rights, password)
VALUES (UUID(), 'admin@vnr.admitme', 'admin', 'Full Access', 'PASTE_BCRYPT_HASH_HERE')
ON DUPLICATE KEY UPDATE
  dept=VALUES(dept),
  rights=VALUES(rights),
  password=VALUES(password);
```

## 7) Configure frontend env
```bash
cp /Users/gouthamlingoju/Projects/AdmitMe/frontend/.env.example /Users/gouthamlingoju/Projects/AdmitMe/frontend/.env
```

Set:
```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## 8) Run
```bash
cd /Users/gouthamlingoju/Projects/AdmitMe/backend
source venv/bin/activate
uvicorn main:app --reload
```

```bash
cd /Users/gouthamlingoju/Projects/AdmitMe/frontend
npm install
npm run dev
```

## 9) Quick auth verification
```bash
curl -X POST "http://127.0.0.1:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@vnr.admitme&password=adminpass"
```

## 10) Optional switch to S3 later
```env
STORAGE_PROVIDER=s3
S3_BUCKET=...
AWS_REGION=...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
S3_ENDPOINT_URL=
```
