from pydantic import BaseModel, EmailStr, constr
from typing import Optional, Dict

class Student(BaseModel):
    # Basic Info
    student_id: Optional[str] = ""
    degree_code: Optional[str] = ""
    hall_ticket_no: Optional[str] = ""
    name: Optional[str] = ""
    father_name: Optional[str] = ""
    mother_name: Optional[str] = ""
    date_of_birth: Optional[str] = ""
    gender: Optional[str] = ""
    identification_mark_1: Optional[str] = ""
    identification_mark_2: Optional[str] = ""
    
    # 10th Details
    tenth_board_name: Optional[str] = ""
    tenth_school_name: Optional[str] = ""
    tenth_hall_ticket_no: Optional[str] = ""
    tenth_max_marks: Optional[str] = ""
    tenth_total_marks: Optional[str] = ""
    tenth_percentage: Optional[str] = ""
    tenth_month_year: Optional[str] = ""
    
    # 12th Details
    twelfth_board_name: Optional[str] = ""
    twelfth_college_name: Optional[str] = ""
    twelfth_hall_ticket_no: Optional[str] = ""
    twelfth_max_marks: Optional[str] = ""
    twelfth_total_marks: Optional[str] = ""
    twelfth_percentage: Optional[str] = ""
    twelfth_subject_scores: Optional[Dict[str, int]] = {}  # Changed to Dict[str, str
    twelfth_month_year: Optional[str] = ""
    
    # Entrance Exams
    eamcet_hall_ticket_no: Optional[str] = ""
    eamcet_rank: Optional[str] = ""
    jee_hall_ticket_no: Optional[str] = ""
    jee_mains_rank: Optional[str] = ""
    
    # Personal Info
    aadhaar_card_number: Optional[str] = ""
    mother_tongue: Optional[str] = ""
    student_phone_no: Optional[str] = ""
    parent_phone_no: Optional[str] = ""
    vnr_email: Optional[str] = ""  # Changed from EmailStr
    student_email: Optional[str] = ""  # Changed from EmailStr
    parent_email: Optional[str] = ""  # Changed from EmailStr
    
    # Reservation & Category
    reservation: Optional[str] = ""  # Changed from bool
    category_name: Optional[str] = ""
    caste_as_per_tc: Optional[str] = ""
    ebc_status: Optional[str] = ""  # Changed from bool
    ews_status: Optional[str] = ""  # Changed from bool
    income: Optional[str] = ""  # Changed from int
    
    # Medical & Nationality
    blood_group: Optional[str] = ""
    nationality: Optional[str] = ""
    religion: Optional[str] = ""
    minority_status: Optional[str] = ""  # Changed from bool
    
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
    ph_status: Optional[str] = ""  # Changed from bool
    scribe_needed: Optional[str] = ""  # Changed from bool

    # Verification Status
    Status: Optional[str] = ""
    tenth_memo_link: Optional[str] = ""
    twelfth_memo_link: Optional[str] = ""
    aadhaar_card_link: Optional[str] = ""
    eamcet_link: Optional[str] = ""
    jee_link: Optional[str] = ""
    tc_link: Optional[str] = ""