from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from uuid import uuid4
from database import supabase
from services.auth_service import get_current_user
from GoogleService import read_google_sheet
from models.SheetModel import SheetStudent
from models.StudentModel import Student
from extractor import extract, prompts
from config.settings import SPREADSHEET_ID
import asyncio
import logging

router = APIRouter()

# Semaphores
GEMINI_SEMAPHORE = asyncio.Semaphore(30)
SUBTASK_SEMAPHORE = asyncio.Semaphore(10)

# Store active WebSocket connections logic remains in main for now or needs a dedicated manager
# For this router, we need access to notify_user. 
# We will import the notify_user function from main via a slightly circular dependency or refactor notify_user to a service/manager.
# For now, let's keep the websocket endpoint in main and pass notification logic via a callback or just event bus.
# Simpler approach: make notify_user available in app state or import it if possible. 
# To avoid circular imports, let's assume we can attach the notify function to app.state or similar.
# Actually, the notify_user function in main depends on active_connections.
# Let's move the websocket logic to main and just call a helper here? 
# Or better: move active_connections and notify_user to a new `services/notification.py`.

# However, for this refactor, let's try to keep it simple. We will leave WebSocket endpoint in main.py 
# and passing the `app` object allows us to access state, but `notify_user` isn't in state.
# We will just redefine `notify_user` here if we move `active_connections` or import it.
# Let's keep `notify_user` in this file or a shared service.
# Ideally, `active_connections` should be a singleton service.

# Let's create a notification service to solve this cleanly.

from services.notification_service import notify_user

def safe_get(result, key):
    if isinstance(result, Exception):
        return ""
    return str(result.get(key) or "")

async def process_student(student_data: SheetStudent, branch: str, app):
    """Process 6 extract calls in parallel for one subtask"""
    # print("\n\nstarted processing student", student_data.name_of_the_student)
    student = Student.from_flat_student(student_data)
    student.degree_code = branch.upper()
    student.branch_code = branch.upper()
    student.status = "Not Viewed"
    board = student.twelfth_board_name
    prompt = prompts[4]  # Default prompt for most boards
    if board in ("TG BIE", "AP BIE"):
        prompt = prompts[4]
    elif board == "ACE and A Level":
        prompt = prompts[5]
    elif board == "ICSC":
        prompt = prompts[6]
    elif board == "CBSE":
        prompt = prompts[7]
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
        Scores = results[1].get("Subject Scores", {}) if isinstance(results[1], dict) else {}
        if Scores is None or not isinstance(Scores, dict):
            Scores = {}
            
        student.tenth_school_name = safe_get(results[0], "tenth_school_name")
        student.tenth_district_code = safe_get(results[0], "district_code")
        student.identification_mark_1 = safe_get(results[0], "identification_marks1")
        student.identification_mark_2 = safe_get(results[0], "identification_marks2")
        student.tenth_ht_no = safe_get(results[0], "tenth_hall_ticket_no")
        student.tenth_maximum_marks = safe_get(results[0], "tenth_max_marks/CGPA")
        student.tenth_total_marks_cgpa = safe_get(results[0], "tenth_total_marks/CGPA")
        student.tenth_percentage = safe_get(results[0], "tenth_percentage")
        student.tenth_month_year = safe_get(results[0], "tenth_month_year")
        student.twelfth_college_name = safe_get(results[2], "College Name")
        student.twelfth_district_code = safe_get(results[0], "district_code")
        student.twelfth_ht_no = safe_get(results[1], "Hall Ticket Number")
        student.twelfth_maximum_marks = safe_get(results[1], "Max Marks")
        student.twelfth_total_marks = safe_get(results[1], "Total Marks")
        student.twelfth_percentage = safe_get(results[2], "Percentage")
        student.twelfth_month_year = safe_get(results[1], "Month_year")
        student.m1 = safe_get(Scores, "M1")
        student.m2 = safe_get(Scores, "M2")
        student.m3 = safe_get(Scores, "M3")
        student.m4 = safe_get(Scores, "M4")
        student.p1 = safe_get(Scores, "P1")
        student.p2 = safe_get(Scores, "P2")
        student.ch1 = safe_get(Scores, "C1")
        student.ch2 = safe_get(Scores, "C2")
        student.plab = safe_get(Scores, "P_Practicals")
        student.chlab = safe_get(Scores, "C_Practicals")
        student.total = safe_get(results[1], "Total Marks")
       
        student_dict = student.model_dump()
        response = supabase.table("students2025").insert(student_dict).execute()

async def sync_task_logic(task_id: str, params: dict, app):
    """Process all subtasks with progress tracking"""
    try:
        # Update to processing status
        supabase.table("tasks").update({"status": "processing"}).eq("id", task_id).execute()
        aadhaar_cards = []
        start = 0
        while True:
            batch = supabase.table("students2025") \
                .select("aadhaar_card_number") \
                .range(start, start + 1000 - 1) \
                .execute().data
            
            if not batch:
                break
            
            aadhaar_cards.extend(batch)
            start += 1000
            
        result = supabase.table('degree_code_counts').select('*').execute().data
        d = {}
        for i in result:
            d[i['branch_code']] = i['student_count']
        
        sheets_service = app.state.sheets_service
        RANGE = f'{params["branch"]}!B3:BS300'
        data_from_sheets = read_google_sheet(sheets_service, SPREADSHEET_ID, RANGE)

        aadhaar_cards = [i["aadhaar_card_number"] for i in aadhaar_cards]
        
        if data_from_sheets is None:
            data_from_sheets = []
            
        data_from_sheets = [row for row in data_from_sheets if row[5] not in aadhaar_cards]  # Filter out already synced students
        
        no_of_students = len(data_from_sheets)
        
        # Process with concurrency control
        for i, student in enumerate(data_from_sheets):
            row = student
            # Check row length and pad if necessary or handle errors
            # Assuming row structure matches SheetStudent fields
            field_names = list(SheetStudent.model_fields.keys())
            
            # Simple zip might lose data if row is short, but Pydantic might complain.
            # Ideally we should validate row length.
            flatstudent_dict = dict(zip(field_names, row))
            # Handle potential extra/missing fields if necessary
            
            try:
                student = SheetStudent(**flatstudent_dict)
                async with SUBTASK_SEMAPHORE:
                    await process_student(student, params["branch"], app)
                    
                    # Update progress every 10% of tasks
                    if (i + 1) % max(1, no_of_students // 10) == 0:
                        progress = int(((i + 1) / no_of_students) * 100)
                        supabase.table("tasks").update({
                            "progress": progress
                        }).eq("id", task_id).execute()
            except Exception as e:
                logging.error(f"Error processing row {i}: {e}")
                # Continue with next student
                continue
        
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

@router.post("/sync/{branch}")
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
    background_tasks.add_task(sync_task_logic, task_id, params, request.app)
    return {"task_id": task_id}

@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    response = supabase.table("tasks").select("*").eq("id", task_id).execute()
    return response.data if response.data else {"error": "Task not found"}

