export interface ReportType {
  id: number;
  code: string;
  name: string;
  description: string | null;
  schema_version: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateReportTypePayload {
  code: string;
  name: string;
  description: string | null;
  schema_version: string;
  is_active: boolean;
}
