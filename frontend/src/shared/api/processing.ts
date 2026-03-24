import { apiClient } from './client';
import type {
  ProcessingTask,
  ProcessingTaskDetail,
} from '../types/processing';

export interface LaunchProcessingPayload {
  report_id: number;
  report_upload_id: number;
  ml_template_id?: number | null;
  created_by?: number | null;
  priority?: number;
  params_json?: Record<string, unknown>;
}

export const processingApi = {
  listTasks: async () => {
    const response = await apiClient.get<ProcessingTask[]>('/processing/tasks');
    return response.data;
  },

  getTask: async (taskId: number) => {
    const response = await apiClient.get<ProcessingTaskDetail>(`/processing/tasks/${taskId}`);
    return response.data;
  },

  launchTask: async (payload: LaunchProcessingPayload) => {
    const response = await apiClient.post<ProcessingTaskDetail>(
      '/processing/tasks',
      payload,
    );
    return response.data;
  },
};