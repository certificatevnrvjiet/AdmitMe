from typing import Dict
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, Response, Request, UploadFile, File
from io import BytesIO
from openpyxl import Workbook
from datetime import datetime
from PIL import Image
import fitz
from services.auth_service import get_current_user, can_access_student_record
from database import supabase
from models.StudentModel import Student
from models.DocumentModel import DocumentUploadResponse
from models.VerificationModel import VerificationUpdate
from services.catalog_service import normalize_branch_code, program_branch_catalog, normalize_student_branch_fields
from services.admissions_2026 import ADMISSIONS_TABLE
from services.status_service import normalize_status, is_transition_allowed, canonicalize_student_status
from services.document_service import (
    normalize_doc_type,
    build_object_key,
    calculate_checksum,
    create_or_update_document,
    fetch_student,
    list_students_for_role,
    migrate_legacy_documents,
    resolve_student_document_ref,
    validate_upload_and_detect_mime,
)
from routers.engines import queue_engine_run

router = APIRouter()

# In-memory cache for file_id to image bytes
image_cache: Dict[str, bytes] = {}
MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024


def _db_datetime(value: datetime | None = None) -> str:
    dt = value or datetime.utcnow()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _pdf_to_png_bytes(pdf_bytes: bytes) -> bytes | None:
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if len(doc) == 0:
            return None
        page = doc[-1]
        pix = page.get_pixmap()
        image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        output = BytesIO()
        image.save(output, format="PNG")
        return output.getvalue()
    except Exception:
        return None

@router.get("/image/{file_id}")
async def get_image(
    file_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Serve images from Google Drive by file ID, with in-memory caching."""
    try:
        providers = getattr(request.app.state, "storage_providers", {})
        gdrive_provider = providers.get("gdrive")
        if not gdrive_provider:
            raise HTTPException(status_code=500, detail="Drive storage provider not available")
  
        # Check cache first
        if file_id in image_cache:
            image_bytes = image_cache[file_id]
        else:
            image_bytes = gdrive_provider.get_bytes(file_id)
            if image_bytes:
                image_cache[file_id] = image_bytes
                if len(image_cache) > 99:
                    image_cache.clear()
        
        if not image_bytes:
            raise HTTPException(status_code=404, detail="Image not found or could not be downloaded")
        
        return Response(
            content=image_bytes,
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=3600"}  # Cache for 1 hour
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve image: {str(e)}")


@router.get("/meta/programs-branches")
async def get_programs_branches():
    return program_branch_catalog()


@router.get("/students")
async def list_students(
    current_user: dict = Depends(get_current_user),
):
    """Standardized students list endpoint with role-based access."""
    try:
        students = list_students_for_role(current_user)
        return {"students": students}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list students: {str(e)}")


@router.get("/students/id/{student_id}")
async def get_student_by_id(
    student_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Fetch one student by Aadhaar/student id."""
    student = fetch_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if not can_access_student_record(current_user, student):
        raise HTTPException(status_code=403, detail="You don't have permission to access this student")

    return {"student": student}


@router.patch("/students/{student_id}/verification")
async def update_student_verification(
    student_id: str,
    payload: VerificationUpdate,
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("rights") == "Read Only":
        raise HTTPException(status_code=403, detail="You don't have enough permissions")

    student = fetch_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if not can_access_student_record(current_user, student):
        raise HTTPException(status_code=403, detail="You don't have permission to update this student")

    next_status = normalize_status(payload.status)
    current_status = normalize_status(student.get("status"))
    if not is_transition_allowed(current_status, next_status):
        raise HTTPException(
            status_code=409,
            detail=f"Invalid status transition: {current_status} -> {next_status}",
        )

    update_payload = {
        "status": next_status,
        "verification_remarks": payload.remarks or "",
        "reviewed_by": payload.reviewed_by or current_user.get("username"),
        "reviewed_at": _db_datetime(payload.reviewed_at),
    }

    response = (
        supabase.table(ADMISSIONS_TABLE)
        .update(update_payload)
        .eq("aadhaar_card_number", student_id)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Student not found")

    return {
        "message": "Verification status updated",
        "student_id": student_id,
        "status": next_status,
        "remarks": payload.remarks or "",
        "reviewed_by": update_payload["reviewed_by"],
        "reviewed_at": update_payload["reviewed_at"],
    }


@router.post("/students/{student_id}/documents/{doc_type}", response_model=DocumentUploadResponse)
async def upload_student_document(
    student_id: str,
    doc_type: str,
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("rights") == "Read Only":
        raise HTTPException(status_code=403, detail="You don't have enough permissions")

    normalized_doc_type = normalize_doc_type(doc_type)
    student = fetch_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if not can_access_student_record(current_user, student):
        raise HTTPException(status_code=403, detail="You don't have permission to upload documents for this student")

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(payload) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds max size of 5MB")

    try:
        content_type = validate_upload_and_detect_mime(payload, file.filename, file.content_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    storage = request.app.state.storage
    object_key = build_object_key(student_id, normalized_doc_type, file.filename or "")
    saved_key = storage.save(object_key, payload, content_type=content_type)
    checksum = calculate_checksum(payload)

    document_row = create_or_update_document(
        student_id=student_id,
        doc_type=normalized_doc_type,
        provider=storage.name,
        object_key=saved_key,
        mime_type=content_type,
        size_bytes=len(payload),
        checksum=checksum,
        status="submitted",
    )

    preview_url = f"/students/{student_id}/documents/{normalized_doc_type}"
    result = DocumentUploadResponse(
        document_id=document_row.get("id"),
        doc_type=normalized_doc_type,
        status=document_row.get("status", "submitted"),
        provider=document_row.get("provider", storage.name),
        object_key=document_row.get("object_key", saved_key),
        preview_url=preview_url,
    )
    queue_engine_run(background_tasks, student_id, request, current_user, [normalized_doc_type])
    return result


@router.get("/students/{student_id}/documents/{doc_type}")
async def get_student_document(
    student_id: str,
    doc_type: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    normalized_doc_type = normalize_doc_type(doc_type)
    student = fetch_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if not can_access_student_record(current_user, student):
        raise HTTPException(status_code=403, detail="You don't have permission to access this document")

    doc_ref = resolve_student_document_ref(student, student_id, normalized_doc_type)
    if not doc_ref:
        raise HTTPException(status_code=404, detail="Document reference not found")

    providers = getattr(request.app.state, "storage_providers", {})
    active_provider_name = getattr(request.app.state.storage, "name", "")
    providers.setdefault(active_provider_name, request.app.state.storage)
    provider = providers.get(doc_ref.provider)
    if not provider:
        raise HTTPException(status_code=500, detail=f"Storage provider not configured: {doc_ref.provider}")

    cache_key = f"{doc_ref.provider}:{doc_ref.key}"
    image_bytes = image_cache.get(cache_key)
    if image_bytes is None:
        image_bytes = provider.get_bytes(doc_ref.key)
        if image_bytes:
            image_cache[cache_key] = image_bytes
            if len(image_cache) > 99:
                image_cache.clear()

    if not image_bytes:
        raise HTTPException(status_code=404, detail="Document not found")

    media_type = "application/octet-stream"
    if doc_ref.provider == "gdrive":
        media_type = "image/png"
    if doc_ref.key.lower().endswith(".pdf"):
        converted = _pdf_to_png_bytes(image_bytes)
        if converted:
            image_bytes = converted
            media_type = "image/png"
        else:
            media_type = "application/pdf"
    elif doc_ref.key.lower().endswith(".png"):
        media_type = "image/png"
    elif doc_ref.key.lower().endswith((".jpg", ".jpeg")):
        media_type = "image/jpeg"

    return Response(
        content=image_bytes,
        media_type=media_type,
        headers={"Cache-Control": "private, max-age=3600"},
    )


@router.post("/documents/migrate-legacy")
async def migrate_legacy_docs(
    request: Request,
    limit: int = 0,
    current_user: dict = Depends(get_current_user),
):
    if (current_user.get("role") or "").lower() != "admin":
        raise HTTPException(status_code=403, detail="Only admin can run migration")

    students = list_students_for_role({"role": "admin"})
    target_storage = request.app.state.storage
    providers = getattr(request.app.state, "storage_providers", {})
    providers.setdefault(target_storage.name, target_storage)

    result = migrate_legacy_documents(
        students=students,
        target_storage=target_storage,
        providers=providers,
        limit=limit if limit > 0 else None,
    )
    return {
        "message": "Legacy document migration completed",
        "target_provider": target_storage.name,
        "result": result,
    }

@router.get("/students/{department}")
async def get_students_by_department(
    department: str,
    current_user: dict = Depends(get_current_user)
):
    try:
        role = (current_user.get("role") or "").lower()
        normalized_department = department.lower()
        if normalized_department != "admin":
            try:
                normalized_department = normalize_branch_code(normalized_department)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid department code")

        normalized_role = role
        if role != "admin":
            try:
                normalized_role = normalize_branch_code(role)
            except ValueError:
                pass

        if normalized_role != "admin" and normalized_role != normalized_department:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to export this department's data"
            )

        # Function to fetch all data in chunks of 1000
        def fetch_all_students(query):
            all_data = []
            start = 0
            chunk_size = 1000
            
            while True:
                chunk = query.range(start, start + chunk_size - 1).execute()
                all_data.extend(chunk.data)

                if len(chunk.data) < chunk_size:
                    break  # No more data

                start += chunk_size
            return all_data

        # Build base query
        if normalized_department == "admin":
            query = supabase.table("students2025").select("*")
        else:
            query = (
                supabase.table("students2025")
                .select("*")
                .or_(f"degree_code.eq.{normalized_department.upper()},branch_code.eq.{normalized_department.upper()}")
            )

        students = fetch_all_students(query)
        students = [normalize_student_branch_fields(canonicalize_student_status(s)) for s in students]

        return {"students": students}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch students: {str(e)}")

@router.put("/student/{aadhaar_card_number}")
def update_student(
    aadhaar_card_number: str,
    updated_student: Student,
    current_user: dict = Depends(get_current_user),
):
    # Permission check
    if current_user.get("rights") == "Read Only":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have enough permissions"
        )

    student = fetch_student(aadhaar_card_number)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if not can_access_student_record(current_user, student):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this student",
        )
    
    # Convert Student model to dictionary
    student_dict = updated_student.model_dump()
    if student_dict.get("status"):
        student_dict["status"] = normalize_status(student_dict.get("status"))
        if not is_transition_allowed(student.get("status"), student_dict["status"]):
            raise HTTPException(
                status_code=409,
                detail=f"Invalid status transition: {normalize_status(student.get('status'))} -> {student_dict['status']}",
            )
    for field in ("branch_code", "degree_code"):
        if student_dict.get(field):
            try:
                student_dict[field] = normalize_branch_code(student_dict[field]).upper()
            except ValueError:
                pass
    student_dict["Time_updated"] = _db_datetime()

    try:
        # Attempt to update the student in Supabase
        response = (
            supabase.table("students2025")
            .update(student_dict)
            .eq("aadhaar_card_number", aadhaar_card_number)
            .execute()
        )

        if response.data:
            return {
                "message": "Student updated successfully",
                "data": response.data
            }
        else:
            raise HTTPException(status_code=404, detail="Student not found")

    except HTTPException:
        # Let explicit HTTPExceptions pass through
        raise
    except Exception as e:
        # Catch unexpected errors
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.get("/export-students/{department}")
async def export_students_excel(
    department: str,
    search_term: str = "",
    status_filter: str = "all",
    admission_category_filter: str = "all",
    current_user: dict = Depends(get_current_user)
):
    """Export filtered students as Excel file"""
    try:
        normalized_department = department.lower()
        if normalized_department != "admin":
            try:
                normalized_department = normalize_branch_code(normalized_department)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid department code")

        normalized_role = (current_user.get("role") or "").lower()
        if normalized_role != "admin":
            try:
                normalized_role = normalize_branch_code(normalized_role)
            except ValueError:
                pass

        # Verify user permissions
        if normalized_role != "admin" and normalized_role != normalized_department:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to export this department's data"
            )
        
        # Pagination helper
        def fetch_all_students(query):
            all_data = []
            start = 0
            chunk_size = 1000
            while True:
                chunk = query.range(start, start + chunk_size - 1).execute()
                all_data.extend(chunk.data or [])
                if not chunk.data or len(chunk.data) < chunk_size:
                    break
                start += chunk_size
            return all_data

        # Get students from database (with pagination)
        if normalized_department == "admin":
            base_query = supabase.table("students2025").select("*")
        else:
            base_query = supabase.table("students2025").select("*") \
                .or_(f"degree_code.eq.{normalized_department.upper()},branch_code.eq.{normalized_department.upper()}")

        students_data = fetch_all_students(base_query)
        
        # Apply filters (same logic as frontend)
        filtered_students = []
        for student in students_data:
            # Flatten student data if needed
            student_data = student.get('data', student)
            student_data = normalize_student_branch_fields(canonicalize_student_status(student_data))
            
            # Apply search filter
            if search_term and search_term.lower() not in student_data.get('student_name', '').lower():
                continue
                
            # Apply department filter
            if normalized_department != 'admin' and student_data.get('branch_code', '').lower() != normalized_department:
                continue
                
            # Apply status filter
            if status_filter != 'all' and student_data.get('status', '').lower() != status_filter:
                continue
                
            # Apply admission category filter
            if admission_category_filter != 'all' and student_data.get('admission_category', '').lower() != admission_category_filter.lower():
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
        filename = f"students_{normalized_department}_{timestamp}.xlsx"
        
        return Response(
            content=excel_file.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.post("/save-to-drive/{department}")
async def save_to_drive_sheet(
    department: str,
    search_term: str = "",
    status_filter: str = "all",
    admission_category_filter: str = "all",
    request: Request = None, 
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
        "roboticsandai": "1vybIqUdF-22H0kWg2H6g7OAHkuvDcJoeruN3QqSndPY",
        "admin":"1senxGU1NEjmcl63NXNniZz0hRfrEVGeoo9u3BKSBg2E"
    }

    try:
        normalized_department = department.lower()
        if normalized_department != "admin":
            try:
                normalized_department = normalize_branch_code(normalized_department)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid department code")

        normalized_role = (current_user.get("role") or "").lower()
        if normalized_role != "admin":
            try:
                normalized_role = normalize_branch_code(normalized_role)
            except ValueError:
                pass

        # Permissions
        if normalized_role != "admin" and normalized_role != normalized_department:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this department's sheet"
            )

        # Pagination helper
        def fetch_all_students(query):
            all_data = []
            start = 0
            chunk_size = 1000
            while True:
                chunk = query.range(start, start + chunk_size - 1).execute()
                all_data.extend(chunk.data or [])
                if not chunk.data or len(chunk.data) < chunk_size:
                    break
                start += chunk_size
            return all_data

        # Get students from database (with pagination)
        if normalized_department == "admin":
            base_query = supabase.table("students2025").select("*")
        else:
            base_query = supabase.table("students2025").select("*") \
                .or_(f"degree_code.eq.{normalized_department.upper()},branch_code.eq.{normalized_department.upper()}")
        students_data = fetch_all_students(base_query)

        # Apply filters
        filtered_students = []
        for student in students_data:
            student_data = student.get('data', student)
            student_data = normalize_student_branch_fields(canonicalize_student_status(student_data))
            if search_term and search_term.lower() not in student_data.get('student_name', '').lower():
                continue
            if normalized_department != 'admin' and student_data.get('branch_code', '').lower() != normalized_department:
                continue
            if status_filter != 'all' and student_data.get('status', '').lower() != status_filter:
                continue
            if admission_category_filter != 'all' and student_data.get('admission_category', '').lower() != admission_category_filter.lower():
                continue
            filtered_students.append(student_data)

        # Prepare data for sheet
        student_fields = list(Student.model_fields.keys())

        # Get Google Sheets service
        sheets_service = request.app.state.sheets_service
        if not sheets_service:
            raise HTTPException(status_code=500, detail="Sheets service not available")

        # Sheet name and range
        range_name = "Sheet1!A1:CZ3000"  # Adjust as needed

        # Prepare all rows: header + data
        header_row = [field.replace('_', ' ').title() for field in student_fields]
        all_rows = [header_row] + [
            [str(student.get(field, "")) for field in student_fields]
            for student in filtered_students
        ]

        # Overwrite the sheet with new data
        sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_IDs[normalized_department],
            range=range_name,
            valueInputOption="RAW",
            body={"values": all_rows}
        ).execute()

        return {"message": f"Sheet overwritten with {len(filtered_students)} students."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Save to drive failed: {str(e)}")
