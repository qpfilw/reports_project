import { apiClient } from './client';
import type { AuditLog, AuditLogDetail } from '../types/audit';

export const auditApi = {
  list: async () => {
    const response = await apiClient.get<AuditLog[]>('/audit');
    return response.data;
  },

  getById: async (auditId: number) => {
    const response = await apiClient.get<AuditLogDetail>(`/audit/${auditId}`);
    return response.data;
  },
};
