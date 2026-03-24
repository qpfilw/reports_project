const ACCESS_TOKEN_KEY = 'rrt_access_token';
const REFRESH_TOKEN_KEY = 'rrt_refresh_token';
const ACTIVE_PROJECT_KEY = 'rrt_active_project';

export const storage = {
  getAccessToken: () => localStorage.getItem(ACCESS_TOKEN_KEY),
  setAccessToken: (value: string) => localStorage.setItem(ACCESS_TOKEN_KEY, value),
  removeAccessToken: () => localStorage.removeItem(ACCESS_TOKEN_KEY),

  getRefreshToken: () => localStorage.getItem(REFRESH_TOKEN_KEY),
  setRefreshToken: (value: string) => localStorage.setItem(REFRESH_TOKEN_KEY, value),
  removeRefreshToken: () => localStorage.removeItem(REFRESH_TOKEN_KEY),

  getActiveProject: () => localStorage.getItem(ACTIVE_PROJECT_KEY),
  setActiveProject: (value: string) => localStorage.setItem(ACTIVE_PROJECT_KEY, value),
  removeActiveProject: () => localStorage.removeItem(ACTIVE_PROJECT_KEY),

  clearSession: () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(ACTIVE_PROJECT_KEY);
  },
};