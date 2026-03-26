import { apiClient } from './client';
import type {
  AuthResponse,
  ChangePasswordRequest,
  LoginRequest,
  RefreshTokenRequest,
  RegisterRequest,
  UpdateMeRequest,
  User,
} from '../types/auth';

export const authApi = {
  login: async (payload: LoginRequest) => {
    const response = await apiClient.post<AuthResponse>('/auth/login', payload);
    return response.data;
  },

  register: async (payload: RegisterRequest) => {
    const response = await apiClient.post<AuthResponse>('/auth/register', payload);
    return response.data;
  },

  me: async () => {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },

  updateMe: async (payload: UpdateMeRequest) => {
    const response = await apiClient.patch<User>('/auth/me', payload);
    return response.data;
  },

  changePassword: async (payload: ChangePasswordRequest) => {
    const response = await apiClient.post<{ message: string }>(
      '/auth/change-password',
      payload,
    );
    return response.data;
  },

  refresh: async (payload: RefreshTokenRequest) => {
    const response = await apiClient.post('/auth/refresh', payload);
    return response.data;
  },
};