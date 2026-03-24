export type ProcessingStatus =
  | 'queued'
  | 'running'
  | 'success'
  | 'failed'
  | 'retry'
  | 'cancelled';

export interface ProcessingTask {
  id: number;
  report_id: number;
  report_upload_id: number;
  ml_template_id: number | null;
  created_by: number | null;
  celery_task_id: string | null;
  status: ProcessingStatus;
  priority: number;
  progress: number;
  params_json: Record<string, unknown>;
  quality_score: number | null;
  warning_count: number;
  error_count: number;
  retry_count: number;
  error_summary: string | null;
  queued_at: string;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
}

export interface ProcessingLog {
  id: number;
  processing_task_id: number;
  level: string;
  stage: string;
  message: string;
  context_json: Record<string, unknown>;
  created_at: string;
}

export interface TaskError {
  id: number;
  processing_task_id: number;
  error_code: string;
  error_type: string;
  field_path: string | null;
  row_number: number | null;
  source_value: string | null;
  details: string | null;
  is_critical: boolean;
  created_at: string;
}

export interface ProcessingTaskDetail extends ProcessingTask {
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
  };
  report_upload: {
    id: number;
    report_id: number;
    project_id: number;
    report_type_id: number;
    uploaded_by: number;
    original_filename: string;
    upload_version: number;
    is_latest: boolean;
    uploaded_at: string;
  };
  ml_template: {
    id: number;
    code: string;
    name: string;
    template_type: string;
    version: string;
    is_default: boolean;
    is_active: boolean;
    target_report_type_id: number | null;
  } | null;
  creator: {
    id: number;
    email: string;
    full_name: string;
  } | null;
  logs: ProcessingLog[];
  errors: TaskError[];
}

export interface TaskProgressResponse {
  task_id: number;
  status: ProcessingStatus;
  progress: number;
  warning_count: number;
  error_count: number;
  started_at: string | null;
  finished_at: string | null;
  error_summary: string | null;
}