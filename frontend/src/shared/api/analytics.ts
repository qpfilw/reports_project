import { apiClient } from './client';
import type {
  AnalyticsOverview,
  CreateDashboardPayload,
  Dashboard,
  DashboardDetail,
  UpdateDashboardPayload,
} from '../types/analytics';

export const analyticsApi = {
  getOverview: async () => {
    const response = await apiClient.get<AnalyticsOverview>('/analytics/overview');
    return response.data;
  },

  listDashboards: async () => {
    const response = await apiClient.get<Dashboard[]>('/analytics/dashboards');
    return response.data;
  },

  getDashboardById: async (dashboardId: number) => {
    const response = await apiClient.get<DashboardDetail>(`/analytics/dashboards/${dashboardId}`);
    return response.data;
  },

  createDashboard: async (payload: CreateDashboardPayload) => {
    const response = await apiClient.post<DashboardDetail>('/analytics/dashboards', payload);
    return response.data;
  },

  updateDashboard: async (dashboardId: number, payload: UpdateDashboardPayload) => {
    const response = await apiClient.patch<DashboardDetail>(
      `/analytics/dashboards/${dashboardId}`,
      payload,
    );
    return response.data;
  },

  deleteDashboard: async (dashboardId: number) => {
    const response = await apiClient.delete<{ message: string }>(
        `/analytics/dashboards/${dashboardId}`,
    );
    return response.data;
  },
};