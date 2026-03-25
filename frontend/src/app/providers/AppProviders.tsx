import type { PropsWithChildren } from 'react';
import { AuthProvider } from '../../features/auth/AuthProvider';
import { ProjectProvider } from '../../features/projects/ProjectContext';

export function AppProviders({ children }: PropsWithChildren) {
  return (
    <AuthProvider>
      <ProjectProvider>{children}</ProjectProvider>
    </AuthProvider>
  );
}