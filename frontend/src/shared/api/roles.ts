import { apiClient } from './client';
import type { Role } from '../types/auth';

export const rolesApi = {
  list: async () => {
    const response = await apiClient.get<Role[]>('/roles');
    return response.data;
  },
};