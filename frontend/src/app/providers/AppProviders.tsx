import type { PropsWithChildren } from 'react';
import { AuthProvider } from '../../features/auth/AuthProvider';
import { ProjectProvider } from '../../features/projects/ProjectContext';
import { ThemeProvider } from './ThemeProvider';

export function AppProviders({ children }: PropsWithChildren) {
  return (
    <ThemeProvider>
      <AuthProvider>
        <ProjectProvider>{children}</ProjectProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}