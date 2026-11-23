"""
FIPP 2.0 — Relational Database Schema & Migration Dry-Run Service.
Executes non-destructive dry-run migration to verify target SQLite/PostgreSQL schema integrity,
token collision analysis, status normalization, and data reconciliation without altering live datastores.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

from app.core.config import PRIMARY_JSON_DATA_FILE
from app.models.db_models import Base, ComplaintModel

CSV_DATASET_PATH = Path(__file__).resolve().parent.parent / "data" / "campus_complaints_dataset.csv"


class MigrationService:
    """Manages schema validation, dry-run reconciliation, and migration audits."""

    def __init__(self, json_path: Path = PRIMARY_JSON_DATA_FILE, csv_path: Path = CSV_DATASET_PATH):
        self.json_path = Path(json_path).resolve()
        self.csv_path = Path(csv_path).resolve()

    def inspect_source_datastores(self) -> Dict[str, Any]:
        """Analyzes active operational JSON store and historical CSV dataset."""
        # 1. JSON Store
        json_records = []
        if self.json_path.is_file():
            try:
                with open(self.json_path, "r", encoding="utf-8") as f:
                    json_records = json.load(f)
            except Exception as e:
                json_records = []

        json_tokens = {r.get("complaint_id") for r in json_records if r.get("complaint_id")}
        json_statuses = {r.get("status") for r in json_records}

        # 2. CSV Dataset
        csv_df = pd.DataFrame()
        if self.csv_path.is_file():
            try:
                csv_df = pd.read_csv(self.csv_path)
            except Exception:
                csv_df = pd.DataFrame()

        csv_tokens = set(csv_df["complaint_id"].dropna().astype(str).tolist()) if "complaint_id" in csv_df.columns else set()
        csv_statuses = set(csv_df["status"].dropna().tolist()) if "status" in csv_df.columns else set()

        # Token Collisions
        collisions = json_tokens.intersection(csv_tokens)

        return {
            "json_store": {
                "path": str(self.json_path),
                "record_count": len(json_records),
                "unique_tokens": len(json_tokens),
                "token_format_sample": list(json_tokens)[:3] if json_tokens else [],
                "distinct_statuses": list(json_statuses),
            },
            "csv_dataset": {
                "path": str(self.csv_path),
                "record_count": len(csv_df),
                "unique_tokens": len(csv_tokens),
                "token_format_sample": list(csv_tokens)[:3] if csv_tokens else [],
                "distinct_statuses": list(csv_statuses),
                "columns": list(csv_df.columns),
            },
            "collision_analysis": {
                "has_collisions": len(collisions) > 0,
                "collision_count": len(collisions),
                "colliding_tokens": list(collisions)[:10],
            },
        }

    def run_dry_run_migration(self, db_url: str = "sqlite:///:memory:") -> Dict[str, Any]:
        """
        Executes a complete dry-run migration against an isolated staging SQLite engine.
        Validates schema creation, record transformation, type casting, and query performance.
        DOES NOT switch the live production application datastore.
        """
        engine = create_engine(db_url, echo=False)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        migration_log = []
        errors = []
        migrated_live_count = 0
        migrated_historical_count = 0

        # Phase A: Migrate Active JSON Operational Records
        json_records = []
        if self.json_path.is_file():
            with open(self.json_path, "r", encoding="utf-8") as f:
                json_records = json.load(f)

        for rec in json_records:
            try:
                cid = rec.get("complaint_id")
                cat = rec.get("category") or rec.get("facility_type") or "General"
                fac = rec.get("facility_type") or rec.get("category") or "General"
                loc = rec.get("location") or "Campus Main Complex"
                bld = rec.get("building") or (loc.split(" - ")[0] if " - " in loc else "Campus Main Complex")
                title = rec.get("title") or rec.get("subject") or f"Issue: {cat}"
                sev = rec.get("severity", "Medium")
                tier = rec.get("priority_tier") or ("Critical" if sev == "Critical" else "High" if sev == "High" else "Medium")
                score = float(rec.get("priority_score", 50.0))

                entry = ComplaintModel(
                    complaint_id=cid,
                    student_id=rec.get("student_id"),
                    student_name=rec.get("student_name") or rec.get("reported_by"),
                    category_type=rec.get("category_type", "Maintenance / Electrical Complaints"),
                    message_type=rec.get("message_type", "Grievance"),
                    category=cat,
                    sub_category=rec.get("sub_category", "General"),
                    specific_categories=rec.get("specific_categories", []),
                    specific_category=rec.get("specific_category"),
                    facility_type=fac,
                    building=bld,
                    sub_block=rec.get("sub_block"),
                    room_type=rec.get("room_type", "Room No"),
                    room_number=rec.get("room_number"),
                    specified_location=rec.get("specified_location"),
                    specific_location=rec.get("specific_location"),
                    location=loc,
                    contact_number=rec.get("contact_number"),
                    availability_date=rec.get("availability_date"),
                    time_slot=rec.get("time_slot"),
                    title=title,
                    subject=rec.get("subject", title),
                    description=rec.get("description", ""),
                    status=rec.get("status", "Submitted"),
                    priority_tier=tier,
                    priority_score=score,
                    allotted_person=rec.get("allotted_person"),
                    department=rec.get("department"),
                    designation=rec.get("designation"),
                    action_taken=rec.get("action_taken"),
                    date_reported=rec.get("date_reported", datetime.now().strftime("%Y-%m-%d %H:%M")),
                    estimated_resolution=rec.get("estimated_resolution"),
                    resolved_at=rec.get("resolved_at"),
                    resolved_by=rec.get("resolved_by"),
                    closing_remarks=rec.get("closing_remarks"),
                    is_reopened=bool(rec.get("is_reopened", False)),
                    reopened_at=rec.get("reopened_at"),
                    has_photo=bool(rec.get("has_photo", False)),
                    photo_name=rec.get("photo_name"),
                    photo_stored_filename=rec.get("photo_stored_filename"),
                    photo_sha256=rec.get("photo_sha256"),
                    remarks_history=rec.get("remarks_history", []),
                    feedback=rec.get("feedback"),
                    score_breakdown=rec.get("score_breakdown"),
                )
                session.add(entry)
                migrated_live_count += 1
            except Exception as e:
                errors.append(f"Error migrating JSON record {rec.get('complaint_id')}: {str(e)}")

        session.commit()

        # Phase B: Verify Database Queries on Migrated Staging Table
        total_in_db = session.query(func.count(ComplaintModel.id)).scalar()
        submitted_count = session.query(func.count(ComplaintModel.id)).filter(ComplaintModel.status == "Submitted").scalar()
        in_prog_count = session.query(func.count(ComplaintModel.id)).filter(ComplaintModel.status.in_(["Under Review", "Assigned", "In Progress"])).scalar()
        resolved_count = session.query(func.count(ComplaintModel.id)).filter(ComplaintModel.status == "Resolved").scalar()

        # Phase C: Test Staging Read Queries
        sample_query = session.execute(
            select(ComplaintModel).where(ComplaintModel.complaint_id == "CMP-2026-001")
        ).scalar_one_or_none()

        session.close()

        return {
            "dry_run_success": len(errors) == 0,
            "engine_url": db_url,
            "migrated_live_count": migrated_live_count,
            "total_records_in_staging": total_in_db,
            "status_breakdown": {
                "Submitted": submitted_count,
                "In Progress / Under Review": in_prog_count,
                "Resolved": resolved_count,
            },
            "sample_verification": {
                "verified_token": sample_query.complaint_id if sample_query else None,
                "verified_facility": sample_query.facility_type if sample_query else None,
                "verified_status": sample_query.status if sample_query else None,
            },
            "errors": errors,
            "production_switch_status": "PRESERVED_JSON_LIVE (No production switch executed)",
        }


migration_service = MigrationService()
