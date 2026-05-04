from typing import Any, Optional
from pydantic import BaseModel, field_validator


class FormField(BaseModel):
    id: Optional[str] = None
    section: str = "General"
    field_key: str
    label: str
    field_type: str = "text"
    required: bool = False
    options: list[str] = []
    help_text: Optional[str] = ""
    sort_order: int = 0
    maps_to_student_field: bool = True

    @field_validator("field_type")
    @classmethod
    def validate_field_type(cls, value: str) -> str:
        cleaned = (value or "text").strip().lower()
        allowed = {"text", "email", "tel", "date", "number", "select", "textarea", "file"}
        if cleaned not in allowed:
            raise ValueError(f"Unsupported field type: {value}")
        return cleaned


class AdmissionFormCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    slug: Optional[str] = None
    status: str = "draft"
    fields: list[FormField] = []


class AdmissionFormUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    slug: Optional[str] = None
    status: Optional[str] = None
    fields: Optional[list[FormField]] = None


class AdmissionFormResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = ""
    slug: str
    status: str
    fields: list[FormField] = []


class FormSubmissionRequest(BaseModel):
    response_data: dict[str, Any]


class FormSubmissionResponse(BaseModel):
    response_id: str
    form_id: str
    student_id: str
    application_reference: str
    status: str
