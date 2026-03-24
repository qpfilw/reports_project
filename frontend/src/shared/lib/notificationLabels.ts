import type { NotificationItem, NotificationType } from '../types/notification';

const NOTIFICATION_TYPE_LABELS: Record<NotificationType, string> = {
  report_status_changed: 'Изменение статуса отчета',
  report_submitted: 'Отчет отправлен',
  report_approved: 'Отчет утвержден',
  report_rejected: 'Отчет отклонен',
  task_failed: 'Ошибка обработки',
  task_completed: 'Обработка завершена',
  system_alert: 'Системное уведомление',
};

export function getNotificationTypeLabel(type: NotificationType) {
  return NOTIFICATION_TYPE_LABELS[type] ?? type;
}

export function getNotificationDisplayTitle(notification: NotificationItem) {
  switch (notification.type) {
    case 'task_completed':
      return 'Обработка завершена';
    case 'task_failed':
      return 'Ошибка обработки';
    case 'report_status_changed':
      return 'Статус отчета изменен';
    case 'report_submitted':
      return 'Отчет отправлен';
    case 'report_approved':
      return 'Отчет утвержден';
    case 'report_rejected':
      return 'Отчет отклонен';
    case 'system_alert':
      return 'Системное уведомление';
    default:
      return notification.title || getNotificationTypeLabel(notification.type);
  }
}

export function getNotificationTypeClassName(type: NotificationType) {
  switch (type) {
    case 'task_completed':
    case 'report_approved':
      return 'notification-type-badge notification-type-success';

    case 'task_failed':
    case 'report_rejected':
      return 'notification-type-badge notification-type-danger';

    case 'report_status_changed':
    case 'report_submitted':
      return 'notification-type-badge notification-type-info';

    case 'system_alert':
    default:
      return 'notification-type-badge notification-type-neutral';
  }
}

export function getNotificationTargetUrl(notification: NotificationItem) {
  if (notification.report_id && notification.type === 'task_completed') {
    return `/reports/${notification.report_id}/result`;
  }

  if (notification.report_id && notification.type === 'task_failed') {
    return notification.processing_task_id
      ? `/tasks/${notification.processing_task_id}`
      : `/reports/${notification.report_id}/result`;
  }

  if (notification.processing_task_id) {
    return `/tasks/${notification.processing_task_id}`;
  }

  if (notification.report_id) {
    return `/reports/${notification.report_id}/result`;
  }

  if (notification.project_id) {
    return `/projects/${notification.project_id}`;
  }

  return '/notifications';
}

export function getNotificationCompactLabel(type: NotificationType) {
  switch (type) {
    case 'task_completed':
      return 'Завершена';
    case 'task_failed':
      return 'Ошибка';
    case 'report_status_changed':
      return 'Статус изменен';
    case 'report_submitted':
      return 'Отправлен';
    case 'report_approved':
      return 'Утвержден';
    case 'report_rejected':
      return 'Отклонен';
    case 'system_alert':
      return 'Системное';
    default:
      return getNotificationTypeLabel(type);
  }
}