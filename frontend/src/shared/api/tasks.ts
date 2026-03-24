import { apiClient } from './client';
import type {
  ProcessingTaskDetail,
  TaskProgressResponse,
} from '../types/processing';

export const tasksApi = {
  getProgress: async (taskId: number) => {
    const response = await apiClient.get<TaskProgressResponse>(`/tasks/${taskId}/progress`);
    return response.data;
  },

  retry: async (taskId: number) => {
    const response = await apiClient.post<ProcessingTaskDetail>(`/tasks/${taskId}/retry`);
    return response.data;
  },

  cancel: async (taskId: number) => {
    const response = await apiClient.post<ProcessingTaskDetail>(`/tasks/${taskId}/cancel`);
    return response.data;
  },
};