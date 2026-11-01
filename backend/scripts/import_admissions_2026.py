"""Import every response from the 2026 master Google workbook into Supabase.

The source ledger keeps every submitted Google Form row.  The canonical
``admissions_2026`` table retains the newest response for each Aadhaar number.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import datetime

from GoogleService import get_sheets_service, read_google_sheet
from config.settings import SPREADSHEET_ID
from database import supabase
from models.Admissions2026 import Admissions2026Applicant
from services.admissions_2026 import ADMISSIONS_RESPONSES_TABLE, ADMISSIONS_TABLE
from services.catalog_service import normalize_branch_code


def _tab_branch(title: str) -> str:
    return normalize_branch_code(title).upper()


def _timestamp(value: str) -> datetime:
    for fmt in ("%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            pass
    return datetime.min


def _fingerprint(tab: str, applicant: Admissions2026Applicant, raw: dict[str, str]) -> str:
    payload = {
        "tab": tab,
        "timestamp": applicant.source_response_timestamp,
        "aadhaar": applicant.aadhaar_card_number,
        "response": raw,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def _chunks(rows: list[dict], size: int = 200):
    for index in range(0, len(rows), size):
        yield rows[index:index + size]


def main() -> None:
    sheets = get_sheets_service()
    metadata = sheets.spreadsheets().get(
        spreadsheetId=SPREADSHEET_ID, fields="sheets.properties.title"
    ).execute()
    tabs = [sheet["properties"]["title"] for sheet in metadata.get("sheets", [])]

    latest_by_aadhaar: dict[str, tuple[datetime, dict]] = {}
    ledger_rows: list[dict] = []
    totals: dict[str, int] = defaultdict(int)
    skipped_without_aadhaar = 0

    for tab in tabs:
        try:
            branch = _tab_branch(tab)
        except ValueError:
            continue
        values = read_google_sheet(sheets, SPREADSHEET_ID, f"'{tab.replace("'", "''")}'!A1:BS") or []
        if not values:
            continue
        headers, response_rows = values[0], values[1:]
        for row in response_rows:
            applicant = Admissions2026Applicant.from_sheet_row(headers, row)
            raw = dict(zip(headers, row))
            fingerprint = _fingerprint(tab, applicant, raw)
            record = applicant.to_student_record(
                branch=branch,
                source_system="google_forms_2026",
                source_spreadsheet_id=SPREADSHEET_ID,
                source_sheet_tab=tab,
            )
            record.update({"admission_year": 2026, "status": "submitted", "extraction_status": "pending"})
            ledger_rows.append({
                "source_spreadsheet_id": SPREADSHEET_ID,
                "source_sheet_tab": tab,
                "source_response_timestamp": applicant.source_response_timestamp,
                "source_response_email": applicant.source_response_email,
                "aadhaar_card_number": applicant.aadhaar_card_number,
                "response_fingerprint": fingerprint,
                "raw_response": raw,
            })
            totals[branch] += 1
            if not applicant.aadhaar_card_number:
                skipped_without_aadhaar += 1
                continue
            timestamp = _timestamp(applicant.source_response_timestamp)
            current = latest_by_aadhaar.get(applicant.aadhaar_card_number)
            if current is None or timestamp >= current[0]:
                latest_by_aadhaar[applicant.aadhaar_card_number] = (timestamp, record)

    canonical_rows = [item[1] for item in latest_by_aadhaar.values()]
    for rows in _chunks(canonical_rows):
        supabase.table(ADMISSIONS_TABLE).upsert(
            rows, on_conflict="admission_year,aadhaar_card_number"
        ).execute()

    # Resolve the generated canonical ids once, so every ledger row can be
    # traced back to the current applicant record for the same Aadhaar number.
    admission_ids = {
        row["aadhaar_card_number"]: row["id"]
        for row in supabase.table(ADMISSIONS_TABLE)
        .select("id,aadhaar_card_number")
        .eq("admission_year", 2026)
        .execute().data
        or []
    }
    for row in ledger_rows:
        row["admission_id"] = admission_ids.get(row["aadhaar_card_number"])

    # Keep the source ledger append-safe.  A repeated run changes no existing
    # row because fingerprints are unique.
    for rows in _chunks(ledger_rows):
        supabase.table(ADMISSIONS_RESPONSES_TABLE).upsert(
            rows, on_conflict="response_fingerprint", ignore_duplicates=True
        ).execute()

    print(json.dumps({
        "tabs": len(totals),
        "source_rows": sum(totals.values()),
        "canonical_applicants": len(canonical_rows),
        "without_aadhaar": skipped_without_aadhaar,
        "rows_by_branch": dict(sorted(totals.items())),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
