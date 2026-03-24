import { apiClient } from './client';
import type {
  CreateMlTemplatePayload,
  MlTemplate,
  MlTemplateDetail,
  UpdateMlTemplatePayload,
} from '../types/template';

export const templatesApi = {
  list: async () => {
    const response = await apiClient.get<MlTemplate[]>('/templates');
    return response.data;
  },

  getById: async (templateId: number) => {
    const response = await apiClient.get<MlTemplateDetail>(`/templates/${templateId}`);
    return response.data;
  },

  create: async (payload: CreateMlTemplatePayload) => {
    const response = await apiClient.post<MlTemplateDetail>('/templates', payload);
    return response.data;
  },

  update: async (templateId: number, payload: UpdateMlTemplatePayload) => {
    const response = await apiClient.patch<MlTemplateDetail>(`/templates/${templateId}`, payload);
    return response.data;
  },
};