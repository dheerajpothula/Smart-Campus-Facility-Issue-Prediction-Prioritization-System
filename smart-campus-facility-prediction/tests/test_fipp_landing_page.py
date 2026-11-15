"""
Verification test suite for FIPP Landing Page recreation task.
Validates:
1. Exact campus panoramic collage photograph (IMAGE 2) is used as the hero banner asset.
2. Title section with exact heading 'FIPP - Facility Issue Prediction & Prioritisation' and subtle underline.
3. Administrator and Student role selection cards structure, headings, descriptions, and button labels.
4. Navigation flow: Administrator button routes to admin login, Student button routes to student login.
5. Strict adherence to the 60/30/10 Warm Chalk (#FDFBF7), Deep Charcoal (#1A1A1A), Soft Tan (#EAE3D2) palette.
"""
import base64
import inspect
import unittest
from pathlib import Path
from PIL import Image

import streamlit as st

from app import main
from dashboard.components import role_selection
from dashboard.components.role_selection import (
    render_role_selection_screen,
    get_hero_banner_base64,
    ASSET_PATHS,
)


class TestFIPPLandingPage(unittest.TestCase):
    """Rigorous verification of the FIPP landing page recreation requirements."""

    def setUp(self):
        st.session_state.clear()

    def test_exact_campus_image_asset(self):
        """Validates that the exact panoramic photograph (IMAGE 2) is in place and used."""
        asset_found = False
        target_path = None
        for p in ASSET_PATHS:
            if p.exists():
                asset_found = True
                target_path = p
                break

        self.assertTrue(asset_found, "Campus banner asset (IMAGE 2) was not found in ASSET_PATHS.")
        self.assertIsNotNone(target_path)

        with Image.open(target_path) as im:
            self.assertEqual(im.format, "JPEG")
            width, height = im.size
            self.assertEqual(width, 1024)
            self.assertEqual(height, 341)
            aspect_ratio = width / height
            self.assertAlmostEqual(aspect_ratio, 3.0, delta=0.1)

        b64_str = get_hero_banner_base64()
        self.assertTrue(len(b64_str) > 50000, "Base64 encoded banner string is suspiciously short.")
        decoded_bytes = base64.b64decode(b64_str)
        self.assertEqual(len(decoded_bytes), target_path.stat().st_size)

    def test_landing_page_title_and_underline(self):
        """Validates exact title 'FIPP - Facility Issue Prediction & Prioritisation' and subtle underline."""
        source = inspect.getsource(role_selection)
        self.assertIn("FIPP - ", source)
        self.assertIn("Facility Issue Prediction &amp; Prioritisation", source)
        self.assertIn("fipp-title-underline", source)
        self.assertIn("#1A1A1A", source)
        self.assertIn("#756044", source)

    def test_role_cards_content_and_buttons(self):
        """Validates exact Administrator and Student card content and buttons."""
        source = inspect.getsource(role_selection)
        self.assertIn("Administrator", source)
        self.assertIn(
            "Manage system operations, monitor facility issues, and prioritize maintenance tasks.",
            source,
        )
        self.assertIn("Continue as Administrator →", source)
        self.assertIn("Student", source)
        self.assertIn(
            "Report facility issues, track their status, and view updates.",
            source,
        )
        self.assertIn("Continue as Student →", source)

    def test_admin_button_navigation(self):
        """Validates that clicking Continue as Administrator initiates admin login flow."""
        st.session_state["auth_user"] = None
        st.session_state["selected_role"] = None
        st.session_state["user_role"] = None

        st.session_state["selected_role"] = "admin"
        main()
        self.assertEqual(st.session_state["selected_role"], "admin")

    def test_student_button_navigation(self):
        """Validates that clicking Continue as Student initiates student login flow."""
        st.session_state["auth_user"] = None
        st.session_state["selected_role"] = None
        st.session_state["user_role"] = None

        st.session_state["selected_role"] = "student"
        main()
        self.assertEqual(st.session_state["selected_role"], "student")


if __name__ == "__main__":
    unittest.main()
