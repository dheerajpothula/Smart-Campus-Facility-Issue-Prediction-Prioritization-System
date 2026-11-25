"""
FIPP 2.0 — Taxonomy Service.
Exposes the authoritative 19-category campus complaint classification hierarchy,
structured campus block & floor reference data, room types, time slots, and legal declarations.
"""
import sys
from pathlib import Path
from typing import Any, Dict, List

from app.services.location_service import location_service

# Ensure smart-campus-facility-prediction is in path for single-source-of-truth import
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SMART_CAMPUS_DIR = PROJECT_ROOT / "smart-campus-facility-prediction"
if str(SMART_CAMPUS_DIR) not in sys.path:
    sys.path.insert(0, str(SMART_CAMPUS_DIR))

from src.data.complaint_categories import (  # noqa: E402
    ACADEMIC_ADMINISTRATIVE_HIERARCHY,
    CAMPUS_SUB_BLOCKS,
    CATEGORY_TYPES,
    CLASSIFICATION_HIERARCHY,
    FAQ_CONFIRMATION_TEXT,
    HOSTEL_MAINTENANCE_CATEGORIES,
    MAINTENANCE_ELECTRICAL_HIERARCHY,
    MESSAGE_TYPES,
    ROOM_TYPES,
    STAGE2_MANDATORY_DECLARATIONS,
    TIME_SLOTS,
)


class TaxonomyService:
    """Provides taxonomy queries, validations, and structured location hierarchy."""

    @staticmethod
    def get_full_hierarchy() -> Dict[str, Any]:
        """Returns the complete taxonomy tree along with active campus block/floor references."""
        blocks_ref = location_service.load_blocks()
        block_names = [str(b["display_name"]) for b in blocks_ref if b.get("display_name")]
        return {
            "category_types": CATEGORY_TYPES,
            "message_types": MESSAGE_TYPES,
            "maintenance_categories": HOSTEL_MAINTENANCE_CATEGORIES,
            "hierarchy": CLASSIFICATION_HIERARCHY,
            "campus_blocks": block_names,
            "blocks_reference": blocks_ref,
            "campus_sub_blocks": CAMPUS_SUB_BLOCKS,
            "room_types": ROOM_TYPES,
            "time_slots": TIME_SLOTS,
            "mandatory_declarations": STAGE2_MANDATORY_DECLARATIONS,
            "faq_confirmation_text": FAQ_CONFIRMATION_TEXT,
        }

    @staticmethod
    def get_categories_for_type(cat_type: str = "Maintenance / Electrical Complaints") -> List[str]:
        return list(CLASSIFICATION_HIERARCHY.get(cat_type, {}).keys())

    @staticmethod
    def get_subcategories(cat_type: str, category: str) -> List[str]:
        cat_dict = CLASSIFICATION_HIERARCHY.get(cat_type, {}).get(category, {})
        return list(cat_dict.keys())

    @staticmethod
    def get_specific_options(cat_type: str, category: str, subcategory: str) -> List[str]:
        cat_dict = CLASSIFICATION_HIERARCHY.get(cat_type, {}).get(category, {})
        return cat_dict.get(subcategory, [])

    @staticmethod
    def is_category_empty(cat_type: str, category: str) -> bool:
        cat_dict = CLASSIFICATION_HIERARCHY.get(cat_type, {}).get(category, {})
        return len(cat_dict) == 0

    @staticmethod
    def has_specific_options(cat_type: str, category: str, subcategory: str) -> bool:
        options = TaxonomyService.get_specific_options(cat_type, category, subcategory)
        return len(options) > 0


taxonomy_service = TaxonomyService()
