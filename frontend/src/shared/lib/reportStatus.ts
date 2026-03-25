export interface ReportStatusOption {
  value: string;
  label: string;
}

const REPORT_STATUS_LABELS: Record<string, string> = {
  draft: 'Черновик',
  uploaded: 'Загружен',
  processing: 'В обработке',
  processed: 'Обработан',
  failed: 'Ошибка',
  on_review: 'На рассмотрении',
  on_approval: 'На утверждении',
  approved: 'Утверждён',
  rejected: 'Отклонён',
  rework: 'На доработке',
  archived: 'Архив',
};

export const reportStatusOptions: ReportStatusOption[] = [
  { value: 'all', label: 'Все статусы' },
  { value: 'draft', label: 'Черновик' },
  { value: 'uploaded', label: 'Загружен' },
  { value: 'processing', label: 'В обработке' },
  { value: 'processed', label: 'Обработан' },
  { value: 'failed', label: 'Ошибка' },
  { value: 'on_review', label: 'На рассмотрении' },
  { value: 'on_approval', label: 'На утверждении' },
  { value: 'approved', label: 'Утверждён' },
  { value: 'rejected', label: 'Отклонён' },
  { value: 'rework', label: 'На доработке' },
  { value: 'archived', label: 'Архив' },
];

export function getReportStatusLabel(status: string) {
  return REPORT_STATUS_LABELS[status] ?? status;
}

export function getReportStatusClassName(status: string) {
  switch (status) {
    case 'draft':
    case 'uploaded':
      return 'status-badge status-badge-neutral';

    case 'processing':
    case 'processed':
      return 'status-badge status-badge-info';

    case 'on_review':
    case 'on_approval':
      return 'status-badge status-badge-pending';

    case 'approved':
      return 'status-badge status-badge-success';

    case 'failed':
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