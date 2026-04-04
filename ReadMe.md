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
- Supabase Project (with `users`, `students2025`, and `tasks` tables)
- Google Cloud Service Account (with Drive, Sheets, and Generative AI access)

### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Environment Variables (`backend/.env`)
Create a `.env` file in the `backend/` directory:
```env
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key

# Google API Configuration
GOOGLE_API_KEY=your_gemini_api_key
GOOGLE_CREDENTIALS=your_google_service_account_json_content
SPREADSHEET_ID=your_main_google_sheet_id

# Security Configuration
SECRET_KEY=your_random_secret_string
ALGORITHM=HS256

# Application Configuration
FRONTEND_URL=http://localhost:5173
```

### 2. Frontend Setup
```bash
cd frontend
npm install
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