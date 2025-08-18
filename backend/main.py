from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from database import supabase
from fastapi import FastAPI, HTTPException, Response, Depends, status, BackgroundTasks, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from models.SheetModel import SheetStudent
from models.StudentModel import Student
from models.UserModel import User, UserCreate, UserUpdate, PasswordChange
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
from fastapi.middleware.cors import CORSMiddleware


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

ORIGINS = [FRONTEND_URL,"http://localhost:5173"]
GEMINI_SEMAPHORE = asyncio.Semaphore(30)  # Adjust based on rate limits
SUBTASK_SEMAPHORE = asyncio.Semaphore(10)  # Control subtask throughput



app.add_middleware(
    CORSMiddleware,
    allow_origins = ORIGINS,  # Adjust this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Helper to verify user credentials
# import bcrypt

def authenticate_user(username: str, password: str):
    try:
        # Fetch user with matching email
        print( "response from supabase\n\n\n")

        response = supabase.table("users").select("*").eq("email", username).single().execute()
        if response.data is None:
            return {"error": "User not found"}

        user = response.data

        # Check bcrypt-hashed password
        # if not bcrypt.checkpw(password.encode(), user["password"].encode()):
        #     return {"error": "Invalid credentials"}

        return {"user": {
            "id": user["id"],
            "email": user["email"],
            "dept": user["dept"],
            "rights": user["rights"]
        }}

    except Exception as e:
        return {"error": str(e)}


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
        student.tenth_district_code = safe_get(results[0],"district_code")
        student.identification_mark_1 = safe_get(results[0], "identification_marks1")
        student.identification_mark_2 = safe_get(results[0], "identification_marks2")
        student.tenth_ht_no = safe_get(results[0], "tenth_hall_ticket_no")
        student.tenth_maximum_marks = safe_get(results[0], "tenth_max_marks/CGPA")
        student.tenth_total_marks_cgpa = safe_get(results[0], "tenth_total_marks/CGPA")
        student.tenth_percentage = safe_get(results[0],"tenth_percentage")
        student.tenth_month_year = safe_get(results[0], "tenth_month_year")
        student.twelfth_college_name = safe_get(results[2], "College Name")
        student.twelfth_district_code = safe_get(results[0],"district_code")
        student.twelfth_ht_no = safe_get(results[1], "Hall Ticket Number")
        student.twelfth_maximum_marks = safe_get(results[1], "Max Marks")
        student.twelfth_total_marks = safe_get(results[1],  "Total Marks")
        student.twelfth_percentage = safe_get(results[2], "Percentage")
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
        response = supabase.table("students2025").insert(student_dict).execute()

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
        aadhaar_cards=supabase.table("students2025").select("aadhaar_card_number").eq("branch_code", params["branch"].upper()).execute().data
        result = supabase.table('degree_code_counts').select('*').execute().data
        d={}
        for i in result:
            d[i['DEGREE_CODE']] = i['student_count']
        count_students_synced = d.get(params["branch"], 0)
        sheets_service=app.state.sheets_service
        RANGE=f'{params["branch"]}!B2:BS4'
        # data_from_sheets = read_google_sheet(sheets_service,SPREADSHEET_ID,RANGE)
        data_from_sheets = read_google_sheet(sheets_service,"1fJ6nY_FtS4EY4c0tewN-IG6Ub9TcEdFtQ-shPu7XnP0",'Sheet1!A1:AS300')

        aadharindex=data_from_sheets[0].index("Aadhaar Card Number")
        aadhaar_cards=[i["aadhaar_card_number"] for i in aadhaar_cards]
        print("\naadhaar cards in db",aadhaar_cards)

        if data_from_sheets is None:
            data_from_sheets = []
        data_from_sheets = [row for row in data_from_sheets if row[aadharindex] not in aadhaar_cards]  # Filter out already synced students
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
    print("HI",form_data)
    user = authenticate_user(form_data.username, form_data.password)
    print(user,'\n\n')
    user=user['user']
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token_data = {
        "sub": user["email"],
        "role": user["dept"]
    }
    access_token = create_access_token(
        data=token_data,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    print(access_token)
    return {"access_token": access_token, "token_type": "bearer", "role": user["dept"]}


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
        response = supabase.table("students2025").select("*").execute()
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
        response = supabase.table("students2025").update(student_dict).eq("aadhaar_card_number", aadhaar_card_number).execute()
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
async def get_students_by_department(department: str,
    current_user:dict=Depends(get_current_user)
):
    try:
        if current_user["role"] != "admin" and current_user["role"] != department:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to export this department's data"
            )
        if department.lower() == "admin":
            response = supabase.table("students2025").select("*").execute()
        else:
            response = supabase.table("students2025").select("*") \
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
            response = supabase.table("students2025").select("*").execute()
        else:
            response = supabase.table("students2025").select("*") \
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

@app.post("/save-to-drive/{department}")
async def save_to_drive_sheet(
    department: str,
    search_term: str = "",
    status_filter: str = "all",
    current_user: dict = Depends(get_current_user)
):
    """
    Save filtered students to Google Sheet (append only new, no duplicates).
    Assumes first row in sheet is header.
    """
    SPREADSHEET_IDs = {
        "aids": "1lVUPIye-IVDuiYcqqPQcUojPeFbcmfIVn_0_7ofKqL4",
        "ae": "1Qwpp65ETTCxzcp0VEX7ZC-j9q8v76Bjw5D54a90ImEM",
        "ce": "1iKONmwrQRWJtoEupnZlgo_-56Cx6DtdUOFIctkhh_S4",
        "csbs": "1HxXmy68UuFYW3Wu1KYOridfAaim_9MZH9f_jKhDsI_o",
        "cse": "1EjKp1MW47OGnirxrujp6jojBHVzaDt_FdpC_-2mjArk",
        "aiml": "1JUfgrhh-LdZxl3HwzbEzI682_sfez7jv363InAxmX6Y",
        "cseds": "1Wx01ZJlRhff9WVamImv2bbOsV9R7rZ-bvEhUNjpdOkg",
        "csecys": "16FcMEjuoo3KcM21FkGZ2MvWWnEIkxyD_BqAmQRKOZLg",
        "cseiot": "1aaFBRJ4YvizkuBFfkK6PDBQOpMAvSoSGKuf4uywUGnA",
        "eee": "1Hzzj0E7jAonqLmHQntVjYysXA_rpwo3h-POyl0bqQCk",
        "ece": "1FrO-zhcshXvZ0VVmwvqfe0lN8IP6ariDkw_pCBy4FA8",  
        "eie": "11-O1FoFwU9bm_PxbBswZ-OJ9GAFpxHVhhGnJL_Nx9K0",
        "it": "1b7mRLZpWm0YFrUJffSUjaRtKal3Z-ZxAh6Kr7qM5wQM",
        "me": "1vFlnZbt8ebS4_cdCkkyFr1j9zwsQkHSLKbfyXvJcKfc",
        "vlsi": "1uNCdi6bp4VTMkugW7qfejH29kLw9BYOCvm7QO0Mfzg",
        "biotechnology": "1KeUep03GXhNZha4qCNaGwX-l6ZnTSBmHtE5wJG6_5hw",
        "roboticsandai": "1vybIqUdF-22H0kWg2H6g7OAHkuvDcJoeruN3QqSndPY"
}


    try:
        # Permissions
        if current_user["role"] != "admin" and current_user["role"] != department:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this department's sheet"
            )

        # Get students from database (same as export)
        if department.lower() == "admin":
            response = supabase.table("students2025").select("*").execute()
        else:

            response = supabase.table("students2025").select("*") \
                .or_(f"degree_code.eq.{department.upper()},branch_code.eq.{department.upper()}") \
                .execute()
        students_data = response.data or []

        # Apply filters
        filtered_students = []
        for student in students_data:
            student_data = student.get('data', student)
            if search_term and search_term.lower() not in student_data.get('student_name', '').lower():
                continue
            if department != 'admin' and student_data.get('branch_code', '').lower() != department:
                continue
            if status_filter != 'all' and student_data.get('status', '').lower() != status_filter:
                continue
            filtered_students.append(student_data)

        # Prepare data for sheet
        student_fields = list(Student.model_fields.keys())

        # Get Google Sheets service
        sheets_service = app.state.sheets_service
        if not sheets_service:
            raise HTTPException(status_code=500, detail="Sheets service not available")

        # Sheet name and range
        sheet_name = 'Sheet1'  # Adjust as needed
        range_name = "Sheet1!A1:CZ1000"  # Adjust as needed


        # Prepare all rows: header + data
        header_row = [field.replace('_', ' ').title() for field in student_fields]
        all_rows = [header_row] + [
            [str(student.get(field, "")) for field in student_fields]
            for student in filtered_students
        ]

        # Overwrite the sheet with new data
        sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_IDs[department.lower()],
            range=range_name,
            valueInputOption="RAW",
            body={"values": all_rows}
        ).execute()

        return {"message": f"Sheet overwritten with {len(filtered_students)} students."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Save to drive failed: {str(e)}")

# User Management Endpoints
@app.get("/users")
async def get_users(current_user: dict = Depends(get_current_user)):
    """Get all users - Admin only"""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can access user management"
        )
    
    try:
        response = supabase.table("users").select("id, email, dept, rights").execute()
        return {"users": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/users")
async def create_user(user_data: UserCreate, current_user: dict = Depends(get_current_user)):
    """Create a new user - Admin only"""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can create users"
        )
    
    try:
        # Check if user already exists
        existing_user = supabase.table("users").select("*").eq("email", user_data.email).execute()
        if existing_user.data:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        # Create user (password should be hashed in production)
        user_dict = user_data.model_dump()
        response = supabase.table("users").insert(user_dict).execute()
        
        if response.data:
            created_user = response.data[0]
            return {
                "message": "User created successfully",
                "user": {
                    "id": created_user["id"],
                    "email": created_user["email"],
                    "dept": created_user["dept"],
                    "rights": created_user["rights"]
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create user")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/users/{user_id}")
async def update_user(user_id: str, user_data: UserUpdate, current_user: dict = Depends(get_current_user)):
    """Update user - Admin only"""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can update users"
        )
    
    try:
        # Check if user exists
        existing_user = supabase.table("users").select("*").eq("id", user_id).execute()
        if not existing_user.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prepare update data (only include non-None values)
        update_data = {}
        if user_data.email is not None:
            update_data["email"] = user_data.email
        if user_data.dept is not None:
            update_data["dept"] = user_data.dept
        if user_data.rights is not None:
            update_data["rights"] = user_data.rights
        if user_data.password is not None:
            update_data["password"] = user_data.password
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Update user
        response = supabase.table("users").update(update_data).eq("id", user_id).execute()
        
        if response.data:
            updated_user = response.data[0]
            return {
                "message": "User updated successfully",
                "user": {
                    "id": updated_user["id"],
                    "email": updated_user["email"],
                    "dept": updated_user["dept"],
                    "rights": updated_user["rights"]
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update user")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """Delete user - Admin only"""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can delete users"
        )
    
    try:
        # Check if user exists
        existing_user = supabase.table("users").select("*").eq("id", user_id).execute()
        if not existing_user.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prevent admin from deleting themselves
        if existing_user.data[0]["email"] == current_user["username"]:
            raise HTTPException(status_code=400, detail="Cannot delete your own account")
        
        # Delete user
        response = supabase.table("users").delete().eq("id", user_id).execute()
        
        if response.data:
            return {"message": "User deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete user")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/users/{user_id}/change-password")
async def change_user_password(user_id: str, password_data: PasswordChange, current_user: dict = Depends(get_current_user)):
    """Change user password - Admin only"""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can change user passwords"
        )
    
    try:
        # Validate password confirmation
        if password_data.new_password != password_data.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")
        
        # Check if user exists
        existing_user = supabase.table("users").select("*").eq("id", user_id).execute()
        if not existing_user.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update password
        response = supabase.table("users").update({"password": password_data.new_password}).eq("id", user_id).execute()
        
        if response.data:
            return {"message": "Password changed successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to change password")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)