from __future__ import annotations

from typing import Any

BRANCH_LABELS: dict[str, str] = {
    "aids": "AIDS",
    "ae": "AE",
    "ce": "CE",
    "csbs": "CSBS",
    "cse": "CSE",
    "aiml": "AIML",
    "cseds": "CSE-DS",
    "csecys": "CSE-CYS",
    "cseiot": "CSE-IOT",
    "eee": "EEE",
    "ece": "ECE",
    "eie": "EIE",
    "it": "IT",
    "me": "ME",
    "vlsi": "VLSI",
    "biotechnology": "Biotechnology",
    "roboticsandai": "Robotics and AI",
}

BRANCH_ALIASES: dict[str, str] = {
    "aml": "aiml",
    "rai": "roboticsandai",
}

ALL_BRANCH_CODES = list(BRANCH_LABELS.keys())

PROGRAM_BRANCH_MAP: dict[str, list[str]] = {
    "BTECH": ALL_BRANCH_CODES,
    "MTECH": ["cse", "ece", "eee", "me", "vlsi"],
}

PROGRAM_LABELS: dict[str, str] = {
    "BTECH": "B.Tech",
    "MTECH": "M.Tech",
}


def normalize_branch_code(code: str | None) -> str:
    value = (code or "").strip().lower()
    if not value:
        raise ValueError("Branch code is required")

    canonical = BRANCH_ALIASES.get(value, value)
    if canonical not in BRANCH_LABELS:
        raise ValueError(f"Unsupported branch code: {code}")
    return canonical


def normalize_program_level(program_level: str | None) -> str:
    value = (program_level or "").strip().upper().replace(".", "")
    if value == "BTECH":
        return "BTECH"
    if value == "MTECH":
        return "MTECH"
    raise ValueError("Program level must be BTECH or MTECH")


def validate_program_branch(program_level: str, branch_code: str) -> None:
    normalized_program = normalize_program_level(program_level)
    normalized_branch = normalize_branch_code(branch_code)
    allowed = PROGRAM_BRANCH_MAP.get(normalized_program, [])
    if normalized_branch not in allowed:
        raise ValueError(
            f"Branch {normalized_branch} is not valid for program {normalized_program}"
        )


def to_db_branch_code(branch_code: str | None) -> str:
    return normalize_branch_code(branch_code).upper()


def to_db_program_level(program_level: str | None) -> str:
    return normalize_program_level(program_level)


def branch_label(branch_code: str | None) -> str:
    if not branch_code:
        return ""
    try:
        return BRANCH_LABELS[normalize_branch_code(branch_code)]
    except ValueError:
        return (branch_code or "").upper()


def program_branch_catalog() -> dict[str, Any]:
    programs = []
    for code, label in PROGRAM_LABELS.items():
        branch_codes = PROGRAM_BRANCH_MAP.get(code, [])
        branches = [
            {
                "code": branch_code,
                "label": BRANCH_LABELS[branch_code],
            }
            for branch_code in branch_codes
        ]
        programs.append(
            {
                "code": code,
                "label": label,
                "branches": branches,
            }
        )

    return {
        "programs": programs,
        "aliases": {k: v for k, v in BRANCH_ALIASES.items()},
    }


def normalize_student_branch_fields(student: dict[str, Any]) -> dict[str, Any]:
    row = dict(student or {})

    branch_value = row.get("branch_code")
    if branch_value:
        try:
            row["branch_code"] = to_db_branch_code(str(branch_value))
        except ValueError:
            pass

    degree_value = row.get("degree_code")
    if degree_value:
        try:
            row["degree_code"] = to_db_branch_code(str(degree_value))
        except ValueError:
            pass

    program_level = row.get("program_level")
    if program_level:
        try:
            row["program_level"] = to_db_program_level(str(program_level))
        except ValueError:
            pass

    return row
