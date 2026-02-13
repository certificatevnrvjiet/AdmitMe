from dotenv import load_dotenv
import os
from pathlib import Path
load_dotenv(Path(__file__).resolve().parent.parent / '.env')
# Supabase configuration
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
SUPABASE_URL = os.getenv('SUPABASE_URL')
# Google API configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
GOOGLE_CREDENTIALS= os.getenv("GOOGLE_CREDENTIALS")
FRONTEND_URL = os.getenv('FRONTEND_URL')

# JWT Configuration
SECRET_KEY = os.getenv('SECRET_KEY', "your-secret-key-change-me") # Fallback for dev, but should be in .env
ALGORITHM = os.getenv('ALGORITHM', "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 60 # Expiration time in minutes

