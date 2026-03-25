export type DashboardType = 'personal' | 'department' | 'executive' | 'system';
export type DashboardSourceType = 'normalized_dataset' | 'report' | 'project_aggregate';

export type DashboardWidgetKey =
  | 'overviewMetrics'
  | 'statusDistribution'
  | 'periodDynamics'
  | 'rowsByReport'
  | 'summaryMetrics'
  | 'latestResults';

export interface DashboardMetricItem {
  key: string;
  label: string;
  value: number | string | null;
  unit?: string | null;
}

export interface AnalyticsOverview {
  total_reports: number;
  total_uploads: number;
  total_tasks: number;
  successful_tasks: number;
  failed_tasks: number;
  total_exports: number;
  average_quality_score: number | null;
  metrics: DashboardMetricItem[];
}

export interface DashboardOwnerSummary {
  id: number;
  email: string;
  full_name: string;
  position?: string | null;
  department?: string | null;
  is_active?: boolean;
}

export interface DashboardReportSummary {
  id: number;
  title: string;
  project_id: number;
  report_type_id: number;
  status: string;
  report_period_start: string;
  report_period_end: string;
  version: number;
  is_archived: boolean;
}

export interface DashboardNormalizedDatasetSummary {
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

export interface Dashboard {
  id: number;
  project_id: number;
  report_id: number | null;
  normalized_dataset_id: number | null;
  owner_id: number;
  name: string;
  description: string | null;
  dashboard_type: DashboardType;
  source_type: DashboardSourceType;
  config_json: Record<string, unknown>;
  filters_json: Record<string, unknown>;
  layout_json: Record<string, unknown>;
  metrics_json: Record<string, unknown>;
  is_shared: boolean;
  is_default: boolean;
  last_generated_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface DashboardDetail extends Dashboard {
  owner: DashboardOwnerSummary;
  report: DashboardReportSummary | null;
  normalized_dataset: DashboardNormalizedDatasetSummary | null;
}

export interface CreateDashboardPayload {
  project_id: number;
  report_id?: number | null;
  normalized_dataset_id?: number | null;
  owner_id: number;
  name: string;
  description?: string | null;
  dashboard_type: DashboardType;
  source_type: DashboardSourceType;
  config_json?: Record<string, unknown>;
  filters_json?: Record<string, unknown>;
  layout_json?: Record<string, unknown>;
  metrics_json?: Record<string, unknown>;
  is_shared?: boolean;
  is_default?: boolean;
}

export interface UpdateDashboardPayload {
  report_id?: number | null;
  normalized_dataset_id?: number | null;
  name?: string;
  description?: string | null;
  dashboard_type?: DashboardType | null;
  source_type?: DashboardSourceType | null;
  config_json?: Record<string, unknown> | null;
  filters_json?: Record<string, unknown> | null;
  layout_json?: Record<string, unknown> | null;
  metrics_json?: Record<string, unknown> | null;
  is_shared?: boolean | null;
  is_default?: boolean | null;
  last_generated_at?: string | null;
}

export const DASHBOARD_TYPE_OPTIONS: Array<{ value: DashboardType; label: string }> = [
  { value: 'personal', label: 'Персональный' },
  { value: 'department', label: 'Подразделение' },
  { value: 'executive', label: 'Руководство' },
  { value: 'system', label: 'Системный' },
];

export const DASHBOARD_SOURCE_TYPE_OPTIONS: Array<{
  value: DashboardSourceType;
  label: string;
}> = [
  { value: 'project_aggregate', label: 'Сводный по проекту' },
  { value: 'report', label: 'По отчёту' },
  { value: 'normalized_dataset', label: 'По набору данных' },
];

export const DASHBOARD_WIDGET_OPTIONS: Array<{
  value: DashboardWidgetKey;
  label: string;
}> = [
  { value: 'overviewMetrics', label: 'Ключевые показатели' },
  { value: 'statusDistribution', label: 'Распределение по статусам' },
  { value: 'periodDynamics', label: 'Динамика по периодам' },
  { value: 'rowsByReport', label: 'Строки по отчётам' },
  { value: 'summaryMetrics', label: 'Показатели из summary_json' },
  { value: 'latestResults', label: 'Последние результаты' },
];

export function getDashboardTypeLabel(type: DashboardType) {
  switch (type) {
    case 'personal':
      return 'Персональный';
    case 'department':
      return 'Подразделение';
    case 'executive':
      return 'Руководство';
    case 'system':
      return 'Системный';
    default:
      return type;
  }
}

export function getDashboardSourceTypeLabel(type: DashboardSourceType) {
  switch (type) {
    case 'project_aggregate':
      return 'Сводный по проекту';
    case 'report':
      return 'По отчёту';
    case 'normalized_dataset':
      return 'По набору данных';
    default:
      return type;
  }
}