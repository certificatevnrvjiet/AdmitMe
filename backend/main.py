from database import db
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from models.FormModel import FormModel
from models.StudentModel import Student
from extractor import extract,prompts
import uuid
import re
from GoogleAuthService import authenticate_google_service, download_image_from_drive

app = FastAPI()

# Add after FastAPI initialization
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        inter_details = extract(form_data["twelfthMarksMemo"],prompts[5])
        
        # Create a unique student ID using UUID
        student_id = str(uuid.uuid4())
        
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
            tenth_max_marks=(tenth_details["tenth_max_marks/CGPA"]),
            tenth_total_marks=tenth_details["tenth_total_marks/CGPA"],
            tenth_percentage=(tenth_details["tenth_percentage"]),
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
            twelfth_max_marks=(inter_details["Max Marks"]),
            twelfth_total_marks=inter_details["Total Marks"],
            twelfth_percentage=(inter_details["Percentage"]),
            twelfth_month_year=inter_details["Month_year"],
            twelfth_subject_scores=inter_details["Subject Scores"],
            tenth_memo_link=re.search(r'id=([a-zA-Z0-9_-]+)', form_data["tenthMarksMemo"]).group(1),
            twelfth_memo_link=re.search(r'id=([a-zA-Z0-9_-]+)', form_data["twelfthMarksMemo"]).group(1),
            aadhaar_card_link=re.search(r'id=([a-zA-Z0-9_-]+)', form_data["aadhaarCard"]).group(1),
            eamcet_link=re.search(r'id=([a-zA-Z0-9_-]+)', form_data["tgEAPCETRank"]).group(1),
            jee_link=re.search(r'id=([a-zA-Z0-9_-]+)', form_data["jeeMainRank"]).group(1),
            tc_link=re.search(r'id=([a-zA-Z0-9_-]+)', form_data["transferCertificate"]).group(1),
        )
        
        # Convert student object to dictionary
        student_dict = student.dict(exclude_none=True)
        
        try:
            # Store in Firestore
            doc_ref = db.collection('studentsdemo').document(student_id)
            doc_ref.set(student_dict)
            
            print("\n=== Student Details Stored in Firebase ===")
            print(f"Document ID: {student_id}")
            print("====================\n")
            
            return {
                "message": "Data Processed and Stored successfully",
                "student_id": student_id,
                "data": student_dict
            }
            
        except Exception as firebase_error:
            print(f"Firebase Error: {firebase_error}")
            raise HTTPException(
                status_code=500,
                detail=f"Error storing data in Firebase: {str(firebase_error)}"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add a new endpoint to retrieve student data
@app.get("/student/{student_id}")
async def get_student(student_id: str):
    try:
        doc_ref = db.collection('studentsdemo').document(student_id)
        doc = doc_ref.get()
        
        if doc.exists:
            return {"data": doc.to_dict()}
        else:
            raise HTTPException(status_code=404, detail="Student not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/drive/image/{file_id}")
async def get_drive_image(file_id: str):
    image_bytes = download_image_from_drive(file_id)
    if image_bytes:
        # Determine the content type (you might need to fetch file metadata for a more reliable type)
        service = authenticate_google_service(DRIVE_SCOPES, token_file='drive_token.pickle', credentials_file='credentials.json', api_name='drive', api_version='v3')
        content_type = "image/jpeg"  # Default
        if service:
            try:
                file_metadata = service.files().get(fileId=file_id, fields='mimeType').execute()
                content_type = file_metadata.get('mimeType', 'image/jpeg')
            except Exception as e:
                print(f"Error getting file metadata: {e}")
        return Response(content=image_bytes, media_type=content_type)
    else:
        raise HTTPException(status_code=404, detail="Image not found or could not be downloaded from Google Drive")
