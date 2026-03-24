import { apiClient } from './client';
import type { Project } from '../types/project';

export const projectsApi = {
  list: async () => {
    const response = await apiClient.get<Project[]>('/projects');
    return response.data;
  },

  getById: async (projectId: number) => {
    const response = await apiClient.get<Project>(`/projects/${projectId}`);
    return response.data;
  },
};