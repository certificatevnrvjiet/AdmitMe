from GoogleService import authenticate_service_account, download_image_from_drive,read_google_sheet
from googleapiclient.discovery import build
from database import supabase
from models.SheetModelLE import SheetStudentLE
from models.StudentModel import Student
import asyncio
import logging

Management_spreadsheet_Id="1wn9mqz7HY-cnVdxS4Z0tLF061HJoFi_VrV1ZFjjXwp8"


def get_short_form(full_form):
    mapping = {
        "AIDS - Artificial Intelligence  & Data Science": "aids",
        "AE - Automobile Engineering": "ae",
        "CE - Civil Engineering": "ce",
        "CSBS - Computer Science & Business Systems": "csbs",
        "CSE - Computer Science & Engineering": "cse",
        "AIML - Artificial Intelligence & Machine Learning": "aiml",
        "CSE - DS - Data Science": "cseds",
        "CSE - CyS - Cyber Security": "csecys",
        "CSE - IOT - Internet of Things": "cseiot",
        "EEE - Electrical & Electronics Engineering": "eee",
        "ECE - Electronics & Communication Engineering": "ece",
        "EIE - Electronics & Instrumentation Engineering": "eie",
        "IT - Information Technology": "it",
        "ME - Mechanical Engineering": "me",
        "RAI - Robotics & AI": "rai",
        "VLSI": "vlsi",
        "BIOT - Bio Technology": "biot",
        "ADMIN - Administration": "admin"
    }
    return mapping.get(full_form)

  # Output: me


from extractor import extract,prompts
GEMINI_SEMAPHORE = asyncio.Semaphore(30)  # Adjust based on rate limits
SUBTASK_SEMAPHORE = asyncio.Semaphore(10)  # Control subtask throughput

credentials = authenticate_service_account()

sheets_service=build('sheets', 'v4', credentials=credentials)
drive_service=build('drive', 'v3', credentials=credentials)


async def process_student(student_data: SheetStudentLE, branch: str):
    print("\nStrted Extracting......")
    """Process 6 extract calls in parallel for one subtask"""
    print("started processing student", student_data.name_of_the_student)
    student = Student.from_flat_leStudent(student_data)
    branch=get_short_form(branch)
    student.degree_code = branch.upper()
    student.branch_code = branch.upper()
    student.status = "Not Viewed"
    board = student.twelfth_board_name
    prompt = prompts[-1]  # Default prompt for most boards
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
        Scores = results[1].get("Subject Scores", {}) if isinstance(results[1], dict)  else {}
        if Scores is None or not isinstance(Scores, dict):
            Scores = {}
        # print("Scores  : ",Scores)
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
        student.twelfth_maximum_marks = "10"
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
        # print("Processing student:", student.model_dump_json(indent=2))
        student_dict = student.model_dump()
        # print(student_dict)
        # for i in student_dict:
        #     print(i,student_dict[i])
        # Insert into Supabase
        response = supabase.table("students2025").insert(student_dict).execute()
        # print(response)


def safe_get(result, key):
    if isinstance(result, Exception):
        return ""
    return str(result.get(key) or "")





async def sync():
    """Process all subtasks with progress tracking"""
    try:
       
        data_from_sheets = read_google_sheet(sheets_service,Management_spreadsheet_Id,'Sheet1!C2:AZ700')
        seen = set()
        filtered_data = []
        for row in reversed(data_from_sheets):
            key = row[5]
            if key not in seen:
                seen.add(key)
                filtered_data.append(row)

        # Reverse back to restore original order
        data_from_sheets = list(reversed(filtered_data))
        # print(len(data_from_sheets))
        # u909
        if data_from_sheets is None:
            data_from_sheets = []
            
        aadhaar_cards=supabase.table("students2025").select("aadhaar_card_number").execute().data

        # aadharindex=data_from_sheets[0].index("Aadhaar Card Number")
        aadhaar_cards=[i["aadhaar_card_number"] for i in aadhaar_cards]
        # print("\naadhaar cards in db",len(aadhaar_cards))

        data_from_sheets = [row for row in data_from_sheets if row[5] not in aadhaar_cards]  # Filter out already synced students

        # print("Data from sheets:", data_from_sheets[1])
        # h
        # print(len(data_from_sheets))
        # lkjhgfd
        for i, student in enumerate(data_from_sheets):
            row = student
            field_names = list(SheetStudentLE.model_fields.keys())
            flatstudent_dict = dict(zip(field_names, row))
            student = SheetStudentLE(**flatstudent_dict)
            # print()
            # for i in student:
            #     print(i)
            # print()
            # h
            async with SUBTASK_SEMAPHORE:
                subtask_result = await process_student(student,student.branch_opted)
                
                # Update progress every 10% of tasks
                # if (i + 1) % max(1, no_of_students // 10) == 0:
                #     progress = int(((i + 1) / no_of_students) * 100)
                #     supabase.table("tasks").update({
                #         "progress": progress
                #     }).eq("id", task_id).execute()
        
        # Final update

    except Exception as e:
       print(e)
if __name__ == "__main__":
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

    print(len(aadhaar_cards))