"""
FIPP — Complete Student Complaint Classification & Location Taxonomy (Stage 2).
Authoritative hierarchy of all 19 Maintenance / Electrical complaint categories,
subcategories, and specific complaint options extracted from LPU_RMS_Hostel_Maintenance_Data-v2.pdf.
"""
from typing import Dict, List, Optional

# 1. High-Level Category Types
CATEGORY_TYPES = [
    "Academic and Administrative Issues",
    "Maintenance / Electrical Complaints",
]

# 2. Message Types (Exact options from LPU RMS portal)
MESSAGE_TYPES = [
    "Grievance",
    "Assistance",
    "Enquiry",
    "Feedback",
    "Positive Feedback",
]

# 3. Complete Authoritative 19-Category Maintenance / Electrical Hierarchy
# Preserves exact category order, naming, punctuation, and casing from the reference PDF.
# Categories with no configured subcategories have empty dicts {}.
# Subcategories listed in the portal but not clicked in the video have empty lists [].
MAINTENANCE_ELECTRICAL_HIERARCHY: Dict[str, Dict[str, List[str]]] = {
    "Air Conditioner": {
        "Split A.C. not working": [
            "Air Filter choke",
            "Fan Motor Problem (Outdoor/Indoor)",
            "Noise Problem",
            "Service",
            "Water Drainage problem",
        ],
        "Window AC not working": [],  # Listed in Sub Category dropdown (not clicked in video)
    },
    "Carpentry": {
        "Almirah/Rack repair": [
            "Almirah repair",
            "Handle/ Kunda repair",
            "Lock repair",
            "Rack repair",
        ],
        "Bed Repair": [
            "Bed back repair",
            "Bed ply repair",
            "Nail and bolt fixing",
        ],
        "Carpentry work in rooms": [],  # Listed in Sub Category dropdown (not clicked in video)
        "Computer /office table": [],  # Listed in Sub Category dropdown (not clicked in video)
        "Door Problem": [
            "Door Closure repair",
            "Door Lock fixing",
            "Door repair",
            "Door Stopper Fixing",
            "New door closer fixing",
        ],
        "Looking glass": [],  # Listed in Sub Category dropdown (not clicked in video)
        "New Door Fitting": [
            "New door fixing",
        ],
        "Revolving chair/ Chair": [
            "Handle repair or change",
            "Hydraulic repair or change",
            "Revolving chair base repair or change",
        ],
        "Study table repair": [],  # Listed in Sub Category dropdown (not clicked in video)
        "Three seater repair": [
            "Handle Tightening and Fixing",
            "Padding and repair or Fixing",
        ],
    },
    "Desert Cooler/Air Cooler (Electrical)": {
        "Desert Cooler Repair": [
            "Motor Problem",
            "Pump Problem",
        ],
        "Desert cooler replacement": [
            "Desert cooler replacement",
        ],
    },
    "Desert Cooler/Air Cooler (Plumbing)": {
        "Desert cooler/Air Cooler": [
            "Desert cooler connection pipe broken",
            "Desert cooler stand missing",
            "Desert cooler leakage or Over flow",
            "Desert cooler pad changing",
        ],
    },
    "Electricity": {
        "Electric Shock": [
            "Electric shock",
        ],
        "Electrical Shaft": [
            "Electrical shaft earthing",
            "General Maintenance (Cleaning, MC Box cover fixing)",
            "Short Circuit (If Vertical Cable Burn)",
        ],
        "Fan Problem": [
            "Greasing",
            "General Problem / Not Working",
            "Regulator Problem /not working",
        ],
        "Geyser Repair": [
            "Geyser not working /not giving hot water",
            "Wiring Problem",
        ],
        "Hot Case": [
            "Hot case",
        ],
        "MCB Box": [
            "Burning smell",
            "Repair",
        ],
        "No Power Supply": [
            "In Room",
            "In corridor area",
        ],
        "Printer Machine": [],  # Listed in Sub Category dropdown (not clicked in video)
        "Short circuit": [
            "In Class Room",
            "In Room",
        ],
        "Switch /Socket room Problem": [
            "Switch /Socket room Problem",
        ],
        "Tube Light/Ceiling lights Problem": [
            "General Problem",
            "Lamp/Tube",
        ],
    },
    "Energy Meter": {
        "Energy meter problem": [
            "Discrepancy in meter reading",
            "General Problem /Not working",
            "Wiring Problem /meter wire",
        ],
    },
    "Gas Welder": {
        "Almirah/Rack repair": [
            "Lock Repair",
            "Rack Repair",
        ],
        "Railing Repair": [
            "Grill Repairing",
        ],
        "Three Seater / Computer chair / Revolving Chair": [
            "General work (Welding work, Chair Base)",
        ],
        "Water Cooler": [
            "Water Cooler body Repair",
            "Water Cooler Legs Repair",
            "Water Cooler Tank Leakage",
        ],
    },
    "Lift": {
        "Door": [
            "Door not closing",
            "Door not opening",
            "Oiling and greasing",
            "Safety browser",
            "sensor not working,door not opening",
        ],
        "Fan": [
            "Fan not working",
        ],
        "Light": [
            "Tube light not working",
        ],
        "Safe problem": [],  # Listed in Sub Category dropdown (not clicked in video)
        "Supply": [
            "Auto ARD Tripping",
        ],
        "Switch": [
            "Switch not working",
        ],
    },
    "Marking": {},  # Category listed in dropdown (not selected in video / no subcategories configured)
    "Mason": {
        "Brick Work": [
            "Lift Fixing",
            "Patch work",
        ],
        "Cement work": [
            "Repair work",
        ],
        "Concrete work": [],  # Listed in Sub Category dropdown (not clicked in video)
        "Grouting in washroom": [
            "Grouting work",
        ],
        "Inter locking": [
            "Inter locking repair",
        ],
        "Printer machine": [],  # Listed in Sub Category dropdown (not clicked in video)
        "Tile Work": [
            "Grouting repair",
            "Tile repair",
        ],
    },
    "Plumbing": {
        "CI pipe repair": [
            "CI pipe repair",
        ],
        "Flush problems": [
            "Leakage Repair with White Cement",
            "Push Cock Fixing",
            "Rubber joint change",
        ],
        "Geyser problem": [
            "Geyser pipe leaking",
            "Flush tank Repair",
            "Repair of seat leakage",
            "Seat cover repair or hinges fitting",
        ],
        "GI pipe": [
            "GI pipe leakage or new pipe fitting",
            "No water in geyser main water line problem",
        ],
        "Roof leakage": [
            "Angle valve damaged to be Changed",
            "Jait Line Broken",
            "Main Inlet/Out Valve piston leakage repair",
        ],
        "Shower": [
            "No water supply in shower main water line problem",
            "Shower broken",
            "Shower Leakage",
        ],
        "Tap problem": [
            "No water in tap main line problem",
            "Tap Broken",
            "Tap leakage",
        ],
        "Urinal pot": [
            "Bottle trap leakage (to fix new with pipe line)",
            "Bottle trap repair",
            "Changing of pot (fixing of new pot with waste coupling set)",
            "Connection pipe repair or new connection pipe fitting",
            "New bottle trap fixing",
            "Urinal pot Leakage",
            "waste coupling repair",
        ],
        "Washbasin": [
            "Connection pipe fitting",
            "New washbasin tap fitting",
            "Old washbasin repair or fitting",
            "Washbasin drain pipe repair or change",
        ],
        "Water Tank": [
            "Tank damage (leakage repair)",
            "Water tank cover and hinges fitting",
        ],
    },
    "School of AI and Emerging Technologies": {},  # Selected in video (03:50-03:54); contains only "Select"
    "Sewerage": {
        "CI pipe blockage": [],  # Listed in Sub Category dropdown (not clicked in video)
        "Main sewer line or Rain drain": [
            "Main sewer line cleaning outer area",
            "Manhole Blockage or Main line Blockage",
        ],
        "Terrace": [
            "Terrace rain jalli blockage",
        ],
        "Washroom blockage": [
            "Floor waste trap",
            "Blockage in room",
            "Open drain blockage",
            "Push cock blockage",
            "Urinal pot blockage",
            "Washbasin blockage",
        ],
        "Water cooler blockage": [
            "Water cooler drain blockage",
        ],
    },
    "Tailor": {
        "Tailor work": [
            "Chair cloth fixing (Per pc)",
            "Curtain work (Per pc)",
            "Flag work (Per pc)",
            "General Work",
            "Notice board cloth (Per pc)",
            "Repair/fixing of three seater (Per pc)",
            "Sofa Repair",
        ],
    },
    "Water Cooler/Drinking water(Cooling Issue)": {
        "Water Cooler/Drinking water issue": [
            "Not Cooling",
            "Water Taste Issue",
        ],
    },
    "Water Cooler/Drinking water(Electrical Issue)": {},  # Listed in dropdown (not selected in video)
    "Water Cooler/Drinking water(Plumbing Issue)": {
        "Plumbing Issue": [
            "No water supply in water cooler main line problem",
            "Water cooler cleaning",
            "Water cooler cover repair or fixing",
            "Water cooler leakage",
            "Water cooler new tap fixing",
            "Water cooler over flow or float valve changing",
            "Water cooler tap leakage",
            "Water cooler tray repair",
        ],
    },
    "Water Purifier / RO System": {
        "Water Purifier / RO System": [
            "Water leakage",
            "Chamber loose",
        ],
    },
    "Welding": {
        "Angle Frame": [],  # Listed in Sub Category dropdown (not clicked in video)
        "Door/Window repair": [
            "Grill Fixing",
            "Hinges/Kabja repair of door/window",
            "Kunda welding",
        ],
        "Main A S Gate Welding": [
            "Gate repair",
            "Kunda Repair",
        ],
    },
}

# 4. Academic and Administrative Hierarchy (Preserved for Stage 1 Compatibility)
ACADEMIC_ADMINISTRATIVE_HIERARCHY: Dict[str, Dict[str, List[str]]] = {
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
}

# 5. Combined Master Classification Hierarchy
CLASSIFICATION_HIERARCHY: Dict[str, Dict[str, Dict[str, List[str]]]] = {
    "Maintenance / Electrical Complaints": MAINTENANCE_ELECTRICAL_HIERARCHY,
    "Academic and Administrative Issues": ACADEMIC_ADMINISTRATIVE_HIERARCHY,
}

# Ordered list of all 19 verified Maintenance / Electrical categories
HOSTEL_MAINTENANCE_CATEGORIES: List[str] = list(MAINTENANCE_ELECTRICAL_HIERARCHY.keys())

# 6. Location Reference Data
CAMPUS_BLOCKS = [
    "BH-1 Boys Hostel",
    "BH-2 Boys Hostel",
    "GH-1 Girls Hostel",
    "GH-2 Girls Hostel",
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
    "A",
    "B",
    "C",
    "D",
    "E",
    "Ground Floor",
    "1st Floor",
    "2nd Floor",
    "3rd Floor",
    "4th Floor",
    "East Wing",
    "West Wing",
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

# The 3 Mandatory Declarations
STAGE2_MANDATORY_DECLARATIONS = [
    "I am responsible for the content typed in query.",
    "I understand that necessary disciplinary action can be initiated against me in case of use of derogatory words or false statements against any Student/Faculty/Staff/Higher Authority.",
    "The information given by me regarding the complaint/request is true to the best of my knowledge and if found false/ wrong, necessary disciplinary action can be initiated against me.",
]

# FAQ Confirmation Alert Text from LPU RMS PDF Page 2
FAQ_CONFIRMATION_TEXT = (
    "Please Agree if you have read the FAQs. Click OK to confirm or Cancel to open FAQs again."
)


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


def is_category_empty(cat_type: str, category: str) -> bool:
    """Returns True if the category has no configured subcategories."""
    cat_dict = CLASSIFICATION_HIERARCHY.get(cat_type, {}).get(category, {})
    return len(cat_dict) == 0


def has_specific_options(cat_type: str, category: str, sub_category: str) -> bool:
    """Returns True if the subcategory has configured specific complaint checkbox options."""
    options = get_specific_categories(cat_type, category, sub_category)
    return len(options) > 0
