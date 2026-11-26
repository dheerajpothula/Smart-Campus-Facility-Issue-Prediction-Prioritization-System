/**
 * FIPP 2.0 — Core TypeScript Type Definitions.
 * Formally aligned with FastAPI Pydantic v2 schemas.
 */

export type UserRole = 'student' | 'admin';

export interface UserProfile {
  id: string;
  name: string;
  role: UserRole;
  title?: string;
  department?: string;
  email?: string;
  block?: string | null;
  room_number?: string | null;
  must_change_password?: boolean;
  identity_verification?: string | null;
}

export interface ProvisionedStudent {
  student_id: string;
  name: string;
  block?: string | null;
  room_number?: string | null;
  is_active: boolean;
  registration_source?: string;
  identity_verification?: string;
  provisioned_at?: string;
  provisioned_by?: string;
}

export interface CampusFloorReference {
  floor_id: string;
  block_id: string;
  floor_label: string;
  sort_order: number;
  verification_status: string;
}

export interface CampusBlockReference {
  block_id: string;
  display_name: string;
  block_category: string;
  floor_count: number | null;
  floor_status: string;
  verification_status: string;
  notes?: string | null;
  floors: CampusFloorReference[];
}

export interface AuthResponse {
  success: boolean;
  access_token: string;
  token?: string;
  token_type: string;
  refresh_token?: string;
  expires_in_seconds: number;
  user: UserProfile;
  message: string;
  is_new_registration?: boolean | null;
}

export interface RemarksHistoryEntry {
  remarks: string;
  update_date: string;
  name: string;
  previous_status?: string | null;
  new_status?: string | null;
  supporting_document?: string | null;
}

export interface FeedbackData {
  rating: number;
  satisfaction?: string;
  comments?: string;
  submitted_at?: string;
}

export interface ComplaintDetail {
  complaint_id: string;
  student_id?: string | null;
  student_name?: string | null;
  category_type: string;
  message_type: string;
  category: string;
  sub_category?: string | null;
  specific_categories: string[];
  specific_category?: string | null;
  facility_type: string;
  building: string;
  block_id?: string | null;
  floor_id?: string | null;
  floor_label?: string | null;
  sub_block?: string | null;
  room_type?: string | null;
  room_number?: string | null;
  specified_location?: string | null;
  specific_location?: string | null;
  location: string;
  contact_number?: string | null;
  availability_date?: string | null;
  time_slot?: string | null;
  title: string;
  subject?: string | null;
  description: string;
  status: 'Submitted' | 'Under Review' | 'Assigned' | 'In Progress' | 'Resolved' | 'Withdrawn';
  priority_tier: 'Low' | 'Medium' | 'High' | 'Critical';
  priority_score: number;
  allotted_person?: string | null;
  department?: string | null;
  designation?: string | null;
  date_reported: string;
  estimated_resolution?: string | null;
  resolved_at?: string | null;
  resolved_by?: string | null;
  resolution_date?: string | null;
  status_history?: Array<{ status: string; timestamp?: string; date?: string }>;
  closing_remarks?: string | null;
  is_reopened: boolean;
  reopened_at?: string | null;
  original_resolved_at?: string | null;
  original_resolved_by?: string | null;
  previous_closing_remarks?: string | null;
  has_photo: boolean;
  photo_name?: string | null;
  photo_stored_filename?: string | null;
  remarks_history: RemarksHistoryEntry[];
  feedback?: FeedbackData | null;
  score_breakdown?: Record<string, number> | null;
  mcpi_details?: McpiExplanation | null;
}

export interface McpiComponentItem {
  key: string;
  label: string;
  weight: number;
  raw_label: string;
  normalized_input: number;
  points: number;
  max_points: number;
}

export interface McpiThresholdItem {
  tier: string;
  rule: string;
  min_score: number;
}

export interface McpiExplanation {
  scoring_type: string;
  is_ml_prediction: boolean;
  priority_score: number;
  priority_tier: string;
  weights: Record<string, number>;
  thresholds: McpiThresholdItem[];
  components: McpiComponentItem[];
  classification_rationale: string;
}

export interface ShapFeatureContribution {
  feature_name: string;
  feature_value: string | number;
  shap_value: number;
  contribution: 'increase' | 'decrease';
  description: string;
}

export interface ShapAvailabilityResponse {
  complaint_id: string;
  available: boolean;
  status: string;
  reason: string;
  model_artifact_present: boolean;
  shap_library_installed: boolean;
  explanation_method?: string | null;
  model_version?: string | null;
  prediction_timestamp?: string | null;
  prediction?: string | number | null;
  base_value?: number | null;
  output_value?: number | null;
  features: ShapFeatureContribution[];
  summary: string;
}

export interface ComplaintIntelligenceResponse {
  complaint_id: string;
  mcpi: McpiExplanation;
  shap: ShapAvailabilityResponse;
}

export interface IntelligenceOverviewResponse {
  capabilities: {
    mcpi_engine: {
      available: boolean;
      scoring_type: string;
      is_ml_prediction: boolean;
      weights: Record<string, number>;
      thresholds: McpiThresholdItem[];
    };
    shap_explainability: {
      available: boolean;
      status: string;
      reason: string;
      model_artifact_present: boolean;
      artifact_filenames: string[];
      shap_library_installed: boolean;
    };
    auxiliary_models: {
      nlp_classifier: Record<string, any>;
      severity_model: Record<string, any>;
    };
    predictive_forecasting: {
      available: boolean;
      status: string;
      reason: string;
    };
  };
  operational_analytics: AnalyticsReportResponse;
}

export interface StudentComplaintListResponse {
  student_id: string;
  student_name: string;
  total_complaints: number;
  open_complaints: number;
  closed_complaints: number;
  records: ComplaintDetail[];
}

export interface AdminComplaintListResponse {
  total_count: number;
  limit: number;
  offset: number;
  records: ComplaintDetail[];
}

export interface DashboardKPIs {
  total: number;
  new: number;
  in_progress: number;
  resolved: number;
  withdrawn: number;
  resolution_rate_percent: number;
  average_turnaround_days?: number | null;
}

export interface TaxonomyHierarchyResponse {
  category_types: string[];
  message_types: string[];
  maintenance_categories: string[];
  hierarchy: Record<string, Record<string, Record<string, string[]>>>;
  campus_blocks: string[];
  blocks_reference?: CampusBlockReference[];
  campus_sub_blocks: string[];
  room_types: string[];
  time_slots: string[];
  mandatory_declarations: string[];
  faq_confirmation_text: string;
}

export interface StudentComplaintCreatePayload {
  category_type: string;
  message_type: string;
  title?: string;
  category: string;
  sub_category?: string;
  specific_categories: string[];
  building: string;
  block_id?: string;
  floor_id?: string;
  floor_label?: string;
  sub_block?: string;
  room_type: string;
  room_number?: string;
  specified_location?: string;
  contact_number: string;
  availability_date: string;
  time_slot: string;
  description: string;
  declarations_accepted: boolean;
  photo_stored_filename?: string;
  photo_sha256?: string;
}

export interface AdminStatusUpdatePayload {
  status: 'Submitted' | 'Under Review' | 'Assigned' | 'In Progress' | 'Resolved' | 'Withdrawn';
  remarks?: string;
  allotted_person?: string;
  squad_assigned?: string;
}

export interface WorkloadSummary {
  active_total: number;
  unassigned_active: number;
  assigned_active: number;
  reopened_count: number;
  average_mcpi_score?: number | null;
  active_average_mcpi_score?: number | null;
  high_critical_active: number;
}

export interface AssignmentDistributionItem {
  assignee: string;
  active_count: number;
  resolved_count: number;
  total_count: number;
}

export interface AnalyticsReportResponse {
  kpis: DashboardKPIs;
  trends: Array<{
    period: string;
    reported_count: number;
    resolved_count: number;
  }>;
  category_distribution: Array<{
    category: string;
    count: number;
    percentage: number;
  }>;
  location_distribution: Array<{
    location?: string;
    building?: string;
    count: number;
    percentage?: number;
    [key: string]: any;
  }>;
  priority_distribution: Record<string, number>;
  aging_brackets: Record<string, number>;
  workload_summary?: WorkloadSummary | null;
  assignment_distribution?: AssignmentDistributionItem[];
  status_distribution?: Record<string, number>;
}
