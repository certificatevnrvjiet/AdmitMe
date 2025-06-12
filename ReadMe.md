    # Student Verification System - VNRVJIET

    A web-based application for managing and verifying student documents and information at VNRVJIET (Vallurupalli Nageswara Rao Vignana Jyothi Institute of Engineering and Technology).

    ## Project Overview

    This system provides a streamlined process for:
    - Document verification and validation
    - Student information management
    - Department-wise student data organization
    - Automated data extraction from documents using Google's Gemini AI

    ## Tech Stack

    ### Frontend
    - React (with Vite)
    - TailwindCSS for styling
    - React Router for navigation
    - Context API for state management
    - React Icons for UI elements

    ### Backend
    - FastAPI
    - Firebase Admin SDK
    - Google Cloud Services
    - Google Drive API
    - Google Gemini AI
    - Python libraries:
    - Pydantic for data validation
    - python-multipart
    - google-cloud-storage
    - PIL (Python Imaging Library)

    ## Features

    1. **Authentication System**
    - Department-specific login
    - Admin dashboard access
    - Role-based authorization

    2. **Document Management**
    - Upload and storage of critical documents
    - Automated information extraction
    - Document verification status tracking

    3. **Student Information**
    - Comprehensive student profiles
    - Academic details
    - Personal information
    - Contact details
    - Category and reservation details

    4. **Dashboard Features**
    - Quick actions panel
    - Verification statistics
    - Student search functionality
    - Status filtering
    - Sorting capabilities

    5. **Dark Mode Support**
    - System-wide theme switching
    - Persistent theme preferences

    ## Installation

    ### Prerequisites
    - Node.js (v14 or higher)
    - Python 3.8+
    - Google Cloud account with necessary APIs enabled
    - Firebase project setup

    ### Frontend Setup
    ```bash
    cd frontend
    npm install
    npm run dev
    ```

    ### Backend Setup
    ```bash
    cd backend
    pip install -r requirements.txt
    uvicorn main:app --reload
    ```

    ### Environment Variables
    Create a `.env` file in the backend directory:
    ```
    GOOGLE_API_KEY=your_google_api_key
    ```

    ## Project Structure

    ```
    FieldProject/
    ├── frontend/
    │   ├── src/
    │   │   ├── components/
    │   │   ├── context/
    │   │   ├── pages/
    │   │   └── assets/
    │   └── public/
    └── backend/
        ├── models/
        ├── database.py
        ├── extractor.py
        ├── GoogleAuthService.py
        └── main.py
    ```

    ## API Endpoints

    - `POST /submit` - Submit student details and documents
    - `GET /student/{student_id}` - Retrieve student information
    - `GET /api/drive/image/{file_id}` - Fetch document images from Google Drive

    ## Authentication

    - Department-specific email domains (`@vnrvjiet.in`)
    - Admin access with dedicated credentials
    - Department-wise dashboard access control

    ## Document Verification Process

    1. Document upload through frontend interface
    2. Automated data extraction using Google Gemini AI
    3. Data validation and storage in Firebase
    4. Status tracking and updates
    5. Department-level verification workflow

    ## Contributors

    - L. Goutham
    - G. Charmi Bai
    - M. Akhila
    - D. L. Sarvani

    ## Project Guidance

    - Dr. V. Baby, HOD [CSE, VNRVJIET]
    - Dr. B.V. Kiranmayee, Professor [CSE, VNRVJIET]
    - Mr. P. Sudheer Benarji, Assistant Professor [CSE, VNRVJIET]

    ## License

    This project is proprietary and confidential. All rights reserved by VNRVJIET.