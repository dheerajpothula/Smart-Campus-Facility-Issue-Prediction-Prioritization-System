"""
FIPP 2.0 — Operational Analytics & Reporting Service.
Aggregates time-series incident trends, category Pareto distributions,
location volume concentration, turnaround times, and generates PII-redacted CSV exports.
"""
import io
import csv
from datetime import datetime, timedelta, date
from typing import Any, Dict, List, Optional
import pandas as pd

from app.services.complaint_service import complaint_service


class AnalyticsService:
    """Provides operational reporting and executive analytics."""

    @staticmethod
    def get_analytics_report(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category: Optional[str] = None,
        location: Optional[str] = None,
        status: Optional[str] = None,
        trend_agg: str = "Daily"
    ) -> Dict[str, Any]:
        """Calculates multi-dimensional operational metrics matching the Admin Reports view."""
        records = complaint_service._load_records()

        # Date filtering
        start_d = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
        end_d = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

        filtered = []
        for r in records:
            rep_date_str = r.get("date_reported", "")
            try:
                r_date = datetime.strptime(rep_date_str[:10], "%Y-%m-%d").date()
                if start_d and r_date < start_d:
                    continue
                if end_d and r_date > end_d:
                    continue
            except Exception:
                pass

            if category and category != "All Categories" and r.get("category") != category and r.get("facility_type") != category:
                continue
            if location and location != "All Locations" and location.lower() not in str(r.get("building") or r.get("location", "")).lower():
                continue
            if status and status != "All Statuses" and r.get("status") != status:
                continue

            filtered.append(r)

        total = len(filtered)
        new_cnt = sum(1 for r in filtered if r.get("status") == "Submitted")
        in_prog_cnt = sum(1 for r in filtered if r.get("status") in ["Under Review", "Assigned", "In Progress"])
        resolved_cnt = sum(1 for r in filtered if r.get("status") == "Resolved")
        withdrawn_cnt = sum(1 for r in filtered if r.get("status") == "Withdrawn")
        rate = round((resolved_cnt / total * 100), 1) if total > 0 else 0.0

        # Turnaround calculation
        turnarounds = []
        for r in filtered:
            if r.get("status") == "Resolved":
                res_time = r.get("resolved_at") or r.get("estimated_resolution")
                rep_time = r.get("date_reported")
                if res_time and rep_time:
                    try:
                        t_res = datetime.strptime(res_time[:16], "%Y-%m-%d %H:%M")
                        t_rep = datetime.strptime(rep_time[:16], "%Y-%m-%d %H:%M")
                        diff = (t_res - t_rep).total_seconds() / 86400.0
                        if diff >= 0:
                            turnarounds.append(diff)
                    except Exception:
                        pass
        avg_turnaround = round(sum(turnarounds) / len(turnarounds), 1) if turnarounds else None

        # Time-series trends
        trend_buckets: Dict[str, Dict[str, int]] = {}
        for r in filtered:
            dt_str = r.get("date_reported", "")[:10]
            if not dt_str:
                continue
            try:
                dt_obj = datetime.strptime(dt_str, "%Y-%m-%d")
                if trend_agg == "Weekly":
                    period_key = f"{dt_obj.year}-W{dt_obj.isocalendar()[1]:02d}"
                elif trend_agg == "Monthly":
                    period_key = dt_obj.strftime("%Y-%m")
                else:
                    period_key = dt_str

                if period_key not in trend_buckets:
                    trend_buckets[period_key] = {"reported": 0, "resolved": 0}
                trend_buckets[period_key]["reported"] += 1
                if r.get("status") == "Resolved":
                    trend_buckets[period_key]["resolved"] += 1
            except Exception:
                continue

        trends = [
            {"period": k, "reported_count": v["reported"], "resolved_count": v["resolved"]}
            for k, v in sorted(trend_buckets.items())
        ]

        # Category distribution
        cat_counts: Dict[str, int] = {}
        for r in filtered:
            c = r.get("category") or r.get("facility_type") or "General"
            cat_counts[c] = cat_counts.get(c, 0) + 1

        cat_dist = [
            {"category": k, "count": v, "percentage": round((v / total * 100), 1) if total > 0 else 0.0}
            for k, v in sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)
        ]

        # Location concentration
        loc_counts: Dict[str, int] = {}
        for r in filtered:
            b = r.get("building") or r.get("location") or "Campus"
            loc_counts[b] = loc_counts.get(b, 0) + 1

        loc_dist = [
            {"building": k, "count": v, "percentage": round((v / total * 100), 1) if total > 0 else 0.0}
            for k, v in sorted(loc_counts.items(), key=lambda x: x[1], reverse=True)
        ]

        # Priority breakdown
        prio_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for r in filtered:
            tier = r.get("priority_tier", "Medium")
            if tier in prio_counts:
                prio_counts[tier] += 1

        # Aging brackets for open requests
        now = datetime.now()
        aging = {"<24h": 0, "1–3d": 0, "3–7d": 0, ">7d": 0}
        for r in filtered:
            if r.get("status") not in ["Resolved", "Withdrawn"]:
                dt_str = r.get("date_reported")
                if dt_str:
                    try:
                        rep_dt = datetime.strptime(dt_str[:16], "%Y-%m-%d %H:%M")
                        hrs = (now - rep_dt).total_seconds() / 3600.0
                        if hrs < 24:
                            aging["<24h"] += 1
                        elif hrs < 72:
                            aging["1–3d"] += 1
                        elif hrs < 168:
                            aging["3–7d"] += 1
                        else:
                            aging[">7d"] += 1
                    except Exception:
                        aging["<24h"] += 1

        return {
            "kpis": {
                "total": total,
                "new": new_cnt,
                "in_progress": in_prog_cnt,
                "resolved": resolved_cnt,
                "withdrawn": withdrawn_cnt,
                "resolution_rate_percent": rate,
                "average_turnaround_days": avg_turnaround,
            },
            "trends": trends,
            "category_distribution": cat_dist,
            "location_distribution": loc_dist,
            "priority_distribution": prio_counts,
            "aging_brackets": aging,
        }

    @staticmethod
    def export_complaints_csv(redact_pii: bool = True) -> str:
        """
        Exports the complaints dataset as CSV string.
        Enforces Indian DPDP Act 2023 compliance by redacting student PII when requested.
        """
        records = complaint_service._load_records()
        output = io.StringIO()
        fieldnames = [
            "complaint_id",
            "date_reported",
            "category_type",
            "message_type",
            "category",
            "sub_category",
            "specific_category",
            "building",
            "sub_block",
            "location",
            "status",
            "priority_tier",
            "priority_score",
            "allotted_person",
            "department",
            "resolved_at",
            "closing_remarks",
            "student_id",
            "student_name",
            "contact_number",
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for r in records:
            row = dict(r)
            if redact_pii:
                row["student_id"] = "[REDACTED]"
                row["student_name"] = "[REDACTED]"
                row["contact_number"] = "[REDACTED]"
            writer.writerow(row)

        return output.getvalue()


analytics_service = AnalyticsService()
