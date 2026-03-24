export type ReportStatus =
  | 'draft'
  | 'on_approval'
  | 'approved'
  | 'rejected'
  | 'rework'
  | 'archived'
  | 'processed';

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