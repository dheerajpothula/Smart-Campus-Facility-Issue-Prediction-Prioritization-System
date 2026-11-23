import { api } from './apiClient';

export interface UploadPhotoResponse {
  success: boolean;
  original_filename: string;
  stored_filename: string;
  sha256: string;
  size_bytes: number;
  mime_type: string;
  dimensions?: { width: number; height: number };
}

export const uploadService = {
  uploadPhoto: async (file: File): Promise<UploadPhotoResponse> => {
    // Client-side quick validation before transmission
    const maxSizeBytes = 10 * 1024 * 1024; // 10 MB
    if (file.size > maxSizeBytes) {
      throw new Error('Photo attachment exceeds 10MB maximum file size limit.');
    }

    const validMimes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];
    if (!validMimes.includes(file.type.toLowerCase())) {
      throw new Error('Invalid file format. Only JPEG, PNG, and WebP raster images are permitted.');
    }

    return api.upload<UploadPhotoResponse>('/api/uploads/photo', file);
  },

  getPhotoUrl: (filename: string): string => {
    const base = import.meta.env.VITE_API_BASE_URL || '';
    return `${base}/api/uploads/${encodeURIComponent(filename)}`;
  },
};
