export type ProjectMemberRole = 'owner' | 'manager' | 'editor' | 'viewer';
export type ProjectAccessStatus = 'requested' | 'approved' | 'rejected';

export interface ProjectUserSummary {
  id: number;
  email: string;
  full_name: string;
  position: string | null;
  department: string | null;
  is_active: boolean;
}

export type ProjectAvailableUser = ProjectUserSummary;

export interface Project {
  id: number;
  name: string;
  code: string;
  description: string | null;
  owner_id: number;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProjectDetail extends Project {
  owner: ProjectUserSummary | null;
}

export interface ProjectMember {
  id: number;
  project_id: number;
  user_id: number;
  member_role: ProjectMemberRole;
  access_status: ProjectAccessStatus;
  added_by: number | null;
  added_at: string;
  requested_at: string;
  request_note: string | null;
  reviewed_by: number | null;
  reviewed_at: string | null;
  review_note: string | null;
  user: ProjectUserSummary;
  creator?: ProjectUserSummary | null;
  reviewer?: ProjectUserSummary | null;
}

export interface CreateProjectPayload {
  name: string;
  code: string;
  description?: string | null;
  owner_id: number;
}

export interface AddProjectMemberPayload {
  user_id: number;
  member_role: ProjectMemberRole;
  request_note?: string | null;
}

export interface UpdateProjectMemberPayload {
  member_role?: ProjectMemberRole;
  review_note?: string | null;
}

export interface RequestProjectAccessPayload {
  member_role: ProjectMemberRole;
  request_note?: string | null;
}

export const PROJECT_MEMBER_ROLE_OPTIONS: Array<{
  value: ProjectMemberRole;
  label: string;
}> = [
  { value: 'viewer', label: 'Наблюдатель' },
  { value: 'editor', label: 'Редактор' },
  { value: 'manager', label: 'Менеджер' },
];

export function getProjectRoleLabel(role: ProjectMemberRole) {
  switch (role) {
    case 'owner':
      return 'Владелец';
    case 'manager':
      return 'Менеджер';
    case 'editor':
      return 'Редактор';
    case 'viewer':
      return 'Наблюдатель';
    default:
      return role;
  }
}

export function getProjectAccessStatusLabel(status: ProjectAccessStatus) {
  switch (status) {
    case 'requested':
      return 'Запрошен';
    case 'approved':
      return 'Одобрен';
    case 'rejected':
      return 'Отклонен';
    default:
      return status;
  }
}