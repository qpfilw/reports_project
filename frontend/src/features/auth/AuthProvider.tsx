import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from 'react';
import { authApi } from '../../shared/api/auth';
import { storage } from '../../shared/lib/storage';
import type {
  AuthResponse,
  LoginRequest,
  RegisterRequest,
  User,
} from '../../shared/types/auth';

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (payload: LoginRequest) => Promise<void>;
  register: (payload: RegisterRequest) => Promise<void>;
  logout: () => void;
  reloadMe: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function applySession(data: AuthResponse, setUser: (user: User | null) => void) {
  storage.setAccessToken(data.tokens.access_token);
  storage.setRefreshToken(data.tokens.refresh_token);
  setUser(data.user);
}

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const logout = useCallback(() => {
    storage.clearSession();
    setUser(null);
  }, []);

  const reloadMe = useCallback(async () => {
    const token = storage.getAccessToken();

    if (!token) {
      setUser(null);
      return;
    }

    try {
      const me = await authApi.me();
      setUser(me);
    } catch {
      logout();
    }
  }, [logout]);

  const login = useCallback(async (payload: LoginRequest) => {
    const response = await authApi.login(payload);
    applySession(response, setUser);
  }, []);

  const register = useCallback(async (payload: RegisterRequest) => {
    const response = await authApi.register(payload);
    applySession(response, setUser);
  }, []);

  useEffect(() => {
    (async () => {
      try {
        await reloadMe();
      } finally {
        setIsLoading(false);
      }
    })();
  }, [reloadMe]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      isLoading,
      login,
      register,
      logout,
      reloadMe,
    }),
    [user, isLoading, login, register, logout, reloadMe],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider');
  }

  return context;
}