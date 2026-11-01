from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator, model_validator

from services.catalog_service import normalize_branch_code
from models.Admissions2026 import Admissions2026Applicant


class StudentApplicationRequest(BaseModel):
    # Personal
    student_name: str
    father_name: str
    mother_name: str
    date_of_birth: str
    gender: str
    aadhaar_card_number: str

    # Academic/exam
    tenth_board_name: str
    twelfth_board_name: str
    eapcet_ht_no: Optional[str] = ""
    eapcet_rank: Optional[str] = ""
    jee_ht_no: Optional[str] = ""
    jee_mains_rank: Optional[str] = ""

    # Contact
    mother_tongue: str
    student_phone: str
    father_phone: str
    mother_phone: str
    student_email: EmailStr
    father_email: Optional[EmailStr] = None
    mother_email: Optional[EmailStr] = None
    father_profession_and_designation: str
    mother_profession_and_designation: str
    primary_contact_person: str

    # Address
    address_dno: str
    address_street: str
    address_village_town: str
    address_mandal: str
    address_district: str
    address_state: str
    address_pincode: str
    rural_urban: str

    # Category/other
    ews_status: str
    category_name: str
    caste_as_per_tc: Optional[str] = ""
    ebc_status: str
    income: str
    minority: Optional[str] = ""
    blood_group: str
    ph_status: str
    scribe: str

    # Admission
    branch: str
    admission_category: str = "Convenor"
    consent: str = ""

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, value: str) -> str:
        cleaned = (value or "").strip().lower()
        allowed = {"male", "female", "transgender"}
        if cleaned not in allowed:
            raise ValueError("Gender must be Male, Female, or Transgender")
        return cleaned.title()

    @field_validator("aadhaar_card_number")
    @classmethod
    def validate_aadhaar(cls, value: str) -> str:
        cleaned = "".join(ch for ch in (value or "") if ch.isdigit())
        if len(cleaned) != 12:
            raise ValueError("Aadhaar must be 12 digits")
        return cleaned

    @field_validator("branch")
    @classmethod
    def validate_branch(cls, value: str) -> str:
        return normalize_branch_code(value)

    def to_admissions2026(self) -> Admissions2026Applicant:
        """Expose the same canonical DTO used by Google Form imports."""
        return Admissions2026Applicant.from_application_payload(self.model_dump())


class StudentApplicationResponse(BaseModel):
    application_reference: str
    student_id: str
    status: str
