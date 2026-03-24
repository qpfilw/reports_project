import { apiClient } from './client';
import type { ReportUpload, ReportUploadDetail } from '../types/upload';

export const uploadsApi = {
  list: async () => {
    const response = await apiClient.get<ReportUpload[]>('/uploads');
    return response.data;
  },

  getById: async (uploadId: number) => {
    const response = await apiClient.get<ReportUploadDetail>(`/uploads/${uploadId}`);
    return response.data;
  },
};