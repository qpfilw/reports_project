import type { RoleCode } from '../types/auth';
import type { ProjectAccessStatus } from '../types/admin';

const ROLE_LABELS: Record<RoleCode, string> = {
  pending: 'Ожидает одобрения',
  admin: 'Администратор',
  manager: 'Менеджер',
  operator: 'Оператор',
  viewer: 'Наблюдатель',
};

const ACCESS_STATUS_LABELS: Record<ProjectAccessStatus, string> = {
  requested: 'Запрошен',
  approved: 'Одобрен',
  rejected: 'Отклонен',
};

export function getRoleLabel(roleCode: RoleCode) {
  return ROLE_LABELS[roleCode] ?? roleCode;
}

export function getAccessStatusLabel(status: ProjectAccessStatus) {
  return ACCESS_STATUS_LABELS[status] ?? status;
}