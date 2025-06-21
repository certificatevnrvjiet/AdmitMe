from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from database import supabase
from fastapi import FastAPI, HTTPException, Response, Depends, status, BackgroundTasks, Request
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
ACCESS_TOKEN_EXPIRE_MINUTES = 10

ORIGINS = ["http://localhost:3000", FRONTEND_URL ]
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
        "role": "admin",
    },
    "normal_user": {
        "username": "normal_user",
        "password": "userpass",
        "role": "user",
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
def create_access_token(data: dict, expires_delta: timedelta = None):
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
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None or role is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return {"username": username, "role": role}

DRIVE_SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


async def process_student(student_data: SheetStudent, app: FastAPI):
    """Process 6 extract calls in parallel for one subtask"""
    print("\n\nstarted processing student", student_data.name_of_the_student)
    student_data=Student.from_flat_student(student_data)
    
    board = student_data.twelfth_board_name
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
        (student_data.tenth_memo_link, prompts[0]),
        (student_data.twelfth_memo_link, prompt),
        (student_data.transfer_certificate_link, prompts[3]),
    ]
    async with GEMINI_SEMAPHORE:
        results = await asyncio.gather(*[
            extract(link, prompt, app.state.drive_service)
            for link, prompt in links_prompts
        ], return_exceptions=True)
        student_data.tenth_school_name = results[0].get("tenth_school_name", "")
        student_data.identification_mark_1 = results[0].get("identification_marks1", "")
        student_data.identification_mark_2 = results[0].get("identification_marks2", "")
        student_data.tenth_ht_no = results[0].get("tenth_hall_ticket_no", "")
        student_data.tenth_maximum_marks = results[0].get("tenth_max_marks/CGPA", "")
        student_data.tenth_total_marks_cgpa = results[0].get("tenth_total_marks/CGPA", "")
        student_data.tenth_month_year = results[0].get("tenth_month_year", "")
        student_data.twelfth_college_name = results[2].get("College Name", "")
        student_data.twelfth_ht_no= results[1].get("Hall Ticket Number", "")
        student_data.twelfth_maximum_marks = results[1].get("Max Marks", "")
        student_data.twelfth_total_marks = results[1].get("Total Marks", "")
        student_data.twelfth_month_year = results[1].get("Month_year", "")
        student_data.nationality = results[2].get("Nationality", "")
        student_data.religion = results[2].get("Religion", "")
        # Convert exceptions to error objects
        print("Processing student:", student_data.model_dump_json(indent=2))
        for i in results:
            print(i)





async def sync(task_id: str, params: dict , app: FastAPI):
    """Process all subtasks with progress tracking"""
    try:
        # Update to processing status
        supabase.table("tasks").update({"status": "processing"}).eq("id", task_id).execute()
        result = supabase.table('degree_code_counts').select('*').execute().data
        d={}
        for i in result:
            d[i['DEGREE_CODE']] = i['student_count']
        count_students_synced = d.get(params["branch"], 0)
        sheets_service=app.state.sheets_service
        RANGE=f'{params["branch"]}!B{count_students_synced + 2}:BS4'
        data_from_sheets = read_google_sheet(sheets_service,SPREADSHEET_ID,RANGE)

        # Prepare subtasks (60-150 groups of 6)
        no_of_students = len(data_from_sheets)
        
        # Process with concurrency control
        for i, student in enumerate(data_from_sheets):
            row = student
            field_names = list(SheetStudent.model_fields.keys())
            flatstudent_dict = dict(zip(field_names, row))
            student = SheetStudent(**flatstudent_dict)
            async with SUBTASK_SEMAPHORE:
                subtask_result = await process_student(student, app)
                
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
        
    except Exception as e:
        supabase.table("tasks").update({
            "status": "failed",
            "error": str(e)
        }).eq("id", task_id).execute()
        logging.exception(f"Task {task_id} failed")


@app.post("/sync/{branch}")
async def start_syncing(branch: str, background_tasks: BackgroundTasks,request: Request):
    task_id = str(uuid4())
    
    # Initialize task in database
    params = {"branch": branch}
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
    
@app.get("/me")
def read_users_me(current_user: dict = Depends(get_current_user)):
    return {"User": current_user['username'],"role":current_user['role']}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)