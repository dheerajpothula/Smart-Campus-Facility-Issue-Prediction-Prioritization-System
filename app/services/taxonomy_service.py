"""
FIPP 2.0 — Taxonomy Service.
Exposes the authoritative LPU RMS 19-category complaint classification hierarchy,
campus blocks, sub-blocks, room types, time slots, and legal declarations.
"""
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure smart-campus-facility-prediction is in path for single-source-of-truth import
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SMART_CAMPUS_DIR = PROJECT_ROOT / "smart-campus-facility-prediction"
if str(SMART_CAMPUS_DIR) not in sys.path:
    sys.path.insert(0, str(SMART_CAMPUS_DIR))

try:
    from src.data.complaint_categories import (
        CATEGORY_TYPES,
        MESSAGE_TYPES,
        MAINTENANCE_ELECTRICAL_HIERARCHY,
        ACADEMIC_ADMINISTRATIVE_HIERARCHY,
        CLASSIFICATION_HIERARCHY,
        HOSTEL_MAINTENANCE_CATEGORIES,
        CAMPUS_BLOCKS,
        CAMPUS_SUB_BLOCKS,
        ROOM_TYPES,
        TIME_SLOTS,
        STAGE2_MANDATORY_DECLARATIONS,
        FAQ_CONFIRMATION_TEXT,
        get_categories_for_type as src_get_categories_for_type,
        get_sub_categories as src_get_sub_categories,
        get_specific_categories as src_get_specific_categories,
        is_category_empty as src_is_category_empty,
        has_specific_options as src_has_specific_options,
    )
except ImportError:
    # Standalone fallback if invoked outside directory context
    from app.services._taxonomy_data import (  # fallback import
        CATEGORY_TYPES,
        MESSAGE_TYPES,
        MAINTENANCE_ELECTRICAL_HIERARCHY,
        ACADEMIC_ADMINISTRATIVE_HIERARCHY,
        CLASSIFICATION_HIERARCHY,
        HOSTEL_MAINTENANCE_CATEGORIES,
        CAMPUS_BLOCKS,
        CAMPUS_SUB_BLOCKS,
        ROOM_TYPES,
        TIME_SLOTS,
        STAGE2_MANDATORY_DECLARATIONS,
        FAQ_CONFIRMATION_TEXT,
    )


class TaxonomyService:
    """Provides taxonomy queries, validations, and hierarchy structures."""

    @staticmethod
    def get_full_hierarchy() -> Dict[str, Any]:
        """Returns the complete taxonomy tree with all 19 categories and location metadata."""
        return {
            "category_types": CATEGORY_TYPES,
            "message_types": MESSAGE_TYPES,
            "maintenance_categories": HOSTEL_MAINTENANCE_CATEGORIES,
            "hierarchy": CLASSIFICATION_HIERARCHY,
            "campus_blocks": CAMPUS_BLOCKS,
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
