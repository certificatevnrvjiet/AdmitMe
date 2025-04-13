from pydantic import BaseModel, EmailStr, constr
from typing import Optional

class Student(BaseModel):
    student_id: Optional[str] = None
    degree_code: Optional[str] = None
    hall_ticket_no: Optional[str] = None
    name: Optional[str] = None
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    date_of_birth: Optional[str] = None  # Store as YYYY-MM-DD format
    gender: Optional[str] = None
    identification_mark_1: Optional[str] = None
    identification_mark_2: Optional[str] = None
    
    # 10th Details
    tenth_board_name: Optional[str] = None
    tenth_school_name: Optional[str] = None
    tenth_hall_ticket_no: Optional[str] = None
    tenth_max_marks: Optional[int] = None
    tenth_total_marks: Optional[str] = None
    tenth_percentage: Optional[float] = None
    tenth_month_year: Optional[str] = None
    
    # 12th Details
    twelfth_board_name: Optional[str] = None
    twelfth_college_name: Optional[str] = None
    twelfth_hall_ticket_no: Optional[str] = None
    twelfth_max_marks: Optional[int] = None
    twelfth_total_marks: Optional[str] = None
    twelfth_percentage: Optional[float] = None
    twelfth_subject_scores: Optional[dict] = None
    twelfth_month_year: Optional[str] = None
    
    # Entrance Exams
    eamcet_hall_ticket_no: Optional[str] = None
    eamcet_rank: Optional[int] = None
    jee_hall_ticket_no: Optional[str] = None
    jee_mains_rank: Optional[int] = None
    
    # Personal Info
    aadhaar_card_number: Optional[str] = None
    mother_tongue: Optional[str] = None
    student_phone_no: Optional[str] = None
    parent_phone_no: Optional[str] = None
    vnr_email: Optional[EmailStr] = None
    student_email: Optional[EmailStr] = None
    parent_email: Optional[EmailStr] = None
    
    # Reservation & Category
    reservation: Optional[bool] = None
    category_name: Optional[str] = None
    caste_as_per_tc: Optional[str] = None
    ebc_status: Optional[bool] = None
    ews_status: Optional[bool] = None
    income: Optional[int] = None
    
    # Medical & Nationality
    blood_group: Optional[str] = None
    nationality: Optional[str] = None
    religion: Optional[str] = None
    minority_status: Optional[bool] = None
    
    # Address
    address_door_no: Optional[str] = None
    address_street: Optional[str] = None
    address_village_town: Optional[str] = None
    address_mandal: Optional[str] = None
    address_district: Optional[str] = None
    address_state: Optional[str] = None
    address_pincode: Optional[str] = None
    rural_urban: Optional[str] = None
    
    # College Details
    admission_category: Optional[str] = None
    section: Optional[str] = None
    branch_code: Optional[str] = None
    college_code: Optional[str] = None
    
    # Special Status
    ph_status: Optional[bool] = None
    scribe_needed: Optional[bool] = None

    # Verification Status
    Status : Optional[str] = None 
    tenth_memo_link: Optional[str] = None
    twelfth_memo_link: Optional[str] = None
    aadhaar_card_link: Optional[str] = None
    eamcet_link: Optional[str] = None
    jee_link: Optional[str] = None
    tc_link: Optional[str] = None
