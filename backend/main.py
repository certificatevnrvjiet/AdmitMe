from database import db
from fastapi import FastAPI, HTTPException, Response, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from models.FormModel import FormModel
from models.StudentModel import Student
from extractor import extract,prompts
import uuid
import re
from GoogleAuthService import authenticate_google_service, download_image_from_drive
from datetime import datetime  # Import datetime for date conversion
from google.cloud import firestore
from google.cloud.firestore import SERVER_TIMESTAMP
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
import uvicorn
from jose import JWTError, jwt


app = FastAPI()

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10

print("Started")
# Add after FastAPI initialization
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
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
        board = form_data["twelfthBoard"]
        if board == "State":
            inter_details = extract(form_data["twelfthMarksMemo"],prompts[4])
        elif board == "AS and A Level":
            inter_details = extract(form_data["twelfthMarksMemo"],prompts[5])
        elif board == "ISC":
            inter_details = extract(form_data["twelfthMarksMemo"],prompts[6])
        elif board == "CBSE":
            inter_details = extract(form_data["twelfthMarksMemo"],prompts[7])
        else:
            raise HTTPException(status_code=400, detail="Unknown board type")

        # Create a unique student ID using UUID
        student_id = str(uuid.uuid4())
        
        # Simply store the date string without conversion
        dob_str = tenth_details["Date of Birth"]  # Already in DD/MM/YYYY format

        # Create Student object and map address fields
        student = Student(
            name=tenth_details["Candidate Name"],
            father_name=tenth_details["Father Name"],
            mother_name=tenth_details["Mother Name"],
            date_of_birth=dob_str,  # Store as string directly
            identification_mark_1=tenth_details["identification_marks1"],
            identification_mark_2=tenth_details["identification_marks2"],
            tenth_board_name=tenth_details["tenth_board_name"],
            tenth_school_name=tenth_details["tenth_school_name"],
            tenth_hall_ticket_no=tenth_details["tenth_hall_ticket_no"],
            tenth_max_marks=(tenth_details["tenth_max_marks/CGPA"]),
            tenth_total_marks=tenth_details["tenth_total_marks/CGPA"],
            tenth_percentage=(tenth_details["tenth_percentage"]),
            tenth_month_year=tenth_details["tenth_month_year"],
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
            twelfth_max_marks=str(inter_details["Max Marks"]),
            twelfth_total_marks=str(inter_details["Total Marks"]),
            twelfth_percentage=str(inter_details["Percentage"]),
            twelfth_month_year=inter_details["Month_year"],
            twelfth_subject_scores=inter_details["Subject Scores"],
            tenth_memo_link=re.search(r'id=([a-zA-Z0-9_-]+)', form_data["tenthMarksMemo"]).group(1),
            twelfth_memo_link=re.search(r'id=([a-zA-Z0-9_-]+)', form_data["twelfthMarksMemo"]).group(1),
            aadhaar_card_link=re.search(r'id=([a-zA-Z0-9_-]+)', form_data["aadhaarCard"]).group(1),
            eamcet_link=re.search(r'id=([a-zA-Z0-9_-]+)', form_data["tgEAPCETRank"]).group(1),
            jee_link=re.search(r'id=([a-zA-Z0-9_-]+)', form_data["jeeMainRank"]).group(1),
            tc_link=re.search(r'id=([a-zA-Z0-9_-]+)', form_data["transferCertificate"]).group(1),
            Status="Not Verified",
        )
        print(student)
        # Convert student object to dictionary
        student_dict = student.dict(exclude_none=True)
        print(student_dict)
        # Store in Firestore (it will automatically convert datetime to Timestamp)
        doc_ref = db.collection('studentsdemo').document(student_id)
        doc_ref.set(student_dict)
        
        return {
            "message": "Data Processed and Stored successfully",
            "student_id": student_id,
            "data": student_dict
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/student/{student_id}")
async def get_student(student_id: str):
    try:
        doc_ref = db.collection('studentsdemo').document(student_id)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            # No need to convert date_of_birth as it's already a string
            return {"data": data}
        else:
            raise HTTPException(status_code=404, detail="Student not found")
            
    except Exception as e:
        print(f"Error retrieving student: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/student/{student_id}")
async def update_student(student_id: str, student: Student):
    try:
        # Check if student exists
        doc_ref = db.collection('studentsdemo').document(student_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Convert student model to dict and exclude None values
        student_dict = student.dict(exclude_none=True, exclude_unset=True)
        
        # Remove id field if present
        student_dict.pop('id', None)
        
        # Handle date_of_birth format validation
        if student_dict.get('date_of_birth'):
            try:
                # Validate date format without converting to datetime
                if not re.match(r'^\d{2}/\d{2}/\d{4}$', student_dict['date_of_birth']):
                    raise ValueError("Date format should be DD/MM/YYYY")
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid date format. Please use DD/MM/YYYY format: {str(e)}"
                )
        
        # Update document in Firestore
        doc_ref.update(student_dict)
        
        return {
            "message": "Student updated successfully",
            "student_id": student_id,
            "data": student_dict
        }
        
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        print(f"Error updating student: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/students")
async def get_students():
    try:
        students_ref = db.collection('studentsdemo')
        docs = students_ref.stream()
        students = []
        for doc in docs:
            data = doc.to_dict()
            # Convert Firestore Timestamp to string format
            # if data.get('date_of_birth'):
            #     timestamp = data['date_of_birth']
            #     if hasattr(timestamp, 'timestamp'):
            #         dt = datetime.fromtimestamp(timestamp.timestamp())
            #         data['date_of_birth'] = dt.strftime('%d/%m/%Y')
            
            # Handle NaN values
            # cleaned_data = {}
            # for key, value in data.items():
            #     if isinstance(value, float) and (value != value):  # Check for NaN
            #         cleaned_data[key] = None
            #     else:
            #         cleaned_data[key] = value
            
            students.append({
                'id': doc.id,
                **data
            })
        
        return {
            "status": "success",
            "students": students
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching students: {str(e)}"
        )

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

@app.get("/test-connection")
async def test_connection():
    try:
        # Try to read from Firestore
        docs = db.collection('studentsdemo').limit(1).stream()
        next(docs, None)
        return {"status": "success", "message": "Firebase connection successful"}
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Firebase connection failed: {str(e)}"
        )

# Update the test_date endpoint
@app.post("/test-date")
async def test_date_handling(data: DateTest):
    try:
        # Convert string date to datetime object using DD/MM/YYYY format
        date_obj = datetime.strptime(data.test_date, "%d/%m/%Y")
        
        # Create document data using datetime directly
        doc_data = {
            "test_date": date_obj,  # Firestore automatically converts datetime to Timestamp
            "description": data.description,
            "created_at": SERVER_TIMESTAMP
        }
        print(type(doc_data["test_date"]))
        # Store in test collection
        doc_ref = db.collection('date_tests').document()
        doc_ref.set(doc_data)
        
        return {
            "status": "success",
            "message": "Date stored successfully",
            "doc_id": doc_ref.id,
            "data": {
                "test_date": date_obj.strftime("%d/%m/%Y"),  # Return in same format
                "description": data.description
            }
        }
    except ValueError as ve:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format. Please use DD/MM/YYYY format (e.g., 01/01/2005)"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error storing date: {str(e)}"
        )


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
    return {"message": current_user['username'],"role":current_user['role']}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)