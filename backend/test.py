from GoogleService import authenticate_service_account, download_image_from_drive,read_google_sheet
from googleapiclient.discovery import build
from database import supabase
from models.SheetModelLE import SheetStudentLE
from models.StudentModel import Student
import asyncio
import logging


from extractor import extract,prompts
GEMINI_SEMAPHORE = asyncio.Semaphore(30)  # Adjust based on rate limits
SUBTASK_SEMAPHORE = asyncio.Semaphore(10)  # Control subtask throughput

credentials = authenticate_service_account()

sheets_service=build('sheets', 'v4', credentials=credentials)
drive_service=build('drive', 'v3', credentials=credentials)


async def process_student(student_data: SheetStudentLE, branch: str):
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
            extract(link, prompt, drive_service)
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


def safe_get(result, key):
    if isinstance(result, Exception):
        return ""
    return str(result.get(key) or "")





async def sync():
    """Process all subtasks with progress tracking"""
    try:
       
        data_from_sheets = read_google_sheet(sheets_service,"1fJ6nY_FtS4EY4c0tewN-IG6Ub9TcEdFtQ-shPu7XnP0",'Sheet1!C2:AS4')

        if data_from_sheets is None:
            data_from_sheets = []

        print("Data from sheets:", data_from_sheets)
        h
        no_of_students = len(data_from_sheets)

        for i, student in enumerate(data_from_sheets):
            row = student
            field_names = list(SheetStudentLE.model_fields.keys())
            flatstudent_dict = dict(zip(field_names, row))
            student = SheetStudentLE(**flatstudent_dict)
            async with SUBTASK_SEMAPHORE:
                subtask_result = await process_student(student)
                
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

if __name__ == "__main__":
    asyncio.run(sync())