import { api } from './apiClient';
import type {
  AdminComplaintListResponse,
  AdminStatusUpdatePayload,
  AnalyticsReportResponse,
  ComplaintDetail,
  DashboardKPIs,
  StudentComplaintCreatePayload,
  StudentComplaintListResponse,
} from '../types';

export const complaintService = {
  // Student APIs
  submitStudentComplaint: async (payload: StudentComplaintCreatePayload): Promise<{
    success: boolean;
    token: string;
    complaint: ComplaintDetail;
    message: string;
  }> => {
    return api.post('/api/student/complaints/submit', payload);
  },

  getStudentComplaints: async (search?: string): Promise<StudentComplaintListResponse> => {
    const query = search ? `?search=${encodeURIComponent(search)}` : '';
    return api.get(`/api/student/complaints${query}`);
  },

  getStudentComplaintDetails: async (complaintId: string): Promise<ComplaintDetail> => {
    return api.get(`/api/student/complaints/${encodeURIComponent(complaintId)}`);
  },

  withdrawComplaint: async (complaintId: string, reason?: string): Promise<{ success: boolean; message: string }> => {
    return api.post(`/api/student/complaints/${encodeURIComponent(complaintId)}/withdraw`, { reason });
  },

  submitFeedback: async (
    complaintId: string,
    rating: number,
    comments?: string
  ): Promise<{ success: boolean; message: string }> => {
    return api.post(`/api/student/complaints/${encodeURIComponent(complaintId)}/feedback`, { rating, comments });
  },

  // Admin APIs
  getAdminKPIs: async (): Promise<DashboardKPIs> => {
    return api.get('/api/admin/kpis');
  },

  getAllAdminComplaints: async (params?: {
    search?: string;
    status?: string;
    category?: string;
    location?: string;
    priority?: string;
    limit?: number;
    offset?: number;
    sort_by?: string;
  }): Promise<AdminComplaintListResponse> => {
    const q = new URLSearchParams();
    if (params?.search) q.append('search', params.search);
    if (params?.status && params.status !== 'All Statuses') q.append('status', params.status);
    if (params?.category && params.category !== 'All Categories') q.append('category', params.category);
    if (params?.location && params.location !== 'All Locations') q.append('location', params.location);
    if (params?.priority && params.priority !== 'All Priorities') q.append('priority', params.priority);
    if (params?.limit) q.append('limit', String(params.limit));
    if (params?.offset) q.append('offset', String(params.offset));
    if (params?.sort_by) q.append('sort_by', params.sort_by);

    const queryStr = q.toString() ? `?${q.toString()}` : '';
    return api.get(`/api/admin/complaints${queryStr}`);
  },

  getUnassignedComplaints: async (limit = 50, offset = 0): Promise<AdminComplaintListResponse> => {
    return api.get(`/api/admin/complaints/unassigned?limit=${limit}&offset=${offset}`);
  },

  getInProgressComplaints: async (limit = 50, offset = 0): Promise<AdminComplaintListResponse> => {
    return api.get(`/api/admin/complaints/in-progress?limit=${limit}&offset=${offset}`);
  },

  getResolvedComplaints: async (limit = 50, offset = 0): Promise<AdminComplaintListResponse> => {
    return api.get(`/api/admin/complaints/resolved?limit=${limit}&offset=${offset}`);
  },

  updateComplaintStatus: async (
    complaintId: string,
    payload: AdminStatusUpdatePayload
  ): Promise<ComplaintDetail> => {
    return api.patch(`/api/admin/complaints/${encodeURIComponent(complaintId)}`, payload);
  },

  reopenComplaint: async (
    complaintId: string,
    remarks: string
  ): Promise<ComplaintDetail> => {
    return api.post(`/api/admin/complaints/${encodeURIComponent(complaintId)}/reopen`, { remarks });
  },

  getAnalyticsReport: async (params?: {
    start_date?: string;
    end_date?: string;
    category?: string;
    location?: string;
    status?: string;
    trend_agg?: string;
  }): Promise<AnalyticsReportResponse> => {
    const q = new URLSearchParams();
    if (params?.start_date) q.append('start_date', params.start_date);
    if (params?.end_date) q.append('end_date', params.end_date);
    if (params?.category) q.append('category', params.category);
    if (params?.location) q.append('location', params.location);
    if (params?.status) q.append('status', params.status);
    if (params?.trend_agg) q.append('trend_agg', params.trend_agg);

    const queryStr = q.toString() ? `?${q.toString()}` : '';
    return api.get(`/api/admin/reports/analytics${queryStr}`);
  },
};
