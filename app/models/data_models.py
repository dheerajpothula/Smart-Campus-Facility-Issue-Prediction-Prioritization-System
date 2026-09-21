from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class LoginRequest(BaseModel):
    username: str = Field(..., description="Student ID (e.g. STU101) or Admin ID (e.g. ADMIN01)")
    password: str = Field(..., description="User password")

class AuthResponse(BaseModel):
    success: bool
    token: str
    user: Dict[str, Any]
    message: str

class PriorityWeights(BaseModel):
    weight_severity: float = Field(0.35, ge=0.0, le=1.0, description="Weight for predicted severity")
    weight_recurrence: float = Field(0.25, ge=0.0, le=1.0, description="Weight for historical recurrence")
    weight_footfall: float = Field(0.20, ge=0.0, le=1.0, description="Weight for location footfall density")
    weight_location_risk: float = Field(0.10, ge=0.0, le=1.0, description="Weight for chronic location risk index")
    weight_impact: float = Field(0.10, ge=0.0, le=1.0, description="Weight for expected user/operational impact")

class ComplaintSubmission(BaseModel):
    reporter_name: Optional[str] = "Student"
    reporter_role: Optional[str] = "Student"
    student_id: Optional[str] = "STU101"
    facility_type: str = Field(..., description="Facility category e.g. Drinking Water / Coolers, Washroom / Plumbing, etc.")
    location: str = Field(..., description="Location e.g. Academic Block C, Student Center & Central Cafeteria")
    description: str = Field(..., min_length=5, max_length=1000)
    image_url: Optional[str] = None
    additional_notes: Optional[str] = None

class StudentComplaintView(BaseModel):
    complaint_id: str
    description: str
    facility_type: str
    location: str
    timestamp: str
    status: str
    priority: str
    priority_score: float

class AdminComplaintUpdate(BaseModel):
    status: Optional[str] = None
    department: Optional[str] = None
    technician_assigned: Optional[str] = None

class ShapFeature(BaseModel):
    feature_name: str
    feature_value: Any
    shap_value: float
    contribution: str  # "increase" or "decrease"
    description: str

class ShapExplanation(BaseModel):
    base_value: float
    output_value: float
    explanation_method: str
    features: List[ShapFeature]
    summary: str

class ComplaintRecord(BaseModel):
    complaint_id: str
    ticket_number: str
    timestamp: str
    reporter_name: str
    reporter_role: str
    student_id: Optional[str] = None
    facility_type: str
    location: str
    description: str
    image_url: Optional[str] = None
    predicted_category: str
    category_confidence: float
    predicted_severity: str
    severity_confidence: float
    recurrence_detected: bool
    recurrence_count: int
    location_risk: str
    footfall_level: str
    footfall_score: float
    severity_score: float
    recurrence_score: float
    location_risk_score: float
    impact_score: float
    expected_impact: str
    priority: str
    priority_score: float
    recommended_action: str
    status: str = "Open"
    technician_assigned: Optional[str] = "Pending Dispatch"
    department: Optional[str] = "General Facilities"
    resolution_time_hours: Optional[float] = None
    is_demo: bool = True
    resolved_at: Optional[str] = None
    shap_explanation: Optional[ShapExplanation] = None

class StatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(Open|Pending|In Progress|Resolved)$")

class PredictiveRiskItem(BaseModel):
    id: str
    facility: str
    location: str
    forecasted_risk_level: str
    predicted_window_days: int
    historical_recurrence_rate: float
    last_reported_date: str
    mean_days_between_issues: float
    prediction_factors: List[str]
    recommended_preventive_action: str
    confidence_score: float
    disclaimer: str = "Prediction ≠ Confirmed Physical Breakdown. Algorithmic issue-risk forecast based on historical recurrence cycles & footfall telemetry."

class LocationRiskItem(BaseModel):
    location_id: str
    location_name: str
    zone: str
    risk_level: str
    risk_score: float
    footfall_tier: str
    active_complaints: int
    recurring_complaints: int
    primary_vulnerabilities: List[str]
    coordinates: Dict[str, float]

class DashboardKPIs(BaseModel):
    total_complaints: int
    open_complaints: int
    in_progress_complaints: int
    resolved_complaints: int
    high_priority_issues: int
    critical_priority_issues: int
    recurring_issues: int
    high_risk_facilities: int
    avg_resolution_hours: float
    is_demo_dataset: bool = True
