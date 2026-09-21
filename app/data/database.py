"""
Production In-Memory & CSV Database Layer.
Loads the primary 5,500-record campus complaint dataset, computes dynamic KPIs,
supports role-based student data filtering, admin complaint management,
and full CSV dataset upload, validation, export, and reset.
"""

import os
import io
import re
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional

DATA_DIR = os.path.dirname(__file__)
CSV_PATH = os.path.join(DATA_DIR, "campus_complaints_dataset.csv")
DEFAULT_CSV_PATH = os.path.join(DATA_DIR, "campus_complaints_default.csv")

SEVERITY_WEIGHT_MAP = {
    "Critical": 95.0,
    "High": 80.0,
    "Medium": 55.0,
    "Low": 35.0
}

# Required columns for dataset validation
REQUIRED_COLUMNS = [
    "complaint_id",
    "facility_category",
    "building_name",
    "complaint_text",
    "severity",
    "status"
]

ALTERNATIVE_COLUMN_MAPPINGS = {
    "facility_type": "facility_category",
    "location": "building_name",
    "description": "complaint_text",
    "estimated_footfall": "footfall_index",
    "resolution_hours": "resolution_time_hours"
}

class CampusDatabase:
    """Manages the primary campus complaints dataset and provides role-aware queries."""

    def __init__(self):
        self._df: pd.DataFrame = pd.DataFrame()
        self._records: List[Dict[str, Any]] = []
        self._user_counter: int = 900
        self.load_dataset()

    def load_dataset(self, csv_file_path: str = CSV_PATH):
        """Loads and processes the CSV dataset with Pandas."""
        if not os.path.exists(csv_file_path):
            if os.path.exists(DEFAULT_CSV_PATH):
                csv_file_path = DEFAULT_CSV_PATH
            else:
                print(f"[ERROR] Dataset file not found at {csv_file_path}")
                return

        df = pd.read_csv(csv_file_path)
        self._df = self._process_dataframe(df)
        self._records = self._df.to_dict(orient="records")
        print(f"[DATASET] Successfully loaded {len(self._records)} complaints from {os.path.basename(csv_file_path)}")

    def _process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cleans, normalizes, and computes priority scores and departments."""
        df = df.copy()

        # Handle column aliasing
        for alt_col, std_col in ALTERNATIVE_COLUMN_MAPPINGS.items():
            if alt_col in df.columns and std_col not in df.columns:
                df[std_col] = df[alt_col]

        # Ensure complaint_id exists
        if "complaint_id" not in df.columns:
            df["complaint_id"] = [f"CMP-2026-{idx+1:05d}" for idx in range(len(df))]

        # Ensure text and facility fields
        df["complaint_text"] = df.get("complaint_text", "").fillna("Campus maintenance report")
        df["facility_category"] = df.get("facility_category", "General Facilities").fillna("General Facilities")
        df["facility_type"] = df["facility_category"]

        # Ensure location / building name
        if "building_name" not in df.columns:
            df["building_name"] = df.get("location", "Campus Main Complex").fillna("Campus Main Complex")
        df["location"] = df["building_name"]

        # Normalise status ('Pending' -> 'Open')
        df["status"] = df.get("status", "Open").fillna("Open").astype(str)
        df["status"] = df["status"].replace({"Pending": "Open"})

        # Normalise severity
        df["severity"] = df.get("severity", "Medium").fillna("Medium").astype(str)

        # Footfall index
        if "footfall_index" not in df.columns:
            df["footfall_index"] = df.get("estimated_footfall", 65.0).fillna(65.0)
        df["footfall_index"] = pd.to_numeric(df["footfall_index"], errors="coerce").fillna(65.0)

        # Recurrence count 30d
        if "recurring_count_30d" not in df.columns:
            df["recurring_count_30d"] = df.get("previous_complaints_30d", 0).fillna(0)
        df["recurring_count_30d"] = pd.to_numeric(df["recurring_count_30d"], errors="coerce").fillna(0).astype(int)
        df["recurrence_detected"] = df["recurring_count_30d"] > 0

        # Department / technician
        if "technician_assigned" not in df.columns:
            df["technician_assigned"] = "Pending Dispatch"
        df["technician_assigned"] = df["technician_assigned"].fillna("Pending Dispatch")

        # Extract department from technician string (e.g. 'Manoj Yadav (Carpentry)' -> 'Carpentry')
        def extract_dept(tech_str):
            if not isinstance(tech_str, str):
                return "General Maintenance"
            match = re.search(r"\((.*?)\)", tech_str)
            return match.group(1).strip() if match else "General Maintenance"

        df["department"] = df["technician_assigned"].apply(extract_dept)

        # Resolution time hours
        if "resolution_time_hours" not in df.columns:
            df["resolution_time_hours"] = df.get("resolution_hours", 24.0).fillna(24.0)
        df["resolution_time_hours"] = pd.to_numeric(df["resolution_time_hours"], errors="coerce").fillna(18.5)

        # Compute priority scores if not present
        severity_scores = df["severity"].map(SEVERITY_WEIGHT_MAP).fillna(55.0)
        recurrence_scores = np.clip(df["recurring_count_30d"] * 20.0 + 20.0, 15.0, 95.0)
        footfall_scores = df["footfall_index"].values
        location_scores = df.get("location_criticality", 0.7).fillna(0.7) * 100.0
        impact_scores = 0.5 * severity_scores + 0.5 * footfall_scores

        calc_priority = (
            0.35 * severity_scores +
            0.25 * recurrence_scores +
            0.20 * footfall_scores +
            0.10 * location_scores +
            0.10 * impact_scores
        )
        df["priority_score"] = np.round(np.clip(calc_priority, 15.0, 99.0), 1)

        def assign_priority_tier(score):
            if score >= 80.0:
                return "Critical"
            elif score >= 65.0:
                return "High"
            elif score >= 45.0:
                return "Medium"
            else:
                return "Low"

        df["priority"] = df["priority_score"].apply(assign_priority_tier)

        # Assign initial student_id for student demo experience
        # Assign first 8 complaints to STU101 (Rahul) and next 6 to STU102 (Priya)
        df["student_id"] = "STU_ANON"
        if len(df) >= 14:
            df.loc[:7, "student_id"] = "STU101"
            df.loc[8:13, "student_id"] = "STU102"

        # Reporter metadata
        df["reporter_name"] = "Campus Student"
        df.loc[df["student_id"] == "STU101", "reporter_name"] = "Rahul Sharma"
        df.loc[df["student_id"] == "STU102", "reporter_name"] = "Priya Patel"
        df["reporter_role"] = "Student"
        df["is_demo"] = True

        return df

    def get_all_records(
        self,
        data_source: str = "all",
        status: Optional[str] = None,
        severity: Optional[str] = None,
        facility_type: Optional[str] = None,
        location: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Returns all records, optionally filtered."""
        results = list(self._records)
        if status and status != "All":
            results = [r for r in results if str(r.get("status", "")).lower() == status.lower()]
        if severity and severity != "All":
            results = [r for r in results if str(r.get("severity", "")).lower() == severity.lower()]
        if facility_type and facility_type != "All":
            results = [r for r in results if facility_type.lower() in str(r.get("facility_type", "")).lower()]
        if location and location != "All":
            results = [r for r in results if location.lower() in str(r.get("location", "")).lower()]
        return results

    # --- Student Specific Queries ---
    def get_student_complaints(self, student_id: str) -> List[Dict[str, Any]]:
        """Returns complaints belonging strictly to the authenticated student."""
        return [r for r in self._records if r.get("student_id") == student_id]

    def get_student_complaint_by_id(self, student_id: str, complaint_id: str) -> Optional[Dict[str, Any]]:
        for r in self._records:
            if (r.get("complaint_id") == complaint_id or r.get("id") == complaint_id) and r.get("student_id") == student_id:
                return r
        return None

    def add_student_complaint(self, student_id: str, student_name: str, record_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Adds a live complaint submitted by a student."""
        self._user_counter += 1
        complaint_id = f"CMP-2026-L{self._user_counter:04d}"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        record_dict["complaint_id"] = complaint_id
        record_dict["id"] = complaint_id
        record_dict["timestamp"] = now_str
        record_dict["student_id"] = student_id
        record_dict["reporter_name"] = student_name
        record_dict["reporter_role"] = "Student"
        record_dict["status"] = "Open"
        record_dict["is_demo"] = False

        # Insert at top of list
        self._records.insert(0, record_dict)
        return record_dict

    # --- Admin Specific Queries ---
    def get_admin_complaints(
        self,
        search: Optional[str] = None,
        location: Optional[str] = None,
        facility_type: Optional[str] = None,
        severity: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
        department: Optional[str] = None,
        recurring: Optional[bool] = None,
        limit: int = 500,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Filtered search across all campus complaints."""
        results = list(self._records)

        if search:
            q = search.lower()
            results = [
                r for r in results
                if q in str(r.get("complaint_id", "")).lower()
                or q in str(r.get("complaint_text", "")).lower()
                or q in str(r.get("location", "")).lower()
                or q in str(r.get("reporter_name", "")).lower()
            ]

        if location and location != "All":
            results = [r for r in results if location.lower() in str(r.get("location", "")).lower()]

        if facility_type and facility_type != "All":
            results = [r for r in results if facility_type.lower() in str(r.get("facility_type", "")).lower()]

        if severity and severity != "All":
            results = [r for r in results if str(r.get("severity", "")).lower() == severity.lower()]

        if priority and priority != "All":
            results = [r for r in results if str(r.get("priority", "")).lower() == priority.lower()]

        if status and status != "All":
            results = [r for r in results if str(r.get("status", "")).lower() == status.lower()]

        if department and department != "All":
            results = [r for r in results if department.lower() in str(r.get("department", "")).lower()]

        if recurring is not None:
            results = [r for r in results if bool(r.get("recurrence_detected", False)) == recurring]

        total_matching = len(results)
        paginated = results[offset : offset + limit]

        return {
            "total": total_matching,
            "count": len(paginated),
            "offset": offset,
            "records": paginated
        }

    def get_by_id(self, complaint_id: str) -> Optional[Dict[str, Any]]:
        for r in self._records:
            if r.get("complaint_id") == complaint_id or r.get("id") == complaint_id:
                return r
        return None

    def admin_update_complaint(
        self,
        complaint_id: str,
        status: Optional[str] = None,
        department: Optional[str] = None,
        technician: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        rec = self.get_by_id(complaint_id)
        if not rec:
            return None
        if status:
            rec["status"] = status
            if status == "Resolved":
                rec["resolved_at"] = datetime.now().isoformat()
        if department:
            rec["department"] = department
        if technician:
            rec["technician_assigned"] = technician
        return rec

    def admin_delete_complaint(self, complaint_id: str) -> bool:
        initial_len = len(self._records)
        self._records = [r for r in self._records if r.get("complaint_id") != complaint_id and r.get("id") != complaint_id]
        return len(self._records) < initial_len

    # --- Dashboard KPIs Calculated Dynamically from Dataset ---
    def get_kpis(self) -> Dict[str, Any]:
        total = len(self._records)
        open_count = sum(1 for r in self._records if r.get("status") in ["Open", "Pending"])
        in_progress = sum(1 for r in self._records if r.get("status") == "In Progress")
        resolved = sum(1 for r in self._records if r.get("status") == "Resolved")
        high_priority = sum(1 for r in self._records if r.get("priority") == "High" and r.get("status") != "Resolved")
        critical_priority = sum(1 for r in self._records if r.get("priority") == "Critical" and r.get("status") != "Resolved")
        recurring = sum(1 for r in self._records if r.get("recurrence_detected", False))

        # Distinct high-risk locations
        high_risk_locs = len(set(
            r.get("location") for r in self._records
            if float(r.get("footfall_index", 0)) >= 85 or r.get("priority") == "Critical"
        ))

        # Average resolution time in hours
        res_times = [float(r["resolution_time_hours"]) for r in self._records if "resolution_time_hours" in r and r.get("status") == "Resolved"]
        avg_res_hours = round(float(np.mean(res_times)), 1) if res_times else 21.4

        return {
            "total_complaints": total,
            "open_complaints": open_count,
            "in_progress_complaints": in_progress,
            "resolved_complaints": resolved,
            "high_priority_issues": high_priority,
            "critical_priority_issues": critical_priority,
            "recurring_issues": recurring,
            "high_risk_facilities": high_risk_locs,
            "avg_resolution_hours": avg_res_hours,
            "is_demo_dataset": True
        }

    # --- Dataset Management (Upload, Validate, Export, Reset) ---
    def get_dataset_summary(self) -> Dict[str, Any]:
        df = pd.DataFrame(self._records)
        if df.empty:
            return {"total_records": 0, "total_columns": 0}

        # Value distributions
        fac_dist = df["facility_category"].value_counts().to_dict() if "facility_category" in df.columns else {}
        sev_dist = df["severity"].value_counts().to_dict() if "severity" in df.columns else {}
        pri_dist = df["priority"].value_counts().to_dict() if "priority" in df.columns else {}
        loc_dist = df["location"].value_counts().head(10).to_dict() if "location" in df.columns else {}

        columns_meta = [
            {"name": col, "dtype": str(df[col].dtype), "missing": int(df[col].isna().sum())}
            for col in df.columns
        ]

        clean_preview = [
            {k: (None if pd.isna(v) else v) for k, v in row.items()}
            for row in df.head(15).to_dict(orient="records")
        ]

        return {
            "total_records": len(df),
            "total_columns": len(df.columns),
            "missing_values_count": int(df.isna().sum().sum()),
            "duplicate_records": int(df.duplicated(subset=["complaint_id"]).sum()) if "complaint_id" in df.columns else 0,
            "columns": columns_meta,
            "facility_distribution": fac_dist,
            "severity_distribution": sev_dist,
            "priority_distribution": pri_dist,
            "location_distribution": loc_dist,
            "preview_rows": clean_preview
        }

    def validate_and_replace_csv(self, file_content: bytes) -> Dict[str, Any]:
        """Validates uploaded CSV and replaces active dataset."""
        try:
            new_df = pd.read_csv(io.BytesIO(file_content))
        except Exception as e:
            return {"success": False, "error": f"Invalid CSV file format: {str(e)}"}

        # Check required columns
        missing = []
        for req_col in REQUIRED_COLUMNS:
            has_col = req_col in new_df.columns
            # Check aliases
            if not has_col:
                for alt_k, alt_v in ALTERNATIVE_COLUMN_MAPPINGS.items():
                    if alt_v == req_col and alt_k in new_df.columns:
                        has_col = True
                        break
            if not has_col:
                missing.append(req_col)

        if missing:
            return {
                "success": False,
                "error": "Dataset validation failed: missing mandatory columns.",
                "missing_columns": missing
            }

        # Process and save
        processed = self._process_dataframe(new_df)
        processed.to_csv(CSV_PATH, index=False)
        self._df = processed
        self._records = self._df.to_dict(orient="records")

        return {
            "success": True,
            "message": f"Successfully ingested {len(self._records)} complaint records into platform.",
            "total_records": len(self._records),
            "columns_count": len(self._df.columns)
        }

    def export_dataset_csv(self) -> str:
        """Exports the active dataset to CSV string."""
        df = pd.DataFrame(self._records)
        return df.to_csv(index=False)

    def reset_to_default_dataset(self) -> Dict[str, Any]:
        """Restores the original 5,500 record dataset."""
        self.load_dataset(DEFAULT_CSV_PATH)
        # Save back to CSV_PATH
        self._df.to_csv(CSV_PATH, index=False)
        return {"success": True, "message": "Dataset successfully restored to default 5,500 historical records."}

campus_db = CampusDatabase()
