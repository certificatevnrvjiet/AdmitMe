from __future__ import annotations

import asyncio
import logging
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request

from database import supabase
from services.admissions_2026 import ADMISSIONS_TABLE
from models.EngineModel import ComparisonOverrideRequest, EngineRunRequest
from services.auth_service import can_access_student_record, get_current_user
from services.document_service import fetch_student
from services.engine_service import get_engine_summary, run_engine_for_student, update_comparison_override
from services.notification_service import notify_user

router = APIRouter()
logger = logging.getLogger(__name__)


async def engine_task_logic(task_id: str, student_id: str, app, username: str, doc_types: list[str] | None = None):
    try:
        supabase.table("tasks").update({"status": "processing", "progress": 10}).eq("id", task_id).execute()
        result = await run_engine_for_student(student_id, app, username=username, doc_types=doc_types)
        supabase.table("tasks").update({
            "status": "completed",
            "progress": 100,
            "result": f"{len(result.get('comparison_results', []))} comparison fields generated",
        }).eq("id", task_id).execute()
        await notify_user(username, {
            "type": "engine_complete",
            "task_id": task_id,
            "student_id": student_id,
            "message": "Extraction, parsing, and comparison completed.",
        })
    except Exception as exc:
        logger.exception("Engine task failed for student_id=%s task_id=%s", student_id, task_id)
        try:
            supabase.table("tasks").update({
                "status": "failed",
                "error": str(exc),
            }).eq("id", task_id).execute()
        except Exception:
            logger.exception("Failed to mark engine task failed for task_id=%s", task_id)
        try:
            await notify_user(username, {
                "type": "engine_failed",
                "task_id": task_id,
                "student_id": student_id,
                "message": "Engine run failed.",
            })
        except Exception:
            logger.exception("Failed to notify engine failure for task_id=%s", task_id)


def queue_engine_run(background_tasks: BackgroundTasks, student_id: str, request: Request, current_user: dict, doc_types: list[str] | None = None) -> str | None:
    task_id = str(uuid4())
    params = {
        "student_id": student_id,
        "username": current_user.get("username"),
        "doc_types": doc_types or [],
    }
    try:
        supabase.table("tasks").insert({
            "id": task_id,
            "status": "queued",
            "params": params,
            "progress": 0,
        }).execute()
    except Exception:
        logger.exception("Failed to queue engine task for student_id=%s", student_id)
        return None
    background_tasks.add_task(
        engine_task_logic,
        task_id,
        student_id,
        request.app,
        current_user.get("username"),
        doc_types,
    )
    return task_id


@router.post("/students/{student_id}/engine-runs")
async def start_student_engine_run(
    student_id: str,
    payload: EngineRunRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    student = fetch_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if not can_access_student_record(current_user, student):
        raise HTTPException(status_code=403, detail="You don't have permission to run engines for this student")
    task_id = queue_engine_run(background_tasks, student_id, request, current_user, payload.doc_types)
    return {"task_id": task_id, "student_id": student_id, "status": "queued"}


@router.get("/students/{student_id}/comparison-results")
async def get_student_comparison_results(
    student_id: str,
    current_user: dict = Depends(get_current_user),
):
    student = fetch_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if not can_access_student_record(current_user, student):
        raise HTTPException(status_code=403, detail="You don't have permission to view this comparison")
    return get_engine_summary(student_id)


@router.patch("/students/{student_id}/comparison-results/{field_name}")
async def update_student_comparison_override(
    student_id: str,
    field_name: str,
    payload: ComparisonOverrideRequest,
    current_user: dict = Depends(get_current_user),
):
    student = fetch_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if not can_access_student_record(current_user, student):
        raise HTTPException(status_code=403, detail="You don't have permission to update this comparison")
    try:
        row = update_comparison_override(
            student_id,
            field_name,
            payload.reviewer_override,
            payload.reviewer_notes,
        )
        return {"comparison_result": row}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


from config.settings import GEMINI_BATCH_ENABLED
from services.gemini_batch_service import (
    poll_and_finalize_batch_job,
    poll_batch_job_until_terminal,
    submit_batch_extraction_for_students,
)


def _get_pending_extraction_student_ids() -> list[str]:
    all_students = supabase.table(ADMISSIONS_TABLE).select("aadhaar_card_number, extraction_status").execute().data or []
    pending_ids = [
        r["aadhaar_card_number"]
        for r in all_students
        if r.get("aadhaar_card_number") and (r.get("extraction_status") or "").lower() != "completed"
    ]
    return list(set(pending_ids))


async def extract_all_live_task_logic(task_id: str, app, username: str):
    try:
        supabase.table("tasks").update({"status": "processing", "progress": 0}).eq("id", task_id).execute()
        
        student_ids = _get_pending_extraction_student_ids()
        no_of_students = len(student_ids)
        
        if no_of_students == 0:
            supabase.table("tasks").update({"status": "completed", "progress": 100, "result": "No pending students found."}).eq("id", task_id).execute()
            await notify_user(username, {"type": "extract_all_complete", "message": "No pending students found."})
            return

        semaphore = asyncio.Semaphore(10)
        completed_count = 0

        async def process_with_semaphore(sid):
            nonlocal completed_count
            async with semaphore:
                try:
                    await run_engine_for_student(sid, app, username=username)
                except Exception as e:
                    logger.error(f"Error extracting student {sid}: {e}")
                finally:
                    completed_count += 1
                    if completed_count % max(1, no_of_students // 10) == 0:
                        progress = int((completed_count / no_of_students) * 100)
                        supabase.table("tasks").update({"progress": progress}).eq("id", task_id).execute()

        await asyncio.gather(*(process_with_semaphore(sid) for sid in student_ids))
        supabase.table("tasks").update({"status": "completed", "progress": 100, "result": f"Processed {no_of_students} students"}).eq("id", task_id).execute()

        await notify_user(username, {"type": "extract_all_complete", "message": f"Bulk extraction completed for {no_of_students} students."})
    except Exception as e:
        supabase.table("tasks").update({"status": "failed", "error": str(e)}).eq("id", task_id).execute()
        await notify_user(username, {"type": "extract_all_failed", "message": "Bulk extraction failed."})

@router.post("/extract-all")
async def start_extract_all_pending(
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can extract all.")
        
    task_id = str(uuid4())
    supabase.table("tasks").insert({
        "id": task_id,
        "status": "queued",
        "params": {"action": "extract-all"},
        "progress": 0
    }).execute()

    if not GEMINI_BATCH_ENABLED:
        background_tasks.add_task(extract_all_live_task_logic, task_id, request.app, current_user.get("username"))
        return {"task_id": task_id, "message": "Bulk extraction started."}

    try:
        student_ids = _get_pending_extraction_student_ids()
        if not student_ids:
            supabase.table("tasks").update({
                "status": "completed",
                "progress": 100,
                "result": "No pending students found.",
            }).eq("id", task_id).execute()
            return {
                "task_id": task_id,
                "batch_job_id": None,
                "total_students": 0,
                "total_documents": 0,
                "message": "No pending students found.",
            }

        result = await submit_batch_extraction_for_students(
            student_ids,
            request.app,
            task_id,
            current_user.get("username"),
        )
        if result.get("batch_job_id"):
            background_tasks.add_task(poll_batch_job_until_terminal, result["batch_job_id"], request.app)
        return {"message": "Bulk extraction submitted to Gemini.", **result}
    except Exception as exc:
        logger.exception("Failed to submit Gemini batch extraction")
        error_msg = str(exc)
        status_code = 500
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "prepayment credits" in error_msg:
            status_code = 429
            error_msg = "Gemini API prepayment credits/quota depleted. Please visit https://ai.studio/projects to top up credits or update GOOGLE_API_KEY in .env."

        supabase.table("tasks").update({"status": "failed", "progress": 100, "error": error_msg}).eq("id", task_id).execute()
        await notify_user(current_user.get("username"), {"type": "extract_all_failed", "task_id": task_id, "message": error_msg})
        raise HTTPException(status_code=status_code, detail=error_msg)


@router.post("/extract-all/batch-jobs/poll")
async def poll_extract_all_batch_jobs(
    request: Request,
    batch_job_id: str | None = None,
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can poll extract-all batch jobs.")

    if batch_job_id:
        return await poll_and_finalize_batch_job(batch_job_id, request.app)

    rows = supabase.table("gemini_batch_jobs").select("*").execute().data or []
    results = []
    for row in rows:
        state = (row.get("state") or "").upper()
        if state in {"JOB_STATE_SUCCEEDED", "JOB_STATE_FAILED", "JOB_STATE_CANCELLED", "JOB_STATE_EXPIRED"}:
            continue
        results.append(await poll_and_finalize_batch_job(row["id"], request.app))
    return {"polled": len(results), "results": results}
