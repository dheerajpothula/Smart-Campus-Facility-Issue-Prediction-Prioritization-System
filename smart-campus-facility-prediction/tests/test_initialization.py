"""
Verification test for project structure, package imports, and page rendering.
"""
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestProjectStructure(unittest.TestCase):
    """Verifies that all required files and directories exist."""

    def test_directories_exist(self):
        expected_dirs = [
            "data/raw",
            "data/processed",
            "data/synthetic",
            "models",
            "src/data",
            "src/preprocessing",
            "src/features",
            "src/training",
            "src/prediction",
            "src/evaluation",
            "dashboard/pages",
            "dashboard/components",
            "notebooks",
            "tests",
            "docs",
        ]
        for rel_dir in expected_dirs:
            target_path = PROJECT_ROOT / rel_dir
            self.assertTrue(
                target_path.is_dir(), f"Expected directory missing: {target_path}"
            )

    def test_files_exist(self):
        expected_files = [
            "app.py",
            "requirements.txt",
            "README.md",
            ".gitignore",
            "src/__init__.py",
            "src/data/__init__.py",
            "src/preprocessing/__init__.py",
            "src/features/__init__.py",
            "src/training/__init__.py",
            "src/prediction/__init__.py",
            "src/evaluation/__init__.py",
            "dashboard/__init__.py",
            "dashboard/pages/__init__.py",
            "dashboard/pages/overview.py",
            "dashboard/pages/complaint_management.py",
            "dashboard/pages/predictive_analytics.py",
            "dashboard/pages/maintenance_priorities.py",
            "dashboard/pages/model_insights.py",
            "dashboard/components/__init__.py",
            "dashboard/components/sidebar.py",
            "dashboard/components/empty_state.py",
        ]
        for rel_file in expected_files:
            target_path = PROJECT_ROOT / rel_file
            self.assertTrue(
                target_path.is_file(), f"Expected file missing: {target_path}"
            )

    def test_page_modules_import(self):
        """Verifies that all page modules import cleanly."""
        from dashboard.pages import (
            complaint_management,
            maintenance_priorities,
            model_insights,
            overview,
            predictive_analytics,
        )

        self.assertTrue(hasattr(overview, "render_page"))
        self.assertTrue(hasattr(complaint_management, "render_page"))
        self.assertTrue(hasattr(predictive_analytics, "render_page"))
        self.assertTrue(hasattr(maintenance_priorities, "render_page"))
        self.assertTrue(hasattr(model_insights, "render_page"))

    def test_sidebar_component_import(self):
        """Verifies sidebar component imports and exports expected symbols."""
        from dashboard.components.sidebar import NAVIGATION_OPTIONS, render_sidebar

        self.assertEqual(len(NAVIGATION_OPTIONS), 5)
        self.assertTrue(callable(render_sidebar))


if __name__ == "__main__":
    unittest.main()
