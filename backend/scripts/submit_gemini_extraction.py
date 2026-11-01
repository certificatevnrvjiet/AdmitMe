"""Submit Gemini batch extraction jobs for pending Admissions 2026 applicants in manageable chunks."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from types import SimpleNamespace
from uuid import uuid4

from GoogleService import get_drive_service
from database import supabase
from services.admissions_2026 import ADMISSIONS_TABLE
from services.gemini_batch_service import submit_batch_extraction_for_students
from storage.gdrive import GoogleDriveStorageProvider

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("submit_gemini_extraction")


def get_all_pending_student_ids(limit: int = 3000) -> list[str]:
    """Retrieve all pending student IDs with pagination to bypass PostgREST 1000-row limit."""
    page_size = 1000
    all_ids: list[str] = []
    start = 0

    while len(all_ids) < limit:
        end = start + min(page_size, limit - len(all_ids)) - 1
        rows = (
            supabase.table(ADMISSIONS_TABLE)
            .select("aadhaar_card_number")
            .eq("extraction_status", "pending")
            .range(start, end)
            .execute()
            .data
            or []
        )
        if not rows:
            break

        for row in rows:
            aadhaar = row.get("aadhaar_card_number")
            if aadhaar:
                clean = "".join(c for c in str(aadhaar) if c.isdigit())
                all_ids.append(clean or str(aadhaar).strip())

        if len(rows) < (end - start + 1):
            break
        start += page_size

    # Deduplicate while preserving order
    seen = set()
    unique_ids = []
    for sid in all_ids:
        if sid not in seen:
            seen.add(sid)
            unique_ids.append(sid)

    return unique_ids


async def submit_chunk(
    chunk_index: int,
    total_chunks: int,
    student_ids: list[str],
    drive_provider: GoogleDriveStorageProvider,
) -> dict:
    task_id = str(uuid4())
    logger.info(
        "[%d/%d] Preparing batch for %d students...",
        chunk_index,
        total_chunks,
        len(student_ids),
    )

    supabase.table("tasks").insert({
        "id": task_id,
        "status": "queued",
        "params": {
            "action": "gemini-extraction",
            "mode": "full-batch",
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "student_count": len(student_ids),
        },
        "progress": 0,
    }).execute()

    app = SimpleNamespace(state=SimpleNamespace(storage_providers={"gdrive": drive_provider}))
    result = await submit_batch_extraction_for_students(
        student_ids, app, task_id, username="system"
    )

    logger.info(
        "[%d/%d] Submitted! BatchJob: %s | GeminiJob: %s | Docs: %d",
        chunk_index,
        total_chunks,
        result.get("batch_job_id"),
        result.get("gemini_job_name"),
        result.get("total_documents", 0),
    )
    return result


async def main(limit: int, batch_size: int) -> None:
    all_pending = get_all_pending_student_ids(limit)
    total_students = len(all_pending)
    if not total_students:
        logger.info("No pending applicants found.")
        return

    logger.info("Found %d pending applicants. Batch size: %d", total_students, batch_size)
    chunks = [all_pending[i:i + batch_size] for i in range(0, total_students, batch_size)]
    total_chunks = len(chunks)
    logger.info("Total batches to submit: %d", total_chunks)

    drive_provider = GoogleDriveStorageProvider(get_drive_service())
    submitted_jobs = []

    for idx, chunk in enumerate(chunks, 1):
        for attempt in range(1, 4):
            try:
                result = await submit_chunk(idx, total_chunks, chunk, drive_provider)
                submitted_jobs.append(result)
                break
            except Exception as exc:
                logger.exception("Attempt %d/3 failed for batch %d/%d: %s", attempt, idx, total_chunks, exc)
                if attempt < 3:
                    await asyncio.sleep(15)
                else:
                    logger.error("Giving up on batch %d/%d after 3 attempts", idx, total_chunks)

    logger.info(
        "Successfully submitted %d of %d batches to Gemini Batch API.",
        len(submitted_jobs),
        total_chunks,
    )
    print(json.dumps({
        "status": "submitted",
        "total_batches": len(submitted_jobs),
        "total_students": sum(j.get("total_students", 0) for j in submitted_jobs),
        "total_documents": sum(j.get("total_documents", 0) for j in submitted_jobs),
        "jobs": [
            {
                "batch_job_id": j.get("batch_job_id"),
                "gemini_job_name": j.get("gemini_job_name"),
                "students": j.get("total_students"),
                "docs": j.get("total_documents"),
            }
            for j in submitted_jobs
        ],
    }, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=3000, help="Maximum pending students to process")
    parser.add_argument("--batch-size", type=int, default=250, help="Number of students per Gemini Batch Job")
    args = parser.parse_args()

    asyncio.run(main(args.limit, args.batch_size))
