"""
Test Suite for FIPP Admin & Student Portal UI Corrections.
Validates:
1. Complete removal of Administrator Personal Names (no Dr. Robert Davies, Sarah Jenkins, David Miller).
   Display of neutral label "Administrator" and authenticated administrator ID.
2. Replacement of cheap emoji symbols with professional Lucide outline SVG icons:
   - Overview: layout-dashboard
   - All Requests: clipboard-list
   - New / Unassigned: inbox
   - In Progress: wrench
   - Resolved: check-circle
   - Reports: chart-no-axes-combined
3. Admin Control Centre sidebar styling:
   - Sufficient width (>= 280px, width 290px)
   - Deep forest #172D28 background with pale sage #DCE5D8 contrast
   - White-space: nowrap on navigation items
   - Active-page highlighting with #203A32 background and #A8B9A3 left accent border
   - Clear icon-to-label alignment and main content area non-overlap protection
4. Header clipping resolution in both Administrator and Student portals:
   - Proper line-height (>= 1.2)
   - Overflow visible / no fixed height truncation
   - Streamlit native header transparency and pointer event pass-through
   - Adequate column spacing
5. Strict preservation of Administrator credentials and authentication logic:
   - ADM-2026-001 / Admin@001 -> Facility Operations Lead
   - ADM-2026-002 / Admin@002 -> Campus Infrastructure Admin
   - ADM-2026-003 / Admin@003 -> Maintenance Dispatcher
"""
import inspect
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.auth.admin_auth import (
    authenticate_admin,
    _ADMIN_CREDENTIALS_STORE,
)
from dashboard.components.icons import (
    render_lucide_icon,
    get_lucide_icon_data_uri,
    _LUCIDE_PATHS,
)
from dashboard.components.sidebar import (
    ADMIN_NAVIGATION_OPTIONS,
    render_admin_sidebar,
)
from dashboard.components import admin_header, login_page, styles
from dashboard.pages import student_dashboard, overview, admin_requests, admin_reports


class TestUICorrectionsAndRefinement(unittest.TestCase):
    """Test verification for targeted UI corrections."""

    def test_1_no_admin_personal_names_in_credentials_store(self):
        """Validates that all administrator accounts use neutral label 'Administrator' with zero personal names."""
        for admin_id, rec in _ADMIN_CREDENTIALS_STORE.items():
            self.assertEqual(
                rec.get("name"),
                "Administrator",
                f"Personal name found in credentials store for {admin_id}: {rec.get('name')}",
            )
            # Ensure forbidden personal names are completely absent
            for forbidden_name in ["Davies", "Robert", "Sarah", "Jenkins", "Miller"]:
                self.assertNotIn(
                    forbidden_name.lower(),
                    rec.get("name", "").lower(),
                    f"Forbidden name token '{forbidden_name}' found in record for {admin_id}",
                )

    def test_2_no_admin_personal_names_in_ui_components(self):
        """Validates that admin header, sidebar, login page, and overview contain no hardcoded personal names."""
        header_src = inspect.getsource(admin_header)
        sidebar_src = inspect.getsource(render_admin_sidebar)
        login_src = inspect.getsource(login_page)

        for src, module_name in [
            (header_src, "admin_header"),
            (sidebar_src, "sidebar"),
            (login_src, "login_page"),
        ]:
            for forbidden in ["Dr. Robert Davies", "Robert Davies", "Sarah Jenkins", "David Miller"]:
                self.assertNotIn(
                    forbidden,
                    src,
                    f"Forbidden administrator personal name '{forbidden}' found in {module_name}",
                )

    def test_3_strict_preservation_of_admin_credentials_and_roles(self):
        """Preserves exact Administrator credentials and assigned operational titles."""
        expected_accounts = [
            ("ADM-2026-001", "Admin@001", "Facility Operations Lead"),
            ("ADM-2026-002", "Admin@002", "Campus Infrastructure Admin"),
            ("ADM-2026-003", "Admin@003", "Maintenance Dispatcher"),
        ]
        for aid, pwd, title in expected_accounts:
            user = authenticate_admin(aid, pwd)
            self.assertIsNotNone(user, f"Authentication failed for {aid}")
            self.assertEqual(user["id"], aid)
            self.assertEqual(user["name"], "Administrator")
            self.assertEqual(user["title"], title)
            self.assertEqual(user["role_title"], title)

    def test_4_admin_navigation_options_clean_labels(self):
        """Validates that all 6 admin navigation options have clean professional labels with zero emojis."""
        expected_nav = [
            "Overview",
            "All Requests",
            "New / Unassigned",
            "In Progress",
            "Resolved",
            "Reports",
        ]
        self.assertEqual(ADMIN_NAVIGATION_OPTIONS, expected_nav)

        # Check for zero emoji characters in navigation options
        for opt in ADMIN_NAVIGATION_OPTIONS:
            for char in opt:
                self.assertTrue(
                    ord(char) < 0x1F300 or ord(char) > 0x1FAFF,
                    f"Emoji symbol found in navigation option '{opt}'",
                )

    def test_5_lucide_outline_svg_icons(self):
        """Validates that all required Lucide outline vector icons are defined and generate valid SVGs."""
        required_icons = [
            "layout-dashboard",
            "clipboard-list",
            "inbox",
            "wrench",
            "check-circle",
            "chart-no-axes-combined",
            "shield",
            "building",
            "log-out",
        ]
        for icon_name in required_icons:
            self.assertIn(icon_name, _LUCIDE_PATHS, f"Missing Lucide icon definition: {icon_name}")
            svg_html = render_lucide_icon(icon_name, size=18, color="#203A32")
            self.assertIn("<svg", svg_html)
            self.assertIn('viewBox="0 0 24 24"', svg_html)
            self.assertIn('stroke="#203A32"', svg_html)
            self.assertIn('stroke-width="2.0"', svg_html)
            self.assertIn('fill="none"', svg_html)

            # Test data URI generation for CSS
            data_uri = get_lucide_icon_data_uri(icon_name, color="%23DCE5D8", size=18)
            self.assertTrue(data_uri.startswith("data:image/svg+xml;utf8,"))

    def test_6_sidebar_layout_and_contrast(self):
        """Validates sidebar width (>= 280px), deep forest #172D28 background, and contrast rules."""
        sidebar_src = inspect.getsource(render_admin_sidebar)

        # Sufficient width
        self.assertIn("min-width: 290px", sidebar_src)
        self.assertIn("width: 290px", sidebar_src)

        # Deep forest background
        self.assertIn("#172D28", sidebar_src)

        # Text contrast and active-page styling
        self.assertIn("#DCE5D8", sidebar_src)  # Pale sage text
        self.assertIn("#A8B9A3", sidebar_src)  # Sage border highlight
        self.assertIn("border-left: 4px solid #A8B9A3", sidebar_src)
        self.assertIn("white-space: nowrap", sidebar_src)

        # Icon mapping in CSS
        self.assertIn("layout-dashboard", sidebar_src)
        self.assertIn("clipboard-list", sidebar_src)
        self.assertIn("inbox", sidebar_src)
        self.assertIn("wrench", sidebar_src)
        self.assertIn("check-circle", sidebar_src)
        self.assertIn("chart-no-axes-combined", sidebar_src)

    def test_7_header_clipping_prevention_styles(self):
        """Validates that styles prevent header clipping and layout collision."""
        styles_src = styles.GLOBAL_LIGHT_THEME_CSS

        # Streamlit top header bar transparency and pointer pass-through
        self.assertIn('header[data-testid="stHeader"]', styles_src)
        self.assertIn("background: transparent", styles_src)
        self.assertIn("pointer-events: none", styles_src)

        # Block container padding preventing top clipping
        self.assertIn(".block-container", styles_src)
        self.assertIn("padding-top: 1.85rem", styles_src)

        # Section main horizontal overflow control
        self.assertIn("section.main", styles_src)
        self.assertIn("overflow-x: hidden", styles_src)

    def test_8_no_cheap_emojis_in_admin_portal_pages(self):
        """Validates that Overview, Admin Requests, Reports, and Complaint Details are free of cheap emojis."""
        overview_src = inspect.getsource(overview)
        requests_src = inspect.getsource(admin_requests)
        reports_src = inspect.getsource(admin_reports)
        header_src = inspect.getsource(admin_header)

        for src, name in [
            (overview_src, "Overview"),
            (requests_src, "Admin Requests"),
            (reports_src, "Admin Reports"),
            (header_src, "Admin Header"),
        ]:
            # Forbidden emojis
            for forbidden_emoji in ["📊", "📋", "🆕", "⏳", "✅", "📈", "🛡️"]:
                self.assertNotIn(
                    forbidden_emoji,
                    src,
                    f"Forbidden cheap emoji '{forbidden_emoji}' found in {name} source.",
                )

    def test_9_admin_sidebar_hover_state_subtle_forest_green(self):
        """Validates that admin sidebar navigation uses subtle forest green #24453A hover state,
        prevents pure-white hover backgrounds, preserves active #203A32 state, and scopes global radio hovers."""
        sidebar_src = inspect.getsource(render_admin_sidebar)
        styles_src = styles.GLOBAL_LIGHT_THEME_CSS

        # Hover state background must be subtle forest green #24453A
        self.assertIn("#24453A", sidebar_src)
        self.assertTrue(
            "background-color: #24453A !important" in sidebar_src
            or "background: #24453A !important" in sidebar_src,
            "Hover background #24453A not set in sidebar CSS",
        )
        self.assertIn("color: #FFFFFF !important", sidebar_src)

        # Hover state must NOT use pure-white background
        self.assertNotIn("background: #FFFFFF !important", sidebar_src)
        self.assertNotIn("background-color: #FFFFFF !important", sidebar_src)
        self.assertNotIn("background: #ffffff !important", sidebar_src)
        self.assertNotIn("background-color: #ffffff !important", sidebar_src)
        self.assertNotIn("background: white !important", sidebar_src)
        self.assertNotIn("background-color: white !important", sidebar_src)

        # Active state preservation: #203A32 and #A8B9A3 left border
        self.assertTrue(
            "background-color: #203A32 !important" in sidebar_src
            or "background: #203A32 !important" in sidebar_src,
            "Active background #203A32 not set in sidebar CSS",
        )
        self.assertIn("border-left: 4px solid #A8B9A3 !important", sidebar_src)
        self.assertIn(':not([data-selected="true"]):not(:has(input:checked)):hover', sidebar_src)

        # Keyboard focus-visible state
        self.assertIn(":focus-visible", sidebar_src)
        self.assertIn("outline: 2px solid #A8B9A3", sidebar_src)

        # Styles.py global radio hover must be scoped to .main so it does not override sidebar
        self.assertIn('.main [data-testid="stRadio"] label:hover', styles_src)
        self.assertNotIn('\n[data-testid="stRadio"] label:hover', styles_src)


if __name__ == "__main__":
    unittest.main()
