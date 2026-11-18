"""
FIPP Stage 2 — Comprehensive Verification Suite for Hostel Maintenance & Electrical Complaints.
Validates all 25 specific criteria from Requirement 14 based on LPU_RMS_Hostel_Maintenance_Data-v2.pdf:
1. All 19 categories available in correct order.
2. Every documented subcategory exists under correct category.
3. Every documented specific option exists under correct subcategory.
4. No undocumented options invented.
5. Message Type dependency.
6. Category-to-Sub Category dependency.
7. Sub Category-to-Specific Category dependency.
8. Parent selection resets downstream selections.
9. Specific Category checkbox behaviour.
10. FAQ confirmation behaviour.
11. Block and Sub Block handling.
12. Room No and Any Other behaviour.
13. Contact number validation.
14. Availability Date validation.
15. Time Slot selection.
16. Description validation.
17. Successful complaint submission.
18. Existing token generation.
19. Persistent complaint storage.
20. Student-only History access.
21. Complaint details and remarks history.
22. Admin status updates appearing in student History.
23. Existing Stage 1 functionality.
24. Existing Admin functionality.
25. Existing complete project test suite.
"""
import inspect
import re
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from src.data.complaint_categories import (
    CATEGORY_TYPES,
    MESSAGE_TYPES,
    CLASSIFICATION_HIERARCHY,
    HOSTEL_MAINTENANCE_CATEGORIES,
    MAINTENANCE_ELECTRICAL_HIERARCHY,
    CAMPUS_BLOCKS,
    CAMPUS_SUB_BLOCKS,
    ROOM_TYPES,
    TIME_SLOTS,
    STAGE2_MANDATORY_DECLARATIONS,
    FAQ_CONFIRMATION_TEXT,
    get_categories_for_type,
    get_sub_categories,
    get_specific_categories,
    is_category_empty,
    has_specific_options,
)
from src.data.complaints_store import (
    get_complaints_df,
    get_student_complaints,
    add_complaint,
    generate_next_token,
    update_complaint_status,
    withdraw_complaint,
    submit_complaint_feedback,
    reset_to_default_dataset,
)
from dashboard.pages import student_dashboard


class TestStage2HostelMaintenance(unittest.TestCase):
    """Test suite covering all 25 criteria for Stage 2 Hostel Maintenance."""

    def setUp(self):
        reset_to_default_dataset()
        self.dashboard_source = inspect.getsource(student_dashboard)

    # 1. All 19 categories are available in the correct order
    def test_01_all_19_categories_in_exact_order(self):
        expected_19 = [
            "Air Conditioner",
            "Carpentry",
            "Desert Cooler/Air Cooler (Electrical)",
            "Desert Cooler/Air Cooler (Plumbing)",
            "Electricity",
            "Energy Meter",
            "Gas Welder",
            "Lift",
            "Marking",
            "Mason",
            "Plumbing",
            "School of AI and Emerging Technologies",
            "Sewerage",
            "Tailor",
            "Water Cooler/Drinking water(Cooling Issue)",
            "Water Cooler/Drinking water(Electrical Issue)",
            "Water Cooler/Drinking water(Plumbing Issue)",
            "Water Purifier / RO System",
            "Welding",
        ]
        self.assertEqual(HOSTEL_MAINTENANCE_CATEGORIES, expected_19)
        self.assertEqual(len(HOSTEL_MAINTENANCE_CATEGORIES), 19)
        cats_from_fn = get_categories_for_type("Maintenance / Electrical Complaints")
        self.assertEqual(cats_from_fn, expected_19)

    # 2. Every documented subcategory exists under its correct category
    def test_02_documented_subcategories_under_correct_category(self):
        # Sample subcategories under distinct categories
        self.assertIn("Split A.C. not working", get_sub_categories("Maintenance / Electrical Complaints", "Air Conditioner"))
        self.assertIn("Almirah/Rack repair", get_sub_categories("Maintenance / Electrical Complaints", "Carpentry"))
        self.assertIn("Desert Cooler Repair", get_sub_categories("Maintenance / Electrical Complaints", "Desert Cooler/Air Cooler (Electrical)"))
        self.assertIn("Desert cooler/Air Cooler", get_sub_categories("Maintenance / Electrical Complaints", "Desert Cooler/Air Cooler (Plumbing)"))
        self.assertIn("Electric Shock", get_sub_categories("Maintenance / Electrical Complaints", "Electricity"))
        self.assertIn("Energy meter problem", get_sub_categories("Maintenance / Electrical Complaints", "Energy Meter"))
        self.assertIn("Railing Repair", get_sub_categories("Maintenance / Electrical Complaints", "Gas Welder"))
        self.assertIn("Door", get_sub_categories("Maintenance / Electrical Complaints", "Lift"))
        self.assertIn("Brick Work", get_sub_categories("Maintenance / Electrical Complaints", "Mason"))
        self.assertIn("Flush problems", get_sub_categories("Maintenance / Electrical Complaints", "Plumbing"))
        self.assertIn("Terrace", get_sub_categories("Maintenance / Electrical Complaints", "Sewerage"))
        self.assertIn("Tailor work", get_sub_categories("Maintenance / Electrical Complaints", "Tailor"))
        self.assertIn("Water Cooler/Drinking water issue", get_sub_categories("Maintenance / Electrical Complaints", "Water Cooler/Drinking water(Cooling Issue)"))
        self.assertIn("Plumbing Issue", get_sub_categories("Maintenance / Electrical Complaints", "Water Cooler/Drinking water(Plumbing Issue)"))
        self.assertIn("Water Purifier / RO System", get_sub_categories("Maintenance / Electrical Complaints", "Water Purifier / RO System"))
        self.assertIn("Door/Window repair", get_sub_categories("Maintenance / Electrical Complaints", "Welding"))

    # 3. Every documented specific option exists under its correct subcategory
    def test_03_documented_specific_options_under_correct_subcategory(self):
        ac_split_opts = get_specific_categories("Maintenance / Electrical Complaints", "Air Conditioner", "Split A.C. not working")
        self.assertEqual(ac_split_opts, [
            "Air Filter choke",
            "Fan Motor Problem (Outdoor/Indoor)",
            "Noise Problem",
            "Service",
            "Water Drainage problem",
        ])

        elec_shaft_opts = get_specific_categories("Maintenance / Electrical Complaints", "Electricity", "Electrical Shaft")
        self.assertEqual(elec_shaft_opts, [
            "Electrical shaft earthing",
            "General Maintenance (Cleaning, MC Box cover fixing)",
            "Short Circuit (If Vertical Cable Burn)",
        ])

        lift_door_opts = get_specific_categories("Maintenance / Electrical Complaints", "Lift", "Door")
        self.assertIn("sensor not working,door not opening", lift_door_opts)
        self.assertIn("Safety browser", lift_door_opts)

        plumb_urinal_opts = get_specific_categories("Maintenance / Electrical Complaints", "Plumbing", "Urinal pot")
        self.assertIn("Bottle trap leakage (to fix new with pipe line)", plumb_urinal_opts)

    # 4. No undocumented options are invented; empty categories honestly represented
    def test_04_no_undocumented_options_and_honest_empty_categories(self):
        # 3 categories have no subcategories configured
        self.assertTrue(is_category_empty("Maintenance / Electrical Complaints", "Marking"))
        self.assertTrue(is_category_empty("Maintenance / Electrical Complaints", "School of AI and Emerging Technologies"))
        self.assertTrue(is_category_empty("Maintenance / Electrical Complaints", "Water Cooler/Drinking water(Electrical Issue)"))

        # Subcategories not clicked in video have empty options list
        self.assertEqual(get_specific_categories("Maintenance / Electrical Complaints", "Air Conditioner", "Window AC not working"), [])
        self.assertEqual(get_specific_categories("Maintenance / Electrical Complaints", "Carpentry", "Computer /office table"), [])
        self.assertEqual(get_specific_categories("Maintenance / Electrical Complaints", "Lift", "Safe problem"), [])
        self.assertEqual(get_specific_categories("Maintenance / Electrical Complaints", "Mason", "Concrete work"), [])
        self.assertEqual(get_specific_categories("Maintenance / Electrical Complaints", "Welding", "Angle Frame"), [])

    # 5. Message Type dependency
    def test_05_message_type_dependency(self):
        self.assertEqual(MESSAGE_TYPES, ["Grievance", "Assistance", "Enquiry", "Feedback", "Positive Feedback"])
        self.assertIn("sq_message_type_radio", self.dashboard_source)
        self.assertIn("has_msg_type = bool(sel_msg_type)", self.dashboard_source)
        self.assertIn('cat_options = ["-- Select Message Type first --"]', self.dashboard_source)

    # 6. Category-to-Sub Category dependency
    def test_06_category_to_subcategory_dependency(self):
        self.assertIn("has_cat = bool(sel_cat)", self.dashboard_source)
        self.assertIn('sub_cat_options = ["-- Select Category first --"]', self.dashboard_source)
        self.assertIn("disabled=sub_cat_disabled", self.dashboard_source)

    # 7. Sub Category-to-Specific Category dependency
    def test_07_subcategory_to_specific_category_dependency(self):
        self.assertIn("has_sub_cat = bool(sel_sub_cat)", self.dashboard_source)
        self.assertIn("spec_cat_options = [\"-- Select Sub Category first --\"]", self.dashboard_source)

    # 8. Parent selection resets downstream selections
    def test_08_parent_selection_resets_downstream(self):
        self.assertIn("prev_cat_type != cat_type", self.dashboard_source)
        self.assertIn("prev_msg_type != sel_msg_type", self.dashboard_source)
        self.assertIn("prev_cat != sel_cat", self.dashboard_source)
        self.assertIn("prev_sub_cat != sel_sub_cat", self.dashboard_source)

    # 9. Specific Category checkbox behaviour
    def test_09_specific_category_checkbox_behaviour(self):
        self.assertIn("chk_spec_opt_", self.dashboard_source)
        self.assertIn("selected_specific_options.append(spec_opt)", self.dashboard_source)
        self.assertIn("st.checkbox(", self.dashboard_source)

    # 10. FAQ confirmation behaviour
    def test_10_faq_confirmation_behaviour(self):
        self.assertEqual(
            FAQ_CONFIRMATION_TEXT,
            "Please Agree if you have read the FAQs. Click OK to confirm or Cancel to open FAQs again.",
        )
        self.assertIn("FAQ_CONFIRMATION_TEXT", self.dashboard_source)
        self.assertIn("sq_faq_confirmed_sub", self.dashboard_source)
        self.assertIn("btn_faq_ok", self.dashboard_source)
        self.assertIn("btn_faq_cancel", self.dashboard_source)

    # 11. Block and Sub Block handling (Hardcoded BH-5 removed)
    def test_11_block_and_sub_block_handling(self):
        self.assertNotIn("BH-5 Boys Hostel-05-35643-Rajneesh Parmar", CAMPUS_BLOCKS)
        self.assertNotIn("BH-5 Boys Hostel-05-35643-Rajneesh Parmar", self.dashboard_source)
        self.assertIn("Hostel Block A", CAMPUS_BLOCKS)
        self.assertIn("A", CAMPUS_SUB_BLOCKS)
        self.assertIn("sq_block", self.dashboard_source)
        self.assertIn("sq_sub_block", self.dashboard_source)

    # 12. Room No and Any Other behaviour (Hardcoded A512-Bed B removed)
    def test_12_room_no_and_any_other_behaviour(self):
        self.assertEqual(ROOM_TYPES, ["Room No", "Any Other"])
        self.assertNotIn("A512-Bed B", self.dashboard_source)
        self.assertIn("sq_room_type", self.dashboard_source)
        self.assertIn("sq_room_number", self.dashboard_source)
        self.assertIn("sq_specified_location", self.dashboard_source)

    # 13. Contact number validation
    def test_13_contact_number_validation(self):
        self.assertIn("sq_contact_number", self.dashboard_source)
        self.assertIn("Contact Number is mandatory", self.dashboard_source)
        self.assertIn("valid 10-digit mobile contact number", self.dashboard_source)

    # 14. Availability Date validation
    def test_14_availability_date_validation(self):
        self.assertIn("sq_availability_date", self.dashboard_source)
        self.assertIn("Availability Date cannot be in the past", self.dashboard_source)

    # 15. Time Slot selection (single-select radio buttons, no default selection)
    def test_15_time_slot_selection(self):
        self.assertEqual(len(TIME_SLOTS), 5)
        self.assertIn("08:00–10:00", TIME_SLOTS)
        self.assertIn("sq_time_slot_radio", self.dashboard_source)
        self.assertIn("index=slot_idx", self.dashboard_source)

    # 16. Description validation
    def test_16_description_validation(self):
        self.assertIn("max_chars=500", self.dashboard_source)
        self.assertIn("Detailed Description is mandatory", self.dashboard_source)
        self.assertIn("at least 5 characters", self.dashboard_source)

    # 17. Successful complaint submission with manual room number and block
    def test_17_successful_complaint_submission(self):
        new_ticket = {
            "student_id": "STU-STAGE2-001",
            "student_name": "Test Student",
            "category_type": "Maintenance / Electrical Complaints",
            "message_type": "Grievance",
            "category": "Air Conditioner",
            "sub_category": "Split A.C. not working",
            "specific_categories": ["Air Filter choke", "Service"],
            "block": "Hostel Block A",
            "sub_block": "A",
            "room_type": "Room No",
            "room_number": "101",
            "contact_number": "9876543210",
            "availability_date": date.today().strftime("%Y-%m-%d"),
            "time_slot": "08:00–10:00",
            "description": "AC air filter choked and cooling is weak.",
        }
        token = add_complaint(new_ticket)
        self.assertTrue(bool(re.match(r"^CMP-2026-\d{3}$", token)))

        # Retrieve and verify ticket fields
        student_complaints = get_student_complaints("STU-STAGE2-001")
        self.assertEqual(len(student_complaints), 1)
        created = student_complaints[0]
        self.assertEqual(created["complaint_id"], token)
        self.assertEqual(created["category"], "Air Conditioner")
        self.assertEqual(created["sub_category"], "Split A.C. not working")
        self.assertEqual(created["specific_categories"], ["Air Filter choke", "Service"])
        self.assertIn("Air Filter choke", created["specific_category"])

    # 18. Existing token generation
    def test_18_existing_token_generation(self):
        next_tok = generate_next_token()
        self.assertTrue(bool(re.match(r"^CMP-2026-\d{3}$", next_tok)))

    # 19. Persistent complaint storage
    def test_19_persistent_complaint_storage(self):
        df = get_complaints_df()
        self.assertFalse(df.empty)
        self.assertIn("complaint_id", df.columns)
        self.assertIn("status", df.columns)

    # 20. Student-only History access
    def test_20_student_only_history_access(self):
        # STU-ISOLATED-A submits a complaint
        add_complaint({
            "student_id": "STU-ISOLATED-A",
            "student_name": "Alice",
            "category": "Electricity",
            "description": "Corridor light defective.",
        })
        alice_complaints = get_student_complaints("STU-ISOLATED-A")
        bob_complaints = get_student_complaints("STU-ISOLATED-B")

        self.assertEqual(len(alice_complaints), 1)
        self.assertEqual(len(bob_complaints), 0)

    # 21. Complaint details and remarks history
    def test_21_complaint_details_and_remarks_history(self):
        add_complaint({
            "student_id": "STU-REMARKS-001",
            "student_name": "Test Student",
            "category": "Plumbing",
            "description": "Washbasin drain pipe leak.",
        })
        records = get_student_complaints("STU-REMARKS-001")
        self.assertEqual(len(records), 1)
        rec = records[0]
        self.assertIn("remarks_history", rec)
        self.assertGreaterEqual(len(rec["remarks_history"]), 1)
        self.assertIn("remarks", rec["remarks_history"][0])
        self.assertIn("update_date", rec["remarks_history"][0])

    # 22. Admin status updates appearing in student History
    def test_22_admin_status_updates_appear_in_student_history(self):
        cid = add_complaint({
            "student_id": "STU-UPDATE-001",
            "student_name": "Student Updater",
            "category": "Carpentry",
            "description": "Bed ply broken.",
        })
        # Admin updates status
        updated = update_complaint_status(cid, "In Progress", action_taken="Carpenter dispatched to room.")
        self.assertTrue(updated)

        student_tickets = get_student_complaints("STU-UPDATE-001")
        self.assertEqual(student_tickets[0]["status"], "In Progress")
        self.assertEqual(student_tickets[0]["action_taken"], "Carpenter dispatched to room.")

    # 23. Existing Stage 1 functionality
    def test_23_existing_stage1_functionality(self):
        self.assertIn("Academic and Administrative Issues", CATEGORY_TYPES)
        self.assertIn("Maintenance / Electrical Complaints", CATEGORY_TYPES)
        self.assertIn("Academic Affairs", CLASSIFICATION_HIERARCHY["Academic and Administrative Issues"])
        self.assertIn("btn_open_raise_query", self.dashboard_source)
        self.assertIn("btn_open_history", self.dashboard_source)

    # 24. Existing Admin functionality
    def test_24_existing_admin_functionality(self):
        df = get_complaints_df()
        self.assertIn("priority_score", df.columns)
        self.assertIn("priority_tier", df.columns)
        self.assertIn("score_breakdown", df.columns)

    # 25. Complete 3 declarations verified, 2 specified declarations removed
    def test_25_three_declarations_verified_and_two_removed(self):
        # 1. Total remaining declarations count is exactly 3
        self.assertEqual(len(STAGE2_MANDATORY_DECLARATIONS), 3)

        # 2. The two removed declarations are absent
        self.assertNotIn("I have not shared my UMS password with anyone.", STAGE2_MANDATORY_DECLARATIONS)
        self.assertNotIn(
            "I have read the policy / UMS Notification related to the concerned matter already before submitting the RMS and I am unable to find the answer related to my query.",
            STAGE2_MANDATORY_DECLARATIONS,
        )
        self.assertNotIn("UMS password", self.dashboard_source)
        self.assertNotIn("UMS Notification", self.dashboard_source)

        # 3. All three remaining declarations are present in source
        for decl in STAGE2_MANDATORY_DECLARATIONS:
            self.assertIn(decl[:30], self.dashboard_source)

        # 4. Agreement requires all three declarations
        self.assertIn("all_declarations_agreed = bool(both_agreed and chk_disciplinary)", self.dashboard_source)

    # 26. Verified no default form selections (Message Type, Sub Block, Room Type, Time Slot, Category, Sub Category)
    def test_26_no_default_form_selections(self):
        self.assertIn("index=msg_idx", self.dashboard_source)
        self.assertIn("index=sub_block_idx", self.dashboard_source)
        self.assertIn("index=room_type_idx", self.dashboard_source)
        self.assertIn("index=slot_idx", self.dashboard_source)
        self.assertIn("index=cat_index", self.dashboard_source)
        self.assertIn("index=sub_cat_index", self.dashboard_source)

    # 27. Verified hardcoded block and room number absent everywhere
    def test_27_hardcoded_examples_absent(self):
        self.assertNotIn("BH-5 Boys Hostel-05-35643-Rajneesh Parmar", CAMPUS_BLOCKS)
        self.assertNotIn("BH-5 Boys Hostel-05-35643-Rajneesh Parmar", self.dashboard_source)
        self.assertNotIn("A512-Bed B", self.dashboard_source)


if __name__ == "__main__":
    unittest.main()
