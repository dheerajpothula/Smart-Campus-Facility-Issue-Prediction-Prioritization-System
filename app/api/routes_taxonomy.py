"""
FIPP 2.0 — Taxonomy API Routes.
Exposes the authoritative 19-category LPU RMS taxonomy hierarchy,
category types, message types, campus locations, room types, and mandatory declarations.
"""
from fastapi import APIRouter
from app.models.data_models import TaxonomyHierarchyResponse
from app.services.taxonomy_service import taxonomy_service

router = APIRouter(prefix="/api/taxonomy", tags=["Taxonomy"])


@router.get("/hierarchy", response_model=TaxonomyHierarchyResponse)
def get_taxonomy_hierarchy():
    """
    Returns the complete hierarchical structure of campus facility classifications,
    including parent-child relationships, specific option checklists, and location data.
    """
    hierarchy_data = taxonomy_service.get_full_hierarchy()
    return TaxonomyHierarchyResponse(**hierarchy_data)
