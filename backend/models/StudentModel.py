from pydantic import BaseModel, EmailStr, constr
from typing import Optional, Union

class Student(BaseModel):
    student_id: Optional[str] = ""
    degree_code: Optional[str] = ""
    hall_ticket_no: Optional[str] = ""
    name: Optional[str] = ""
    father_name: Optional[str] = ""
    mother_name: Optional[str] = ""
    date_of_birth: Optional[str] = ""  # Store as YYYY-MM-DD format
    gender: Optional[str] = ""
    identification_mark_1: Optional[str] = ""
    identification_mark_2: Optional[str] = ""
    
    # 10th Details
    tenth_board_name: Optional[str] = ""
    tenth_school_name: Optional[str] = ""
    tenth_hall_ticket_no: Optional[str] = ""
    tenth_max_marks: Optional[Union[int, str]] = None
    tenth_total_marks: Optional[str] = ""   
    tenth_percentage: Optional[float] = ""
    tenth_month_year: Optional[str] = ""
    
    # 12th Details
    twelfth_board_name: Optional[str] = ""
    twelfth_college_name: Optional[str] = ""
    twelfth_hall_ticket_no: Optional[str] = ""
    twelfth_max_marks: Optional[Union[int, str]] = None
    twelfth_total_marks: Optional[str] = ""
    twelfth_percentage: Optional[float] = ""
    twelfth_subject_scores: Optional[dict] = ""
    twelfth_month_year: Optional[str] = ""
    
    # Entrance Exams
    eamcet_hall_ticket_no: Optional[str] = ""
    eamcet_rank: Optional[Union[int, str]] = None
    jee_hall_ticket_no: Optional[str] = ""
    jee_mains_rank: Optional[Union[int, str]] = None
    
    # Personal Info
    aadhaar_card_number: Optional[str] = ""
    mother_tongue: Optional[str] = ""
    student_phone_no: Optional[str] = ""
    parent_phone_no: Optional[str] = ""
    vnr_email: Optional[EmailStr] = ""
    student_email: Optional[EmailStr] = ""
    parent_email: Optional[EmailStr] = ""
    
    # Reservation & Category
    reservation: Optional[Union[bool, str]] = None
    category_name: Optional[str] = ""
    caste_as_per_tc: Optional[str] = ""
    ebc_status: Optional[Union[bool, str]] = None
    ews_status: Optional[Union[bool, str]] = None
    income: Optional[Union[int, str]] = None
    
    # Medical

# Firebase Security Rules