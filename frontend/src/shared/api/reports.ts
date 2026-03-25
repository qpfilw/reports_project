import { apiClient } from './client';
import type {
  Report,
  ReportDetail,
  ReportStatusUpdatePayload,
  ReportWorkflowPayload,
  UpdateReportPayload,
} from '../types/report';
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
    const response = await apiClient.get<ReportDetail>(`/reports/${reportId}`);
    return response.data;
  },

  create: async (payload: CreateReportPayload) => {
    const response = await apiClient.post<ReportDetail>('/reports', payload);
    return response.data;
  },

  update: async (reportId: number, payload: UpdateReportPayload) => {
    const response = await apiClient.patch<ReportDetail>(`/reports/${reportId}`, payload);
    return response.data;
  },

  updateStatus: async (reportId: number, payload: ReportStatusUpdatePayload) => {
    const response = await apiClient.patch<ReportDetail>(`/reports/${reportId}/status`, payload);
    return response.data;
  },

  archive: async (reportId: number, last_comment?: string | null) => {
    const response = await apiClient.patch<ReportDetail>(`/reports/${reportId}/status`, {
      status: 'archived',
      last_comment: last_comment ?? null,
    });
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

  submitForReview: async (reportId: number, payload: ReportWorkflowPayload) => {
    const response = await apiClient.post<ReportDetail>(`/reports/${reportId}/submit-review`, payload);
    return response.data;
  },

  submitForApproval: async (reportId: number, payload: ReportWorkflowPayload) => {
    const response = await apiClient.post<ReportDetail>(`/reports/${reportId}/submit-approval`, payload);
    return response.data;
  },

  approve: async (reportId: number, payload: ReportWorkflowPayload) => {
    const response = await apiClient.post<ReportDetail>(`/reports/${reportId}/approve`, payload);
    return response.data;
  },

  reject: async (reportId: number, payload: ReportWorkflowPayload) => {
    const response = await apiClient.post<ReportDetail>(`/reports/${reportId}/reject`, payload);
    return response.data;
  },

  sendToRework: async (reportId: number, payload: ReportWorkflowPayload) => {
    const response = await apiClient.post<ReportDetail>(`/reports/${reportId}/rework`, payload);
    return response.data;
  },
};