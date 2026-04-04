from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator, model_validator

from services.catalog_service import (
    normalize_branch_code,
    normalize_program_level,
    validate_program_branch,
)


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
    program_level: str = "BTECH"
    branch_code: str = "cse"
    degree_code: Optional[str] = None
    admission_category: str = "Convenor"

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

    @field_validator("program_level")
    @classmethod
    def validate_program_level(cls, value: str) -> str:
        return normalize_program_level(value)

    @field_validator("branch_code")
    @classmethod
    def validate_branch_code(cls, value: str) -> str:
        return normalize_branch_code(value)

    @field_validator("degree_code")
    @classmethod
    def validate_degree_code(cls, value: Optional[str]) -> Optional[str]:
        if value is None or not str(value).strip():
            return None
        return normalize_branch_code(value)

    @model_validator(mode="after")
    def validate_program_branch_pair(self):
        validate_program_branch(self.program_level, self.branch_code)
        if not self.degree_code:
            self.degree_code = self.branch_code
        return self


class StudentApplicationResponse(BaseModel):
    application_reference: str
    student_id: str
    status: str
