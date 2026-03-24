export type ExportFormat = 'csv' | 'xlsx' | 'pdf';

export interface ExportArtifact {
  id: number;
  processing_task_id: number | null;
  report_id: number | null;
  dashboard_id: number | null;
  format: ExportFormat;
  storage_path: string;
  file_size: number;
  checksum_sha256: string | null;
  created_by: number | null;
  created_at: string;
}

export interface ExportArtifactDetail extends ExportArtifact {
  processing_task: {
    id: number;
    report_id: number;
    report_upload_id: number;
    status: string;
    progress: number;
    priority: number;
    created_at: string;
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
}