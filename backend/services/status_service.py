from __future__ import annotations

from typing import Any

CANONICAL_STATUSES = {
    "submitted",
    "under_review",
    "approved",
    "rejected",
    "resubmission_required",
}

STATUS_ALIASES = {
    "not viewed": "submitted",
    "pending": "under_review",
    "verified": "approved",
    "not_viewed": "submitted",
}

ALLOWED_TRANSITIONS = {
    "submitted": {"under_review", "resubmission_required", "approved", "rejected"},
    "under_review": {"approved", "rejected", "resubmission_required"},
    "resubmission_required": {"submitted", "under_review"},
    "approved": set(),
    "rejected": {"submitted", "under_review"},
}


def normalize_status(value: str | None, default: str = "submitted") -> str:
    if not value:
        return default

    raw = str(value).strip().lower().replace("-", "_")
    mapped = STATUS_ALIASES.get(raw, raw)
    if mapped in CANONICAL_STATUSES:
        return mapped
    return default


def is_transition_allowed(current_status: str | None, new_status: str | None) -> bool:
    current = normalize_status(current_status)
    target = normalize_status(new_status)
    if current == target:
        return True
    return target in ALLOWED_TRANSITIONS.get(current, set())


def canonicalize_student_status(student: dict[str, Any]) -> dict[str, Any]:
    row = dict(student or {})
    row["status"] = normalize_status(row.get("status"))
    return row
