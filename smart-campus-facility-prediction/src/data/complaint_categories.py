"""
FIPP — Student Complaint Classification & Location Taxonomy.
Defines the Stage 1 category hierarchy, message types, and campus locations.
Configurable and extensible for Stage 2 expansion.
"""
from typing import Dict, List

# 1. High-Level Category Types
CATEGORY_TYPES = [
    "Academic and Administrative Issues",
    "Maintenance / Electrical Complaints",
]

# 2. Message Types
MESSAGE_TYPES = [
    "Grievance",
    "Assistance",
    "Enquiry",
    "Feedback",
    "Positive Feedback",
]

# 3. Hierarchical Classification Taxonomy:
# Category Type -> Category -> Sub Category -> List of Specific Categories
CLASSIFICATION_HIERARCHY: Dict[str, Dict[str, Dict[str, List[str]]]] = {
    "Maintenance / Electrical Complaints": {
        "Electrical or lighting issues": {
            "Power Supply & Outages": [
                "Total Power Blackout",
                "Voltage Fluctuation",
                "Circuit Breaker Tripping",
                "UPS / Inverter Failure",
            ],
            "Lighting & Fixtures": [
                "Tube Light / LED Panel Defective",
                "Flickering Ceiling Light",
                "Corridor / Staircase Light Off",
                "Switchboard / Socket Sparking",
            ],
            "Fans & Ventilation": [
                "Ceiling Fan Not Working",
                "Fan Regulator Broken",
                "Exhaust Fan Defective",
            ],
        },
        "Plumbing": {
            "Water Supply & Pipelines": [
                "No Water Supply",
                "Low Water Pressure",
                "Pipe Leakage / Burst",
                "Main Supply Valve Leakage",
            ],
            "Drainage & Washroom Fixtures": [
                "Drainage Clogged / Blocked",
                "Tap / Faucet Broken or Leaking",
                "Flush Tank Malfunction",
                "Washbasin Choked",
            ],
        },
        "Water cooler or water supply": {
            "Drinking Water Facilities": [
                "Water Cooler Not Cooling",
                "Sensor / Dispenser Tap Malfunction",
                "Water Filter Cartridge Replacement",
                "Water Pooling around Dispenser",
            ],
        },
        "Washroom cleanliness": {
            "Hygiene & Housekeeping": [
                "Washroom Floor Dirty / Wet",
                "Toilet Commode Unclean",
                "Foul Odour / Ventilation Issue",
                "Soap / Sanitizer Dispenser Empty",
            ],
        },
        "Garbage overflow": {
            "Campus Waste Management": [
                "Dustbin / Waste Container Overflowing",
                "Corridor Litter Accumulation",
                "Mess / Cafeteria Waste Bin Full",
            ],
        },
        "HVAC": {
            "Air Conditioning & Climate": [
                "AC Unit Not Cooling",
                "AC Compressor Tripping",
                "Water Dripping from Indoor Unit",
                "Thermostat / Remote Defective",
            ],
        },
        "Other maintenance issues": {
            "Civil & Carpentry": [
                "Broken Door Lock / Handle",
                "Window Glass / Latch Damaged",
                "Study Desk / Chair Damaged",
                "Ceiling Plaster / Wall Tile Loose",
            ],
            "IT & Audio-Visual": [
                "LAN Port / Internet Connectivity Inactive",
                "Wi-Fi Access Point Not Responding",
                "Classroom Projector Display Fault",
            ],
        },
    },
    "Academic and Administrative Issues": {
        "Academic Affairs": {
            "Classroom & Course Operations": [
                "Class Schedule Clash",
                "Course Portal / LMS Access Discrepancy",
                "Lecture Hall Audio-Visual Setup Assistance",
                "Faculty Consultation Request",
            ],
            "Examinations & Evaluations": [
                "Admit Card / Exam Schedule Query",
                "Grade Sheet Discrepancy Clarification",
                "Re-evaluation Application Inquiry",
            ],
        },
        "Administrative Services": {
            "Student Documentation": [
                "Student ID Card Correction / Re-issue",
                "Bonafide / Character Certificate Issuance",
                "Official Transcript / Grade Report Request",
            ],
            "Accounts & Financial Services": [
                "Fee Receipt Verification",
                "Scholarship Disbursal Inquiry",
                "Hostel / Caution Deposit Refund",
            ],
        },
        "Library & Learning Resources": {
            "Library Facilities": [
                "Digital Library Login / Account Issue",
                "Book Borrowing / Return Record Clarification",
                "Quiet Reading Room Facility Assistance",
            ],
        },
    },
}

# 4. Campus Location Taxonomy
CAMPUS_BLOCKS = [
    "Hostel Block A",
    "Hostel Block B",
    "Hostel Block C",
    "Academic Block 1",
    "Academic Block 2",
    "Academic Block 3 (Data Science)",
    "Central Library",
    "Science Complex & Labs",
    "Student Cafeteria",
    "Sports Complex & Gym",
    "Administrative Block",
    "Campus Grounds / Parking",
]

CAMPUS_SUB_BLOCKS = [
    "Ground Floor",
    "1st Floor",
    "2nd Floor",
    "3rd Floor",
    "4th Floor",
    "East Wing",
    "West Wing",
    "North Wing",
    "South Wing",
    "Central Atrium",
    "Basement",
]

ROOM_TYPES = [
    "Room No",
    "Any Other",
]

TIME_SLOTS = [
    "08:00–10:00",
    "10:00–12:00",
    "12:00–14:00",
    "14:00–16:00",
    "16:00–18:00",
]


def get_categories_for_type(cat_type: str) -> List[str]:
    """Returns available categories for the selected category type."""
    return list(CLASSIFICATION_HIERARCHY.get(cat_type, {}).keys())


def get_sub_categories(cat_type: str, category: str) -> List[str]:
    """Returns available sub-categories for the selected category."""
    cat_dict = CLASSIFICATION_HIERARCHY.get(cat_type, {}).get(category, {})
    return list(cat_dict.keys())


def get_specific_categories(cat_type: str, category: str, sub_category: str) -> List[str]:
    """Returns available specific categories for the selected sub-category."""
    cat_dict = CLASSIFICATION_HIERARCHY.get(cat_type, {}).get(category, {})
    return cat_dict.get(sub_category, [])
