export type ReportStatus =
  | 'draft'
  | 'uploaded'
  | 'processing'
  | 'processed'
  | 'failed'
  | 'on_review'
  | 'on_approval'
  | 'approved'
  | 'rejected'
  | 'rework'
  | 'archived';

export interface ReportUserSummary {
  id: number;
  email: string;
  full_name: string;
  position: string | null;
  department: string | null;
  is_active: boolean;
}

export interface ReportTypeSummary {
  id: number;
  code: string;
  name: string;
  schema_version: string;
  is_active: boolean;
}

export interface ReportMlTemplateSummary {
  id: number;
  code: string;
  name: string;
  template_type: 'classification' | 'extraction' | 'normalization' | 'hybrid';
  version: string;
  is_active: boolean;
}

export interface Report {
  id: number;
  project_id: number;
  report_type_id: number;
  title: string;
  description: string | null;
  report_period_start: string;
  report_period_end: string;
  status: ReportStatus;
  creator_id: number;
  current_assignee_id: number | null;
  approver_id: number | null;
  ml_template_id: number | null;
  version: number;
  submitted_at: string | null;
  approved_at: string | null;
  rejected_at: string | null;
  last_comment: string | null;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface ReportDetail extends Report {
  report_type: ReportTypeSummary;
  creator: ReportUserSummary;
  current_assignee: ReportUserSummary | null;
  approver: ReportUserSummary | null;
  ml_template: ReportMlTemplateSummary | null;
}

export interface ReportWorkflowPayload {
  last_comment?: string | null;
  current_assignee_id?: number | null;
  approver_id?: number | null;
}

export interface UpdateReportPayload {
  report_type_id?: number | null;
  title?: string;
  description?: string | null;
  report_period_start?: string | null;
  report_period_end?: string | null;
  current_assignee_id?: number | null;
  approver_id?: number | null;
  ml_template_id?: number | null;
  version?: number | null;
  last_comment?: string | null;
  is_archived?: boolean | null;
}

export interface ReportStatusUpdatePayload {
  status: ReportStatus;
  last_comment?: string | null;
  current_assignee_id?: number | null;
  approver_id?: number | null;
}