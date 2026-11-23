"""
FIPP Production Database Restore Utility.
Restores complaints.json from a verified backup snapshot.
Performs SHA-256 integrity checks and generates an automatic pre-restore safety snapshot.
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_data_file() -> Path:
    """Returns the active data file path from environment or default project location."""
    env_path = os.environ.get("FIPP_DATA_FILE")
    if env_path:
        return Path(env_path).resolve()
    return PROJECT_ROOT / "data" / "processed" / "complaints.json"


def calculate_sha256(file_path: Path) -> str:
    """Computes hexadecimal SHA-256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def restore_database(
    backup_file: Path,
    target_data_file: Path | None = None,
    verify_checksum: bool = True,
) -> dict:
    """
    Restores the complaints database from a specified backup snapshot.

    Args:
        backup_file: Path to the backup JSON file.
        target_data_file: Path to destination complaints.json.
        verify_checksum: Whether to verify against .sha256 sidecar if present.

    Returns:
        Dict with status, target_file, pre_restore_snapshot, restored_records.
    """
    backup_path = Path(backup_file).resolve()
    dest_file = Path(target_data_file).resolve() if target_data_file else get_data_file()

    if not backup_path.is_file():
        return {
            "status": "error",
            "message": f"Backup file not found: {backup_path}",
        }

    # Verify backup JSON parseability
    try:
        with open(backup_path, "r", encoding="utf-8") as f:
            records = json.load(f)
            if not isinstance(records, list):
                return {
                    "status": "error",
                    "message": "Backup content is not a valid JSON array of complaint records.",
                }
            restored_count = len(records)
    except Exception as e:
        return {
            "status": "error",
            "message": f"Backup file is corrupted: {e}",
        }

    # Verify checksum sidecar if present
    sidecar_path = backup_path.with_name(f"{backup_path.name}.sha256")
    actual_hash = calculate_sha256(backup_path)

    if verify_checksum and sidecar_path.is_file():
        expected_line = sidecar_path.read_text(encoding="utf-8").strip()
        expected_hash = expected_line.split()[0]
        if actual_hash != expected_hash:
            return {
                "status": "error",
                "message": f"Backup SHA-256 verification failed! Expected {expected_hash}, found {actual_hash}.",
            }

    # Pre-restore safety snapshot if current data file exists
    safety_snapshot_path = None
    if dest_file.is_file():
        dest_dir = dest_file.parent
        dest_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safety_snapshot_path = dest_dir / f"complaints_pre_restore_{timestamp}.json"
        shutil.copy2(dest_file, safety_snapshot_path)

    # Atomic write to destination
    try:
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        temp_dest = dest_file.with_suffix(".restore_tmp")
        shutil.copy2(backup_path, temp_dest)
        os.replace(temp_dest, dest_file)
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to replace active database file: {e}",
        }

    return {
        "status": "success",
        "target_file": str(dest_file),
        "backup_file": str(backup_path),
        "sha256": actual_hash,
        "pre_restore_snapshot": str(safety_snapshot_path) if safety_snapshot_path else None,
        "restored_records": restored_count,
        "restored_at": datetime.now().isoformat(),
    }


def main():
    parser = argparse.ArgumentParser(description="FIPP Database Restore Utility")
    parser.add_argument("backup_file", help="Path to backup JSON file to restore")
    parser.add_argument("--data-file", help="Target complaints.json path")
    parser.add_argument("--no-verify", action="store_true", help="Skip SHA-256 sidecar verification")
    args = parser.parse_args()

    result = restore_database(
        backup_file=Path(args.backup_file),
        target_data_file=Path(args.data_file) if args.data_file else None,
        verify_checksum=not args.no_verify,
    )

    if result["status"] == "success":
        print(f"[OK] Database successfully restored to {result['target_file']}")
        print(f"     Restored {result['restored_records']} records (SHA-256: {result['sha256']})")
        if result["pre_restore_snapshot"]:
            print(f"     Pre-restore safety snapshot created: {result['pre_restore_snapshot']}")
        sys.exit(0)
    else:
        print(f"[ERROR] Restore failed: {result['message']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
