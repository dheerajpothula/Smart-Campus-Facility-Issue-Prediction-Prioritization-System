"""
FIPP Production Database Integrity Verification Utility.
Audits complaints.json against schema, sequential token constraints, and lifecycle invariants.
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

VALID_STATUSES = {
    "Submitted",
    "Under Review",
    "Assigned",
    "In Progress",
    "Resolved",
    "Withdrawn",
}


def get_data_file() -> Path:
    """Returns the active data file path from environment or default project location."""
    env_path = os.environ.get("FIPP_DATA_FILE")
    if env_path:
        return Path(env_path).resolve()
    return PROJECT_ROOT / "data" / "processed" / "complaints.json"


def verify_database_integrity(data_file: Path | None = None) -> dict:
    """
    Performs full integrity audit on the complaints datastore.

    Args:
        data_file: Optional path to JSON file.

    Returns:
        Dict with status, total_records, token_duplicates, schema_errors, warnings.
    """
    target_file = Path(data_file).resolve() if data_file else get_data_file()

    errors = []
    warnings = []

    if not target_file.is_file():
        return {
            "status": "error",
            "file": str(target_file),
            "total_records": 0,
            "errors": [f"Database file not found: {target_file}"],
            "warnings": [],
        }

    try:
        with open(target_file, "r", encoding="utf-8") as f:
            records = json.load(f)
    except Exception as e:
        return {
            "status": "error",
            "file": str(target_file),
            "total_records": 0,
            "errors": [f"Database file is unparseable JSON: {e}"],
            "warnings": [],
        }

    if not isinstance(records, list):
        return {
            "status": "error",
            "file": str(target_file),
            "total_records": 0,
            "errors": ["Root JSON entity is not an array of complaint records."],
            "warnings": [],
        }

    total_records = len(records)
    seen_tokens = set()
    token_numbers = []

    pattern = re.compile(r"^CMP-2026-(\d+)$")

    for idx, r in enumerate(records):
        cid = r.get("complaint_id")
        if not cid:
            errors.append(f"Record index {idx} has missing or empty complaint_id.")
            continue

        cid_str = str(cid).strip()
        match = pattern.match(cid_str)
        if not match:
            warnings.append(f"Record '{cid_str}' does not conform to standard CMP-2026-XXX token pattern.")
        else:
            token_num = int(match.group(1))
            token_numbers.append(token_num)

        if cid_str in seen_tokens:
            errors.append(f"Duplicate complaint token detected: '{cid_str}' at index {idx}.")
        seen_tokens.add(cid_str)

        # Status validation
        status = r.get("status")
        if not status or status not in VALID_STATUSES:
            errors.append(f"Record '{cid_str}' has non-canonical status '{status}'.")

        # Mandatory fields
        if not r.get("title") and not r.get("subject"):
            errors.append(f"Record '{cid_str}' has missing title/subject.")

        if not r.get("category") and not r.get("facility_type"):
            errors.append(f"Record '{cid_str}' has missing category/facility_type.")

        if not r.get("location") and not r.get("building"):
            warnings.append(f"Record '{cid_str}' has missing location/building.")

        # Resolved records audit
        if status == "Resolved":
            if not r.get("resolved_at") and not r.get("closing_remarks"):
                warnings.append(f"Resolved record '{cid_str}' has no resolved_at timestamp or closing remarks.")

    # Check for sequential continuity
    if token_numbers:
        sorted_tokens = sorted(token_numbers)
        min_tok, max_tok = sorted_tokens[0], sorted_tokens[-1]
        expected_range = set(range(min_tok, max_tok + 1))
        missing_tokens = expected_range - set(sorted_tokens)
        if missing_tokens:
            missing_formatted = [f"CMP-2026-{m:03d}" for m in sorted(missing_tokens)]
            warnings.append(f"Potential token gap(s) detected: {', '.join(missing_formatted)}")

    status_verdict = "healthy" if not errors else "corrupted"

    return {
        "status": status_verdict,
        "file": str(target_file),
        "total_records": total_records,
        "unique_tokens": len(seen_tokens),
        "errors": errors,
        "warnings": warnings,
        "audited_at": datetime.now().isoformat(),
    }


def main():
    parser = argparse.ArgumentParser(description="FIPP Database Integrity Auditor")
    parser.add_argument("--data-file", help="Path to complaints.json to audit")
    args = parser.parse_args()

    audit = verify_database_integrity(Path(args.data_file) if args.data_file else None)

    print(f"==================================================")
    print(f"FIPP DATABASE INTEGRITY REPORT")
    print(f"File: {audit['file']}")
    print(f"Status: {audit['status'].upper()}")
    print(f"Total Records: {audit['total_records']} (Unique Tokens: {audit.get('unique_tokens', 0)})")
    print(f"==================================================")

    if audit["errors"]:
        print("\n[ERRORS DETECTED]:")
        for err in audit["errors"]:
            print(f"  ❌ {err}")

    if audit["warnings"]:
        print("\n[WARNINGS / ADVISORIES]:")
        for warn in audit["warnings"]:
            print(f"  ⚠️  {warn}")

    if audit["status"] == "healthy":
        print("\n✅ Database is healthy, schema-compliant, and production-ready.")
        sys.exit(0)
    else:
        print("\n❌ Database has integrity violations that require attention.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
