from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


VALID_VERIFICATION_STATUSES = {
    "submitted",
    "under_review",
    "approved",
    "rejected",
    "resubmission_required",
}


class VerificationUpdate(BaseModel):
    status: str
    remarks: Optional[str] = ""
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        cleaned = (value or "").strip().lower()
        if cleaned not in VALID_VERIFICATION_STATUSES:
            raise ValueError(f"Unsupported verification status: {value}")
        return cleaned
