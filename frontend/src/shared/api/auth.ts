import { apiClient } from './client';
import type {
  AuthResponse,
  LoginRequest,
  RefreshTokenRequest,
  RegisterRequest,
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

  refresh: async (payload: RefreshTokenRequest) => {
    const response = await apiClient.post('/auth/refresh', payload);
    return response.data;
  },
};