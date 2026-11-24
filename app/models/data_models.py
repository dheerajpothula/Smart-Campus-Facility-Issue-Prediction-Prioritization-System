"""
FIPP 2.0 — Comprehensive Pydantic v2 Data Models & API Contracts.
Strictly encapsulates all taxonomy, student workflows, administrator operations,
MCPI priority weights, and machine learning telemetry schemas.
"""
import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


# ============================================================================
# 1. AUTHENTICATION SCHEMAS
# ============================================================================

class LoginRequest(BaseModel):
    username: str = Field(..., description="Administrator ID (e.g. ADM-2026-001) or Student ID (e.g. STU-2026-001 / STU101)")
    password: str = Field(..., min_length=1, description="Confidential user password")


class UserProfile(BaseModel):
    id: str
    name: str
    role: str
    title: Optional[str] = ""
    department: Optional[str] = ""
    email: Optional[str] = ""
    block: Optional[str] = None
    room_number: Optional[str] = None


class TokenResponse(BaseModel):
    success: bool = True
    access_token: str
    token: Optional[str] = None
    token_type: str = "bearer"
    refresh_token: Optional[str] = None
    expires_in_seconds: int = 3600
    user: UserProfile
    message: str = "Authenticated successfully."

    @model_validator(mode="after")
    def populate_token_alias(self) -> "TokenResponse":
        if not self.token and self.access_token:
            self.token = self.access_token
        return self


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# Legacy prototype submission model alias for backward compatibility
class ComplaintSubmission(BaseModel):
    reporter_name: Optional[str] = "Student"
    reporter_role: Optional[str] = "Student"
    student_id: Optional[str] = "STU101"
    facility_type: str = Field(..., description="Facility category e.g. Drinking Water / Coolers, Washroom / Plumbing, etc.")
    location: str = Field(..., description="Location e.g. Academic Block C, Student Center & Central Cafeteria")
    description: str = Field(..., min_length=5, max_length=1000)
    image_url: Optional[str] = None
    additional_notes: Optional[str] = None


# ============================================================================
# 2. TAXONOMY SCHEMAS (LPU RMS 19-CATEGORY HIERARCHY)
# ============================================================================

class TaxonomyHierarchyResponse(BaseModel):
    category_types: List[str]
    message_types: List[str]
    maintenance_categories: List[str]
    hierarchy: Dict[str, Dict[str, Dict[str, List[str]]]]
    campus_blocks: List[str]
    campus_sub_blocks: List[str]
    room_types: List[str]
    time_slots: List[str]
    mandatory_declarations: List[str]
    faq_confirmation_text: str


# ============================================================================
# 3. COMPLAINT WORKFLOW SCHEMAS
# ============================================================================

class StudentComplaintCreate(BaseModel):
    category_type: str = Field("Maintenance / Electrical Complaints", description="Category Type classification")
    message_type: str = Field(..., description="Message Type e.g. Grievance, Assistance, Enquiry, Feedback")
    title: Optional[str] = Field(None, description="Complaint Title or brief subject")
    category: str = Field(..., description="One of the 19 verified Maintenance / Electrical categories")
    sub_category: Optional[str] = Field(None, description="Subcategory selected under the category")
    specific_categories: List[str] = Field(default_factory=list, description="Specific issue options checked")
    building: str = Field(..., description="Campus Block or Building")
    sub_block: Optional[str] = Field(None, description="Sub Block or Wing")
    room_type: Optional[str] = Field("Room No", description="Room No vs Any Other")
    room_number: Optional[str] = Field(None, description="Room number if room_type is Room No")
    specified_location: Optional[str] = Field(None, description="Detailed location if room_type is Any Other")
    contact_number: str = Field(..., description="10-digit mobile contact number")
    availability_date: str = Field(..., description="Inspection availability date (YYYY-MM-DD)")
    time_slot: str = Field(..., description="Preferred inspection time slot")
    description: str = Field(..., min_length=5, max_length=500, description="Detailed problem description (5-500 chars)")
    declarations_accepted: bool = Field(..., description="Must confirm all 3 mandatory declarations")
    photo_stored_filename: Optional[str] = Field(None, description="Server-sanitized photo filename from upload endpoint")
    photo_sha256: Optional[str] = Field(None, description="Cryptographic SHA256 digest of verified attachment")

    @field_validator("declarations_accepted")
    @classmethod
    def check_declarations(cls, v: bool) -> bool:
        if not v:
            raise ValueError("All 3 mandatory declarations must be accepted before submitting a query.")
        return v

    @field_validator("contact_number")
    @classmethod
    def validate_contact(cls, v: str) -> str:
        clean = re.sub(r"[^\d]", "", v or "")
        if len(clean) < 10 or len(clean) > 13:
            raise ValueError("Contact Number must be a valid mobile phone number of at least 10 digits.")
        return clean

    @field_validator("availability_date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        try:
            d = datetime.strptime(v.strip(), "%Y-%m-%d").date()
            if d < date.today():
                raise ValueError("Availability Date cannot be in the past.")
        except ValueError as exc:
            if "Availability Date cannot" in str(exc):
                raise exc
            raise ValueError("Availability Date must be formatted as YYYY-MM-DD.")
        return v.strip()


class WithdrawalRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=300, description="Optional reason for withdrawing query")


class FeedbackRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Satisfaction rating from 1 (Poor) to 5 (Excellent)")
    comments: Optional[str] = Field(None, max_length=500, description="Constructive improvement feedback")


class AdminStatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(Submitted|Under Review|Assigned|In Progress|Resolved|Withdrawn)$")
    remarks: Optional[str] = Field(None, description="Administrative or triage remarks to record in audit trail")
    allotted_person: Optional[str] = Field(None, description="Name of assigned technician / engineering lead")
    squad_assigned: Optional[str] = Field(None, description="Department or maintenance squad assigned")


class AdminReopenRequest(BaseModel):
    remarks: str = Field(..., min_length=3, max_length=500, description="Reason for reopening resolved ticket")


# ============================================================================
# 4. COMPLAINT REPRESENTATION SCHEMAS
# ============================================================================

class RemarksHistoryEntry(BaseModel):
    remarks: str
    update_date: str
    name: str
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    supporting_document: Optional[str] = "None"


class ComplaintDetail(BaseModel):
    complaint_id: str
    student_id: Optional[str] = None
    student_name: Optional[str] = None
    category_type: str = "Maintenance / Electrical Complaints"
    message_type: str = "Grievance"
    category: str
    sub_category: Optional[str] = None
    specific_categories: List[str] = Field(default_factory=list)
    specific_category: Optional[str] = None
    facility_type: str
    building: str
    sub_block: Optional[str] = None
    room_type: Optional[str] = None
    room_number: Optional[str] = None
    specified_location: Optional[str] = None
    specific_location: Optional[str] = None
    location: str
    contact_number: Optional[str] = None
    availability_date: Optional[str] = None
    time_slot: Optional[str] = None
    title: str
    subject: Optional[str] = None
    description: str
    status: str = "Submitted"
    priority_tier: str = "Medium"
    priority_score: float = 50.0
    allotted_person: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    date_reported: str
    estimated_resolution: Optional[str] = None
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None
    closing_remarks: Optional[str] = None
    is_reopened: bool = False
    reopened_at: Optional[str] = None
    has_photo: bool = False
    photo_name: Optional[str] = None
    photo_stored_filename: Optional[str] = None
    remarks_history: List[RemarksHistoryEntry] = Field(default_factory=list)
    feedback: Optional[Dict[str, Any]] = None
    score_breakdown: Optional[Dict[str, float]] = None


class StudentComplaintListResponse(BaseModel):
    student_id: str
    student_name: str
    total_complaints: int
    open_complaints: int
    closed_complaints: int
    records: List[ComplaintDetail]


class AdminComplaintListResponse(BaseModel):
    total_count: int
    limit: int
    offset: int
    records: List[ComplaintDetail]


# ============================================================================
# 5. METRICS, KPIS & ANALYTICS SCHEMAS
# ============================================================================

class DashboardKPIs(BaseModel):
    total: int = Field(..., description="Total campus complaints")
    new: int = Field(..., description="New / Unassigned complaints awaiting triage")
    in_progress: int = Field(..., description="Active work orders in progress or assigned")
    resolved: int = Field(..., description="Resolved tickets in archive")
    withdrawn: int = Field(0, description="Withdrawn queries")
    resolution_rate_percent: float = Field(..., description="Ratio of resolved tickets")
    average_turnaround_days: Optional[float] = Field(None, description="Average turnaround in days")


class TrendPoint(BaseModel):
    period: str
    reported_count: int
    resolved_count: int = 0


class CategoryDistributionItem(BaseModel):
    category: str
    count: int
    percentage: float


class AnalyticsReportResponse(BaseModel):
    kpis: DashboardKPIs
    trends: List[TrendPoint]
    category_distribution: List[CategoryDistributionItem]
    location_distribution: List[Dict[str, Any]]
    priority_distribution: Dict[str, int]
    aging_brackets: Dict[str, int]


# ============================================================================
# 6. ML, SHAP & PREDICTIVE SCHEMAS
# ============================================================================

class PriorityWeights(BaseModel):
    severity: float = Field(0.35, ge=0.0, le=1.0)
    location_criticality: float = Field(0.25, ge=0.0, le=1.0)
    recurrence_probability: float = Field(0.25, ge=0.0, le=1.0)
    impact_population: float = Field(0.15, ge=0.0, le=1.0)

    # Legacy / prototype engine attribute compatibility
    weight_severity: Optional[float] = None
    weight_recurrence: Optional[float] = None
    weight_footfall: Optional[float] = None
    weight_location_risk: Optional[float] = None
    weight_impact: Optional[float] = None

    @model_validator(mode="after")
    def sync_weights(self) -> "PriorityWeights":
        if self.weight_severity is not None:
            self.severity = self.weight_severity
        else:
            self.weight_severity = self.severity

        if self.weight_recurrence is not None:
            self.recurrence_probability = self.weight_recurrence
        else:
            self.weight_recurrence = self.recurrence_probability

        if self.weight_footfall is not None:
            self.impact_population = self.weight_footfall
        else:
            self.weight_footfall = self.impact_population

        if self.weight_location_risk is not None:
            self.location_criticality = self.weight_location_risk
        else:
            self.weight_location_risk = self.location_criticality

        if self.weight_impact is not None:
            self.impact_population = self.weight_impact
        else:
            self.weight_impact = self.impact_population
        return self

    @property
    def total(self) -> float:
        return round(self.severity + self.location_criticality + self.recurrence_probability + self.impact_population, 4)

    def normalize(self) -> "PriorityWeights":
        s = self.severity + self.location_criticality + self.recurrence_probability + self.impact_population
        if s <= 0:
            return PriorityWeights()
        return PriorityWeights(
            severity=round(self.severity / s, 3),
            location_criticality=round(self.location_criticality / s, 3),
            recurrence_probability=round(self.recurrence_probability / s, 3),
            impact_population=round(self.impact_population / s, 3),
        )


class ShapFeatureContribution(BaseModel):
    feature_name: str
    feature_value: Any
    shap_value: float
    contribution: str  # "increase" or "decrease"
    description: str


# Alias for ML explainer backward-compatibility
ShapFeature = ShapFeatureContribution


class ShapExplanationResponse(BaseModel):
    base_value: float
    output_value: float
    explanation_method: Optional[str] = "Exact Linear/TreeSHAP Game-Theoretic Attribution"
    features: List[ShapFeatureContribution]
    summary: str


# Alias for ML explainer backward-compatibility
ShapExplanation = ShapExplanationResponse


class PredictiveMaintenanceItem(BaseModel):
    id: str
    facility: str
    location: str
    predicted_risk_level: str
    probability_percent: float
    days_to_projected_failure: int
    recommended_preventive_action: str
    disclaimer: str = "Prediction ≠ Confirmed Physical Breakdown. Algorithmic forecast based on historical recurrence cycles."


class PredictiveRiskItem(BaseModel):
    id: str
    facility: str
    location: str
    forecasted_risk_level: str
    predicted_window_days: int
    historical_recurrence_rate: Any
    last_reported_date: str
    mean_days_between_issues: Any
    prediction_factors: List[str]
    recommended_preventive_action: str
    confidence_score: float
    disclaimer: str

