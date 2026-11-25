import { api } from './apiClient';
import type {
  ComplaintIntelligenceResponse,
  IntelligenceOverviewResponse,
} from '../types';

export const intelligenceService = {
  getOverview: async (): Promise<IntelligenceOverviewResponse> => {
    return api.get('/api/admin/intelligence/overview');
  },

  getComplaintIntelligence: async (
    complaintId: string
  ): Promise<ComplaintIntelligenceResponse> => {
    return api.get(
      `/api/admin/intelligence/complaint/${encodeURIComponent(complaintId)}`
    );
  },
};
