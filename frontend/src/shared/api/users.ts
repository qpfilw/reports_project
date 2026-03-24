import { apiClient } from './client';
import type { AdminUserListItem } from '../types/admin';

export const usersApi = {
  list: async (roleCode?: string) => {
    const response = await apiClient.get<AdminUserListItem[]>('/users', {
      params: roleCode ? { role_code: roleCode } : {},
    });
    return response.data;
  },
};