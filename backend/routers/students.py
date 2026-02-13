from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from io import BytesIO
from openpyxl import Workbook
from datetime import datetime
from services.auth_service import get_current_user
from database import supabase
from models.StudentModel import Student
from GoogleService import download_image_from_drive

router = APIRouter()

# In-memory cache for file_id to image bytes
image_cache: Dict[str, bytes] = {}

@router.get("/image/{file_id}")
async def get_image(
    file_id: str,
    request: Request
):
    """Serve images from Google Drive by file ID, with in-memory caching"""
    try:
        if not hasattr(request.app.state, 'drive_service') or not request.app.state.drive_service:
            # Try to init if missing or just fail gracefully? 
            # In lifespan we init it. If it failed there, it's None.
             raise HTTPException(status_code=500, detail="Drive service not available")
  
        # Check cache first
        if file_id in image_cache:
            # print("Cache hit for file_id:", file_id)
            image_bytes = image_cache[file_id]
        else:
            # Download image from Google Drive
            image_bytes = await download_image_from_drive(file_id, request.app.state.drive_service)
            if image_bytes:
                image_cache[file_id] = image_bytes  # Cache the result
                if len(image_cache) > 99:
                    image_cache.clear()
        
        if not image_bytes:
            raise HTTPException(status_code=404, detail="Image not found or could not be downloaded")
        
        return Response(
            content=image_bytes,
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=3600"}  # Cache for 1 hour
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve image: {str(e)}")

@router.get("/students/{department}")
async def get_students_by_department(
    department: str,
    current_user: dict = Depends(get_current_user)
):
    try:
        if current_user["role"] != "admin" and current_user["role"] != department:
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
        if department.lower() == "admin":
            query = supabase.table("students2025").select("*")
        else:
            query = (
                supabase.table("students2025")
                .select("*")
                .or_(f"degree_code.eq.{department.upper()},branch_code.eq.{department.upper()}")
            )

        students = fetch_all_students(query)

        return {"students": students}

    except Exception as e:
        return {"error": str(e)}

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
    
    # Convert Student model to dictionary
    student_dict = updated_student.model_dump()
    student_dict["Time_updated"] = datetime.utcnow().isoformat() + "Z"

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
        # Verify user permissions
        if current_user["role"] != "admin" and current_user["role"] != department:
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
        if department.lower() == "admin":
            base_query = supabase.table("students2025").select("*")
        else:
            base_query = supabase.table("students2025").select("*") \
                .or_(f"degree_code.eq.{department.upper()},branch_code.eq.{department.upper()}")

        students_data = fetch_all_students(base_query)
        
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
        filename = f"students_{department}_{timestamp}.xlsx"
        
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
        # Permissions
        if current_user["role"] != "admin" and current_user["role"] != department:
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
        if department.lower() == "admin":
            base_query = supabase.table("students2025").select("*")
        else:
            base_query = supabase.table("students2025").select("*") \
                .or_(f"degree_code.eq.{department.upper()},branch_code.eq.{department.upper()}")
        students_data = fetch_all_students(base_query)

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
            spreadsheetId=SPREADSHEET_IDs[department.lower()],
            range=range_name,
            valueInputOption="RAW",
            body={"values": all_rows}
        ).execute()

        return {"message": f"Sheet overwritten with {len(filtered_students)} students."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Save to drive failed: {str(e)}")
