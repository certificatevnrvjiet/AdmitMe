from typing import Any, Optional
from pydantic import BaseModel


class EngineRunRequest(BaseModel):
    doc_types: Optional[list[str]] = None
    force: bool = True


class ComparisonOverrideRequest(BaseModel):
    field_name: str
    reviewer_override: bool = True
    reviewer_notes: Optional[str] = ""


class ComparisonResult(BaseModel):
    id: Optional[str] = None
    student_id: str
    field_name: str
    filled_value: Optional[str] = ""
    extracted_value: Optional[str] = ""
    match_status: str
    severity: str
    source_doc_type: Optional[str] = None
    extraction_run_id: Optional[str] = None
    reviewer_override: bool = False
    reviewer_notes: Optional[str] = ""


class EngineRunResponse(BaseModel):
    task_id: str
    student_id: str
    status: str


class EngineSummary(BaseModel):
    student_id: str
    extraction_runs: list[dict[str, Any]]
    parsed_extractions: list[dict[str, Any]]
    comparison_results: list[dict[str, Any]]
