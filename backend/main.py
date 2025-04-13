from database import db
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models.FormModel import FormModel
from models.StudentModel import Student
from extractor import extract,prompts

app = FastAPI()

DRIVE_SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

@app.post("/submit")
async def receive_form_data(data: FormModel):
    try:
        # Convert FormModel to dict
        form_data = data.dict()
        tenth_details = extract(form_data["tenthMarksMemo"],prompts[0])
        uidai_details = extract(form_data["aadhaarCard"],prompts[1])
        eamcet_details = extract(form_data["tgEAPCETRank"],prompts[2])
        jee_details = extract(form_data["jeeMainRank"],prompts[2])
        tc_details = extract(form_data["transferCertificate"],prompts[3])
        inter_details = extract(form_data["twelfthMarksMemo"],prompts[4])
        
        # Create Student object and map address fields
        student = Student(
            name=tenth_details["Candidate Name"],
            father_name=tenth_details["Father Name"],
            mother_name=tenth_details["Mother Name"],
            date_of_birth=tenth_details["Date of Birth"],
            identification_mark_1=tenth_details["identification_marks1"],
            identification_mark_2=tenth_details["identification_marks2"],
            tenth_board_name=tenth_details["tenth_board_name"],
            tenth_school_name=tenth_details["tenth_school_name"],
            tenth_hall_ticket_no=tenth_details["tenth_hall_ticket_no"],
            tenth_max_marks=float(tenth_details["tenth_max_marks/CGPA"]),
            tenth_total_marks=tenth_details["tenth_total_marks/CGPA"],
            tenth_percentage=float(tenth_details["tenth_percentage"]),
            tenth_month_year=tenth_details["tenth_month_year"],
            # ...existing fields mapping...
            address_street=form_data["address"]["street"],
            address_village_town=form_data["address"]["village"],
            address_mandal=form_data["address"]["mandal"],
            address_district=form_data["address"]["district"],
            address_state=form_data["address"]["state"],
            address_pincode=form_data["address"]["pincode"],
            branch_code=form_data["branch"],
            admission_category=form_data["admissionCategory"],
            student_phone_no=form_data["phone"],
            parent_phone_no=form_data["parentPhone"],
            student_email=form_data["email"],
            parent_email=form_data["parentEmail"],
            blood_group=form_data["bloodGroup"],
            college_code='07',
            gender=uidai_details["Gender"],
            aadhaar_card_number=uidai_details["Number"],
            eamcet_hall_ticket_no=eamcet_details["HT Number"],
            eamcet_rank=eamcet_details["Rank"],
            jee_hall_ticket_no=jee_details["HT Number"],
            jee_mains_rank=jee_details["Rank"],
            mother_tongue=tc_details["Mother Tongue"],
            religion=tc_details["Religion"],
            caste_as_per_tc=tc_details["Caste as per TC"],
            nationality=tc_details["Nationality"],
            twelfth_college_name=tc_details["College Name"],
            twelfth_board_name=inter_details["Board Name"],
            twelfth_hall_ticket_no=inter_details["Hall Ticket Number"],
            twelfth_max_marks=float(inter_details["Max Marks"]),
            twelfth_total_marks=inter_details["Total Marks"],
            twelfth_percentage=float(inter_details["Percentage"]),
            twelfth_month_year=inter_details["Month_year"],
            twelfth_subject_scores=inter_details["Subject Scores"],
        )
        
        
         # Print student details in a formatted way
        print("\n=== Student Details ===")
        student_dict = student.dict(exclude_none=True)  # Only print non-None values
        for key, value in student_dict.items():
            print(f"{key}: {value}")
        print("====================\n")
        
        return {"message": "Data Processed successfully", "data": student.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
