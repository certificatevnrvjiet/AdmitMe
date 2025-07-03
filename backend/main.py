from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from database import supabase
from fastapi import FastAPI, HTTPException, Response, Depends, status, BackgroundTasks, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from models.SheetModel import SheetStudent
from models.StudentModel import Student
from extractor import extract,prompts
from uuid import uuid4
import re
from GoogleService import authenticate_service_account, download_image_from_drive,read_google_sheet
from datetime import datetime 
from datetime import datetime, timedelta
import uvicorn
from jose import JWTError, jwt
from config.settings import FRONTEND_URL,SPREADSHEET_ID
from contextlib import asynccontextmanager
from googleapiclient.discovery import build
import asyncio
import logging
from typing import Optional, Dict
from openpyxl import Workbook
from io import BytesIO


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup: Authenticate and store service in app state
    credentials = authenticate_service_account()
    if credentials:
        app.state.sheets_service = build('sheets', 'v4', credentials=credentials)
        app.state.drive_service = build('drive', 'v3', credentials=credentials)
        app.state.db = supabase
    else:
        app.state.sheets_service = None
    yield
    # Teardown (if needed)
    # e.g., closing resources



app = FastAPI(lifespan=lifespan)

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

ORIGINS = ["http://localhost:5173", FRONTEND_URL ]
GEMINI_SEMAPHORE = asyncio.Semaphore(30)  # Adjust based on rate limits
SUBTASK_SEMAPHORE = asyncio.Semaphore(10)  # Control subtask throughput



app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,  # Adjust this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


fake_users_db = {
    "admin@vnrvjiet.in": {
        "username": "admin@vnrvjiet.in",
        "password": "adminpass",
        "role": "admin"
    },
    "aidsadmin": {
        "username": "aidsadmin",
        "password": "aidspass",
        "role": "aids"
    },
    "aeadmin": {
        "username": "aeadmin",
        "password": "aepass",
        "role": "ae"
    },
    "ceadmin": {
        "username": "ceadmin",
        "password": "cepass",
        "role": "ce"
    },
    "csbsadmin": {
        "username": "csbsadmin",
        "password": "csbspass",
        "role": "csbs"
    },
    "cseadmin": {
        "username": "cseadmin",
        "password": "csepass",
        "role": "cse"
    },
    "amladmin": {
        "username": "amladmin",
        "password": "amlpass",
        "role": "aml"
    },
    "csedsadmin": {
        "username": "csedsadmin",
        "password": "csedspass",
        "role": "cseds"
    },
    "csecysadmin": {
        "username": "csecysadmin",
        "password": "csecyspass",
        "role": "csecys"
    },
    "cseiotadmin": {
        "username": "cseiotadmin",
        "password": "cseiotpass",
        "role": "cseiot"
    },
    "eeeadmin": {
        "username": "eeeadmin",
        "password": "eeepass",
        "role": "eee"
    },
    "eceadmin": {
        "username": "eceadmin",
        "password": "ecepass",
        "role": "ece"
    },
    "eieadmin": {
        "username": "eieadmin",
        "password": "eiepass",
        "role": "eie"
    },
    "itadmin": {
        "username": "itadmin",
        "password": "itpass",
        "role": "it"
    },
    "meadmin": {
        "username": "meadmin",
        "password": "mepass",
        "role": "me"
    }
}


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Helper to verify user credentials
def authenticate_user(username: str, password: str):
    user = fake_users_db.get(username)
    if not user or user["password"] != password:
        return None
    return user

# Create JWT token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        if username is None or role is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return {"username": username, "role": role}

DRIVE_SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Store active WebSocket connections: {username: websocket}
active_connections: Dict[str, WebSocket] = {}

@app.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket, token: str):
    # Authenticate user from token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            await websocket.close()
            return
    except Exception:
        await websocket.close()
        return

    await websocket.accept()
    active_connections[username] = websocket
    try:
        while True:
            await websocket.receive_text()  # Keep alive
    except WebSocketDisconnect:
        if username in active_connections:
            del active_connections[username]

# Utility to send notification
async def notify_user(username: str, message: dict):
    websocket = active_connections.get(username)
    if websocket:
        await websocket.send_json(message)

async def process_student(student_data: SheetStudent, branch: str, app: FastAPI):
    """Process 6 extract calls in parallel for one subtask"""
    print("\n\nstarted processing student", student_data.name_of_the_student)
    student = Student.from_flat_student(student_data)
    student.degree_code = branch.upper()
    student.branch_code = branch.upper()
    student.status = "Not Viewed"
    board = student.twelfth_board_name
    print("Processing board:", board)
    prompt = prompts[4]  # Default prompt for most boards
    if board in ("TG BIE", "AP BIE"):
        prompt=prompts[4]
    elif board == "ACE and A Level":
        prompt=prompts[5]
    elif board == "ICSC":
        prompt=prompts[6]
    elif board == "CBSE":
        prompt=prompts[7]
    links_prompts = [
        (student.tenth_memo_link, prompts[0]),
        (student.twelfth_memo_link, prompt),
        (student.transfer_certificate_link, prompts[3]),
    ]
    async with GEMINI_SEMAPHORE:
        results = await asyncio.gather(*[
            extract(link, prompt, app.state.drive_service)
            for link, prompt in links_prompts if link is not None
        ], return_exceptions=True)
        print("Results:", results[1])
        Scores = results[1].get("Subject Scores", {}) if isinstance(results[1], dict)  else {}
        if Scores is None or not isinstance(Scores, dict):
            Scores = {}
        print("Scores  : ",Scores)
        student.tenth_school_name = safe_get(results[0], "tenth_school_name")
        student.identification_mark_1 = safe_get(results[0], "identification_marks1")
        student.identification_mark_2 = safe_get(results[0], "identification_marks2")
        student.tenth_ht_no = safe_get(results[0], "tenth_hall_ticket_no")
        student.tenth_maximum_marks = safe_get(results[0], "tenth_max_marks/CGPA")
        student.tenth_total_marks_cgpa = safe_get(results[0], "tenth_total_marks/CGPA")
        student.tenth_month_year = safe_get(results[0], "tenth_month_year")
        student.twelfth_college_name = safe_get(results[2], "College Name")
        student.twelfth_ht_no = safe_get(results[1], "Hall Ticket Number")
        student.twelfth_maximum_marks = safe_get(results[1], "Max Marks")
        student.twelfth_total_marks = safe_get(results[1], "Total Marks")
        student.twelfth_month_year = safe_get(results[1], "Month_year")
        student.nationality = safe_get(results[2], "Nationality")
        student.religion = safe_get(results[2], "Religion")
        student.m1=safe_get(Scores, "M1")
        student.m2=safe_get(Scores, "M2")
        student.m3=safe_get(Scores, "M3")
        student.m4=safe_get(Scores, "M4")
        student.p1=safe_get(Scores, "P1")
        student.p2=safe_get(Scores, "P2")
        student.ch1=safe_get(Scores, "C1")
        student.ch2=safe_get(Scores, "C2")
        student.plab=safe_get(Scores, "P_Practicals")
        student.chlab=safe_get(Scores, "C_Practicals")
        student.total=safe_get(results[1], "Total Marks")
       

        # Convert exceptions to error objects
        print("Processing student:", student.model_dump_json(indent=2))
        student_dict = student.model_dump()

        # Insert into Supabase
        response = supabase.table("students").insert(student_dict).execute()

        # Print the response
        # print("Insert response:", response)


def safe_get(result, key):
    if isinstance(result, Exception):
        return ""
    return str(result.get(key) or "")


async def sync(task_id: str, params: dict , app: FastAPI):
    """Process all subtasks with progress tracking"""
    try:
        # Update to processing status
        supabase.table("tasks").update({"status": "processing"}).eq("id", task_id).execute()
        aadhaar_cards=supabase.table("students").select("aadhaar_card_number").eq("branch_code", params["branch"].upper()).execute().data
        result = supabase.table('degree_code_counts').select('*').execute().data
        d={}
        for i in result:
            d[i['DEGREE_CODE']] = i['student_count']
        count_students_synced = d.get(params["branch"], 0)
        sheets_service=app.state.sheets_service
        RANGE=f'{params["branch"]}!B2:BS4'
        data_from_sheets = read_google_sheet(sheets_service,SPREADSHEET_ID,RANGE)
        # print("Data from sheets:", data_from_sheets[].index("557119422790"))
        aadhaar_cards=[i["aadhaar_card_number"] for i in aadhaar_cards]
        print("\naadhaar cards in db",aadhaar_cards)

        if data_from_sheets is None:
            data_from_sheets = []
        data_from_sheets = [row for row in data_from_sheets if row[5] not in aadhaar_cards]  # Filter out already synced students
        # Prepare subtasks (60-150 groups of 6)
        print("Data from sheets:", data_from_sheets)
        no_of_students = len(data_from_sheets)
        # print(data_from_sheets["n"])
        # Process with concurrency control
        for i, student in enumerate(data_from_sheets):
            row = student
            field_names = list(SheetStudent.model_fields.keys())
            flatstudent_dict = dict(zip(field_names, row))
            student = SheetStudent(**flatstudent_dict)
            async with SUBTASK_SEMAPHORE:
                subtask_result = await process_student(student, params["branch"], app)
                
                # Update progress every 10% of tasks
                if (i + 1) % max(1, no_of_students // 10) == 0:
                    progress = int(((i + 1) / no_of_students) * 100)
                    supabase.table("tasks").update({
                        "progress": progress
                    }).eq("id", task_id).execute()
        
        # Final update
        supabase.table("tasks").update({
            "status": "completed",
            "result": f"{no_of_students} students processed",
            "progress": 100
        }).eq("id", task_id).execute()
        # Notify user
        await notify_user(params["username"], {
            "type": "sync_complete",
            "task_id": task_id,
            "message": f"Sync for {params['branch']} completed!"
        })
    except Exception as e:
        supabase.table("tasks").update({
            "status": "failed",
            "error": str(e)
        }).eq("id", task_id).execute()
        logging.exception(f"Task {task_id} failed")
        # Notify user
        await notify_user(params["username"], {
            "type": "sync_failed",
            "task_id": task_id,
            "message": f"Sync for {params['branch']} failed!"
        })


@app.post("/sync/{branch}")
async def start_syncing(
    branch: str, 
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    # Verify if user has permission to sync this branch
    if current_user["role"] != "admin" and current_user["role"] != branch:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to sync this branch"
        )

    task_id = str(uuid4())
    
    # Initialize task in database
    params = {"branch": branch, "username": current_user["username"]}
    supabase.table("tasks").insert({
        "id": task_id,
        "status": "queued",
        "params": params,
        "progress": 0
    }).execute()
    
    # Start background processing
    background_tasks.add_task(sync, task_id, params, request.app)
    return {"task_id": task_id}

@app.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    response = supabase.table("tasks").select("*").eq("id", task_id).execute()
    return response.data if response.data else {"error": "Task not found"}


@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    print(form_data)
    user = authenticate_user(form_data.username, form_data.password)
    print(form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token_data = {
        "sub": user["username"],
        "role": user["role"]
    }
    access_token = create_access_token(
        data=token_data,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    print(access_token)
    return {"access_token": access_token, "token_type": "bearer", "role": user["role"]}


@app.get("/api/verify-token")
def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        # Decode and verify the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check expiration
        exp = payload.get("exp")
        if not exp or datetime.fromtimestamp(exp) < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
            )
        
        # Return user details along with validation status
        return {
            "valid": True,
            "user": payload.get("sub"),
            "role": payload.get("role"),
            "expires": datetime.fromtimestamp(exp).isoformat()
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Token validation error: {str(e)}"
        )
    

@app.get("/students")
async def get_students():
    try:
        response = supabase.table("students").select("*").execute()
        return {"students": response.data}
    except Exception as e:
        return {"error": str(e)}


@app.put("/student/{aadhaar_card_number}")
def update_student(aadhaar_card_number: str, updated_student: Student):
    # Convert to dict
    student_dict = updated_student.model_dump()
    print("student_dict", student_dict)
    # Update in Supabase
    try:
        response = supabase.table("students").update(student_dict).eq("aadhaar_card_number", aadhaar_card_number).execute()
        if response.data:
            return {"message": "Student updated successfully", "data": response.data}
        else:
            raise HTTPException(status_code=404, detail="Student not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/me")
def read_users_me(current_user: dict = Depends(get_current_user)):
    return {"User": current_user['username'],"role":current_user['role']}

@app.get("/students/{department}")
async def get_students_by_department(department: str):
    try:
        if department.lower() == "admin":
            response = supabase.table("students").select("*").execute()
        else:
            # Try both degree_code and branch_code for compatibility
            response = supabase.table("students").select("*") \
                .or_(f"degree_code.eq.{department.upper()},branch_code.eq.{department.upper()}") \
                .execute()
        return {"students": response.data}
    except Exception as e:
        return {"error": str(e)}

@app.get("/export-students/{department}")
async def export_students_excel(
    department: str,
    search_term: str = "",
    status_filter: str = "all",
    current_user: dict = Depends(get_current_user)
):
    """Export filtered students as Excel file"""
    try:
        # Verify user permissions
        if current_user["role"] != "admin" and current_user["role"] != department:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to export this department's data"
            )
        
        # Get students from database
        if department.lower() == "admin":
            response = supabase.table("students").select("*").execute()
        else:
            response = supabase.table("students").select("*") \
                .or_(f"degree_code.eq.{department.upper()},branch_code.eq.{department.upper()}") \
                .execute()
        
        students_data = response.data or []
        
        # Apply filters (same logic as frontend)
        filtered_students = []
        for student in students_data:
            # Flatten student data if needed
            student_data = student.get('data', student)
            
            # Apply search filter
            if search_term and search_term.lower() not in student_data.get('student_name', '').lower():
                continue
                
            # Apply department filter
            if department != 'admin' and student_data.get('branch_code', '').lower() != department:
                continue
                
            # Apply status filter
            if status_filter != 'all' and student_data.get('status', '').lower() != status_filter:
                continue
                
            filtered_students.append(student_data)
        
        # Create Excel workbook
        wb = Workbook()
        ws = wb.active
        if ws:
            ws.title = f"Students_{department}"
        
        # Get all field names from Student model
        student_fields = list(Student.model_fields.keys())
        
        # Write headers
        for col, field in enumerate(student_fields, 1):
            if ws:
                ws.cell(row=1, column=col, value=field.replace('_', ' ').title())
        
        # Write data
        for row, student in enumerate(filtered_students, 2):
            for col, field in enumerate(student_fields, 1):
                if ws:
                    ws.cell(row=row, column=col, value=student.get(field, ''))
        
        # Save to BytesIO
        excel_file = BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"students_{department}_{timestamp}.xlsx"
        
        return Response(
            content=excel_file.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

# In-memory cache for file_id to image bytes
image_cache: Dict[str, bytes] = {}

@app.get("/image/{file_id}")
async def get_image(
    file_id: str,
    # current_user: dict = Depends(get_current_user)  # Require authentication
):
    """Serve images from Google Drive by file ID, with in-memory caching"""
    try:
        if not app.state.drive_service:
            raise HTTPException(status_code=500, detail="Drive service not available")
        
        # Check cache first
        if file_id in image_cache:
            image_bytes = image_cache[file_id]
        else:
            # Download image from Google Drive
            image_bytes = await download_image_from_drive(file_id, app.state.drive_service)
            if image_bytes:
                image_cache[file_id] = image_bytes  # Cache the result
        
        if not image_bytes:
            raise HTTPException(status_code=404, detail="Image not found or could not be downloaded")
        
        return Response(
            content=image_bytes,
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=3600"}  # Cache for 1 hour
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve image: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)