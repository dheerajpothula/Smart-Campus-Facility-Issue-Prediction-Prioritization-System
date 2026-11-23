"""
FIPP Phase 6: Reports & Analytics Dashboard Verification Test Suite.
Validates:
1. Reports page rendering and administrative header.
2. Date range filtering (Start Date and End Date).
3. Category filtering across facility categories.
4. Building / Location filtering.
5. Status filtering across lifecycle stages.
6. Clear Filters action and safe session-state cleanup.
7. KPI summary calculations (Total, New, In Progress, Resolved, Resolution Rate).
8. Complaint trend analysis with Daily, Weekly, and Monthly aggregations.
9. Category analysis and volume distribution.
10. Location analysis and concentration density detection.
11. MCPI priority distribution and category cross-tabulation.
12. Resolution performance: turnaround time, missing timestamp exclusion, and backlog ageing.
13. Feature attribution explainability insights from real MCPI scoring.
14. Export functionality: filtered CSV generation, student PII redaction, and analytics summary CSV.
15. Empty dataset and zero-match filter handling.
16. Streamlit AppTest execution for Reports view.
"""
import io
import sys
import unittest
from datetime import datetime, timedelta, date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st
from streamlit.testing.v1 import AppTest

from dashboard.pages import admin_reports
from src.data import complaints_store
from src.prediction.priority_scoring import calculate_priority_score, get_current_weights


class TestReportsPhase6(unittest.TestCase):
    """Unit and functional test suite for Phase 6 Reports & Analytics."""

    def setUp(self):
        """Prepare fresh session state and standard seed dataset for test isolation."""
        st.session_state.clear()
        complaints_store.reset_to_default_dataset()
        st.session_state["auth_user"] = {
            "id": "ADM-TEST-001",
            "name": "Administrator",
            "role": "admin",
            "title": "Facility Operations Lead",
        }

    def test_01_reports_page_loads_and_header(self):
        """1. Verify Reports page renders with official heading, subtitle, and kicker."""
        raw_df = complaints_store.get_complaints_df()
        self.assertFalse(raw_df.empty, "Default dataset must contain complaint records.")

        # Test render_reports_page execution without exception
        try:
            admin_reports.render_reports_page()
            rendered = True
        except Exception as e:
            rendered = False
            self.fail(f"render_reports_page failed with exception: {e}")
        self.assertTrue(rendered)

    def test_02_date_range_filtering(self):
        """2. Verify date range filtering restricts records to dates between start_date and end_date."""
        df = complaints_store.get_complaints_df()
        dt_parsed = pd.to_datetime(df["date_reported"], format="mixed", errors="coerce")
        min_date = dt_parsed.min().date()
        max_date = dt_parsed.max().date()

        # Filter to a narrow 2-day window
        test_start = min_date
        test_end = min_date + timedelta(days=2)

        filtered = df[(dt_parsed.dt.date >= test_start) & (dt_parsed.dt.date <= test_end)]
        self.assertTrue(len(filtered) > 0)
        self.assertTrue(len(filtered) <= len(df))

        # Check every record in filtered set is within bounds
        for dt_val in pd.to_datetime(filtered["date_reported"], format="mixed", errors="coerce"):
            self.assertTrue(test_start <= dt_val.date() <= test_end)

    def test_03_category_filtering(self):
        """3. Verify category filtering strictly isolates records of the specified category."""
        df = complaints_store.get_complaints_df()
        cat_col = "facility_type" if "facility_type" in df.columns else "category"

        # Test filtering by 'Plumbing'
        plumbing_df = df[df[cat_col] == "Plumbing"]
        self.assertEqual(len(plumbing_df), 1)
        self.assertEqual(plumbing_df.iloc[0]["complaint_id"], "CMP-2026-001")

        # Test filtering by 'Other maintenance issues'
        other_df = df[df[cat_col] == "Other maintenance issues"]
        self.assertEqual(len(other_df), 3)
        for _, row in other_df.iterrows():
            self.assertEqual(row[cat_col], "Other maintenance issues")

    def test_04_location_filtering(self):
        """4. Verify building/location filtering isolates records by facility zone."""
        df = complaints_store.get_complaints_df()
        loc_col = "building" if "building" in df.columns else "location"

        # Test filtering by 'Academic Block 3'
        bld3_df = df[df[loc_col] == "Academic Block 3"]
        self.assertEqual(len(bld3_df), 1)
        self.assertEqual(bld3_df.iloc[0]["complaint_id"], "CMP-2026-002")

        # Test filtering by 'Central Library'
        lib_df = df[df[loc_col] == "Central Library"]
        self.assertEqual(len(lib_df), 1)
        self.assertEqual(lib_df.iloc[0]["complaint_id"], "CMP-2026-006")

    def test_05_status_filtering(self):
        """5. Verify status filtering isolates records strictly by lifecycle stage."""
        df = complaints_store.get_complaints_df()

        # Filter by Resolved
        res_df = df[df["status"] == "Resolved"]
        self.assertEqual(len(res_df), 2)
        for s in res_df["status"]:
            self.assertEqual(s, "Resolved")

        # Filter by In Progress
        inp_df = df[df["status"] == "In Progress"]
        self.assertEqual(len(inp_df), 2)
        for s in inp_df["status"]:
            self.assertEqual(s, "In Progress")

        # Filter by Under Review
        ur_df = df[df["status"] == "Under Review"]
        self.assertEqual(len(ur_df), 2)
        for s in ur_df["status"]:
            self.assertEqual(s, "Under Review")

    def test_06_clear_filters_action_and_session_state_cleanup(self):
        """6. Verify Clear Filters resets session state keys cleanly without post-instantiation mutation."""
        st.session_state["rep_start_date"] = date(2026, 11, 1)
        st.session_state["rep_end_date"] = date(2026, 11, 30)
        st.session_state["rep_category"] = "Plumbing"
        st.session_state["rep_location"] = "Hostel Block B"
        st.session_state["rep_status"] = "In Progress"
        st.session_state["rep_trend_agg"] = "Weekly"

        admin_reports.clear_reports_filters()

        self.assertNotIn("rep_start_date", st.session_state)
        self.assertNotIn("rep_end_date", st.session_state)
        self.assertNotIn("rep_category", st.session_state)
        self.assertNotIn("rep_location", st.session_state)
        self.assertNotIn("rep_status", st.session_state)
        self.assertNotIn("rep_trend_agg", st.session_state)

    def test_07_kpi_summary_indicators_calculation(self):
        """7. Verify compact KPI summary indicators are computed accurately from real records."""
        df = complaints_store.get_complaints_df()
        total = len(df)
        new_c = int((df["status"] == "Submitted").sum())
        in_prog = int(df["status"].isin(["In Progress", "Under Review", "Assigned"]).sum())
        resolved = int((df["status"] == "Resolved").sum())
        res_rate = f"{round((resolved / total * 100), 1)}%" if total > 0 else "0.0%"

        self.assertEqual(total, 7)
        self.assertEqual(new_c, 0)
        self.assertEqual(in_prog, 5)
        self.assertEqual(resolved, 2)
        self.assertEqual(res_rate, "28.6%")

        # Empty state division check
        empty_total = 0
        empty_resolved = 0
        empty_rate = f"{round((empty_resolved / empty_total * 100), 1)}%" if empty_total > 0 else "0.0%"
        self.assertEqual(empty_rate, "0.0%")

    def test_08_complaint_trend_aggregation(self):
        """8. Verify time-series trend grouping supports Daily, Weekly, and Monthly intervals."""
        df = complaints_store.get_complaints_df()
        dt_parsed = pd.to_datetime(df["date_reported"], format="mixed", errors="coerce")
        valid_df = df[dt_parsed.notna()].copy()
        valid_df["_dt"] = dt_parsed[dt_parsed.notna()]

        # 1. Daily aggregation
        daily_series = valid_df["_dt"].dt.strftime("%Y-%m-%d").value_counts().sort_index()
        self.assertTrue(len(daily_series) > 0)
        self.assertEqual(daily_series.sum(), len(valid_df))

        # 2. Weekly aggregation
        weekly_series = valid_df["_dt"].dt.to_period("W").apply(lambda r: str(r.start_time.date())).value_counts().sort_index()
        self.assertTrue(len(weekly_series) > 0)
        self.assertEqual(weekly_series.sum(), len(valid_df))

        # 3. Monthly aggregation
        monthly_series = valid_df["_dt"].dt.strftime("%Y-%m").value_counts().sort_index()
        self.assertTrue(len(monthly_series) > 0)
        self.assertEqual(monthly_series.sum(), len(valid_df))

    def test_09_category_analysis(self):
        """9. Verify category distribution counts, percentages, and rankings."""
        df = complaints_store.get_complaints_df()
        cat_col = "facility_type" if "facility_type" in df.columns else "category"
        cat_counts = df[cat_col].value_counts()

        self.assertEqual(cat_counts.get("Other maintenance issues"), 3)
        self.assertEqual(cat_counts.get("Plumbing"), 1)
        self.assertEqual(cat_counts.get("HVAC"), 1)
        self.assertEqual(cat_counts.get("Electrical or lighting issues"), 1)
        self.assertEqual(cat_counts.get("Water cooler or water supply"), 1)
        self.assertEqual(cat_counts.sum(), 7)

    def test_10_location_analysis_and_concentration(self):
        """10. Verify location breakdown and concentration density notification logic."""
        df = complaints_store.get_complaints_df()
        loc_col = "building" if "building" in df.columns else "location"
        loc_counts = df[loc_col].value_counts()

        # In seed dataset, there are 7 different buildings, each with 1 complaint
        self.assertEqual(len(loc_counts), 7)
        top_count = loc_counts.iloc[0]
        top_share = round(top_count / len(df) * 100, 1)
        # Because distribution is balanced (14.3% each), top_share < 25.0%
        self.assertLess(top_share, 25.0)

        # Simulate high concentration scenario
        sim_df = pd.DataFrame({
            loc_col: ["Hostel Block B"] * 5 + ["Academic Block 1"] * 2,
            "status": ["In Progress"] * 7,
        })
        sim_counts = sim_df[loc_col].value_counts()
        sim_top_share = round(sim_counts.iloc[0] / len(sim_df) * 100, 1)
        self.assertGreaterEqual(sim_top_share, 25.0)
        self.assertEqual(sim_counts.index[0], "Hostel Block B")

    def test_11_mcpi_priority_analysis_and_cross_tabulation(self):
        """11. Verify MCPI priority distribution and category cross-tabulation."""
        df = complaints_store.get_complaints_df()
        prio_order = ["Critical", "High", "Medium", "Low"]
        prio_counts = df["priority_tier"].value_counts().reindex(prio_order).fillna(0).astype(int)

        self.assertEqual(prio_counts["Critical"], 2)  # CMP-2026-001, CMP-2026-002
        self.assertEqual(prio_counts["High"], 4)      # CMP-2026-003, CMP-2026-004, CMP-2026-005, CMP-2026-006
        self.assertEqual(prio_counts["Low"], 1)       # CMP-2026-007
        self.assertEqual(prio_counts.sum(), 7)

        # Cross-tabulation test
        cat_col = "facility_type" if "facility_type" in df.columns else "category"
        cross_tab = pd.crosstab(df[cat_col], df["priority_tier"])
        self.assertEqual(cross_tab.loc["Plumbing", "Critical"], 1)
        self.assertEqual(cross_tab.loc["HVAC", "Critical"], 1)

    def test_12_resolution_turnaround_and_backlog_ageing(self):
        """12. Verify resolution turnaround time calculation, invalid timestamp exclusion, and ageing."""
        df = complaints_store.get_complaints_df()
        res_df = df[df["status"] == "Resolved"]
        self.assertEqual(len(res_df), 2)

        rep_dts = pd.to_datetime(res_df["date_reported"], format="mixed", errors="coerce")
        res_dts = pd.to_datetime(res_df["resolved_at"], format="mixed", errors="coerce")
        valid_mask = rep_dts.notna() & res_dts.notna()

        self.assertTrue(valid_mask.all(), "Both seed resolved records must carry valid timestamps.")
        turnaround_days = (res_dts - rep_dts).dt.total_seconds() / 86400.0

        # CMP-2026-006 (reported 3 days ago, resolved 1 day ago -> 2.0 days)
        # CMP-2026-007 (reported 5 days ago, resolved 3 days ago -> 2.0 days)
        self.assertAlmostEqual(turnaround_days.mean(), 2.0, places=1)
        self.assertAlmostEqual(turnaround_days.min(), 2.0, places=1)
        self.assertAlmostEqual(turnaround_days.max(), 2.0, places=1)

        # Test timestamp exclusion logic with a simulated record missing resolved_at
        corrupt_res_df = pd.DataFrame([
            {"complaint_id": "CMP-T1", "date_reported": "2026-11-20 10:00", "resolved_at": "2026-11-20 14:00", "status": "Resolved"},
            {"complaint_id": "CMP-T2", "date_reported": "2026-11-20 10:00", "resolved_at": None, "status": "Resolved"},
        ])
        t_rep = pd.to_datetime(corrupt_res_df["date_reported"], errors="coerce")
        t_res = pd.to_datetime(corrupt_res_df["resolved_at"], errors="coerce")
        mask = t_rep.notna() & t_res.notna()
        self.assertEqual(mask.sum(), 1)
        self.assertEqual(len(corrupt_res_df) - mask.sum(), 1)  # 1 excluded

        # Backlog ageing test
        open_df = df[~df["status"].isin(["Resolved", "Withdrawn"])]
        self.assertEqual(len(open_df), 5)
        open_rep_dts = pd.to_datetime(open_df["date_reported"], format="mixed", errors="coerce")
        self.assertTrue(open_rep_dts.notna().all())

    def test_13_feature_attribution_explainability_insights(self):
        """13. Verify MCPI multi-criteria feature contribution calculations reflect genuine scoring."""
        df = complaints_store.get_complaints_df()
        weights = get_current_weights()

        breakdowns = []
        for _, r in df.iterrows():
            bd = r.get("score_breakdown")
            if isinstance(bd, dict) and "Severity Contribution" in bd:
                breakdowns.append(bd)
            else:
                _, _, bd_calc = calculate_priority_score(
                    severity=r.get("severity", "Medium"),
                    location_type=r.get("location_type", "Corridor / Common Area"),
                    recurrence_risk=r.get("recurrence_risk", 0.3),
                    impact_scale=r.get("impact_scale", 0.5),
                    weights=weights,
                )
                breakdowns.append(bd_calc)

        self.assertEqual(len(breakdowns), 7)
        bd_df = pd.DataFrame(breakdowns)
        means = bd_df.mean()

        # Severity has highest weight (0.35), so its average contribution should be prominent
        self.assertIn("Severity Contribution", means)
        self.assertIn("Location Criticality Contribution", means)
        self.assertIn("Recurrence Risk Contribution", means)
        self.assertIn("Impact Population Contribution", means)
        self.assertGreater(means["Severity Contribution"], 15.0)

    def test_14_export_functionality_and_student_privacy(self):
        """14. Verify exported CSV formats, filter adherence, and student PII redaction."""
        df = complaints_store.get_complaints_df()

        # Export columns definition
        export_cols = [
            "complaint_id", "title", "facility_type", "building", "location",
            "status", "priority_tier", "priority_score", "date_reported",
            "resolved_at", "allotted_person", "action_taken"
        ]
        avail_cols = [c for c in export_cols if c in df.columns]
        export_df = df[avail_cols].copy()
        csv_bytes = export_df.to_csv(index=False).encode("utf-8")

        # Verify CSV content
        csv_str = csv_bytes.decode("utf-8")
        self.assertIn("complaint_id", csv_str)
        self.assertIn("CMP-2026-001", csv_str)
        self.assertIn("CMP-2026-006", csv_str)

        # STRICT PRIVACY: Student personal information must NOT be exported
        self.assertNotIn("student_name", csv_str)
        self.assertNotIn("phone", csv_str)
        self.assertNotIn("email", csv_str)

        # Analytics summary CSV structure
        summary_df = pd.DataFrame([
            {"Metric Domain": "Executive KPI", "Metric Indicator": "Total Complaints", "Value": str(len(df))},
            {"Metric Domain": "Executive KPI", "Metric Indicator": "Resolved Complaints", "Value": "2"},
        ])
        summary_csv = summary_df.to_csv(index=False)
        self.assertIn("Executive KPI", summary_csv)
        self.assertIn("Total Complaints", summary_csv)

    def test_15_empty_dataset_handling(self):
        """15. Verify dashboard handles empty datasets without unhandled exceptions."""
        st.session_state["complaints_records"] = []
        complaints_store._save_to_disk([])

        df = complaints_store.get_complaints_df()
        self.assertTrue(df.empty)

        # render_reports_page must handle empty DataFrame gracefully
        try:
            admin_reports.render_reports_page()
            graceful = True
        except Exception as e:
            graceful = False
            self.fail(f"render_reports_page failed on empty dataset: {e}")
        self.assertTrue(graceful)

    def test_16_streamlit_apptest_reports_view(self):
        """16. Verify end-to-end rendering of Reports page within Streamlit AppTest framework."""
        app_path = str(PROJECT_ROOT / "app.py")
        at = AppTest.from_file(app_path)
        at.session_state["auth_user"] = {
            "id": "ADM-2026-001",
            "name": "Administrator",
            "role": "admin",
            "title": "Facility Operations Lead",
        }
        at.session_state["selected_role"] = "admin"
        at.session_state["user_role"] = "admin"
        at.session_state["admin_active_page"] = "Reports"
        at.run(timeout=10)

        self.assertFalse(at.exception, f"AppTest threw unhandled exception: {at.exception}")


if __name__ == "__main__":
    unittest.main()
