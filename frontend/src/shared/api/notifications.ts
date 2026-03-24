import { apiClient } from './client';
import type {
  NotificationDetail,
  NotificationItem,
  NotificationUpdatePayload,
} from '../types/notification';

export const notificationsApi = {
  list: async () => {
    const response = await apiClient.get<NotificationItem[]>('/notifications');
    return response.data;
  },

  getById: async (notificationId: number) => {
    const response = await apiClient.get<NotificationDetail>(`/notifications/${notificationId}`);
    return response.data;
  },

  listByUser: async (userId: number) => {
    const response = await apiClient.get<NotificationItem[]>(`/notifications/users/${userId}`);
    return response.data;
  },

  update: async (notificationId: number, payload: NotificationUpdatePayload) => {
    const response = await apiClient.patch<NotificationDetail>(
      `/notifications/${notificationId}`,
      payload,
    );
    return response.data;
  },

  markRead: async (notificationId: number) => {
    const response = await apiClient.post<NotificationDetail>(
      `/notifications/${notificationId}/read`,
      {},
    );
    return response.data;
  },

  markAllRead: async (notifications: NotificationItem[]) => {
    const unread = notifications.filter((item) => !item.is_read);
    await Promise.all(unread.map((item) => notificationsApi.markRead(item.id)));
  },
};