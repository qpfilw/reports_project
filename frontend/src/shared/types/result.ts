export interface NormalizedDataset {
  id: number;
  processing_task_id: number;
  report_id: number;
  rows_count: number;
  schema_data: Record<string, unknown>;
  summary_json: Record<string, unknown>;
  preview_json: Array<Record<string, unknown>>;
  data_location: string;
  created_at: string;
}

export interface NormalizedDatasetDetail extends NormalizedDataset {
  processing_task: {
    id: number;
    report_id: number;
    report_upload_id: number;
    ml_template_id: number | null;
    status: string;
    progress: number;
    priority: number;
    created_at: string;
  };
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
}