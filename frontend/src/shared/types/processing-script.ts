export interface ProcessingScript {
  id: number;
  code: string;
  name: string;
  description: string | null;
  target_report_type_id: number | null;
  script_code: string;
  version: string;
  is_default: boolean;
  is_active: boolean;
  validation_json: Record<string, unknown>;
  created_by: number | null;
  created_at: string;
  updated_at: string;
}

export interface ProcessingScriptDetail extends ProcessingScript {
  creator: {
    id: number;
    email: string;
    full_name: string;
  } | null;
}

export interface CreateProcessingScriptPayload {
  code: string;
  name: string;
  description?: string | null;
  target_report_type_id?: number | null;
  script_code: string;
  version?: string;
  is_default?: boolean;
  is_active?: boolean;
  validation_json?: Record<string, unknown>;
  created_by?: number | null;
}

export interface UpdateProcessingScriptPayload {
  code?: string;
  name?: string;
  description?: string | null;
  target_report_type_id?: number | null;
  script_code?: string;
  version?: string;
  is_default?: boolean;
  is_active?: boolean;
  validation_json?: Record<string, unknown> | null;
  created_by?: number | null;
}

export interface ValidateProcessingScriptPayload {
  script_code: string;
  sample_context?: Record<string, unknown> | null;
  sample_row?: Record<string, unknown> | null;
}

export interface ValidateProcessingScriptResult {
  is_valid: boolean;
  message: string;
  output_row: Record<string, unknown> | null;
  added_columns: string[];
  error: string | null;
}
