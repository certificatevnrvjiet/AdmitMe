from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File, Request, Response, status

from database import supabase
from models.ApplicationModel import StudentApplicationRequest, StudentApplicationResponse
from models.DocumentModel import DocumentUploadResponse
from services.auth_service import get_current_user, is_student_owner, is_student_user
from services.catalog_service import to_db_branch_code, to_db_program_level
from services.status_service import normalize_status
from services.document_service import (
    LEGACY_DOC_FIELD_MAP,
    build_object_key,
    calculate_checksum,
    create_or_update_document,
    fetch_student,
    normalize_doc_type,
    validate_upload_and_detect_mime,
)
from routers.engines import queue_engine_run

router = APIRouter()

MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024
DEPRECATION_SUNSET = "Wed, 31 Dec 2026 23:59:59 GMT"


def _build_application_reference(student_id: str) -> str:
    return f"ADM-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{student_id[-4:]}"


def _db_now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _require_student_user(current_user: dict):
    if not is_student_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only authenticated student users can submit applications",
        )


def _set_deprecation_headers(response: Response, successor_path: str):
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = DEPRECATION_SUNSET
    response.headers["Link"] = f'<{successor_path}>; rel="successor-version"'


async def _create_application_core(
    payload: StudentApplicationRequest,
    current_user: dict,
) -> StudentApplicationResponse:
    _require_student_user(current_user)

    actor_email = (current_user.get("username") or "").strip().lower()
    student_email = str(payload.student_email or "").strip().lower()
    if not actor_email or actor_email != student_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student users can submit applications only for their own email",
        )

    student_id = payload.aadhaar_card_number
    application_reference = _build_application_reference(student_id)

    parent_email = payload.father_email
    parent_phone = payload.father_phone
    if (payload.primary_contact_person or "").strip().lower() == "mother":
        parent_email = payload.mother_email
        parent_phone = payload.mother_phone

    branch_code = to_db_branch_code(payload.branch_code)
    degree_code = to_db_branch_code(payload.degree_code or payload.branch_code)
    program_level = to_db_program_level(payload.program_level)

    existing = (
        supabase.table("students2025")
        .select("aadhaar_card_number,student_email,application_reference")
        .eq("aadhaar_card_number", student_id)
        .limit(1)
        .execute()
    )
    existing_row = existing.data[0] if existing.data else None
    if existing_row:
        owner_email = (existing_row.get("student_email") or "").strip().lower()
        if owner_email and owner_email != actor_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to modify this application",
            )
        application_reference = existing_row.get("application_reference") or application_reference

    student_row = {
        "student_name": payload.student_name,
        "father_name": payload.father_name,
        "mother_name": payload.mother_name,
        "date_of_birth": payload.date_of_birth,
        "gender": payload.gender,
        "aadhaar_card_number": payload.aadhaar_card_number,
        "program_level": program_level,
        "degree_code": degree_code,
        "branch_code": branch_code,
        "admission_category": payload.admission_category,
        "application_reference": application_reference,
        "status": normalize_status("submitted"),
        "Time_updated": _db_now(),
        "tenth_board_name": payload.tenth_board_name,
        "twelfth_board_name": payload.twelfth_board_name,
        "eapcet_ht_no": payload.eapcet_ht_no,
        "eapcet_rank": payload.eapcet_rank,
        "jee_ht_no": payload.jee_ht_no,
        "jee_mains_rank": payload.jee_mains_rank,
        "mother_tongue": payload.mother_tongue,
        "student_phone": payload.student_phone,
        "father_phone": payload.father_phone,
        "mother_phone": payload.mother_phone,
        "student_email": student_email,
        "father_email": str(payload.father_email or ""),
        "mother_email": str(payload.mother_email or ""),
        "parent_email": str(parent_email or ""),
        "parent_phone": str(parent_phone or ""),
        "father_profession_and_designation": payload.father_profession_and_designation,
        "mother_profession_and_designation": payload.mother_profession_and_designation,
        "address_dno": payload.address_dno,
        "address_street": payload.address_street,
        "address_village_town": payload.address_village_town,
        "address_mandal": payload.address_mandal,
        "address_district": payload.address_district,
        "address_state": payload.address_state,
        "address_pincode": payload.address_pincode,
        "rural_urban": payload.rural_urban,
        "ews_status": payload.ews_status,
        "category_name": payload.category_name,
        "caste_as_per_tc": payload.caste_as_per_tc,
        "ebc_status": payload.ebc_status,
        "income": payload.income,
        "minority": payload.minority,
        "blood_group": payload.blood_group,
        "ph_status": payload.ph_status,
        "scribe": payload.scribe,
        "student_type": "regular",
    }

    if existing_row:
        (
            supabase.table("students2025")
            .update(student_row)
            .eq("aadhaar_card_number", student_id)
            .execute()
        )
    else:
        supabase.table("students2025").insert(student_row).execute()

    return StudentApplicationResponse(
        application_reference=application_reference,
        student_id=student_id,
        status=normalize_status("submitted"),
    )


async def _upload_application_document_core(
    student_id: str,
    doc_type: str,
    request: Request,
    file: UploadFile,
    current_user: dict,
) -> DocumentUploadResponse:
    _require_student_user(current_user)

    student = fetch_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Application not found. Submit application form first.")

    if not is_student_owner(current_user, student):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to upload documents for this application",
        )

    normalized_doc_type = normalize_doc_type(doc_type)
    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(payload) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds max size of 5MB")

    try:
        content_type = validate_upload_and_detect_mime(payload, file.filename, file.content_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    storage = request.app.state.storage
    object_key = build_object_key(student_id, normalized_doc_type, file.filename or "")
    saved_key = storage.save(object_key, payload, content_type=content_type)
    checksum = calculate_checksum(payload)

    document_row = create_or_update_document(
        student_id=student_id,
        doc_type=normalized_doc_type,
        provider=storage.name,
        object_key=saved_key,
        mime_type=content_type,
        size_bytes=len(payload),
        checksum=checksum,
        status=normalize_status("submitted"),
    )

    legacy_field = LEGACY_DOC_FIELD_MAP.get(normalized_doc_type)
    if legacy_field:
        (
            supabase.table("students2025")
            .update({
                legacy_field: f"{storage.name}:{saved_key}",
                "Time_updated": _db_now(),
            })
            .eq("aadhaar_card_number", student_id)
            .execute()
        )

    return DocumentUploadResponse(
        document_id=document_row.get("id"),
        doc_type=normalized_doc_type,
        status=document_row.get("status", normalize_status("submitted")),
        provider=document_row.get("provider", storage.name),
        object_key=document_row.get("object_key", saved_key),
        preview_url=f"/students/{student_id}/documents/{normalized_doc_type}",
    )


@router.post("/applications", response_model=StudentApplicationResponse)
async def create_student_application(
    payload: StudentApplicationRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    response = await _create_application_core(payload, current_user)
    queue_engine_run(background_tasks, response.student_id, request, current_user, [])
    return response


@router.post("/public/applications", response_model=StudentApplicationResponse)
async def create_student_application_legacy(
    payload: StudentApplicationRequest,
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    _set_deprecation_headers(response, "/applications")
    result = await _create_application_core(payload, current_user)
    queue_engine_run(background_tasks, result.student_id, request, current_user, [])
    return result


@router.post("/applications/{student_id}/documents/{doc_type}", response_model=DocumentUploadResponse)
async def upload_application_document(
    student_id: str,
    doc_type: str,
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    result = await _upload_application_document_core(student_id, doc_type, request, file, current_user)
    queue_engine_run(background_tasks, student_id, request, current_user, [result.doc_type])
    return result


@router.post("/public/applications/{student_id}/documents/{doc_type}", response_model=DocumentUploadResponse)
async def upload_application_document_legacy(
    student_id: str,
    doc_type: str,
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    _set_deprecation_headers(response, f"/applications/{student_id}/documents/{doc_type}")
    result = await _upload_application_document_core(student_id, doc_type, request, file, current_user)
    queue_engine_run(background_tasks, student_id, request, current_user, [result.doc_type])
    return result
