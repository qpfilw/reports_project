import { apiClient } from './client';
import type {
  CreateProcessingScriptPayload,
  ProcessingScript,
  ProcessingScriptDetail,
  UpdateProcessingScriptPayload,
  ValidateProcessingScriptPayload,
  ValidateProcessingScriptResult,
} from '../types/processing-script';

export const processingScriptsApi = {
  list: async () => {
    const response = await apiClient.get<ProcessingScript[]>('/processing-scripts');
    return response.data;
  },

  getById: async (scriptId: number) => {
    const response = await apiClient.get<ProcessingScriptDetail>(`/processing-scripts/${scriptId}`);
    return response.data;
  },

  validate: async (payload: ValidateProcessingScriptPayload) => {
    const response = await apiClient.post<ValidateProcessingScriptResult>('/processing-scripts/validate', payload);
    return response.data;
  },

  create: async (payload: CreateProcessingScriptPayload) => {
    const response = await apiClient.post<ProcessingScriptDetail>('/processing-scripts', payload);
    return response.data;
  },

  update: async (scriptId: number, payload: UpdateProcessingScriptPayload) => {
    const response = await apiClient.patch<ProcessingScriptDetail>(`/processing-scripts/${scriptId}`, payload);
    return response.data;
  },
};
