export interface ReportUpload {
  id: number;
  report_id: number;
  project_id: number;
  report_type_id: number;
  uploaded_by: number;
  original_filename: string;
  storage_path: string;
  content_type: string | null;
  file_size: number;
  checksum_sha256: string | null;
  is_latest: boolean;
  upload_version: number;
  uploaded_at: string;
  comment: string | null;
}

export interface ReportUploadDetail extends ReportUpload {
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
  report_type: {
    id: number;
    code: string;
    name: string;
    schema_version: string;
    is_active: boolean;
  };
  uploader: {
    id: number;
    email: string;
    full_name: string;
  };
}