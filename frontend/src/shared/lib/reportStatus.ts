export interface ReportStatusOption {
  value: string;
  label: string;
}

const REPORT_STATUS_LABELS: Record<string, string> = {
  draft: 'Черновик',
  on_approval: 'На утверждении',
  approved: 'Утвержден',
  rejected: 'Отклонен',
  rework: 'На доработке',
  archived: 'Архив',
  processed: 'Обработан',
};

export const reportStatusOptions: ReportStatusOption[] = [
  { value: 'all', label: 'Все статусы' },
  { value: 'draft', label: 'Черновик' },
  { value: 'on_approval', label: 'На утверждении' },
  { value: 'approved', label: 'Утвержден' },
  { value: 'rejected', label: 'Отклонен' },
  { value: 'rework', label: 'На доработке' },
  { value: 'archived', label: 'Архив' },
  { value: 'processed', label: 'Обработан' },
];

export function getReportStatusLabel(status: string) {
  return REPORT_STATUS_LABELS[status] ?? status;
}

export function getReportStatusClassName(status: string) {
  switch (status) {
    case 'draft':
      return 'status-badge status-badge-neutral';
    case 'on_approval':
      return 'status-badge status-badge-pending';
    case 'approved':
      return 'status-badge status-badge-success';
    case 'processed':
      return 'status-badge status-badge-info';
    case 'rejected':
      return 'status-badge status-badge-danger';
    case 'rework':
      return 'status-badge status-badge-warning';
    case 'archived':
      return 'status-badge status-badge-muted';
    default:
      return 'status-badge status-badge-neutral';
  }
}