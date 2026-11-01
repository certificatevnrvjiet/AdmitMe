"""Canonical admission DTO for every 2026 intake path.

Google Form responses, the public application form, and staff edits all use
the same student-facing field names before being persisted to ``admissions_2026``.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, field_validator


def _normalise_heading(value: str) -> str:
    return "".join(character for character in str(value).lower() if character.isalnum())


SHEET_HEADER_FIELDS: dict[str, str] = {
    "timestamp": "source_response_timestamp",
    "emailaddress": "source_response_email",
    "nameofthestudent": "student_name",
    "fathersname": "father_name",
    "mothersname": "mother_name",
    "dateofbirth": "date_of_birth",
    "gender": "gender",
    "aadhaarcardnumber": "aadhaar_card_number",
    "eapcethallticketno": "eapcet_ht_no",
    "eapcetrank": "eapcet_rank",
    "jeehallticketno": "jee_ht_no",
    "jeecrlrank": "jee_mains_rank",
    "mothertongue": "mother_tongue",
    "religion": "religion",
    "nationality": "nationality",
    "studentphonenumber": "student_phone",
    "fatherphonenumber": "father_phone",
    "motherphonenumber": "mother_phone",
    "studentemail": "student_email",
    "fatheremail": "father_email",
    "motheremail": "mother_email",
    "fatherprofessionanddesignation": "father_profession_and_designation",
    "motherprofessionanddesignation": "mother_profession_and_designation",
    "primarycontactperson": "primary_contact_person",
    "doorno": "address_dno",
    "streetname": "address_street",
    "villagename": "address_village_town",
    "mandalname": "address_mandal",
    "districtname": "address_district",
    "statename": "address_state",
    "pincode": "address_pincode",
    "ruralurban": "rural_urban",
    "ewsstatus": "ews_status",
    "castecategory": "category_name",
    "casteaspertc": "caste_as_per_tc",
    "ebcstatus": "ebc_status",
    "annualincomeofparent": "income",
    "minority": "minority",
    "bloodgroup": "blood_group",
    "phstatus": "ph_status",
    "phscribe": "scribe",
    "10thboard": "tenth_board_name",
    "12thboardname": "twelfth_board_name",
    "passportsizephoto": "candidate_pic",
    "convenorallotmentorder": "allotment_order",
    "convenorjoiningreport": "joining_report",
    "10thmemo": "tenth_memo_link",
    "12thmemo": "twelfth_memo_link",
    "aadhaarcard": "aadhaar_link",
    "eapcetrankcard": "eapcet_rank_card_link",
    "jeerankcard": "jee_rank_card_link",
    "transfercertificate": "transfer_certificate_link",
    "consent": "consent",
}


class Admissions2026Applicant(BaseModel):
    source_response_timestamp: str = ""
    source_response_email: str = ""
    student_name: str = ""
    father_name: str = ""
    mother_name: str = ""
    date_of_birth: str = ""
    gender: str = ""
    aadhaar_card_number: str = ""
    eapcet_ht_no: str = ""
    eapcet_rank: str = ""
    jee_ht_no: str = ""
    jee_mains_rank: str = ""
    mother_tongue: str = ""
    religion: str = ""
    nationality: str = ""
    student_phone: str = ""
    father_phone: str = ""
    mother_phone: str = ""
    student_email: str = ""
    father_email: str = ""
    mother_email: str = ""
    father_profession_and_designation: str = ""
    mother_profession_and_designation: str = ""
    primary_contact_person: str = ""
    address_dno: str = ""
    address_street: str = ""
    address_village_town: str = ""
    address_mandal: str = ""
    address_district: str = ""
    address_state: str = ""
    address_pincode: str = ""
    rural_urban: str = ""
    ews_status: str = ""
    category_name: str = ""
    caste_as_per_tc: str = ""
    ebc_status: str = ""
    income: str = ""
    minority: str = ""
    blood_group: str = ""
    ph_status: str = ""
    scribe: str = ""
    tenth_board_name: str = ""
    twelfth_board_name: str = ""
    candidate_pic: str = ""
    allotment_order: str = ""
    joining_report: str = ""
    tenth_memo_link: str = ""
    twelfth_memo_link: str = ""
    aadhaar_link: str = ""
    eapcet_rank_card_link: str = ""
    jee_rank_card_link: str = ""
    transfer_certificate_link: str = ""
    consent: str = ""
    branch: str = ""
    admission_category: str = "Convenor"

    @field_validator("aadhaar_card_number")
    @classmethod
    def normalise_aadhaar(cls, value: str) -> str:
        return "".join(character for character in str(value or "") if character.isdigit())

    @classmethod
    def from_sheet_row(cls, headers: list[str], row: list[str]) -> "Admissions2026Applicant":
        payload: dict[str, Any] = {}
        for index, heading in enumerate(headers):
            field_name = SHEET_HEADER_FIELDS.get(_normalise_heading(heading))
            if field_name:
                payload[field_name] = row[index] if index < len(row) else ""
        return cls.model_validate(payload)

    @classmethod
    def from_application_payload(cls, payload: dict[str, Any]) -> "Admissions2026Applicant":
        return cls.model_validate(payload)

    def to_student_record(
        self,
        *,
        branch: str,
        source_system: str | None = None,
        source_spreadsheet_id: str = "",
        source_sheet_tab: str = "",
    ) -> dict[str, Any]:
        record = self.model_dump(
            exclude={"primary_contact_person", "source_response_timestamp", "source_response_email"}
        )
        record["branch"] = branch.upper()
        if self.primary_contact_person.strip().lower() == "mother":
            record["parent_phone"] = self.mother_phone
            record["parent_email"] = self.mother_email
        else:
            record["parent_phone"] = self.father_phone
            record["parent_email"] = self.father_email
        if source_system:
            record.update({
                "source_system": source_system,
                "source_spreadsheet_id": source_spreadsheet_id,
                "source_sheet_tab": source_sheet_tab,
                "source_response_timestamp": self.source_response_timestamp,
                "source_response_email": self.source_response_email,
            })
        return record
