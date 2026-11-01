from __future__ import annotations

import asyncio
import base64
import concurrent.futures
import json
import logging
import mimetypes
import os
import tempfile
from datetime import datetime
from io import BytesIO
from typing import Any
from uuid import uuid4

import fitz
from PIL import Image
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass

from config.settings import GEMINI_BATCH_POLL_INTERVAL, GEMINI_MODEL, GOOGLE_API_KEY
from database import supabase
from services.admissions_2026 import ADMISSIONS_TABLE
from extractor import parse_gemini_json
from services.document_service import fetch_student, parse_document_ref
from services.engine_service import (
    _db_now,
    _get_document_rows,
    _insert,
    _list_rows,
    _prompt_for_doc,
    parse_extraction,
    replace_comparison_results,
)
from services.notification_service import notify_user

logger = logging.getLogger(__name__)

VALID_ADMISSIONS_COLUMNS = {
    "aadhaar_link", "address_district", "address_dno", "address_mandal",
    "address_pincode", "address_state", "address_street", "address_village_town",
    "admission_category", "admission_year", "allotment_order", "application_reference",
    "blood_group", "branch", "candidate_pic", "caste_as_per_tc", "category_name",
    "ch1", "ch2", "chlab", "consent", "date_of_birth", "eapcet_ht_no", "eapcet_rank",
    "eapcet_rank_card_link", "ebc_status", "ews_status", "extraction_status",
    "father_email", "father_name", "father_phone", "father_profession_and_designation",
    "gender", "identification_mark_1", "identification_mark_2", "income",
    "jee_ht_no", "jee_mains_rank", "jee_rank_card_link", "joining_report",
    "m1", "m2", "m3", "m4", "minority", "mother_email", "mother_name",
    "mother_phone", "mother_profession_and_designation", "mother_tongue",
    "nationality", "p1", "p2", "parent_email", "parent_phone", "ph_status",
    "plab", "religion", "rural_urban", "scribe", "student_email", "student_name",
    "student_phone", "tenth_board_name", "tenth_ht_no", "tenth_maximum_marks",
    "tenth_memo_link", "tenth_month_year", "tenth_percentage", "tenth_school_name",
    "tenth_total_marks_cgpa", "transfer_certificate_link", "twelfth_board_name",
    "twelfth_college_name", "twelfth_ht_no", "twelfth_maximum_marks",
    "twelfth_memo_link", "twelfth_month_year", "twelfth_percentage",
    "twelfth_total_marks", "verification_remarks"
}

TERMINAL_STATES = {
    "JOB_STATE_SUCCEEDED",
    "JOB_STATE_FAILED",
    "JOB_STATE_CANCELLED",
    "JOB_STATE_EXPIRED",
    "SUCCEEDED",
    "FAILED",
    "CANCELLED",
    "EXPIRED",
}
SUCCESS_STATES = {"JOB_STATE_SUCCEEDED", "SUCCEEDED", "COMPLETED"}


def _now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _json_params(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def _task_row(task_id: str) -> dict[str, Any] | None:
    rows = supabase.table("tasks").select("*").eq("id", task_id).execute().data or []
    return rows[0] if rows else None


def _batch_job_row(batch_job_id: str) -> dict[str, Any] | None:
    rows = supabase.table("gemini_batch_jobs").select("*").eq("id", batch_job_id).execute().data or []
    return rows[0] if rows else None


def _batch_job_for_task(task_id: str) -> dict[str, Any] | None:
    rows = supabase.table("gemini_batch_jobs").select("*").eq("task_id", task_id).execute().data or []
    return rows[0] if rows else None


def _update_task(task_id: str, payload: dict[str, Any]) -> None:
    supabase.table("tasks").update(payload).eq("id", task_id).execute()


def _update_batch_job(batch_job_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    payload = {**payload, "updated_at": _now()}
    rows = supabase.table("gemini_batch_jobs").update(payload).eq("id", batch_job_id).execute().data or []
    return rows[0] if rows else _batch_job_row(batch_job_id)


async def _emit(username: str | None, payload: dict[str, Any]) -> None:
    if not username:
        return
    try:
        await notify_user(username, payload)
    except Exception:
        logger.exception("Failed to emit batch progress notification")


def _batch_progress_from_counts(state: str, total_docs: int, completed_docs: int) -> int:
    state = (state or "").upper()
    if state in SUCCESS_STATES:
        return 100
    if state in {"JOB_STATE_FAILED", "FAILED", "JOB_STATE_CANCELLED", "CANCELLED", "JOB_STATE_EXPIRED", "EXPIRED"}:
        return 100
    if total_docs > 0 and completed_docs > 0:
        return min(95, 80 + int((completed_docs / total_docs) * 15))
    if state in {"JOB_STATE_RUNNING", "RUNNING"}:
        return 40
    if state in {"JOB_STATE_PENDING", "PENDING", "STATE_UNSPECIFIED"}:
        return 25
    return 20


def _get_image_bytes_from_ref(ref_str: str, storage_providers: dict[str, Any]) -> tuple[bytes, str] | None:
    try:
        parsed_ref = parse_document_ref(ref_str)
        if not parsed_ref:
            return None

        provider = storage_providers.get(parsed_ref.provider)
        if not provider:
            return None

        content = provider.get_bytes(parsed_ref.key)
        if not content:
            return None

        content_type = mimetypes.guess_type(parsed_ref.key)[0] or "image/jpeg"
        if content_type == "application/pdf" or parsed_ref.key.lower().endswith(".pdf") or content[:4] == b"%PDF":
            doc = fitz.open(stream=content, filetype="pdf")
            if len(doc) == 0:
                return None
            page = doc[0]
            pix = page.get_pixmap(dpi=150)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        else:
            img = Image.open(BytesIO(content))

        if img.mode != "RGB":
            img = img.convert("RGB")

        max_dim = 1800
        if max(img.size) > max_dim:
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

        out_buf = BytesIO()
        img.save(out_buf, format="JPEG", quality=85)
        return out_buf.getvalue(), "image/jpeg"
    except Exception:
        logger.exception("Error fetching batch input bytes for %s", ref_str)
        return None


def create_batch_request_payload(
    batch_key: str,
    prompt: str,
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
) -> dict[str, Any]:
    base64_data = base64.b64encode(image_bytes).decode("utf-8")
    return {
        "key": batch_key,
        "request": {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": base64_data,
                            }
                        },
                    ],
                }
            ],
            "generation_config": {
                "response_mime_type": "application/json",
                "temperature": 0.1,
            },
        },
    }


def parse_gemini_response_text(text: str) -> dict[str, Any]:
    try:
        return parse_gemini_json(text)
    except Exception as exc:
        return {"error": str(exc), "raw_text": text or ""}


def _extract_response_text(item: dict[str, Any]) -> tuple[str, str]:
    response = item.get("response") or item.get("result") or {}
    error = item.get("error") or response.get("error") or ""
    if error:
        return "", json.dumps(error) if isinstance(error, dict) else str(error)

    candidates = response.get("candidates") or []
    if candidates:
        content = candidates[0].get("content") or {}
        parts = content.get("parts") or []
        for part in parts:
            if isinstance(part, dict) and part.get("text"):
                return str(part["text"]), ""
    return "", "No output"


def _extract_batch_state(job: Any) -> str:
    state = getattr(job, "state", None)
    if hasattr(state, "name"):
        return str(state.name).upper()
    if state:
        return str(state).upper()
    data = _to_dict(job)
    return str(data.get("state") or "STATE_UNSPECIFIED").upper()


def _extract_output_file_name(job: Any) -> str | None:
    for attr in ("dest", "output", "output_info", "outputInfo"):
        obj = getattr(job, attr, None)
        if obj is not None:
            for field in ("file_name", "fileName", "responses_file", "responsesFile"):
                val = getattr(obj, field, None)
                if val:
                    return str(val)

    data = _to_dict(job)
    for key in ("dest", "output", "output_info", "outputInfo"):
        dest_data = data.get(key)
        if isinstance(dest_data, dict):
            val = dest_data.get("fileName") or dest_data.get("file_name") or dest_data.get("responsesFile") or dest_data.get("responses_file")
            if val:
                return str(val)
    return None


def _to_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    for attr in ("to_json_dict", "model_dump", "dict"):
        fn = getattr(value, attr, None)
        if callable(fn):
            try:
                data = fn()
                return data if isinstance(data, dict) else {}
            except Exception:
                continue
    return {}


class GeminiBatchService:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or GOOGLE_API_KEY
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is not set.")
        from google import genai
        self.client = genai.Client(api_key=self.api_key)

    def _client(self):
        return self.client

    def submit_batch_job(self, jsonl_file_path: str, display_name: str, model: str = GEMINI_MODEL) -> tuple[str, str]:
        client = self._client()
        try:
            from google.genai import types

            upload_config = types.UploadFileConfig(display_name=display_name, mime_type="application/jsonl")
        except Exception:
            upload_config = {"display_name": display_name, "mime_type": "application/jsonl"}

        uploaded_file = client.files.upload(file=jsonl_file_path, config=upload_config)
        uploaded_name = getattr(uploaded_file, "name", None)
        if not uploaded_name:
            raise RuntimeError("Gemini Files API did not return an uploaded file name")

        job = client.batches.create(
            model=model,
            src=uploaded_name,
            config={"display_name": display_name},
        )
        job_name = getattr(job, "name", None)
        if not job_name:
            raise RuntimeError("Gemini Batch API did not return a job name")
        return str(job_name), str(uploaded_name)

    def get_batch_status(self, job_name: str) -> tuple[str, str | None]:
        client = self._client()
        job = client.batches.get(name=job_name)
        return _extract_batch_state(job), _extract_output_file_name(job)

    def download_batch_results(self, output_file_name: str) -> list[dict[str, Any]]:
        client = self._client()
        try:
            content = client.files.download(file=output_file_name)
        except TypeError:
            content = client.files.download(name=output_file_name)

        if isinstance(content, bytes):
            text = content.decode("utf-8")
        elif isinstance(content, str):
            text = content
        else:
            text = getattr(content, "text", "")

        results: list[dict[str, Any]] = []
        for line in text.splitlines():
            if line.strip():
                results.append(json.loads(line))
        return results


async def submit_batch_extraction_for_students(
    student_ids: list[str],
    app,
    task_id: str,
    username: str | None,
) -> dict[str, Any]:
    providers = getattr(app.state, "storage_providers", {})
    batch_service = GeminiBatchService()
    batch_job_id = str(uuid4())
    temp_dir = tempfile.mkdtemp(prefix="admitme-gemini-batch-")
    jsonl_path = os.path.join(temp_dir, f"{task_id}.jsonl")

    _update_task(task_id, {"status": "processing", "progress": 5})

    # 1. Fetch student profiles in bulk
    students_list: list[dict[str, Any]] = []
    for i in range(0, len(student_ids), 200):
        chunk_ids = student_ids[i:i + 200]
        try:
            res = supabase.table(ADMISSIONS_TABLE).select("*").in_("aadhaar_card_number", chunk_ids).execute()
            students_list.extend(res.data or [])
        except Exception:
            logger.exception("Failed to bulk fetch students for batch submission")

    students_by_id: dict[str, dict[str, Any]] = {}
    for s in students_list:
        clean = "".join(c for c in str(s.get("aadhaar_card_number") or "") if c.isdigit())
        if clean:
            students_by_id[clean] = s
        raw = str(s.get("aadhaar_card_number") or "").strip()
        if raw:
            students_by_id[raw] = s

    # 2. Collect work items for all documents
    work_items: list[tuple[str, dict[str, Any], dict[str, Any], str, str]] = []
    for student_id in student_ids:
        clean = "".join(c for c in str(student_id or "") if c.isdigit())
        student = students_by_id.get(clean) or students_by_id.get(student_id)
        if not student:
            continue
        doc_rows = _get_document_rows(student)
        for doc in doc_rows:
            doc_type = doc["doc_type"]
            prompt, _ = _prompt_for_doc(doc_type, student)
            batch_key = f"{batch_job_id}:{uuid4().hex}"
            work_items.append((clean or student_id, student, doc, prompt, batch_key))

    # 3. Fetch images and build batch payloads in parallel (up to 10 workers)
    def _fetch_worker(item: tuple[str, dict[str, Any], dict[str, Any], str, str]):
        s_id, stud, doc, prmt, b_key = item
        ref_str = f"{doc['provider']}:{doc['object_key']}"
        try:
            img_data = _get_image_bytes_from_ref(ref_str, providers)
            if not img_data:
                return None
            img_bytes, mime_type = img_data
            run_payload = {
                "id": str(uuid4()),
                "student_id": s_id,
                "document_id": doc.get("document_id"),
                "doc_type": doc["doc_type"],
                "provider": doc.get("provider"),
                "object_key": doc.get("object_key"),
                "status": "submitted",
                "raw_output": {},
                "error": "",
                "batch_job_id": batch_job_id,
                "batch_key": b_key,
                "created_at": _db_now(),
                "updated_at": _db_now(),
            }
            entry = create_batch_request_payload(b_key, prmt, img_bytes, mime_type)
            return s_id, run_payload, entry
        except Exception:
            logger.exception("Failed to process document %s for student %s", ref_str, s_id)
            return None

    processed_runs: list[dict[str, Any]] = []
    batch_entries: list[dict[str, Any]] = []
    student_ids_with_docs: set[str] = set()

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        results = await asyncio.to_thread(lambda: list(executor.map(_fetch_worker, work_items)))

    for res in results:
        if res:
            s_id, run_payload, entry = res
            processed_runs.append(run_payload)
            batch_entries.append(entry)
            student_ids_with_docs.add(s_id)

    total_documents = len(batch_entries)
    total_students = len(student_ids_with_docs)
    if total_documents == 0:
        _update_task(task_id, {"status": "completed", "progress": 100, "result": "No documents found to extract."})
        await _emit(username, {"type": "extract_all_complete", "task_id": task_id, "message": "No documents found to extract."})
        return {
            "task_id": task_id,
            "batch_job_id": None,
            "total_students": 0,
            "total_documents": 0,
        }

    # 4. Bulk insert extraction_runs in chunks of 200
    for i in range(0, len(processed_runs), 200):
        chunk = processed_runs[i:i + 200]
        try:
            supabase.table("extraction_runs").insert(chunk).execute()
        except Exception:
            logger.exception("Failed to bulk insert extraction_runs chunk")

    # 5. Bulk update extraction_status to 'submitted' for students with docs
    active_ids = list(student_ids_with_docs)
    for i in range(0, len(active_ids), 200):
        chunk_ids = active_ids[i:i + 200]
        try:
            supabase.table(ADMISSIONS_TABLE).update({"extraction_status": "submitted"}).in_("aadhaar_card_number", chunk_ids).execute()
        except Exception:
            logger.exception("Failed to bulk update extraction_status to submitted")

    with open(jsonl_path, "w", encoding="utf-8") as handle:
        for entry in batch_entries:
            handle.write(json.dumps(entry) + "\n")

    _update_task(task_id, {"progress": 12})
    display_name = f"admitme-extract-all-{task_id}"
    job_name, input_file_name = await asyncio.to_thread(
        batch_service.submit_batch_job,
        jsonl_path,
        display_name,
        GEMINI_MODEL,
    )

    batch_row = _insert(
        "gemini_batch_jobs",
        {
            "id": batch_job_id,
            "task_id": task_id,
            "gemini_job_name": job_name,
            "input_file_name": input_file_name,
            "output_file_name": "",
            "model": GEMINI_MODEL,
            "state": "JOB_STATE_PENDING",
            "total_students": total_students,
            "total_documents": total_documents,
            "completed_documents": 0,
            "failed_documents": 0,
            "submitted_by": username or "",
            "error": "",
            "created_at": _now(),
            "updated_at": _now(),
            "submitted_at": _now(),
            "completed_at": None,
        },
    )

    params = _json_params((_task_row(task_id) or {}).get("params"))
    params.update(
        {
            "action": "extract-all",
            "batch_job_id": batch_job_id,
            "gemini_job_name": job_name,
            "total_students": total_students,
            "total_documents": total_documents,
        }
    )
    _update_task(task_id, {"status": "submitted", "progress": 20, "params": params})
    await _emit(
        username,
        {
            "type": "extract_all_submitted",
            "task_id": task_id,
            "batch_job_id": batch_job_id,
            "batch_state": "JOB_STATE_PENDING",
            "progress": 20,
            "total_students": total_students,
            "total_documents": total_documents,
            "completed_documents": 0,
            "failed_documents": 0,
            "message": f"Submitted {total_documents} documents to Gemini.",
        },
    )

    try:
        os.remove(jsonl_path)
        os.rmdir(temp_dir)
    except Exception:
        logger.debug("Could not clean up temporary batch JSONL", exc_info=True)

    return {
        "task_id": task_id,
        "batch_job_id": batch_job_id,
        "gemini_job_name": job_name,
        "total_students": total_students,
        "total_documents": total_documents,
        "batch_job": batch_row,
    }


async def poll_and_finalize_batch_job(batch_job_id: str, app, notify: bool = True) -> dict[str, Any]:
    batch_job = _batch_job_row(batch_job_id)
    if not batch_job:
        raise ValueError("Batch job not found")

    task_id = batch_job["task_id"]
    username = batch_job.get("submitted_by") or None
    job_name = batch_job.get("gemini_job_name")
    if not job_name:
        raise ValueError("Batch job has no Gemini job name")

    service = GeminiBatchService()
    state, output_file = await asyncio.to_thread(service.get_batch_status, job_name)
    total_docs = int(batch_job.get("total_documents") or 0)
    completed_docs = int(batch_job.get("completed_documents") or 0)
    progress = _batch_progress_from_counts(state, total_docs, completed_docs)

    payload: dict[str, Any] = {"state": state}
    if output_file:
        payload["output_file_name"] = output_file
    batch_job = _update_batch_job(batch_job_id, payload) or batch_job
    _update_task(task_id, {"status": "processing" if state not in TERMINAL_STATES else "processing", "progress": progress})

    if notify:
        await _emit(
            username,
            {
                "type": "extract_all_progress",
                "task_id": task_id,
                "batch_job_id": batch_job_id,
                "batch_state": state,
                "progress": progress,
                "total_documents": total_docs,
                "completed_documents": completed_docs,
                "failed_documents": int(batch_job.get("failed_documents") or 0),
                "message": f"Gemini batch state: {state}",
            },
        )

    if state not in TERMINAL_STATES:
        return {"state": state, "completed": False}

    if state not in SUCCESS_STATES:
        error = f"Gemini Batch Job ended with state {state}"
        _update_batch_job(batch_job_id, {"state": state, "error": error, "completed_at": _now()})
        _update_task(task_id, {"status": "failed", "progress": 100, "error": error})
        await _emit(username, {"type": "extract_all_failed", "task_id": task_id, "batch_job_id": batch_job_id, "message": error})
        return {"state": state, "completed": True, "failed": True}

    output_file_name = output_file or batch_job.get("output_file_name")
    if not output_file_name:
        raise RuntimeError("Gemini batch succeeded but no output file was returned")

    _update_task(task_id, {"status": "processing", "progress": 85})
    raw_results = await asyncio.to_thread(service.download_batch_results, output_file_name)
    result = await _finalize_batch_results(batch_job_id, raw_results, username)
    return {"state": state, "completed": True, **result}


async def _finalize_batch_results(batch_job_id: str, raw_results: list[dict[str, Any]], username: str | None) -> dict[str, Any]:
    batch_job = _batch_job_row(batch_job_id)
    if not batch_job:
        raise ValueError("Batch job not found")

    task_id = batch_job["task_id"]
    page_size = 1000
    runs: list[dict[str, Any]] = []
    start = 0
    while True:
        chunk = (
            supabase.table("extraction_runs")
            .select("*")
            .eq("batch_job_id", batch_job_id)
            .range(start, start + page_size - 1)
            .execute()
            .data
            or []
        )
        if not chunk:
            break
        runs.extend(chunk)
        if len(chunk) < page_size:
            break
        start += page_size
    runs_by_key = {row.get("batch_key"): row for row in runs if row.get("batch_key")}
    student_parsed_rows: dict[str, list[dict[str, Any]]] = {}
    student_has_failures: dict[str, bool] = {}
    student_field_updates: dict[str, dict[str, Any]] = {}
    all_parsed_rows: list[dict[str, Any]] = []
    completed_docs = 0
    failed_docs = 0

    for item in raw_results:
        batch_key = item.get("key") or item.get("custom_id")
        run = runs_by_key.get(batch_key)
        if not run:
            continue

        student_id = run["student_id"]
        doc_type = run["doc_type"]
        raw_text, error_msg = _extract_response_text(item)
        raw_output = parse_gemini_response_text(raw_text) if raw_text else {"error": error_msg or "No output"}
        status = "failed" if raw_output.get("error") else "completed"
        completed_docs += 1

        if status == "failed":
            failed_docs += 1
            student_has_failures[student_id] = True

        parsed_fields = parse_extraction(doc_type, raw_output)
        parsed_fields.pop("aadhaar_card_number", None)
        if parsed_fields:
            student_field_updates.setdefault(student_id, {}).update(parsed_fields)

        parsed_row = {
            "id": str(uuid4()),
            "extraction_run_id": run["id"],
            "student_id": student_id,
            "doc_type": doc_type,
            "parsed_fields": parsed_fields,
            "confidence": {key: "extracted" for key in parsed_fields},
            "created_at": _db_now(),
        }
        all_parsed_rows.append(parsed_row)
        student_parsed_rows.setdefault(student_id, []).append(parsed_row)

    # 1. Bulk insert parsed_extractions in chunks of 200
    for i in range(0, len(all_parsed_rows), 200):
        chunk = all_parsed_rows[i:i + 200]
        try:
            supabase.table("parsed_extractions").insert(chunk).execute()
        except Exception:
            logger.exception("Failed to bulk insert parsed_extractions chunk")

    # 2. Update admissions_2026 once per student with all merged extracted fields
    for student_id, fields in student_field_updates.items():
        clean_id = "".join(c for c in str(student_id or "") if c.isdigit())
        safe_fields = {
            k: str(v).strip()
            for k, v in fields.items()
            if k in VALID_ADMISSIONS_COLUMNS and k != "aadhaar_card_number" and v not in (None, "")
        }
        if not safe_fields:
            continue
        try:
            res = supabase.table(ADMISSIONS_TABLE).update(safe_fields).eq("aadhaar_card_number", clean_id).execute()
            if not res.data and student_id != clean_id:
                supabase.table(ADMISSIONS_TABLE).update(safe_fields).eq("aadhaar_card_number", student_id).execute()
        except Exception:
            logger.exception("Failed to update admissions_2026 for student %s", student_id)

    missing_runs = [row for key, row in runs_by_key.items() if key not in {item.get("key") or item.get("custom_id") for item in raw_results}]
    for run in missing_runs:
        failed_docs += 1
        student_has_failures[run["student_id"]] = True

    # 3. Update comparison_results and final extraction_status once per student
    for student_id in {row["student_id"] for row in runs}:
        student = fetch_student(student_id)
        if not student:
            continue
        parsed_rows = student_parsed_rows.get(student_id) or []
        try:
            replace_comparison_results(student, parsed_rows)
        except Exception:
            logger.exception("Failed comparison results for student %s", student_id)
        final_status = "failed" if student_has_failures.get(student_id) else "completed"
        clean_id = "".join(c for c in str(student_id or "") if c.isdigit())
        try:
            res = supabase.table(ADMISSIONS_TABLE).update({"extraction_status": final_status}).eq("aadhaar_card_number", clean_id).execute()
            if not res.data and student_id != clean_id:
                supabase.table(ADMISSIONS_TABLE).update({"extraction_status": final_status}).eq("aadhaar_card_number", student_id).execute()
        except Exception:
            logger.exception("Failed to update extraction_status for student %s", student_id)

    total_docs = int(batch_job.get("total_documents") or len(runs))
    _update_batch_job(
        batch_job_id,
        {
            "state": "JOB_STATE_SUCCEEDED",
            "completed_documents": min(total_docs, completed_docs),
            "failed_documents": failed_docs,
            "completed_at": _now(),
        },
    )
    _update_task(
        task_id,
        {
            "status": "completed",
            "progress": 100,
            "result": f"Batch extracted {completed_docs} documents for {len({row['student_id'] for row in runs})} students.",
        },
    )
    await _emit(
        username,
        {
            "type": "extract_all_complete",
            "task_id": task_id,
            "batch_job_id": batch_job_id,
            "batch_state": "JOB_STATE_SUCCEEDED",
            "progress": 100,
            "total_documents": total_docs,
            "completed_documents": min(total_docs, completed_docs),
            "failed_documents": failed_docs,
            "message": f"Bulk extraction completed: {completed_docs}/{total_docs} documents processed.",
        },
    )
    return {"processed_documents": completed_docs, "failed_documents": failed_docs}


async def poll_batch_job_until_terminal(batch_job_id: str, app) -> None:
    while True:
        try:
            result = await poll_and_finalize_batch_job(batch_job_id, app)
            if result.get("completed"):
                return
        except Exception as exc:
            batch_job = _batch_job_row(batch_job_id)
            task_id = batch_job.get("task_id") if batch_job else ""
            username = batch_job.get("submitted_by") if batch_job else None
            error = str(exc)
            logger.exception("Batch polling failed for batch_job_id=%s", batch_job_id)
            if batch_job:
                _update_batch_job(batch_job_id, {"state": "JOB_STATE_FAILED", "error": error, "completed_at": _now()})
            if task_id:
                _update_task(task_id, {"status": "failed", "progress": 100, "error": error})
            await _emit(username, {"type": "extract_all_failed", "task_id": task_id, "batch_job_id": batch_job_id, "message": error})
            return
        await asyncio.sleep(max(10, GEMINI_BATCH_POLL_INTERVAL))


async def resume_unfinished_batch_jobs(app) -> int:
    try:
        rows = supabase.table("gemini_batch_jobs").select("*").execute().data or []
    except Exception as exc:
        logger.warning(f"Could not load Gemini batch jobs for startup resume: {exc}")
        return 0

    count = 0
    for row in rows:
        state = (row.get("state") or "").upper()
        if state in TERMINAL_STATES:
            continue
        asyncio.create_task(poll_batch_job_until_terminal(row["id"], app))
        count += 1
    if count:
        logger.info("Resumed %s unfinished Gemini batch job(s)", count)
    return count


def task_status_with_batch(task_id: str) -> list[dict[str, Any]] | dict[str, str]:
    task = _task_row(task_id)
    if not task:
        return {"error": "Task not found"}

    batch_job = _batch_job_for_task(task_id)
    if batch_job:
        task["batch_job_id"] = batch_job.get("id")
        task["batch_state"] = batch_job.get("state")
        task["total_students"] = batch_job.get("total_students")
        task["total_documents"] = batch_job.get("total_documents")
        task["completed_documents"] = batch_job.get("completed_documents")
        task["failed_documents"] = batch_job.get("failed_documents")
        task["submitted_at"] = batch_job.get("submitted_at")
        task["completed_at"] = batch_job.get("completed_at")
    return [task]
