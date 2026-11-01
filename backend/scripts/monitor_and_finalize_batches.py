"""Poll and finalize all running Gemini batch jobs until completion."""

from __future__ import annotations

import asyncio
import logging
import time
from types import SimpleNamespace

from database import supabase
from services.gemini_batch_service import TERMINAL_STATES, poll_and_finalize_batch_job

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("batch_monitor")


def get_active_batch_jobs() -> list[dict]:
    rows = (
        supabase.table("gemini_batch_jobs")
        .select("*")
        .order("created_at", desc=False)
        .execute()
        .data
        or []
    )
    return [r for r in rows if (r.get("state") or "").upper() not in TERMINAL_STATES]


async def monitor_loop(poll_interval: int = 30) -> None:
    app = SimpleNamespace(state=SimpleNamespace())
    logger.info("Starting Gemini Batch monitor...")

    while True:
        active_jobs = get_active_batch_jobs()
        if not active_jobs:
            logger.info("All Gemini Batch jobs have reached terminal states!")
            break

        logger.info("Active batch jobs remaining: %d", len(active_jobs))
        for job in active_jobs:
            job_id = job["id"]
            gemini_name = job.get("gemini_job_name")
            try:
                res = await poll_and_finalize_batch_job(job_id, app, notify=False)
                state = res.get("state")
                logger.info(
                    "Job %s (%s): state=%s, completed=%s",
                    job_id,
                    gemini_name,
                    state,
                    res.get("completed"),
                )
            except Exception as exc:
                logger.warning("Error checking job %s: %s", job_id, exc)

        await asyncio.sleep(poll_interval)


if __name__ == "__main__":
    asyncio.run(monitor_loop(poll_interval=30))
