from __future__ import annotations

import re
from datetime import datetime
from typing import Any
from uuid import uuid4

from database import supabase
from extractor import extract_from_document_ref, prompts
from services.document_service import (
    LEGACY_DOC_FIELD_MAP,
    fetch_student,
    get_document_row,
    resolve_student_document_ref,
)


IMPORTANT_FIELDS = {
    "student_name": {"severity": "high", "kind": "name"},
    "father_name": {"severity": "high", "kind": "name"},
    "mother_name": {"severity": "high", "kind": "name"},
    "date_of_birth": {"severity": "high", "kind": "date"},
    "gender": {"severity": "high", "kind": "text"},
    "aadhaar_card_number": {"severity": "high", "kind": "digits"},
    "tenth_ht_no": {"severity": "medium", "kind": "text"},
    "twelfth_ht_no": {"severity": "medium", "kind": "text"},
    "eapcet_ht_no": {"severity": "medium", "kind": "text"},
    "eapcet_rank": {"severity": "medium", "kind": "number"},
    "jee_ht_no": {"severity": "medium", "kind": "text"},
    "jee_mains_rank": {"severity": "medium", "kind": "number"},
    "tenth_board_name": {"severity": "low", "kind": "text"},
    "twelfth_board_name": {"severity": "low", "kind": "text"},
    "tenth_total_marks_cgpa": {"severity": "medium", "kind": "number"},
    "twelfth_total_marks": {"severity": "medium", "kind": "number"},
    "tenth_percentage": {"severity": "low", "kind": "number"},
    "twelfth_percentage": {"severity": "low", "kind": "number"},
    "category_name": {"severity": "medium", "kind": "text"},
    "caste_as_per_tc": {"severity": "medium", "kind": "text"},
}


DOC_PROMPT_INDEX = {
    "tenth_memo": 0,
    "aadhaar": 1,
    "transfer_certificate": 3,
    "twelfth_memo": 4,
    "jee_rank_card": 2,
    "eapcet_rank_card": 2,
}


def _db_now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _new_id() -> str:
    return str(uuid4())


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_name(value: Any) -> str:
    text = re.sub(r"[^a-z0-9 ]+", " ", _as_text(value).lower())
    return re.sub(r"\s+", " ", text).strip()


def _normalize_digits(value: Any) -> str:
    return re.sub(r"\D+", "", _as_text(value))


def _normalize_number(value: Any) -> str:
    text = _as_text(value)
    match = re.search(r"\d+(?:\.\d+)?", text.replace(",", ""))
    if not match:
        return ""
    number = float(match.group(0))
    return str(int(number)) if number.is_integer() else f"{number:.2f}".rstrip("0").rstrip(".")


def _normalize_date(value: Any) -> str:
    text = _as_text(value)
    if not text:
        return ""
    parts = re.findall(r"\d+", text)
    if len(parts) >= 3:
        first, second, third = parts[:3]
        if len(first) == 4:
            year, month, day = first, second.zfill(2), third.zfill(2)
        else:
            day, month, year = first.zfill(2), second.zfill(2), third
        return f"{day}/{month}/{year}"
    return text.lower()


def _normalize_for_compare(value: Any, kind: str) -> str:
    if kind == "name":
        return _normalize_name(value)
    if kind == "digits":
        return _normalize_digits(value)
    if kind == "number":
        return _normalize_number(value)
    if kind == "date":
        return _normalize_date(value)
    return re.sub(r"\s+", " ", _as_text(value).lower()).strip()


def _first(raw: dict[str, Any], *keys: str) -> str:
    for key in keys:
        if key in raw and raw.get(key) not in (None, ""):
            return _as_text(raw.get(key))
    lowered = {str(k).lower(): v for k, v in raw.items()}
    for key in keys:
        value = lowered.get(key.lower())
        if value not in (None, ""):
            return _as_text(value)
    return ""


def parse_extraction(doc_type: str, raw: dict[str, Any]) -> dict[str, str]:
    if not isinstance(raw, dict) or raw.get("error"):
        return {}

    scores = raw.get("Subject Scores") if isinstance(raw.get("Subject Scores"), dict) else {}
    parsed: dict[str, str] = {}

    if doc_type == "tenth_memo":
        parsed.update({
            "student_name": _first(raw, "Candidate Name", "Name"),
            "father_name": _first(raw, "Father Name"),
            "mother_name": _first(raw, "Mother Name"),
            "date_of_birth": _first(raw, "Date of Birth"),
            "tenth_board_name": _first(raw, "tenth_board_name", "Board Name"),
            "tenth_school_name": _first(raw, "tenth_school_name"),
            "tenth_ht_no": _first(raw, "tenth_hall_ticket_no", "Hall Ticket Number"),
            "tenth_total_marks_cgpa": _first(raw, "tenth_total_marks/CGPA", "Total Marks"),
            "tenth_maximum_marks": _first(raw, "tenth_max_marks/CGPA", "Max Marks"),
            "tenth_percentage": _first(raw, "tenth_percentage", "Percentage"),
            "tenth_month_year": _first(raw, "tenth_month_year", "Month_year"),
            "identification_mark_1": _first(raw, "identification_marks1"),
            "identification_mark_2": _first(raw, "identification_marks2"),
        })
    elif doc_type == "aadhaar":
        parsed.update({
            "aadhaar_card_number": _first(raw, "Number", "Aadhaar Number"),
            "gender": _first(raw, "Gender"),
        })
    elif doc_type == "transfer_certificate":
        parsed.update({
            "nationality": _first(raw, "Nationality"),
            "religion": _first(raw, "Religion"),
            "twelfth_college_name": _first(raw, "College Name"),
            "caste_as_per_tc": _first(raw, "Caste", "Caste as per TC"),
        })
    elif doc_type == "twelfth_memo":
        parsed.update({
            "twelfth_board_name": _first(raw, "Board Name"),
            "twelfth_ht_no": _first(raw, "Hall Ticket Number"),
            "twelfth_maximum_marks": _first(raw, "Max Marks"),
            "twelfth_total_marks": _first(raw, "Total Marks", "'Total Marks'"),
            "twelfth_percentage": _first(raw, "Percentage"),
            "twelfth_month_year": _first(raw, "Month_year", "Month_Passing"),
            "m1": _as_text(scores.get("M1")),
            "m2": _as_text(scores.get("M2")),
            "m3": _as_text(scores.get("M3")),
            "m4": _as_text(scores.get("M4")),
            "p1": _as_text(scores.get("P1")),
            "p2": _as_text(scores.get("P2")),
            "ch1": _as_text(scores.get("C1")),
            "ch2": _as_text(scores.get("C2")),
            "plab": _as_text(scores.get("P_Practicals")),
            "chlab": _as_text(scores.get("C_Practicals")),
        })
    elif doc_type == "jee_rank_card":
        parsed.update({
            "jee_ht_no": _first(raw, "HT Number", "Hall Ticket Number"),
            "jee_mains_rank": _first(raw, "Rank"),
        })
    elif doc_type == "eapcet_rank_card":
        parsed.update({
            "eapcet_ht_no": _first(raw, "HT Number", "Hall Ticket Number"),
            "eapcet_rank": _first(raw, "Rank"),
        })

    return {key: value for key, value in parsed.items() if value not in ("", None)}


def _insert(table: str, payload: dict[str, Any]) -> dict[str, Any]:
    payload = {"id": _new_id(), **payload}
    response = supabase.table(table).insert(payload).execute()
    if response.data:
        return response.data[0]
    return payload


def _list_rows(table: str, student_id: str) -> list[dict[str, Any]]:
    try:
        return supabase.table(table).select("*").eq("student_id", student_id).execute().data or []
    except Exception:
        return []


def _get_document_rows(student: dict[str, Any], doc_types: list[str] | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    wanted = doc_types or list(LEGACY_DOC_FIELD_MAP.keys())
    student_id = student.get("aadhaar_card_number")
    for doc_type in wanted:
        ref = resolve_student_document_ref(student, student_id, doc_type)
        if not ref:
            continue
        document_row = get_document_row(student_id, doc_type) or {}
        rows.append({
            "document_id": document_row.get("id"),
            "doc_type": doc_type,
            "provider": ref.provider,
            "object_key": ref.key,
        })
    return rows


def _prompt_for_doc(doc_type: str, student: dict[str, Any]) -> str:
    if doc_type == "twelfth_memo":
        board = (student.get("twelfth_board_name") or "").strip()
        if board == "ACE and A Level":
            return prompts[5]
        if board == "ICSE":
            return prompts[6]
        if board == "CBSE":
            return prompts[7]
    return prompts[DOC_PROMPT_INDEX.get(doc_type, 4)]


def replace_comparison_results(student: dict[str, Any], parsed_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    student_id = student.get("aadhaar_card_number")
    supabase.table("comparison_results").delete().eq("student_id", student_id).execute()

    extracted_by_field: dict[str, tuple[str, str, str | None]] = {}
    for row in parsed_rows:
        fields = row.get("parsed_fields") or {}
        if not isinstance(fields, dict):
            continue
        for field, value in fields.items():
            if field in IMPORTANT_FIELDS and _as_text(value):
                extracted_by_field[field] = (
                    _as_text(value),
                    row.get("doc_type") or "",
                    row.get("extraction_run_id"),
                )

    results: list[dict[str, Any]] = []
    for field, config in IMPORTANT_FIELDS.items():
        extracted_value, doc_type, run_id = extracted_by_field.get(field, ("", "", None))
        filled_value = _as_text(student.get(field))
        if not extracted_value:
            match_status = "missing_extracted"
        elif not filled_value:
            match_status = "missing_filled"
        elif _normalize_for_compare(filled_value, config["kind"]) == _normalize_for_compare(extracted_value, config["kind"]):
            match_status = "match"
        else:
            match_status = "mismatch"

        payload = {
            "student_id": student_id,
            "field_name": field,
            "filled_value": filled_value,
            "extracted_value": extracted_value,
            "match_status": match_status,
            "severity": config["severity"],
            "source_doc_type": doc_type,
            "extraction_run_id": run_id,
            "reviewer_override": False,
            "reviewer_notes": "",
            "created_at": _db_now(),
            "updated_at": _db_now(),
        }
        results.append(_insert("comparison_results", payload))
    return results


async def run_engine_for_student(
    student_id: str,
    app,
    username: str | None = None,
    doc_types: list[str] | None = None,
) -> dict[str, Any]:
    student = fetch_student(student_id)
    if not student:
        raise ValueError("Student not found")

    providers = getattr(app.state, "storage_providers", {})
    document_rows = _get_document_rows(student, doc_types)
    parsed_rows: list[dict[str, Any]] = []
    extraction_runs: list[dict[str, Any]] = []

    for document in document_rows:
        doc_type = document["doc_type"]
        run = _insert("extraction_runs", {
            "student_id": student_id,
            "document_id": document.get("document_id"),
            "doc_type": doc_type,
            "provider": document.get("provider"),
            "object_key": document.get("object_key"),
            "status": "processing",
            "raw_output": {},
            "error": "",
            "created_at": _db_now(),
            "updated_at": _db_now(),
        })
        raw_output = await extract_from_document_ref(
            f"{document['provider']}:{document['object_key']}",
            _prompt_for_doc(doc_type, student),
            providers,
        )
        status = "failed" if isinstance(raw_output, dict) and raw_output.get("error") else "completed"
        supabase.table("extraction_runs").update({
            "status": status,
            "raw_output": raw_output if isinstance(raw_output, dict) else {"value": raw_output},
            "error": raw_output.get("error", "") if isinstance(raw_output, dict) else "",
            "updated_at": _db_now(),
        }).eq("id", run["id"]).execute()
        run = {**run, "status": status, "raw_output": raw_output}
        extraction_runs.append(run)

        parsed_fields = parse_extraction(doc_type, raw_output if isinstance(raw_output, dict) else {})
        parsed_row = _insert("parsed_extractions", {
            "extraction_run_id": run["id"],
            "student_id": student_id,
            "doc_type": doc_type,
            "parsed_fields": parsed_fields,
            "confidence": {key: "extracted" for key in parsed_fields},
            "created_at": _db_now(),
        })
        parsed_rows.append(parsed_row)

    comparison_rows = replace_comparison_results(student, parsed_rows or _list_rows("parsed_extractions", student_id))
    return {
        "student_id": student_id,
        "extraction_runs": extraction_runs,
        "parsed_extractions": parsed_rows,
        "comparison_results": comparison_rows,
        "triggered_by": username,
    }


def get_engine_summary(student_id: str) -> dict[str, Any]:
    return {
        "student_id": student_id,
        "extraction_runs": _list_rows("extraction_runs", student_id),
        "parsed_extractions": _list_rows("parsed_extractions", student_id),
        "comparison_results": _list_rows("comparison_results", student_id),
    }


def update_comparison_override(
    student_id: str,
    field_name: str,
    reviewer_override: bool,
    reviewer_notes: str | None,
) -> dict[str, Any]:
    rows = (
        supabase.table("comparison_results")
        .select("*")
        .eq("student_id", student_id)
        .eq("field_name", field_name)
        .limit(1)
        .execute()
        .data
        or []
    )
    if not rows:
        raise ValueError("Comparison result not found")
    row = rows[0]
    response = (
        supabase.table("comparison_results")
        .update({
            "reviewer_override": reviewer_override,
            "reviewer_notes": reviewer_notes or "",
            "updated_at": _db_now(),
        })
        .eq("id", row["id"])
        .execute()
    )
    return response.data[0] if response.data else {**row, "reviewer_override": reviewer_override, "reviewer_notes": reviewer_notes or ""}
