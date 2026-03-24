import { apiClient } from './client';
import type { ExportArtifact, ExportArtifactDetail, ExportFormat } from '../types/export';

interface RunExportPayload {
  processing_task_id: number;
  report_id?: number | null;
  format: ExportFormat;
}

export const exportsApi = {
  list: async () => {
    const response = await apiClient.get<ExportArtifact[]>('/exports');
    return response.data;
  },

  run: async (payload: RunExportPayload) => {
    const response = await apiClient.post<ExportArtifactDetail>('/exports/run', payload);
    return response.data;
  },

  download: async (exportId: number) => {
    const response = await apiClient.get<Blob>(`/exports/${exportId}/download`, {
      responseType: 'blob',
    });
    return response.data;
  },
};