"""
FIPP 2.0 — Operational Analytics & Reporting Service.
Aggregates time-series incident trends, category Pareto distributions,
location volume concentration, turnaround times, and generates PII-redacted CSV exports.
"""
import io
import csv
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.services.complaint_service import complaint_service, parse_timestamp


def _period_key(dt_obj: datetime, trend_agg: str) -> str:
    """Formats a datetime into Daily, Weekly (ISO week), or Monthly bucket keys."""
    agg = (trend_agg or "Daily").strip().lower()
    if agg in ("weekly", "week"):
        iso_year, iso_week, _ = dt_obj.isocalendar()
        return f"{iso_year}-W{iso_week:02d}"
    if agg in ("monthly", "month"):
        return dt_obj.strftime("%Y-%m")
    return dt_obj.strftime("%Y-%m-%d")


class AnalyticsService:
    """Provides operational reporting and executive analytics."""

    @staticmethod
    def _filter_records(
        records: List[Dict[str, Any]],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category: Optional[str] = None,
        location: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Applies consistent date-range, category, location, and status filtering."""
        start_d = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
        end_d = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

        filtered: List[Dict[str, Any]] = []
        for r in records:
            if start_d or end_d:
                rep_dt = parse_timestamp(r.get("date_reported"))
                if not rep_dt:
                    continue
                r_date = rep_dt.date()
                if start_d and r_date < start_d:
                    continue
                if end_d and r_date > end_d:
                    continue

            if category and category != "All Categories" and r.get("category") != category and r.get("facility_type") != category:
                continue
            if location and location != "All Locations" and location.lower() not in str(r.get("building") or r.get("location", "")).lower():
                continue
            if status and status != "All Statuses" and r.get("status") != status:
                continue

            filtered.append(r)
        return filtered

    @classmethod
    def get_analytics_report(
        cls,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category: Optional[str] = None,
        location: Optional[str] = None,
        status: Optional[str] = None,
        trend_agg: str = "Daily"
    ) -> Dict[str, Any]:
        """Calculates multi-dimensional operational metrics matching the Admin Reports view."""
        records = complaint_service._load_records()
        filtered = cls._filter_records(
            records,
            start_date=start_date,
            end_date=end_date,
            category=category,
            location=location,
            status=status,
        )

        total = len(filtered)
        new_cnt = sum(1 for r in filtered if r.get("status") == "Submitted")
        in_prog_cnt = sum(1 for r in filtered if r.get("status") in ["Under Review", "Assigned", "In Progress"])
        resolved_cnt = sum(1 for r in filtered if r.get("status") == "Resolved")
        withdrawn_cnt = sum(1 for r in filtered if r.get("status") == "Withdrawn")
        eligible_total = total - withdrawn_cnt
        rate = round((resolved_cnt / eligible_total * 100), 1) if eligible_total > 0 else 0.0

        # Turnaround calculation strictly from genuine submission and resolution timestamps
        turnarounds = []
        for r in filtered:
            if r.get("status") == "Resolved":
                t_res = parse_timestamp(r.get("resolved_at"))
                t_rep = parse_timestamp(r.get("date_reported"))
                if t_res and t_rep:
                    diff = (t_res - t_rep).total_seconds() / 86400.0
                    if diff >= 0:
                        turnarounds.append(diff)
        avg_turnaround = round(sum(turnarounds) / len(turnarounds), 1) if turnarounds else None

        # Time-series trends (reported grouped by date_reported; resolved grouped by genuine resolved_at)
        trend_buckets: Dict[str, Dict[str, int]] = {}
        for r in filtered:
            rep_dt = parse_timestamp(r.get("date_reported"))
            if rep_dt:
                rep_key = _period_key(rep_dt, trend_agg)
                bucket = trend_buckets.setdefault(rep_key, {"reported": 0, "resolved": 0})
                bucket["reported"] += 1

            if r.get("status") == "Resolved":
                res_dt = parse_timestamp(r.get("resolved_at"))
                if res_dt:
                    res_key = _period_key(res_dt, trend_agg)
                    bucket = trend_buckets.setdefault(res_key, {"reported": 0, "resolved": 0})
                    bucket["resolved"] += 1

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

        # Priority breakdown using existing/normalized MCPI tiers and scores
        prio_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        status_counts = {
            "Submitted": 0,
            "Under Review": 0,
            "Assigned": 0,
            "In Progress": 0,
            "Resolved": 0,
            "Withdrawn": 0,
        }
        all_mcpi_scores: List[float] = []
        active_mcpi_scores: List[float] = []
        active_total = 0
        unassigned_active = 0
        assigned_active = 0
        reopened_count = 0
        high_critical_active = 0
        assignee_buckets: Dict[str, Dict[str, int]] = {}

        for r in filtered:
            norm = complaint_service.normalize_record(r)
            tier = norm.get("priority_tier", "Medium")
            score_val = float(norm.get("priority_score", 0.0))
            all_mcpi_scores.append(score_val)
            if tier in prio_counts:
                prio_counts[tier] += 1

            st = str(norm.get("status") or "Submitted")
            if st in status_counts:
                status_counts[st] += 1

            if norm.get("is_reopened"):
                reopened_count += 1

            is_active = st not in ("Resolved", "Withdrawn")
            person = str(norm.get("allotted_person") or "").strip()
            dept = str(norm.get("department") or "").strip()
            assignee_label = person or dept or "Unassigned"

            bucket = assignee_buckets.setdefault(
                assignee_label,
                {"active_count": 0, "resolved_count": 0, "total_count": 0},
            )
            bucket["total_count"] += 1
            if st == "Resolved":
                bucket["resolved_count"] += 1
            elif is_active:
                bucket["active_count"] += 1

            if is_active:
                active_total += 1
                active_mcpi_scores.append(score_val)
                if person or dept:
                    assigned_active += 1
                else:
                    unassigned_active += 1
                if tier in ("Critical", "High"):
                    high_critical_active += 1

        avg_mcpi = round(sum(all_mcpi_scores) / len(all_mcpi_scores), 1) if all_mcpi_scores else None
        active_avg_mcpi = round(sum(active_mcpi_scores) / len(active_mcpi_scores), 1) if active_mcpi_scores else None

        assignment_distribution = [
            {
                "assignee": name,
                "active_count": counts["active_count"],
                "resolved_count": counts["resolved_count"],
                "total_count": counts["total_count"],
            }
            for name, counts in sorted(
                assignee_buckets.items(),
                key=lambda item: (item[1]["active_count"], item[1]["total_count"]),
                reverse=True,
            )
        ]

        # Aging brackets for open requests (excluding unparseable timestamps rather than inventing age)
        now = datetime.now()
        aging = {"<24h": 0, "1–3d": 0, "3–7d": 0, ">7d": 0}
        for r in filtered:
            if r.get("status") not in ["Resolved", "Withdrawn"]:
                rep_dt = parse_timestamp(r.get("date_reported"))
                if rep_dt:
                    hrs = max(0.0, (now - rep_dt).total_seconds() / 3600.0)
                    if hrs < 24:
                        aging["<24h"] += 1
                    elif hrs < 72:
                        aging["1–3d"] += 1
                    elif hrs < 168:
                        aging["3–7d"] += 1
                    else:
                        aging[">7d"] += 1

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
            "workload_summary": {
                "active_total": active_total,
                "unassigned_active": unassigned_active,
                "assigned_active": assigned_active,
                "reopened_count": reopened_count,
                "average_mcpi_score": avg_mcpi,
                "active_average_mcpi_score": active_avg_mcpi,
                "high_critical_active": high_critical_active,
            },
            "assignment_distribution": assignment_distribution,
            "status_distribution": status_counts,
        }

    @classmethod
    def export_complaints_csv(
        cls,
        redact_pii: bool = True,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category: Optional[str] = None,
        location: Optional[str] = None,
        status: Optional[str] = None,
    ) -> str:
        """
        Exports filtered complaint records as a CSV string.
        Masks direct student identifiers (student_id, student_name, contact_number) by default;
        room/location details and technician names remain in operational exports.
        Does not claim full DPDP Act 2023 compliance.
        """
        records = complaint_service._load_records()
        filtered = cls._filter_records(
            records,
            start_date=start_date,
            end_date=end_date,
            category=category,
            location=location,
            status=status,
        )
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

        for r in filtered:
            row = dict(complaint_service.normalize_record(r))
            if redact_pii:
                row["student_id"] = "[REDACTED]"
                row["student_name"] = "[REDACTED]"
                row["contact_number"] = "[REDACTED]"
            writer.writerow(row)

        return output.getvalue()


analytics_service = AnalyticsService()
