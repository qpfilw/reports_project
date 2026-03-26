import type { AuditAction, AuditEntityType } from '../types/audit';

export function getAuditActionLabel(action: AuditAction) {
  switch (action) {
    case 'create':
      return 'Создание';
    case 'update':
      return 'Изменение';
    case 'delete':
      return 'Удаление';
    case 'submit':
      return 'Отправка';
    case 'approve':
      return 'Утверждение';
    case 'reject':
      return 'Отклонение';
    case 'process_start':
      return 'Старт обработки';
    case 'process_retry':
      return 'Повтор обработки';
    case 'process_finish':
      return 'Завершение обработки';
    case 'login':
      return 'Вход';
    case 'logout':
      return 'Выход';
    case 'export':
      return 'Экспорт';
    default:
      return action;
  }
}

export function getAuditEntityLabel(entityType: AuditEntityType) {
  switch (entityType) {
    case 'user':
      return 'Пользователь';
    case 'project':
      return 'Проект';
    case 'report':
      return 'Отчёт';
    case 'report_upload':
      return 'Загрузка';
    case 'template':
      return 'ML-шаблон';
    case 'task':
      return 'Задача';
    case 'dashboard':
      return 'Дашборд';
    default:
      return entityType;
  }
}
