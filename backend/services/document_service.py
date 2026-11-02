from __future__ import annotations

import hashlib
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from database import supabase
from storage.base import DocumentRef
from storage.gdrive import GoogleDriveStorageProvider
from services.catalog_service import normalize_branch_code, normalize_student_branch_fields
from services.status_service import canonicalize_student_status, normalize_status
from services.admissions_2026 import ADMISSIONS_TABLE


LEGACY_DOC_FIELD_MAP = {
    "aadhaar": "aadhaar_link",
    "transfer_certificate": "transfer_certificate_link",
    "tenth_memo": "tenth_memo_link",
    "twelfth_memo": "twelfth_memo_link",
    "jee_rank_card": "jee_rank_card_link",
    "eapcet_rank_card": "eapcet_rank_card_link",
}

ALLOWED_UPLOAD_MIME_TYPES = {"application/pdf", "image/png", "image/jpeg"}
ALLOWED_UPLOAD_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}


def _db_now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

def _normalize_student_record(student: dict[str, Any]) -> dict[str, Any]:
    row = canonicalize_student_status(student)
    row = normalize_student_branch_fields(row)
    if not row.get("student_type"):
        row["student_type"] = "regular"
    if not row.get("ht_no"):
        row["ht_no"] = (
            row.get("eapcet_ht_no")
            or row.get("jee_ht_no")
            or row.get("application_reference")
            or row.get("aadhaar_card_number")
        )
    if not row.get("branch_code"):
        row["branch_code"] = row.get("branch")
    if not row.get("degree_code"):
        row["degree_code"] = row.get("branch")
    if not row.get("program_level"):
        row["program_level"] = "BTECH"
    return row


def normalize_doc_type(doc_type: str) -> str:
    normalized = (doc_type or "").strip().lower().replace(" ", "_")
    if normalized not in LEGACY_DOC_FIELD_MAP:
        raise ValueError(f"Unsupported document type: {doc_type}")
    return normalized


def parse_document_ref(raw_value: str) -> DocumentRef | None:
    if not raw_value:
        return None

    value = raw_value.strip()
    if ":" in value and not value.lower().startswith("http"):
        provider, key = value.split(":", 1)
        provider = provider.strip().lower()
        key = key.strip()
        if provider and key:
            return DocumentRef(provider=provider, key=key)

    file_id = GoogleDriveStorageProvider.extract_file_id(value)
    if file_id:
        return DocumentRef(provider="gdrive", key=file_id)

    return None


def build_object_key(student_id: str, doc_type: str, filename: str) -> str:
    ext = ""
    if filename and "." in filename:
        ext = filename.rsplit(".", 1)[-1].lower()
        ext = f".{ext}"
    elif doc_type.endswith("memo"):
        ext = ".pdf"
    else:
        ext = ".png"

    safe_student_id = (student_id or "unknown").replace("/", "_").replace("..", "_")
    return f"students/{safe_student_id}/{doc_type}_{uuid4().hex}{ext}"


def calculate_checksum(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def guess_mime_type(filename: str | None) -> str:
    if filename:
        guessed, _ = mimetypes.guess_type(filename)
        if guessed:
            return guessed
    return "application/octet-stream"

def sniff_mime_type(content: bytes) -> str | None:
    if not content:
        return None
    if content.startswith(b"%PDF-"):
        return "application/pdf"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if content[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    return None

def validate_upload_and_detect_mime(
    content: bytes,
    filename: str | None,
    declared_mime_type: str | None = None,
) -> str:
    ext = Path(filename or "").suffix.lower()
    if ext and ext not in ALLOWED_UPLOAD_EXTENSIONS:
        raise ValueError("Unsupported file extension. Allowed: .pdf, .png, .jpg, .jpeg")

    sniffed = sniff_mime_type(content)
    guessed = guess_mime_type(filename)
    normalized_declared = (declared_mime_type or "").strip().lower()
    if normalized_declared == "image/jpg":
        normalized_declared = "image/jpeg"

    candidate = sniffed
    if not candidate and guessed in ALLOWED_UPLOAD_MIME_TYPES:
        candidate = guessed
    if not candidate and normalized_declared in ALLOWED_UPLOAD_MIME_TYPES:
        candidate = normalized_declared
    if candidate not in ALLOWED_UPLOAD_MIME_TYPES:
        raise ValueError("Unsupported file type. Allowed: PDF, PNG, JPG, JPEG")

    if (
        normalized_declared
        and normalized_declared in ALLOWED_UPLOAD_MIME_TYPES
        and candidate != normalized_declared
    ):
        raise ValueError("Uploaded file content does not match declared MIME type")

    return candidate


def fetch_student(student_id: str) -> dict[str, Any] | None:
    try:
        clean_id = "".join(c for c in str(student_id or "") if c.isdigit())
        if clean_id:
            response = (
                supabase.table(ADMISSIONS_TABLE)
                .select("*")
                .eq("aadhaar_card_number", clean_id)
                .limit(1)
                .execute()
            )
            if response.data:
                return _normalize_student_record(response.data[0])

        raw_id = str(student_id or "").strip()
        if raw_id:
            response = (
                supabase.table(ADMISSIONS_TABLE)
                .select("*")
                .eq("aadhaar_card_number", raw_id)
                .limit(1)
                .execute()
            )
            if response.data:
                return _normalize_student_record(response.data[0])
    except Exception:
        return None
    return None


def list_students_for_role(current_user: dict[str, Any]) -> list[dict[str, Any]]:
    role = (current_user.get("role") or "").lower()
    username = (current_user.get("username") or "").strip().lower()

    if role == "admin":
        query = supabase.table(ADMISSIONS_TABLE).select("*")
    elif role == "student":
        query = (
            supabase.table(ADMISSIONS_TABLE)
            .select("*")
            .eq("student_email", username)
        )
    else:
        try:
            role = normalize_branch_code(role)
        except ValueError:
            pass

        query = (
            supabase.table(ADMISSIONS_TABLE)
            .select("*")
            .eq("branch", role.upper())
        )

    all_rows: list[dict[str, Any]] = []
    start = 0
    chunk_size = 1000

    while True:
        chunk = query.range(start, start + chunk_size - 1).execute()
        rows = chunk.data or []
        all_rows.extend(_normalize_student_record(row) for row in rows)
        if len(rows) < chunk_size:
            break
        start += chunk_size

    return all_rows


def get_document_row(student_id: str, doc_type: str) -> dict[str, Any] | None:
    try:
        response = (
            supabase.table("documents")
            .select("*")
            .eq("student_id", student_id)
            .eq("doc_type", doc_type)
            .order("updated_at", desc=True)
            .limit(1)
            .execute()
        )
        if response.data:
            return response.data[0]
    except Exception:
        return None
    return None


def create_or_update_document(
    student_id: str,
    doc_type: str,
    provider: str,
    object_key: str,
    mime_type: str,
    size_bytes: int,
    checksum: str,
    status: str = "submitted",
) -> dict[str, Any]:
    now = _db_now()
    payload = {
        "student_id": student_id,
        "doc_type": doc_type,
        "provider": provider,
        "object_key": object_key,
        "mime_type": mime_type,
        "size_bytes": size_bytes,
        "checksum": checksum,
        "status": normalize_status(status),
        "updated_at": now,
        "created_at": now,
    }

    # Supabase upsert requires constraints; fallback to delete+insert for compatibility.
    try:
        existing = get_document_row(student_id, doc_type)
        if existing and existing.get("id"):
            (
                supabase.table("documents")
                .update(payload)
                .eq("id", existing["id"])
                .execute()
            )
            return {**existing, **payload}

        inserted = supabase.table("documents").insert(payload).execute()
        if inserted.data:
            return inserted.data[0]
    except Exception:
        pass

    return payload


def resolve_student_document_ref(student: dict[str, Any], student_id: str, doc_type: str) -> DocumentRef | None:
    document_row = get_document_row(student_id, doc_type)
    if document_row and document_row.get("provider") and document_row.get("object_key"):
        return DocumentRef(
            provider=document_row["provider"],
            key=document_row["object_key"],
        )

    legacy_field = LEGACY_DOC_FIELD_MAP.get(doc_type)
    if not legacy_field:
        return None

    legacy_value = (student or {}).get(legacy_field)
    return parse_document_ref(legacy_value)


def migrate_legacy_documents(
    students: list[dict[str, Any]],
    target_storage,
    providers: dict[str, Any],
    limit: int | None = None,
) -> dict[str, Any]:
    migrated = 0
    failed = 0
    skipped = 0
    failures: list[dict[str, str]] = []

    max_items = limit if (limit is not None and limit > 0) else None

    for student in students:
        student_id = student.get("aadhaar_card_number")
        if not student_id:
            skipped += 1
            continue

        for doc_type, legacy_field in LEGACY_DOC_FIELD_MAP.items():
            if max_items is not None and migrated >= max_items:
                return {
                    "migrated": migrated,
                    "failed": failed,
                    "skipped": skipped,
                    "failures": failures,
                }

            existing = get_document_row(student_id, doc_type)
            if existing:
                skipped += 1
                continue

            legacy_value = student.get(legacy_field)
            parsed = parse_document_ref(legacy_value)
            if not parsed:
                skipped += 1
                continue

            source_provider = providers.get(parsed.provider)
            if not source_provider:
                failed += 1
                failures.append({
                    "student_id": student_id,
                    "doc_type": doc_type,
                    "reason": f"Provider not configured: {parsed.provider}",
                })
                continue

            try:
                content = source_provider.get_bytes(parsed.key)
                if not content:
                    raise ValueError("Empty content")

                object_key = build_object_key(student_id, doc_type, f"{doc_type}.pdf")
                saved_key = target_storage.save(object_key, content, content_type="application/octet-stream")
                checksum = calculate_checksum(content)

                create_or_update_document(
                    student_id=student_id,
                    doc_type=doc_type,
                    provider=target_storage.name,
                    object_key=saved_key,
                    mime_type="application/octet-stream",
                    size_bytes=len(content),
                    checksum=checksum,
                    status="submitted",
                )
                migrated += 1
            except Exception as exc:
                failed += 1
                failures.append({
                    "student_id": student_id,
                    "doc_type": doc_type,
                    "reason": str(exc),
                })

    return {
        "migrated": migrated,
        "failed": failed,
        "skipped": skipped,
        "failures": failures,
    }
