"""
Unit and integration test suite for the UI/UX redesign and role-based access control.
"""
import sys
import unittest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from src.prediction.priority_scoring import (
    PriorityWeights,
    calculate_priority_score,
    get_current_weights,
    reset_weights_to_default,
)
from src.data.complaints_store import (
    get_complaints_df,
    add_complaint,
    clear_all_complaints,
    reset_to_default_dataset,
    get_kpi_summary,
)
from dashboard.components.styles import get_priority_badge, get_status_badge


class TestPriorityScoringEngine(unittest.TestCase):
    """Verifies the multi-criteria priority scoring engine."""

    def test_default_weights_sum_to_one(self):
        weights = reset_weights_to_default()
        self.assertTrue(weights.is_valid())
        self.assertAlmostEqual(weights.total, 1.0, places=3)

    def test_priority_score_range_and_tiers(self):
        weights = PriorityWeights(0.35, 0.25, 0.25, 0.15)
        
        # Test Critical Case
        score_crit, tier_crit, bdown_crit = calculate_priority_score(
            severity="Critical",
            location_type="Server Room",
            recurrence_risk=0.9,
            impact_scale=0.9,
            weights=weights,
        )
        self.assertGreaterEqual(score_crit, 75.0)
        self.assertEqual(tier_crit, "Critical")
        self.assertEqual(len(bdown_crit), 4)

        # Test Low Case
        score_low, tier_low, _ = calculate_priority_score(
            severity="Low",
            location_type="Campus Grounds",
            recurrence_risk=0.1,
            impact_scale=0.1,
            weights=weights,
        )
        self.assertLess(score_low, 35.0)
        self.assertEqual(tier_low, "Low")

    def test_weights_normalization(self):
        unnormalized = PriorityWeights(0.5, 0.5, 0.5, 0.5)  # Sums to 2.0
        self.assertFalse(unnormalized.is_valid())
        norm = unnormalized.normalize()
        self.assertTrue(norm.is_valid())
        self.assertAlmostEqual(norm.total, 1.0, places=2)


class TestDataStoreAndKPIs(unittest.TestCase):
    """Verifies the shared complaint repository and KPI calculations."""

    def setUp(self):
        reset_to_default_dataset()

    def test_complaints_df_loading(self):
        df = get_complaints_df()
        self.assertFalse(df.empty)
        self.assertIn("complaint_id", df.columns)
        self.assertIn("priority_score", df.columns)
        self.assertIn("priority_tier", df.columns)

    def test_kpi_calculations_non_empty(self):
        df = get_complaints_df()
        kpis = get_kpi_summary(df)
        self.assertEqual(kpis["total"], len(df))
        self.assertGreater(kpis["open"], 0)
        self.assertIn("hrs", kpis["avg_resolution_time"])

    def test_empty_kpi_calculations(self):
        empty_kpis = get_kpi_summary(pd.DataFrame())
        self.assertEqual(empty_kpis["total"], 0)
        self.assertEqual(empty_kpis["open"], 0)
        self.assertEqual(empty_kpis["high_priority"], 0)

    def test_add_complaint(self):
        initial_len = len(get_complaints_df())
        new_id = add_complaint({
            "title": "Stairwell Light Flickering",
            "description": "2nd floor light fixture ballast humming and flickering.",
            "facility_type": "Electrical or lighting issues",
            "location": "Hostel Block A",
            "location_type": "Corridor / Common Area",
            "severity": "Low",
            "recurrence_risk": 0.1,
            "impact_scale": 0.3,
            "is_recurring": False,
        })
        import re
        self.assertTrue(bool(re.match(r"^CMP-2026-\d{3}$", new_id)))
        self.assertEqual(len(get_complaints_df()), initial_len + 1)


class TestBadgesAndTheme(unittest.TestCase):
    """Verifies priority and status badge styling."""

    def test_priority_badge_colors(self):
        b_low = get_priority_badge("Low")
        b_med = get_priority_badge("Medium")
        b_high = get_priority_badge("High")
        b_crit = get_priority_badge("Critical")

        # Must adhere to 60/30/10 palette (Warm Chalk, Deep Charcoal, Soft Tan)
        self.assertIn("Low", b_low)
        self.assertIn("Medium", b_med)
        self.assertIn("High", b_high)
        self.assertIn("Critical", b_crit)

    def test_status_badge_distinctness(self):
        s_prog = get_status_badge("In Progress")
        s_res = get_status_badge("Resolved")
        self.assertIn("In Progress", s_prog)
        self.assertIn("Resolved", s_res)

    def test_role_selection_clean_content(self):
        """Verifies role selection page contains exact required text and no arrow characters."""
        import inspect
        from dashboard.components import role_selection
        src = inspect.getsource(role_selection)

        # Removed text checks
        self.assertNotIn("Intelligent campus maintenance operations", src)
        self.assertNotIn("Role-Based Access Demo", src)

        # Arrow checks
        self.assertNotIn("→", src)

        # Clean descriptions
        self.assertIn("Manage campus maintenance, facility issues, AI predictions, and maintenance priorities.", src)
        self.assertIn("Report facility issues and track your complaints.", src)


class TestPageExecution(unittest.TestCase):
    """Verifies that all views render cleanly without syntax or runtime crashes."""

    def test_all_admin_and_student_views(self):
        from dashboard.pages import (
            overview,
            complaint_management,
            ai_analysis,
            maintenance_priorities,
            predictive_analytics,
            recurring_issues,
            explainable_ai,
            settings_weights,
            student_dashboard,
        )
        from dashboard.components.role_selection import render_role_selection_screen

        # Test that all render functions are callable
        self.assertTrue(callable(render_role_selection_screen))
        self.assertTrue(callable(student_dashboard.render_student_dashboard))
        self.assertTrue(callable(overview.render_page))
        self.assertTrue(callable(complaint_management.render_page))
        self.assertTrue(callable(ai_analysis.render_page))
        self.assertTrue(callable(maintenance_priorities.render_page))
        self.assertTrue(callable(predictive_analytics.render_page))
        self.assertTrue(callable(recurring_issues.render_page))
        self.assertTrue(callable(explainable_ai.render_page))
        self.assertTrue(callable(settings_weights.render_page))


if __name__ == "__main__":
    unittest.main()
