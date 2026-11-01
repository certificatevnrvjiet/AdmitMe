from typing import Optional
from pydantic import BaseModel
from models.SheetModel import SheetStudent
from models.SheetModelLE import SheetStudentLE
from models.SheetModelB import SheetModelB
from models.Admissions2026 import Admissions2026Applicant
from datetime import datetime

class Student(BaseModel):
    ht_no: Optional[str] = ""
    student_name: Optional[str] = ""
    father_name: Optional[str] = ""
    mother_name: Optional[str] = ""
    date_of_birth: Optional[str] = ""
    gender: Optional[str] = ""
    identification_mark_1: Optional[str] = ""
    identification_mark_2: Optional[str] = ""
    tenth_board_name: Optional[str] = ""
    tenth_school_name: Optional[str] = ""
    tenth_district_code: Optional[str] = ""
    tenth_ht_no: Optional[str] = ""
    tenth_maximum_marks: Optional[str] = ""
    tenth_total_marks_cgpa: Optional[str] = ""
    tenth_percentage: Optional[str] = ""
    tenth_month_year: Optional[str] = ""
    twelfth_board_name: Optional[str] = ""
    twelfth_college_name: Optional[str] = ""
    twelfth_district_code: Optional[str] = ""
    twelfth_ht_no: Optional[str] = ""
    twelfth_maximum_marks: Optional[str] = ""
    twelfth_total_marks: Optional[str] = ""
    twelfth_percentage: Optional[str] = ""
    m1: Optional[str] = ""
    m2: Optional[str] = ""
    m3: Optional[str] = ""
    m4: Optional[str] = ""
    p1: Optional[str] = ""
    p2: Optional[str] = ""
    ch1: Optional[str] = ""
    ch2: Optional[str] = ""
    plab: Optional[str] = ""
    chlab: Optional[str] = ""
    total: Optional[str] = ""
    twelfth_groups_percentage: Optional[str] = ""
    twelfth_month_year: Optional[str] = ""
    eapcet_ht_no: Optional[str] = ""
    eapcet_rank: Optional[str] = ""
    jee_ht_no: Optional[str] = ""
    jee_mains_rank: Optional[str] = ""
    aadhaar_card_number: Optional[str] = ""
    mother_tongue: Optional[str] = ""
    student_phone: Optional[str] = ""
    parent_phone: Optional[str] = ""
    parent_email: Optional[str] = ""
    father_phone: Optional[str] = ""
    mother_phone: Optional[str] = ""
    student_passport_no: Optional[str] = ""
    father_passport_no: Optional[str] = ""
    mother_passport_no: Optional[str] = ""
    vnr_email: Optional[str] = ""
    student_email: Optional[str] = ""
    father_email: Optional[str] = ""
    mother_email: Optional[str] = ""
    father_profession_and_designation: Optional[str] = ""
    mother_profession_and_designation: Optional[str] = ""
    reservation: Optional[str] = ""
    category_name: Optional[str] = ""
    caste_as_per_tc: Optional[str] = ""
    ebc_status: Optional[str] = ""
    ews_status: Optional[str] = ""
    income: Optional[str] = ""
    blood_group: Optional[str] = ""
    nationality: Optional[str] = ""
    religion: Optional[str] = ""
    minority: Optional[str] = ""
    address_dno: Optional[str] = ""
    address_street: Optional[str] = ""
    address_village_town: Optional[str] = ""
    address_mandal: Optional[str] = ""
    address_district: Optional[str] = ""
    address_state: Optional[str] = ""
    address_pincode: Optional[str] = ""
    rural_urban: Optional[str] = ""
    admission_category: Optional[str] = ""
    section: Optional[str] = ""
    branch: Optional[str] = ""
    college_code: Optional[str] = "07"
    ph_status: Optional[str] = ""
    scribe: Optional[str] = ""
    status: Optional[str] = ""
    candidate_pic: Optional[str] = ""
    allotment_order: Optional[str] = ""
    joining_report: Optional[str] = ""
    aadhaar_link: Optional[str] = ""
    transfer_certificate_link: Optional[str] = ""
    tenth_memo_link: Optional[str] = ""
    twelfth_memo_link: Optional[str] = ""
    jee_rank_card_link: Optional[str] = ""
    eapcet_rank_card_link: Optional[str] = ""
    consent: Optional[str] = ""
    student_type: Optional[str]=""
    Time_updated: Optional[datetime] = None  # Timestamp for last update
    extraction_status: Optional[str] = "pending"

    @classmethod
    def from_admissions2026(cls, applicant: Admissions2026Applicant) -> 'Student':
        """Create a database student from the canonical 2026 admission DTO."""
        return cls(**applicant.to_student_record(branch=applicant.branch or ""))

    @classmethod
    def from_flat_student(cls, flat_student: SheetStudent) -> 'Student':
        return cls(
            student_name=flat_student.name_of_the_student,
            father_name=flat_student.fathers_name,
            mother_name=flat_student.mothers_name,
            date_of_birth=flat_student.date_of_birth,
            gender=flat_student.gender,
            aadhaar_card_number=flat_student.aadhaar_card_number,
            
            # Exam Details
            eapcet_ht_no=flat_student.eapcet_hall_ticket_no,
            eapcet_rank=flat_student.eapcet_rank,
            jee_ht_no=flat_student.jee_hall_ticket_no,
            jee_mains_rank=flat_student.jee_crl_rank,
            
            # Personal Info
            mother_tongue=flat_student.mother_tongue,
            religion=flat_student.religion,
            nationality=flat_student.nationality,
            
            # Contact Info
            student_phone=flat_student.student_phone_number,
            father_phone=flat_student.father_phone_number,
            mother_phone=flat_student.mother_phone_number,
            student_email=flat_student.student_email,
            father_email=flat_student.father_email,
            mother_email=flat_student.mother_email,
            parent_email=(
                flat_student.mother_email
                if flat_student.primary_contact_person == "Mother"
                else flat_student.father_email
            ),
            parent_phone=(
                flat_student.mother_phone_number
                if flat_student.primary_contact_person == "Mother"
                else flat_student.father_phone_number
            ),
            
            # Profession
            father_profession_and_designation=flat_student.father_profession_and_designation,
            mother_profession_and_designation=flat_student.mother_profession_and_designation,
            
            # Address
            address_dno=flat_student.door_no,
            address_street=flat_student.street_name,
            address_village_town=flat_student.village_name,
            address_mandal=flat_student.mandal_name,
            address_district=flat_student.district_name,
            address_state=flat_student.state_name,
            address_pincode=flat_student.pincode,
            rural_urban=flat_student.rural_urban,
            
            # Reservation & Caste
            ews_status=flat_student.ews_status,
            category_name=flat_student.caste_category,
            caste_as_per_tc=flat_student.caste_as_per_tc,
            ebc_status=flat_student.ebc_status,
            income=flat_student.annual_income_of_parent,
            minority=flat_student.minority,
            
            # Medical
            blood_group=flat_student.blood_group,
            ph_status=flat_student.ph_status,
            scribe=flat_student.ph_scribe,
            
            # Academics
            tenth_board_name=flat_student.tenth_board,
            twelfth_board_name=flat_student.twelfth_board_name,
            
            # Documents / Uploads
            candidate_pic=flat_student.passport_size_photo,
            allotment_order=flat_student.convenor_allotment_order,
            joining_report=flat_student.convenor_joining_report,
            tenth_memo_link=flat_student.tenth_memo,
            twelfth_memo_link=flat_student.twelfth_memo,
            aadhaar_link=flat_student.aadhaar_card,
            eapcet_rank_card_link=flat_student.eapcet_rank_card,
            jee_rank_card_link=flat_student.jee_rank_card,
            transfer_certificate_link=flat_student.transfer_certificate,
            student_type="regular",  # Mark as regular student
            program_level="BTECH",
        )

    @classmethod
    def from_flat_leStudent(cls, flat_student: SheetStudentLE) -> 'Student':
        return cls(
            student_name=flat_student.name_of_the_student,
            father_name=flat_student.fathers_name,
            mother_name=flat_student.mothers_name,
            date_of_birth=flat_student.date_of_birth,
            gender=flat_student.gender,
            aadhaar_card_number=flat_student.aadhaar_card_number,
            eapcet_ht_no=flat_student.ecet_hall_ticket_no,  # ECET instead of EAPCET for LE
            eapcet_rank=flat_student.ecet_rank,  # ECET rank instead of EAPCET rank
            mother_tongue=flat_student.mother_tongue,
            student_phone=flat_student.student_phone_number,
            father_phone=flat_student.father_phone_number,
            mother_phone=flat_student.mother_phone_number,
            student_email=flat_student.student_email,
            father_email=flat_student.father_email,
            mother_email=flat_student.mother_email,
            parent_email=flat_student.mother_email if flat_student.primary_contact_person == "Mother" else flat_student.father_email,
            parent_phone=flat_student.mother_phone_number if flat_student.primary_contact_person == "Mother" else flat_student.father_phone_number,
            father_profession_and_designation=flat_student.father_profession_and_designation,
            mother_profession_and_designation=flat_student.mother_profession_and_designation,
            address_dno=flat_student.door_no,
            address_street=flat_student.street_name,
            address_village_town=flat_student.village_name,
            address_mandal=flat_student.mandal_name,
            address_district=flat_student.district_name,
            address_state=flat_student.state_name,
            address_pincode=flat_student.pincode,
            rural_urban=flat_student.rural_urban,
            ews_status=flat_student.ews_status,
            category_name=flat_student.caste_category,
            caste_as_per_tc=flat_student.caste_as_per_tc,
            ebc_status=flat_student.ebc_status,
            income=flat_student.annual_income_of_parent,
            minority=flat_student.minority,
            blood_group=flat_student.blood_group,
            ph_status=flat_student.ph_status,
            scribe=flat_student.ph_scribe,
            tenth_board_name=flat_student.tenth_board,
            twelfth_board_name=flat_student.diploma_board_name,  # Diploma board instead of 12th board
            tenth_memo_link=flat_student.tenth_memo,
            twelfth_memo_link=flat_student.diploma_certificate,  # Diploma certificate instead of 12th memo
            aadhaar_link=flat_student.aadhaar_card,
            eapcet_rank_card_link=flat_student.ecet_rank_card,  # ECET rank card instead of EAPCET
            transfer_certificate_link=flat_student.transfer_certificate,
            student_type="LE",  # Mark as Lateral Entry student
            program_level="BTECH",
        )

    @classmethod
    def from_flat_BStudent(cls, flat_student: 'SheetModelB') -> 'Student':
        return cls(
            student_name=flat_student.student_name_10th,
            father_name=flat_student.fathers_name_10th,
            mother_name=flat_student.mothers_name_10th,
            date_of_birth=flat_student.date_of_birth,
            gender=flat_student.gender,
            aadhaar_card_number=flat_student.aadhaar_card_number,
            student_passport_no=flat_student.student_passport_no,
            father_passport_no=flat_student.father_passport_no,
            mother_passport_no=flat_student.mother_passport_no,
            eapcet_ht_no=flat_student.eapcet_hall_ticket_no,
            eapcet_rank=flat_student.eapcet_rank,
            jee_ht_no=flat_student.jee_hall_ticket_no,
            jee_mains_rank=flat_student.jee_crl_rank,
            mother_tongue=flat_student.mother_tongue,
            student_phone=flat_student.student_phone_number,
            father_phone=flat_student.father_phone_number,
            mother_phone=flat_student.mother_phone_number,
            student_email=flat_student.student_email,
            father_email=flat_student.father_email,
            mother_email=flat_student.mother_email,
            parent_email=(
                flat_student.mother_email
                if flat_student.primary_contact_person == "Mother"
                else flat_student.father_email
            ),
            parent_phone=(
                flat_student.mother_phone_number
                if flat_student.primary_contact_person == "Mother"
                else flat_student.father_phone_number
            ),
            father_profession_and_designation=flat_student.father_profession_and_designation,
            mother_profession_and_designation=flat_student.mother_profession_and_designation,
            address_dno=flat_student.door_no,
            address_street=flat_student.street_name,
            address_village_town=flat_student.village_name,
            address_mandal=flat_student.mandal_name,
            address_district=flat_student.district_name,
            address_state=flat_student.state_name,
            address_pincode=flat_student.pincode,
            rural_urban=flat_student.rural_urban,
            ews_status=flat_student.ews_status,
            category_name=flat_student.caste_category,
            caste_as_per_tc=flat_student.caste_as_per_tc,
            ebc_status=flat_student.ebc_status,
            income=flat_student.annual_income_of_parent,
            nationality=flat_student.nationality,
            religion=flat_student.religion,
            minority=flat_student.minority,
            blood_group=flat_student.blood_group,
            ph_status=flat_student.ph_status,
            scribe=flat_student.ph_scribe,
            tenth_board_name=flat_student.tenth_board,
            twelfth_board_name=flat_student.twelfth_board_name,
            tenth_memo_link=flat_student.tenth_memo,
            twelfth_memo_link=flat_student.twelfth_memo,
            aadhaar_link=flat_student.aadhaar_card,
            eapcet_rank_card_link=flat_student.eapcet_rank_card,
            jee_rank_card_link=flat_student.jee_rank_card,
            transfer_certificate_link=flat_student.transfer_certificate,
            student_type="regular",
            admission_category="Cat-B",
            program_level="BTECH",
        )
