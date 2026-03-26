export type AuditAction =
  | 'create'
  | 'update'
  | 'delete'
  | 'submit'
  | 'approve'
  | 'reject'
  | 'process_start'
  | 'process_retry'
  | 'process_finish'
  | 'login'
  | 'logout'
  | 'export';

export type AuditEntityType =
  | 'user'
  | 'project'
  | 'report'
  | 'report_upload'
  | 'template'
  | 'task'
  | 'dashboard';

export interface AuditLog {
  id: number;
  user_id: number | null;
  project_id: number | null;
  action: AuditAction;
  entity_type: AuditEntityType;
  entity_id: number | null;
  before_json: Record<string, unknown> | null;
  after_json: Record<string, unknown> | null;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
}

export interface AuditUserSummary {
  id: number;
  email: string;
  full_name: string;
  position: string | null;
  department: string | null;
  is_active: boolean;
}

export interface AuditProjectSummary {
  id: number;
  name: string;
  code: string;
  description: string | null;
  owner_id: number;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuditLogDetail extends AuditLog {
  user: AuditUserSummary | null;
  project: AuditProjectSummary | null;
}
