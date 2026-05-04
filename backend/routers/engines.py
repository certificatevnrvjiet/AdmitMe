from __future__ import annotations

import logging
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request

from database import supabase
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
