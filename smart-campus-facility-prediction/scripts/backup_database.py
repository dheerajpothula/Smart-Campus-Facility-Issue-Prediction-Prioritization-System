"""
FIPP Production Database Backup Utility.
Creates timestamped, SHA-256 verified snapshots of complaints.json.
Supports automated backup rotation, retention policies, and custom backup targets.
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_data_file() -> Path:
    """Returns the active data file path from environment or default project location."""
    env_path = os.environ.get("FIPP_DATA_FILE")
    if env_path:
        return Path(env_path).resolve()
    return PROJECT_ROOT / "data" / "processed" / "complaints.json"


def get_backup_dir() -> Path:
    """Returns the backup target directory from environment or default project location."""
    env_dir = os.environ.get("FIPP_BACKUP_DIR")
    if env_dir:
        return Path(env_dir).resolve()
    return PROJECT_ROOT / "data" / "backups"


def calculate_sha256(file_path: Path) -> str:
    """Computes hexadecimal SHA-256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def create_database_backup(
    data_file: Path | None = None,
    backup_dir: Path | None = None,
    retention_days: int | None = None,
) -> dict:
    """
    Performs a verified backup of the complaints datastore.

    Args:
        data_file: Optional path to source JSON file.
        backup_dir: Optional path to backup destination directory.
        retention_days: Optional retention window in days.

    Returns:
        Dict with status, backup_file, sha256, record_count, and pruned_count.
    """
    source_file = Path(data_file).resolve() if data_file else get_data_file()
    dest_dir = Path(backup_dir).resolve() if backup_dir else get_backup_dir()

    if retention_days is None:
        retention_days = int(os.environ.get("FIPP_BACKUP_RETENTION_DAYS", "30"))

    if not source_file.is_file():
        return {
            "status": "error",
            "message": f"Source database file does not exist: {source_file}",
            "backup_file": None,
        }

    # Verify source JSON validity before copying
    try:
        with open(source_file, "r", encoding="utf-8") as f:
            records = json.load(f)
            record_count = len(records) if isinstance(records, list) else 0
    except Exception as e:
        return {
            "status": "error",
            "message": f"Source database file is corrupt or unparseable: {e}",
            "backup_file": None,
        }

    dest_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"complaints_backup_{timestamp}.json"
    backup_path = dest_dir / backup_filename
    checksum_path = dest_dir / f"{backup_filename}.sha256"

    # Copy file atomically
    shutil.copy2(source_file, backup_path)

    # Compute and verify checksums
    src_hash = calculate_sha256(source_file)
    dst_hash = calculate_sha256(backup_path)

    if src_hash != dst_hash:
        backup_path.unlink(missing_ok=True)
        return {
            "status": "error",
            "message": "Checksum mismatch during backup copy verification.",
            "backup_file": None,
        }

    # Write SHA-256 sidecar file
    checksum_content = f"{dst_hash}  {backup_filename}\n"
    checksum_path.write_text(checksum_content, encoding="utf-8")

    # Prune expired backups according to retention policy
    pruned_count = 0
    if retention_days > 0:
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        for old_file in dest_dir.glob("complaints_backup_*.json"):
            try:
                # Extract date from filename: complaints_backup_YYYYMMDD_HHMMSS.json
                parts = old_file.stem.split("_")
                if len(parts) >= 3:
                    file_date_str = parts[2]
                    file_date = datetime.strptime(file_date_str, "%Y%m%d")
                    if file_date < cutoff_date:
                        old_file.unlink(missing_ok=True)
                        sidecar = old_file.with_name(f"{old_file.name}.sha256")
                        sidecar.unlink(missing_ok=True)
                        pruned_count += 1
            except Exception:
                pass

    return {
        "status": "success",
        "backup_file": str(backup_path),
        "checksum_file": str(checksum_path),
        "sha256": dst_hash,
        "record_count": record_count,
        "pruned_backups": pruned_count,
        "created_at": datetime.now().isoformat(),
    }


def main():
    parser = argparse.ArgumentParser(description="FIPP Database Backup Utility")
    parser.add_argument("--data-file", help="Path to complaints.json")
    parser.add_argument("--backup-dir", help="Target backup directory")
    parser.add_argument("--retention-days", type=int, default=30, help="Backup retention window in days")
    args = parser.parse_args()

    result = create_database_backup(
        data_file=Path(args.data_file) if args.data_file else None,
        backup_dir=Path(args.backup_dir) if args.backup_dir else None,
        retention_days=args.retention_days,
    )

    if result["status"] == "success":
        print(f"[OK] Backup created successfully: {result['backup_file']}")
        print(f"     Records: {result['record_count']} | SHA-256: {result['sha256']}")
        if result["pruned_backups"] > 0:
            print(f"     Pruned {result['pruned_backups']} expired backup(s).")
        sys.exit(0)
    else:
        print(f"[ERROR] Backup failed: {result['message']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
