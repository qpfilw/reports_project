import { apiClient } from './client';
import type { MlTemplate } from '../types/template';
import type {
  MlPipelineResult,
  TemplatePredictionResult,
} from '../types/ml-pipeline';

export const mlApi = {
  listTemplates: async (reportTypeId?: number) => {
    const response = await apiClient.get<MlTemplate[]>('/ml/templates', {
      params: {
        ...(reportTypeId ? { report_type_id: reportTypeId } : {}),
        only_active: true,
      },
    });

    return response.data;
  },

  predictTemplateForUpload: async (uploadId: number) => {
    const response = await apiClient.get<TemplatePredictionResult>(
      `/ml/uploads/${uploadId}/template-prediction`,
    );
    return response.data;
  },

  getPipelineResult: async (taskId: number) => {
    const response = await apiClient.get<MlPipelineResult>(
      `/ml/tasks/${taskId}/pipeline-result`,
    );
    return response.data;
  },
};