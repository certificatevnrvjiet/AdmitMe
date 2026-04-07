# AdmitMe - Student Verification & Management System

A sophisticated web-based application designed for VNRVJIET (Vallurupalli Nageswara Rao Vignana Jyothi Institute of Engineering and Technology) to manage, verify, and automate student document processing during admissions.

## 🚀 Key Features

1.  **AI-Powered Data Extraction**: Automatically extracts student data from Tenth, Twelfth, and Transfer Certificates using **Google Gemini AI**.
2.  **Google Sheets Synchronization**: Seamlessly syncs student data from departmental Google Sheets into the central database.
3.  **Department-Wise Management**: Role-based access for different departments (CSE, ECE, EEE, etc.) with department-specific dashboards.
4.  **Admin Control**: Comprehensive user management, rights allocation, and cross-departmental data exports.
5.  **Real-time Notifications**: WebSocket-based notifications for long-running synchronization tasks.
6.  **Document Management**: Direct integration with Google Drive for serving and managing student memos and certificates with in-memory caching for performance.

## 🛠 Tech Stack

### Frontend
- **React (Vite)**
- **TailwindCSS** for styling
- **Context API** for state management
- **Lucide React** & **React Icons** for UI elements

### Backend
- **FastAPI** (Python framework)
- **Supabase** (PostgreSQL Database & data storage)
- **Google Gemini AI** (Generative AI for document data extraction)
- **Google Cloud APIs** (Drive & Sheets integrations)
- **PyMuPDF** & **Pillow** (Document and image processing)
- **Bcrypt** & **JWT** (Secure authentication)

## 📁 Project Structure

```text
AdmitMe/
├── frontend/             # React Vite application
│   ├── src/
│   │   ├── components/   # Reusable UI Components
│   │   ├── context/      # Application State & Auth context
│   │   ├── pages/        # Dashboard, Student Details, & Login pages
│   │   └── assets/       # Styles & Images
├── backend/              # FastAPI application
│   ├── config/           # Application settings & Env loader
│   ├── models/           # Pydantic models & Database schemas
│   ├── routers/          # API endpoints (Auth, Students, Sync)
│   ├── services/         # Business logic (Notifications, Auth service)
│   ├── extractor.py      # Gemini AI extraction logic & prompts
│   ├── GoogleService.py  # Google Drive & Sheets integration logic
│   ├── database.py       # Supabase client initialization
│   └── main.py           # Application entry point & WebSocket handler
```

## ⚙️ Installation & Setup

### Prerequisites
- Node.js (v18+)
- Python 3.9+
- MySQL Server (Local) or a Supabase Project
- Google Cloud Service Account (with Generative AI and optionally Drive & Sheets access)

*(Note: The project supports either a Local MySQL database or a Supabase cloud database. See `backend/MYSQL_ENV_SETUP.md` or `backend/DB_ENV_SETUP.md` for deep-dive database setups).*

### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Environment Variables
Copy the example environment file and fill in your details:
```bash
cp .env.example .env
```
Ensure you choose the correct `DB_PROVIDER` (`mysql` or `supabase`), configure the database credentials, and set up your `GOOGLE_API_KEY` for AI features.

#### Database Initialization
Run the bootstrap SQL script against your chosen database to create the required tables (`users`, `students2025`, `tasks`, `documents`, etc.).
- **MySQL:** `mysql -u root -p < migrations/000_bootstrap_core_schema_mysql.sql`
- **Supabase:** Run `migrations/000_bootstrap_core_schema.sql` in your SQL Editor.

*(Make sure to seed your first Admin user as explained in the setup guides!)*

#### Start the Backend
```bash
# Create local storage directory if required
mkdir -p data/admitme

# Start the API server
uvicorn main:app --reload
```
The API will run on `http://127.0.0.1:8000`.

### 2. Frontend Setup
```bash
cd ../frontend
npm install
```

#### Environment Variables
Copy the frontend environment example:
```bash
cp .env.example .env
```
Confirm `VITE_API_BASE_URL` is mapped to your backend correctly.

#### Start the Frontend
```bash
npm run dev
```

## 📡 Core API Endpoints

- `POST /token` - Authenticate user and receive JWT.
- `GET /me` - Retrieve current logged-in user profile.
- `POST /sync/{branch}` - Trigger AI-based sync from Google Sheets.
- `GET /students/{department}` - Fetch student records for a specific department.
- `PUT /student/{aadhaar}` - Update student verification status and details.
- `GET /image/{file_id}` - Proxy and cache student document images from Google Drive.
- `WS /ws/{username}` - Real-time notification channel for background tasks.

## 📄 License

Proprietary and confidential. Developed for VNRVJIET.
All rights reserved by VNRVJIET Department of CSE.