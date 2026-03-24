export type TemplateType =
  | 'classification'
  | 'extraction'
  | 'normalization'
  | 'hybrid';

export interface MlTemplate {
  id: number;
  code: string;
  name: string;
  description: string | null;
  template_type: TemplateType;
  target_report_type_id: number | null;
  department: string | null;
  config_json: Record<string, unknown>;
  metrics_json: Record<string, unknown>;
  model_path: string | null;
  version: string;
  is_default: boolean;
  is_active: boolean;
  created_by: number | null;
  created_at: string;
  updated_at: string;
}

export interface MlTemplateDetail extends MlTemplate {
  creator: {
    id: number;
    email: string;
    full_name: string;
  } | null;
}

export interface CreateMlTemplatePayload {
  code: string;
  name: string;
  description?: string | null;
  template_type: TemplateType;
  target_report_type_id?: number | null;
  department?: string | null;
  config_json?: Record<string, unknown>;
  metrics_json?: Record<string, unknown>;
  model_path?: string | null;
  version?: string;
  is_default?: boolean;
  is_active?: boolean;
  created_by?: number | null;
}

export interface UpdateMlTemplatePayload {
  code?: string;
  name?: string;
  description?: string | null;
  template_type?: TemplateType;
  target_report_type_id?: number | null;
  department?: string | null;
  config_json?: Record<string, unknown> | null;
  metrics_json?: Record<string, unknown> | null;
  model_path?: string | null;
  version?: string;
  is_default?: boolean;
  is_active?: boolean;
}

export const TEMPLATE_TYPE_OPTIONS: Array<{ value: TemplateType; label: string }> = [
  { value: 'classification', label: 'Классификация' },
  { value: 'extraction', label: 'Извлечение' },
  { value: 'normalization', label: 'Нормализация' },
  { value: 'hybrid', label: 'Гибридный' },
];