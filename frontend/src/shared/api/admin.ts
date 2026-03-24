import { apiClient } from './client';
import type { RoleCode, User } from '../types/auth';
import type {
  AdminOverview,
  AdminPendingUser,
  AdminProjectAccessRequest,
} from '../types/admin';

export const adminApi = {
  overview: async () => {
    const response = await apiClient.get<AdminOverview>('/admin/overview');
    return response.data;
  },

  pendingUsers: async () => {
    const response = await apiClient.get<AdminPendingUser[]>('/admin/pending-users');
    return response.data;
  },

  approveUser: async (userId: number, roleCode: RoleCode) => {
    const response = await apiClient.post<User>(`/admin/users/${userId}/approve`, {
      role_code: roleCode,
    });
    return response.data;
  },

  rejectUser: async (userId: number, reason?: string) => {
    const response = await apiClient.post<User>(`/admin/users/${userId}/reject`, {
      reason: reason?.trim() || null,
    });
    return response.data;
  },

  assignUserRole: async (userId: number, roleCode: RoleCode) => {
    const response = await apiClient.post<User>(`/admin/users/${userId}/assign-role`, {
      role_code: roleCode,
    });
    return response.data;
  },

  blockUser: async (userId: number, reason?: string) => {
    const response = await apiClient.post<User>(`/admin/users/${userId}/block`, {
      reason: reason?.trim() || null,
    });
    return response.data;
  },

  unblockUser: async (userId: number, reason?: string) => {
    const response = await apiClient.post<User>(`/admin/users/${userId}/unblock`, {
      reason: reason?.trim() || null,
    });
    return response.data;
  },

  projectAccessRequests: async (accessStatus: 'requested' | 'approved' | 'rejected' = 'requested') => {
    const response = await apiClient.get<AdminProjectAccessRequest[]>('/admin/project-access-requests', {
      params: { access_status: accessStatus },
    });
    return response.data;
  },

  approveProjectAccess: async (memberId: number) => {
    const response = await apiClient.post<AdminProjectAccessRequest>(
      `/admin/project-access-requests/${memberId}/approve`,
      {},
    );
    return response.data;
  },

  rejectProjectAccess: async (memberId: number, reviewNote?: string) => {
    const response = await apiClient.post<AdminProjectAccessRequest>(
      `/admin/project-access-requests/${memberId}/reject`,
      {
        review_note: reviewNote?.trim() || null,
      },
    );
    return response.data;
  },
};