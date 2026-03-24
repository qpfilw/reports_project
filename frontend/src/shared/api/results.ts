import { apiClient } from './client';
import type { NormalizedDataset, NormalizedDatasetDetail } from '../types/result';

export const resultsApi = {
  list: async () => {
    const response = await apiClient.get<NormalizedDataset[]>('/results');
    return response.data;
  },

  getById: async (resultId: number) => {
    const response = await apiClient.get<NormalizedDatasetDetail>(`/results/${resultId}`);
    return response.data;
  },

  getByTask: async (taskId: number) => {
    const response = await apiClient.get<NormalizedDatasetDetail>(`/results/by-task/${taskId}`);
    return response.data;
  },
};