from pydantic import BaseModel, EmailStr, constr
from typing import Optional, Union
from datetime import date, datetime  # Import date and datetime types
from google.cloud.firestore import SERVER_TIMESTAMP
from pydantic import BaseModel, EmailStr, constr
from typing import Optional

class Student(BaseModel):
    student_id: Optional[str] = ""
    degree_code: Optional[str] = ""
    hall_ticket_no: Optional[str] = ""
    name: Optional[str] = ""
    father_name: Optional[str] = ""
    mother_name: Optional[str] = ""
    date_of_birth: Optional[datetime] = None  # Store as YYYY-MM-DD format
    gender: Optional[str] = ""
    identification_mark_1: Optional[str] = ""
    identification_mark_2: Optional[str] = ""
    
    # 10th Details
    tenth_board_name: Optional[str] = ""
    tenth_school_name: Optional[str] = ""
    tenth_hall_ticket_no: Optional[str] = ""
    tenth_max_marks: Optional[int] = ""
    tenth_total_marks: Optional[str] = ""
    tenth_percentage: Optional[float] = ""
    tenth_month_year: Optional[str] = ""
    
    # 12th Details
    twelfth_board_name: Optional[str] = ""
    twelfth_college_name: Optional[str] = ""
    twelfth_hall_ticket_no: Optional[str] = ""
    twelfth_max_marks: Optional[int] = ""
    twelfth_total_marks: Optional[str] = ""
    twelfth_percentage: Optional[float] = ""
    twelfth_subject_scores: Optional[dict] = ""
    twelfth_month_year: Optional[str] = ""
    
    # Entrance Exams
    eamcet_hall_ticket_no: Optional[str] = ""
    eamcet_rank: Optional[int] = ""
    jee_hall_ticket_no: Optional[str] = ""
    jee_mains_rank: Optional[int] = ""
    
    # Personal Info
    aadhaar_card_number: Optional[str] = ""
    mother_tongue: Optional[str] = ""
    student_phone_no: Optional[str] = ""
    parent_phone_no: Optional[str] = ""
    vnr_email: Optional[EmailStr] = ""
    student_email: Optional[EmailStr] = ""
    parent_email: Optional[EmailStr] = ""
    
    # Reservation & Category
    reservation: Optional[bool] = ""
    category_name: Optional[str] = ""
    caste_as_per_tc: Optional[str] = ""
    ebc_status: Optional[bool] = ""
    ews_status: Optional[bool] = ""
    income: Optional[int] = ""
    
    # Medical & Nationality
    blood_group: Optional[str] = ""
    nationality: Optional[str] = ""
    religion: Optional[str] = ""
    minority_status: Optional[bool] = ""
    
    # Address
    address_door_no: Optional[str] = ""
    address_street: Optional[str] = ""
    address_village_town: Optional[str] = ""
    address_mandal: Optional[str] = ""
    address_district: Optional[str] = ""
    address_state: Optional[str] = ""
    address_pincode: Optional[str] = ""
    rural_urban: Optional[str] = ""
    
    # College Details
    admission_category: Optional[str] = ""
    section: Optional[str] = ""
    branch_code: Optional[str] = ""
    college_code: Optional[str] = ""
    
    # Special Status
    ph_status: Optional[bool] = ""
    scribe_needed: Optional[bool] = ""

    # Verification Status
    Status : Optional[str] = "" 
    tenth_memo_link: Optional[str] = ""
    twelfth_memo_link: Optional[str] = ""
    aadhaar_card_link: Optional[str] = ""
    eamcet_link: Optional[str] = ""
    jee_link: Optional[str] = ""
    tc_link: Optional[str] = ""