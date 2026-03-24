import type { PropsWithChildren } from 'react';
import { Navigate } from 'react-router-dom';
import type { RoleCode } from '../../shared/types/auth';
import { useAuth } from './AuthProvider';

interface RoleGuardProps extends PropsWithChildren {
  roles: RoleCode[];
}

export function RoleGuard({ roles, children }: RoleGuardProps) {
  const { user } = useAuth();

  if (!user || !roles.includes(user.role.code)) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}