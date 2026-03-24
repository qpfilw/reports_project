export type NotificationType =
  | 'report_status_changed'
  | 'report_submitted'
  | 'report_approved'
  | 'report_rejected'
  | 'task_failed'
  | 'task_completed'
  | 'system_alert';

export interface NotificationItem {
  id: number;
  user_id: number;
  project_id: number | null;
  report_id: number | null;
  processing_task_id: number | null;
  type: NotificationType;
  title: string;
  message: string;
  payload_json: Record<string, unknown>;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
}

export interface NotificationDetail extends NotificationItem {
  user: {
    id: number;
    email: string;
    full_name: string;
  };
  project: {
    id: number;
    name: string;
    code: string;
    description: string | null;
    owner_id: number;
    is_archived: boolean;
    created_at: string;
    updated_at: string;
  } | null;
  report: {
    id: number;
    title: string;
    project_id: number;
    report_type_id: number;
    status: string;
    report_period_start: string;
    report_period_end: string;
    version: number;
    is_archived: boolean;
  } | null;
  processing_task: {
    id: number;
    report_id: number;
    report_upload_id: number;
    ml_template_id: number | null;
    status: string;
    progress: number;
    priority: number;
    created_at: string;
  } | null;
}

export interface NotificationUpdatePayload {
  title?: string;
  message?: string;
  payload_json?: Record<string, unknown>;
  is_read?: boolean;
  read_at?: string | null;
}