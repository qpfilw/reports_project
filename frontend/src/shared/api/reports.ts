import { apiClient } from './client';
import type { Report } from '../types/report';
import type { ReportUploadDetail } from '../types/upload';

export interface CreateReportPayload {
  project_id: number;
  report_type_id: number;
  title: string;
  description?: string | null;
  report_period_start: string;
  report_period_end: string;
  creator_id: number;
  current_assignee_id?: number | null;
  approver_id?: number | null;
  ml_template_id?: number | null;
}

export const reportsApi = {
  list: async () => {
    const response = await apiClient.get<Report[]>('/reports');
    return response.data;
  },

  getById: async (reportId: number) => {
    const response = await apiClient.get<Report>(`/reports/${reportId}`);
    return response.data;
  },

  create: async (payload: CreateReportPayload) => {
    const response = await apiClient.post<Report>('/reports', payload);
    return response.data;
  },

  uploadFile: async (reportId: number, file: File, comment?: string) => {
    const formData = new FormData();
    formData.append('file', file);

    if (comment?.trim()) {
      formData.append('comment', comment.trim());
    }

    const response = await apiClient.post<ReportUploadDetail>(
      `/reports/${reportId}/uploads/file`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      },
    );

    return response.data;
  },
};