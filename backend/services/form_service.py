from __future__ import annotations

import re
from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status

from database import supabase
from models.FormModel import AdmissionFormCreate, AdmissionFormUpdate, FormField
from services.status_service import normalize_status


STUDENT_FIELD_KEYS = {
    "student_name", "father_name", "mother_name", "date_of_birth", "gender",
    "aadhaar_card_number", "mother_tongue", "student_phone", "father_phone",
    "mother_phone", "student_email", "father_email", "mother_email",
    "father_profession_and_designation", "mother_profession_and_designation",
    "parent_phone", "parent_email", "address_dno", "address_street",
    "address_village_town", "address_mandal", "address_district",
    "address_state", "address_pincode", "rural_urban", "ews_status",
    "category_name", "caste_as_per_tc", "ebc_status", "income", "minority",
    "blood_group", "ph_status", "scribe", "tenth_board_name",
    "twelfth_board_name", "eapcet_ht_no", "eapcet_rank", "jee_ht_no",
    "jee_mains_rank", "program_level", "branch_code", "degree_code",
    "admission_category",
}

PHONE_FIELD_KEYS = {"student_phone", "father_phone", "mother_phone", "parent_phone"}


DEFAULT_FORM_FIELDS = [
    FormField(section="Personal", field_key="student_name", label="Name of the Student", required=True, sort_order=10),
    FormField(section="Personal", field_key="father_name", label="Father's Name", required=True, sort_order=20),
    FormField(section="Personal", field_key="mother_name", label="Mother's Name", required=True, sort_order=30),
    FormField(section="Personal", field_key="date_of_birth", label="Date of Birth", field_type="date", required=True, sort_order=40),
    FormField(section="Personal", field_key="gender", label="Gender", field_type="select", required=True, options=["Male", "Female", "Transgender"], sort_order=50),
    FormField(section="Personal", field_key="aadhaar_card_number", label="Aadhaar Card Number", required=True, sort_order=60),
    FormField(section="Contact", field_key="mother_tongue", label="Mother Tongue", required=True, sort_order=70),
    FormField(section="Contact", field_key="student_phone", label="Student Phone Number", field_type="tel", required=True, sort_order=80),
    FormField(section="Contact", field_key="father_phone", label="Father Phone Number", field_type="tel", required=True, sort_order=90),
    FormField(section="Contact", field_key="mother_phone", label="Mother Phone Number", field_type="tel", required=True, sort_order=100),
    FormField(section="Contact", field_key="student_email", label="Student Email", field_type="email", required=True, sort_order=110),
    FormField(section="Contact", field_key="father_email", label="Father Email", field_type="email", sort_order=120),
    FormField(section="Contact", field_key="mother_email", label="Mother Email", field_type="email", sort_order=130),
    FormField(section="Contact", field_key="father_profession_and_designation", label="Father Profession and Designation", required=True, sort_order=140),
    FormField(section="Contact", field_key="mother_profession_and_designation", label="Mother Profession and Designation", required=True, sort_order=150),
    FormField(section="Contact", field_key="primary_contact_person", label="Primary Contact Person", field_type="select", required=True, options=["Father", "Mother"], sort_order=160),
    FormField(section="Address", field_key="address_dno", label="Door No", required=True, sort_order=170),
    FormField(section="Address", field_key="address_street", label="Street Name", required=True, sort_order=180),
    FormField(section="Address", field_key="address_village_town", label="Village/Town", required=True, sort_order=190),
    FormField(section="Address", field_key="address_mandal", label="Mandal", required=True, sort_order=200),
    FormField(section="Address", field_key="address_district", label="District", required=True, sort_order=210),
    FormField(section="Address", field_key="address_state", label="State", required=True, sort_order=220),
    FormField(section="Address", field_key="address_pincode", label="Pincode", required=True, sort_order=230),
    FormField(section="Address", field_key="rural_urban", label="Rural / Urban", field_type="select", required=True, options=["Rural", "Urban"], sort_order=240),
    FormField(section="Category", field_key="ews_status", label="EWS Status", field_type="select", required=True, options=["Yes", "No"], sort_order=250),
    FormField(section="Category", field_key="category_name", label="Caste Category", field_type="select", required=True, options=["OC", "BC-A", "BC-B", "BC-C", "BC-D", "BC-E", "SC", "ST"], sort_order=260),
    FormField(section="Category", field_key="caste_as_per_tc", label="Caste as per TC", required=True, sort_order=270),
    FormField(section="Category", field_key="ebc_status", label="EBC Status", field_type="select", required=True, options=["Yes", "No"], sort_order=280),
    FormField(section="Category", field_key="income", label="Annual Income of Parent", field_type="select", required=True, options=["Below 1 lakhs", "Below 1.5 lakhs", "Below 2 lakhs", "Below 2.5 lakhs", "Below 8 lakhs", "Above 8 lakhs"], sort_order=290),
    FormField(section="Category", field_key="minority", label="Minority", field_type="select", options=["Yes", "No"], sort_order=300),
    FormField(section="Category", field_key="blood_group", label="Blood Group", field_type="select", required=True, options=["A +", "A -", "B +", "B -", "O +", "O -", "AB +", "AB -"], sort_order=310),
    FormField(section="Category", field_key="ph_status", label="PH Status", field_type="select", required=True, options=["Yes", "No"], sort_order=320),
    FormField(section="Category", field_key="scribe", label="PH Scribe", field_type="select", required=True, options=["Yes", "No"], sort_order=330),
    FormField(section="Academic", field_key="program_level", label="Program", field_type="select", required=True, options=["BTECH", "MTECH"], sort_order=340),
    FormField(section="Academic", field_key="branch_code", label="Branch", required=True, sort_order=350),
    FormField(section="Academic", field_key="tenth_board_name", label="10th Board", field_type="select", required=True, options=["TG BSE", "CBSE", "AP BSE", "ACE and A Level", "IBDP", "ICSE", "Other"], sort_order=360),
    FormField(section="Academic", field_key="twelfth_board_name", label="12th Board", field_type="select", required=True, options=["TG BIE", "CBSE", "AP BIE", "ACE and A Level", "IBDP", "ICSE", "Other"], sort_order=370),
    FormField(section="Academic", field_key="eapcet_ht_no", label="EAPCET Hall Ticket No", sort_order=380),
    FormField(section="Academic", field_key="eapcet_rank", label="EAPCET Rank", field_type="number", sort_order=390),
    FormField(section="Academic", field_key="jee_ht_no", label="JEE Hall Ticket No", sort_order=400),
    FormField(section="Academic", field_key="jee_mains_rank", label="JEE CRL Rank", field_type="number", sort_order=410),
    FormField(section="Documents", field_key="tenth_memo", label="10th Memo", field_type="file", required=True, maps_to_student_field=False, sort_order=420),
    FormField(section="Documents", field_key="twelfth_memo", label="12th Memo", field_type="file", required=True, maps_to_student_field=False, sort_order=430),
    FormField(section="Documents", field_key="aadhaar", label="Aadhaar Card", field_type="file", required=True, maps_to_student_field=False, sort_order=440),
    FormField(section="Documents", field_key="transfer_certificate", label="Transfer Certificate / Bonafide", field_type="file", required=True, maps_to_student_field=False, sort_order=450),
    FormField(section="Documents", field_key="eapcet_rank_card", label="EAPCET Rank Card", field_type="file", maps_to_student_field=False, sort_order=460),
    FormField(section="Documents", field_key="jee_rank_card", label="JEE Rank Card", field_type="file", maps_to_student_field=False, sort_order=470),
]


def _db_now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _new_id() -> str:
    return str(uuid4())


def _slugify(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", (value or "admission-form").lower()).strip("-")
    return text or "admission-form"


def _field_to_row(form_id: str, field: FormField) -> dict[str, Any]:
    return {
        "id": field.id or _new_id(),
        "form_id": form_id,
        "section": field.section,
        "field_key": field.field_key,
        "label": field.label,
        "field_type": field.field_type,
        "required": field.required,
        "options": field.options or [],
        "help_text": field.help_text or "",
        "sort_order": field.sort_order,
        "maps_to_student_field": field.maps_to_student_field,
    }


def default_admission_form() -> dict[str, Any]:
    return {
        "id": "default-admission",
        "title": "B.Tech 2026 Admission Form",
        "description": "Submit B.Tech 2026 admission details and supporting documents.",
        "slug": "btech-2026",
        "status": "published",
        "is_default": True,
        "fields": [field.model_dump() for field in DEFAULT_FORM_FIELDS],
    }


def _hydrate_form(row: dict[str, Any]) -> dict[str, Any]:
    try:
        fields = (
            supabase.table("admission_form_fields")
            .select("*")
            .eq("form_id", row["id"])
            .execute()
            .data
            or []
        )
    except Exception:
        fields = []
    fields = sorted(fields, key=lambda field: int(field.get("sort_order") or 0))
    return {**row, "fields": fields}


def list_forms() -> list[dict[str, Any]]:
    try:
        rows = supabase.table("admission_forms").select("*").execute().data or []
    except Exception:
        return [default_admission_form()]
    forms = [_hydrate_form(row) for row in rows]
    if not any(form.get("id") == "default-admission" for form in forms):
        forms.insert(0, default_admission_form())
    return forms


def list_public_forms() -> list[dict[str, Any]]:
    forms = [form for form in list_forms() if form.get("status") == "published"]
    return forms or [default_admission_form()]


def get_form(form_id: str) -> dict[str, Any] | None:
    if form_id == "default-admission":
        return default_admission_form()
    try:
        rows = supabase.table("admission_forms").select("*").eq("id", form_id).limit(1).execute().data or []
    except Exception:
        return None
    return _hydrate_form(rows[0]) if rows else None


def get_public_form(slug: str = "admission") -> dict[str, Any]:
    try:
        rows = (
            supabase.table("admission_forms")
            .select("*")
            .eq("slug", slug)
            .eq("status", "published")
            .limit(1)
            .execute()
            .data
            or []
        )
    except Exception:
        rows = []
    if rows:
        return _hydrate_form(rows[0])
    if slug in {"admission", "btech-2026", "default-admission"}:
        return default_admission_form()
    raise HTTPException(status_code=404, detail="Published form not found")


def create_form(payload: AdmissionFormCreate, username: str) -> dict[str, Any]:
    form_id = _new_id()
    slug = _slugify(payload.slug or payload.title)
    form = {
        "id": form_id,
        "title": payload.title,
        "description": payload.description or "",
        "slug": slug,
        "status": payload.status if payload.status in {"draft", "published"} else "draft",
        "created_by": username,
        "created_at": _db_now(),
        "updated_at": _db_now(),
    }
    supabase.table("admission_forms").insert(form).execute()
    fields = payload.fields or DEFAULT_FORM_FIELDS
    for index, field in enumerate(fields):
        if not field.sort_order:
            field.sort_order = (index + 1) * 10
        supabase.table("admission_form_fields").insert(_field_to_row(form_id, field)).execute()
    return get_form(form_id) or {**form, "fields": []}


def update_form(form_id: str, payload: AdmissionFormUpdate) -> dict[str, Any]:
    form = get_form(form_id)
    if not form or form.get("is_default"):
        raise HTTPException(status_code=404, detail="Form not found")

    update_payload = {key: value for key, value in payload.model_dump(exclude={"fields"}).items() if value is not None}
    if "slug" in update_payload:
        update_payload["slug"] = _slugify(update_payload["slug"])
    if "status" in update_payload and update_payload["status"] not in {"draft", "published"}:
        update_payload["status"] = "draft"
    update_payload["updated_at"] = _db_now()
    if update_payload:
        supabase.table("admission_forms").update(update_payload).eq("id", form_id).execute()

    if payload.fields is not None:
        supabase.table("admission_form_fields").delete().eq("form_id", form_id).execute()
        for index, field in enumerate(payload.fields):
            if not field.sort_order:
                field.sort_order = (index + 1) * 10
            supabase.table("admission_form_fields").insert(_field_to_row(form_id, field)).execute()

    return get_form(form_id) or form


def delete_form(form_id: str) -> None:
    if form_id == "default-admission":
        raise HTTPException(status_code=400, detail="Default form cannot be deleted")
    supabase.table("admission_form_fields").delete().eq("form_id", form_id).execute()
    supabase.table("admission_forms").delete().eq("id", form_id).execute()


def _require_submission_fields(form: dict[str, Any], response_data: dict[str, Any]) -> None:
    missing = []
    for field in form.get("fields", []):
        if field.get("field_key") == "caste_as_per_tc":
            field["required"] = True
        if field.get("field_type") == "file":
            continue
        if field.get("required") and not str(response_data.get(field.get("field_key"), "")).strip():
            missing.append(field.get("label") or field.get("field_key"))
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required fields: {', '.join(missing)}")


def _validate_digit_fields(form: dict[str, Any], response_data: dict[str, Any]) -> None:
    for field in form.get("fields", []):
        key = field.get("field_key")
        if field.get("field_type") != "tel" and key not in PHONE_FIELD_KEYS:
            continue
        value = str(response_data.get(key) or "").strip()
        if value and not value.isdigit():
            raise HTTPException(status_code=400, detail=f"{field.get('label') or key} must contain digits only")


def submit_form_response(form_id: str, response_data: dict[str, Any], current_user: dict[str, Any]) -> dict[str, Any]:
    form = get_form(form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    if form.get("status") != "published":
        raise HTTPException(status_code=400, detail="Form is not published")

    _require_submission_fields(form, response_data)
    _validate_digit_fields(form, response_data)
    actor_email = (current_user.get("username") or "").strip().lower()
    student_email = str(response_data.get("student_email") or "").strip().lower()
    if not actor_email or actor_email != student_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student users can submit forms only for their own email",
        )

    student_id = re.sub(r"\D+", "", str(response_data.get("aadhaar_card_number") or ""))
    if len(student_id) != 12:
        raise HTTPException(status_code=400, detail="Aadhaar must be 12 digits")

    application_reference = response_data.get("application_reference") or f"ADM-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{student_id[-4:]}"
    student_row: dict[str, Any] = {
        "aadhaar_card_number": student_id,
        "application_reference": application_reference,
        "student_email": student_email,
        "status": normalize_status("submitted"),
        "student_type": "regular",
        "Time_updated": _db_now(),
    }
    custom_data: dict[str, Any] = {}
    for field in form.get("fields", []):
        key = field.get("field_key")
        if not key or field.get("field_type") == "file":
            continue
        value = response_data.get(key, "")
        if key in STUDENT_FIELD_KEYS and field.get("maps_to_student_field", True):
            student_row[key] = value
        else:
            custom_data[key] = value
    if not student_row.get("degree_code"):
        student_row["degree_code"] = student_row.get("branch_code", "")
    if not student_row.get("program_level"):
        student_row["program_level"] = "BTECH"
    primary_contact = str(response_data.get("primary_contact_person") or "").strip().lower()
    if primary_contact == "mother":
        student_row["parent_phone"] = str(response_data.get("mother_phone") or "")
        student_row["parent_email"] = str(response_data.get("mother_email") or "")
    else:
        student_row["parent_phone"] = str(response_data.get("father_phone") or "")
        student_row["parent_email"] = str(response_data.get("father_email") or "")

    existing = (
        supabase.table("students2025")
        .select("aadhaar_card_number,student_email,application_reference")
        .eq("aadhaar_card_number", student_id)
        .limit(1)
        .execute()
        .data
        or []
    )
    if existing:
        owner_email = (existing[0].get("student_email") or "").strip().lower()
        if owner_email and owner_email != actor_email:
            raise HTTPException(status_code=403, detail="You are not allowed to modify this application")
        if existing[0].get("application_reference"):
            student_row["application_reference"] = existing[0]["application_reference"]
        supabase.table("students2025").update(student_row).eq("aadhaar_card_number", student_id).execute()
    else:
        supabase.table("students2025").insert(student_row).execute()

    response_id = _new_id()
    response_row = {
        "id": response_id,
        "form_id": form_id,
        "student_id": student_id,
        "submitted_by": actor_email,
        "response_data": {**response_data, "_custom": custom_data},
        "status": "submitted",
        "created_at": _db_now(),
        "updated_at": _db_now(),
    }
    try:
        supabase.table("form_responses").insert(response_row).execute()
    except Exception:
        # The default admission form remains usable before the optional forms
        # migration is applied; the student row is still the source of truth.
        pass
    return {
        "response_id": response_id,
        "form_id": form_id,
        "student_id": student_id,
        "application_reference": student_row["application_reference"],
        "status": "submitted",
    }


def list_form_responses(form_id: str) -> list[dict[str, Any]]:
    return supabase.table("form_responses").select("*").eq("form_id", form_id).execute().data or []


def get_student_form_response(
    form_id: str,
    current_user: dict[str, Any],
    include_private_document_fields: bool = False,
) -> dict[str, Any] | None:
    actor_email = (current_user.get("username") or "").strip().lower()
    if not actor_email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    form = get_form(form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    response_row: dict[str, Any] | None = None
    try:
        rows = (
            supabase.table("form_responses")
            .select("*")
            .eq("form_id", form_id)
            .eq("submitted_by", actor_email)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
            .data
            or []
        )
        response_row = rows[0] if rows else None
    except Exception:
        response_row = None

    if not response_row and form.get("id") == "default-admission":
        try:
            students = (
                supabase.table("students2025")
                .select("*")
                .eq("student_email", actor_email)
                .order("Time_updated", desc=True)
                .limit(1)
                .execute()
                .data
                or []
            )
        except Exception:
            students = []
        if not students:
            return None
        student = students[0]
        response_data = {
            field.get("field_key"): student.get(field.get("field_key"), "")
            for field in form.get("fields", [])
            if field.get("field_key") and field.get("field_type") != "file"
        }
        response_row = {
            "id": None,
            "form_id": form_id,
            "student_id": student.get("aadhaar_card_number"),
            "submitted_by": actor_email,
            "response_data": response_data,
            "status": student.get("status") or "submitted",
            "created_at": student.get("created_at"),
            "updated_at": student.get("updated_at") or student.get("Time_updated"),
            "application_reference": student.get("application_reference"),
        }

    documents: list[dict[str, Any]] = []
    student_id = response_row.get("student_id")
    if student_id:
        try:
            columns = "id,student_id,doc_type,provider,mime_type,size_bytes,status,created_at,updated_at"
            if include_private_document_fields:
                columns = "*"
            documents = (
                supabase.table("documents")
                .select(columns)
                .eq("student_id", student_id)
                .execute()
                .data
                or []
            )
        except Exception:
            documents = []

    return {
        **response_row,
        "form": {
            "id": form.get("id"),
            "title": form.get("title"),
            "slug": form.get("slug"),
            "description": form.get("description"),
        },
        "documents": documents,
    }
