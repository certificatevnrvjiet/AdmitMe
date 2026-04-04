from dotenv import load_dotenv
import os
from pathlib import Path
load_dotenv(Path(__file__).resolve().parent.parent / '.env')
# Supabase configuration
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
SUPABASE_URL = os.getenv('SUPABASE_URL')

# Database provider: supabase | mysql
DB_PROVIDER = os.getenv("DB_PROVIDER", "supabase").lower()

# MySQL configuration (used when DB_PROVIDER=mysql)
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DB = os.getenv("MYSQL_DB", "admitme")
MYSQL_USER = os.getenv("MYSQL_USER", "admitme_app")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
# Google API configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
GOOGLE_CREDENTIALS= os.getenv("GOOGLE_CREDENTIALS")
FRONTEND_URL = os.getenv('FRONTEND_URL')

# Storage configuration
STORAGE_PROVIDER = os.getenv("STORAGE_PROVIDER", "local")
LOCAL_STORAGE_ROOT = os.getenv("LOCAL_STORAGE_ROOT", "./data/admitme")
S3_BUCKET = os.getenv("S3_BUCKET")
AWS_REGION = os.getenv("AWS_REGION")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")

# JWT Configuration
SECRET_KEY = os.getenv('SECRET_KEY', "your-secret-key-change-me") # Fallback for dev, but should be in .env
ALGORITHM = os.getenv('ALGORITHM', "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 60 # Expiration time in minutes
