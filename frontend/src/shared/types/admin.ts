import type { User, RoleCode } from './auth';

export const APPROVABLE_ROLE_CODES: RoleCode[] = ['viewer', 'operator', 'manager'];

export interface AdminOverview {
  total_users: number;
  active_users: number;
  blocked_users: number;
  pending_users: number;
  total_projects: number;
  archived_projects: number;
  total_reports: number;
  total_tasks: number;
  total_failed_tasks: number;
  total_notifications: number;
  unread_notifications: number;
  total_audit_logs: number;
  pending_project_access_requests: number;
}

export interface AdminUserListItem {
  id: number;
  email: string;
  full_name: string;
  position: string | null;
  department: string | null;
  is_active: boolean;
  is_blocked: boolean;
  last_login_at: string | null;
  role_id: number;
  created_at: string;
  updated_at: string;
}

export interface AdminPendingUser extends User {}

export type ProjectAccessStatus = 'requested' | 'approved' | 'rejected';
export type ProjectMemberRole = 'owner' | 'manager' | 'editor' | 'viewer';

export interface AdminProjectAccessRequest {
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
  project: {
    id: number;
    name: string;
    code: string;
    description: string | null;
    owner_id: number;
    is_archived: boolean;
    created_at: string;
    updated_at: string;
  };
  user: {
    id: number;
    email: string;
    full_name: string;
    position: string | null;
    department: string | null;
    is_active: boolean;
  };
  creator: {
    id: number;
    email: string;
    full_name: string;
    position: string | null;
    department: string | null;
    is_active: boolean;
  } | null;
  reviewer: {
    id: number;
    email: string;
    full_name: string;
    position: string | null;
    department: string | null;
    is_active: boolean;
  } | null;
}