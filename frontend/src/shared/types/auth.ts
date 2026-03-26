export type RoleCode = 'pending' | 'admin' | 'manager' | 'operator' | 'viewer';

export interface Role {
  id: number;
  code: RoleCode;
  name: string;
}

export interface User {
  id: number;
  email: string;
  full_name: string;
  position: string | null;
  department: string | null;
  is_active: boolean;
  is_blocked: boolean;
  role: Role;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  position?: string | null;
  department?: string | null;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface AuthResponse {
  user: User;
  tokens: TokenPair;
}

export interface UpdateMeRequest {
  email?: string;
  full_name?: string;
  position?: string | null;
  department?: string | null;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}