import { createContext, useContext, useEffect, useMemo, useState, type PropsWithChildren } from 'react';
import { USER_SETTINGS_KEYS, type ThemeMode } from '../../shared/lib/userSettings';

interface ThemeContextValue {
  themeMode: ThemeMode;
  setThemeMode: (theme: ThemeMode) => void;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

export function applyThemeMode(theme: ThemeMode) {
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;
}

function readStoredThemeMode(): ThemeMode {
  if (typeof window === 'undefined') {
    return 'light';
  }

  const stored = window.localStorage.getItem(USER_SETTINGS_KEYS.themeMode);
  return stored === 'dark' ? 'dark' : 'light';
}

export function ThemeProvider({ children }: PropsWithChildren) {
  const [themeMode, setThemeModeState] = useState<ThemeMode>(() => readStoredThemeMode());

  const setThemeMode = (theme: ThemeMode) => {
    setThemeModeState(theme);

    if (typeof window !== 'undefined') {
      window.localStorage.setItem(USER_SETTINGS_KEYS.themeMode, theme);
    }

    applyThemeMode(theme);
  };

  useEffect(() => {
    applyThemeMode(themeMode);
  }, [themeMode]);

  useEffect(() => {
    const handleStorage = (event: StorageEvent) => {
      if (event.key !== USER_SETTINGS_KEYS.themeMode) {
        return;
      }

      setThemeModeState(event.newValue === 'dark' ? 'dark' : 'light');
    };

    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  const value = useMemo<ThemeContextValue>(() => ({
    themeMode,
    setThemeMode,
  }), [themeMode]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useThemeMode() {
  const context = useContext(ThemeContext);

  if (!context) {
    throw new Error('useThemeMode must be used within ThemeProvider');
  }

  return context;
}
