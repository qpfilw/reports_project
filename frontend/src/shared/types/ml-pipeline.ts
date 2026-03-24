export interface TemplatePrediction {
  template_id: number | null;
  template_code: string | null;
  confidence: number;
}

export interface TemplatePredictionResult {
  best_match: TemplatePrediction | null;
  candidates: TemplatePrediction[];
}

export interface ColumnMatchSuggestion {
  source_column: string;
  target_field: string;
  confidence: number;
  rule: string | null;
}

export interface AnomalyItem {
  row_number: number | null;
  field_path: string | null;
  anomaly_type: string;
  severity: string;
  message: string;
  source_value: string | null;
  confidence: number | null;
}

export interface MlPipelineResult {
  selected_template: {
    id: number;
    code: string;
    name: string;
    template_type: string;
    version: string;
    is_default: boolean;
    is_active: boolean;
    target_report_type_id: number | null;
  } | null;
  template_prediction: TemplatePredictionResult | null;
  column_matches: ColumnMatchSuggestion[];
  anomalies: AnomalyItem[];
  quality_score: number | null;
  mapping_confirmation_required: boolean;
  diagnostics: Record<string, unknown>;
}