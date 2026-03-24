import { apiClient } from './client';
import type { ReportType } from '../types/report-type';

export const reportTypesApi = {
  list: async () => {
    const response = await apiClient.get<ReportType[]>('/report-types');
    return response.data;
  },

  getById: async (reportTypeId: number) => {
    const response = await apiClient.get<ReportType>(`/report-types/${reportTypeId}`);
    return response.data;
  },
};