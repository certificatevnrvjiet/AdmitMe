from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from uuid import uuid4
from database import supabase
from services.auth_service import get_current_user
from GoogleService import read_google_sheet
from models.Admissions2026 import Admissions2026Applicant
from models.StudentModel import Student
from extractor import extract_from_document_ref, prompts
from services.engine_service import SCHEMA_MAPPING
from config.settings import SPREADSHEET_ID
from services.catalog_service import normalize_branch_code
from services.admissions_2026 import ADMISSIONS_RESPONSES_TABLE, ADMISSIONS_TABLE
import asyncio
import hashlib
import json
import logging

router = APIRouter()

# Semaphores
GEMINI_SEMAPHORE = asyncio.Semaphore(30)
SUBTASK_SEMAPHORE = asyncio.Semaphore(10)

from services.notification_service import notify_user
from services.gemini_batch_service import task_status_with_batch

def safe_get(result, key):
    if isinstance(result, Exception):
        return ""
    return str(result.get(key) or "")


def _normalise_label(value: str) -> str:
    """Make sheet headings and branch names safe to compare."""
    return "".join(character for character in str(value).lower() if character.isalnum())


def _find_sheet_tab(sheets_service, spreadsheet_id: str, branch: str) -> str:
    """Return the workbook tab matching a branch such as CSE or UG - CSE."""
    metadata = sheets_service.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        fields="sheets.properties.title",
    ).execute()
    requested = _normalise_label(branch)
    requested_without_ug = requested.removeprefix("ug")

    for sheet in metadata.get("sheets", []):
        title = sheet["properties"]["title"]
        normalized_title = _normalise_label(title)
        if normalized_title in {requested, requested_without_ug, f"ug{requested_without_ug}"}:
            # Quote the name because the new tabs contain spaces and hyphens.
            return f"'{title.replace("'", "''")}'"

    raise ValueError(f"No worksheet matches branch '{branch}'")


def _row_to_sheet_student(headers: list[str], row: list[str]) -> Admissions2026Applicant:
    """Build the canonical 2026 DTO from a named Google Sheets row."""
    return Admissions2026Applicant.from_sheet_row(headers, row)

async def process_student(student_data: Admissions2026Applicant, branch: str, app):
    """Process 6 extract calls in parallel for one subtask"""
    # print("\n\nstarted processing student", student_data.name_of_the_student)
    student = Student.from_admissions2026(student_data)
    student.branch = branch.upper()
    student.status = "submitted"
    board = student.twelfth_board_name
    prompt = prompts[4]  # Default prompt for most boards
    schema = SCHEMA_MAPPING[4]
    if board in ("TG BIE", "AP BIE"):
        prompt = prompts[4]
        schema = SCHEMA_MAPPING[4]
    elif board == "ACE and A Level":
        prompt = prompts[5]
        schema = SCHEMA_MAPPING[5]
    elif board == "ICSE":
        prompt = prompts[6]
        schema = SCHEMA_MAPPING[6]
    elif board == "CBSE":
        prompt = prompts[7]
        schema = SCHEMA_MAPPING[7]
    links_prompts = [
        (student.tenth_memo_link, prompts[0], SCHEMA_MAPPING[0]),
        (student.twelfth_memo_link, prompt, schema),
        (student.transfer_certificate_link, prompts[3], SCHEMA_MAPPING[3]),
    ]

    providers = getattr(app.state, "storage_providers", {})
    async with GEMINI_SEMAPHORE:
        results = await asyncio.gather(*[
            extract_from_document_ref(link, p_prompt, providers, p_schema)
            for link, p_prompt, p_schema in links_prompts if link is not None
        ], return_exceptions=True)
        tenth_result = results[0] if len(results) > 0 else {}
        twelfth_result = results[1] if len(results) > 1 else {}
        transfer_result = results[2] if len(results) > 2 else {}

        Scores = twelfth_result.get("Subject Scores", {}) if isinstance(twelfth_result, dict) else {}
        if Scores is None or not isinstance(Scores, dict):
            Scores = {}
            
        student.tenth_school_name = safe_get(tenth_result, "tenth_school_name")
        student.tenth_district_code = safe_get(tenth_result, "district_code")
        student.identification_mark_1 = safe_get(tenth_result, "identification_marks1")
        student.identification_mark_2 = safe_get(tenth_result, "identification_marks2")
        student.tenth_ht_no = safe_get(tenth_result, "tenth_hall_ticket_no")
        student.tenth_maximum_marks = safe_get(tenth_result, "tenth_max_marks/CGPA")
        student.tenth_total_marks_cgpa = safe_get(tenth_result, "tenth_total_marks/CGPA")
        student.tenth_percentage = safe_get(tenth_result, "tenth_percentage")
        student.tenth_month_year = safe_get(tenth_result, "tenth_month_year")
        student.twelfth_college_name = safe_get(transfer_result, "College Name")
        student.twelfth_district_code = safe_get(twelfth_result, "district_code")
        student.twelfth_ht_no = safe_get(twelfth_result, "Hall Ticket Number")
        student.twelfth_maximum_marks = safe_get(twelfth_result, "Max Marks")
        student.twelfth_total_marks = safe_get(twelfth_result, "Total Marks")
        student.twelfth_percentage = safe_get(twelfth_result, "Percentage")
        student.twelfth_month_year = safe_get(twelfth_result, "Month_year")
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
        student.total = safe_get(twelfth_result, "Total Marks")
       
        student_dict = student.model_dump()
        response = supabase.table(ADMISSIONS_TABLE).insert(student_dict).execute()

async def sync_task_logic(task_id: str, params: dict, app):
    """Process all subtasks with progress tracking"""
    try:
        # Update to processing status
        supabase.table("tasks").update({"status": "processing"}).eq("id", task_id).execute()
        aadhaar_cards = []
        start = 0
        while True:
            batch = supabase.table(ADMISSIONS_TABLE) \
                .select("aadhaar_card_number") \
                .range(start, start + 1000 - 1) \
                .execute().data
            
            if not batch:
                break
            
            aadhaar_cards.extend(batch)
            start += 1000
            
        sheets_service = app.state.sheets_service
        tab_name = _find_sheet_tab(sheets_service, SPREADSHEET_ID, params["branch"])
        data_from_sheets = read_google_sheet(sheets_service, SPREADSHEET_ID, f"{tab_name}!A1:BS") or []
        headers, response_rows = (data_from_sheets[0], data_from_sheets[1:]) if data_from_sheets else ([], [])
        students_to_sync = []
        for row_index, row in enumerate(response_rows, start=2):
            try:
                student_data = _row_to_sheet_student(headers, row)
                students_to_sync.append((student_data, row))
            except Exception as e:
                logging.error(f"Error mapping sheet row {row_index}: {e}")

        no_of_students = len(students_to_sync)
        
        # First, insert/create initial student records from sheet rows
        new_student_ids: set[str] = set()
        for i, (student_data, row) in enumerate(students_to_sync):
            try:
                student_dict = student_data.to_student_record(
                    branch=params["branch"],
                    source_system="google_forms_2026",
                    source_spreadsheet_id=SPREADSHEET_ID,
                    source_sheet_tab=tab_name[1:-1].replace("''", "'"),
                )
                student_dict.update({
                    "admission_year": 2026,
                    "status": "submitted",
                    "extraction_status": "pending",
                })
                admission = supabase.table(ADMISSIONS_TABLE).upsert(
                    student_dict,
                    on_conflict="admission_year,aadhaar_card_number",
                ).execute()
                admission_id = admission.data[0].get("id") if admission.data else None
                raw_response = dict(zip(headers, row))
                fingerprint = hashlib.sha256(
                    json.dumps(
                        {
                            "tab": tab_name,
                            "timestamp": student_data.source_response_timestamp,
                            "aadhaar": student_data.aadhaar_card_number,
                            "response": raw_response,
                        },
                        sort_keys=True,
                        default=str,
                    ).encode()
                ).hexdigest()
                supabase.table(ADMISSIONS_RESPONSES_TABLE).upsert({
                    "admission_id": admission_id,
                    "source_spreadsheet_id": SPREADSHEET_ID,
                    "source_sheet_tab": tab_name[1:-1].replace("''", "'"),
                    "source_response_timestamp": student_data.source_response_timestamp,
                    "source_response_email": student_data.source_response_email,
                    "aadhaar_card_number": student_data.aadhaar_card_number,
                    "response_fingerprint": fingerprint,
                    "raw_response": raw_response,
                }, on_conflict="response_fingerprint").execute()
                if student_data.aadhaar_card_number:
                    new_student_ids.add(student_data.aadhaar_card_number)
            except Exception as e:
                logging.error(f"Error saving sheet student row {i}: {e}")
                continue

        # Import deliberately does not trigger Gemini extraction. It is a
        # separate, explicit workflow after staff has reviewed imported data.
        if new_student_ids:
            supabase.table("tasks").update({"progress": 100}).eq("id", task_id).execute()

        supabase.table("tasks").update({
            "status": "completed",
            "result": f"{no_of_students} students synced & processed",
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
    """
    Initializes a background syncing task for a given branch and returns the task ID.
    Enforces role-based permissions to ensure users only sync their authorized branches.
    """
    try:
        normalized_branch = normalize_branch_code(branch)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    role = (current_user.get("role") or "").lower()
    if role != "admin":
        try:
            role = normalize_branch_code(role)
        except ValueError:
            pass
    # Verify against canonical 2026 codes, so legacy roles such as AIDS can
    # continue to sync the AID tab.
    if role != "admin" and role != normalized_branch:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to sync this branch"
        )

    task_id = str(uuid4())
    
    # Initialize task in database
    params = {"branch": normalized_branch, "username": current_user["username"]}
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
    """
    Fetches the current status and progress of a background syncing task.
    """
    return task_status_with_batch(task_id)
