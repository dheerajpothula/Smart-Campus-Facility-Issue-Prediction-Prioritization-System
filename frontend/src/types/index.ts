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
}
