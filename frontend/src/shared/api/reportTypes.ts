import { apiClient } from './client';
import type { CreateReportTypePayload, ReportType } from '../types/report-type';

export const reportTypesApi = {
  list: async () => {
    const response = await apiClient.get<ReportType[]>('/report-types');
    return response.data;
  },

  getById: async (reportTypeId: number) => {
    const response = await apiClient.get<ReportType>(`/report-types/${reportTypeId}`);
    return response.data;
  },

  create: async (payload: CreateReportTypePayload) => {
    const response = await apiClient.post<ReportType>('/report-types', payload);
    return response.data;
  },
};