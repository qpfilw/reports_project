import type { ProcessingStatus } from '../types/processing';

const PROCESSING_STATUS_LABELS: Record<ProcessingStatus, string> = {
  queued: 'В очереди',
  running: 'Выполняется',
  success: 'Успешно',
  failed: 'Ошибка',
  retry: 'Повторная попытка',
  cancelled: 'Отменена',
};

const PROCESSING_STAGE_LABELS: Record<string, string> = {
  init: 'Инициализация',
  bootstrap: 'Подготовка',
  queue: 'Постановка в очередь',
  start: 'Запуск',
  read: 'Чтение файла',
  dispatch: 'Передача в обработку',
  ml_prediction: 'ML-анализ',
  file_validation: 'Проверка файла',
  structure_validation: 'Проверка структуры',
  parsing: 'Разбор файла',
  parsing_rows: 'Разбор строк',
  parse_source: 'Чтение исходных данных',
  template_selection: 'Выбор шаблона',
  template_detection: 'Определение шаблона',
  mapping: 'Сопоставление полей',
  normalization: 'Нормализация',
  normalization_rows: 'Нормализация строк',
  postprocessing: 'Постобработка',
  validation: 'Контрольная проверка',
  persist_result: 'Сохранение результата',
  export: 'Экспорт',
  notification: 'Уведомление',
  retry: 'Повторная обработка',
  cancel: 'Отмена задачи',
  complete: 'Завершение обработки',
  failed: 'Ошибка обработки',
  finish: 'Завершение',
};

const PROCESSING_LEVEL_LABELS: Record<string, string> = {
  debug: 'Отладка',
  info: 'Информация',
  warning: 'Предупреждение',
  error: 'Ошибка',
  critical: 'Критическая ошибка',
};

const PROCESSING_ERROR_TYPE_LABELS: Record<string, string> = {
  validation_error: 'Ошибка валидации',
  parsing_error: 'Ошибка разбора файла',
  mapping_error: 'Ошибка сопоставления полей',
  normalization_error: 'Ошибка нормализации',
  template_selection_error: 'Ошибка выбора шаблона',
  template_detection_error: 'Ошибка определения шаблона',
  export_error: 'Ошибка экспорта',
  system_error: 'Системная ошибка',
  ml_error: 'Ошибка ML-контура',
  business_error: 'Бизнес-ошибка',
};

const PROCESSING_MESSAGE_LABELS: Record<string, string> = {
  'Задача отправлена в Celery worker.': 'Задача передана обработчику Celery.',
};

function humanizeCode(value: string) {
  return value
    .replace(/[._-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/^./, (char) => char.toUpperCase());
}

export function getProcessingStatusLabel(status: ProcessingStatus) {
  return PROCESSING_STATUS_LABELS[status] ?? status;
}

export function getProcessingStageLabel(stage?: string | null) {
  if (!stage) return '-';
  return PROCESSING_STAGE_LABELS[stage] ?? humanizeCode(stage);
}

export function getProcessingLevelLabel(level?: string | null) {
  if (!level) return '-';
  return PROCESSING_LEVEL_LABELS[level.toLowerCase()] ?? humanizeCode(level);
}

export function getProcessingErrorTypeLabel(errorType?: string | null) {
  if (!errorType) return '-';
  return PROCESSING_ERROR_TYPE_LABELS[errorType] ?? humanizeCode(errorType);
}

export function getProcessingMessageLabel(message?: string | null) {
  if (!message) return '-';
  return PROCESSING_MESSAGE_LABELS[message] ?? message;
}