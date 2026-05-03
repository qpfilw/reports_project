import type { TemplateType } from '../types/template';

const TEMPLATE_TYPE_LABELS: Record<TemplateType, string> = {
  classification: 'Классификация',
  extraction: 'Извлечение данных',
  normalization: 'Нормализация',
  hybrid: 'Гибридный режим',
};

const TEMPLATE_TYPE_DESCRIPTIONS: Record<TemplateType, string> = {
  classification: 'Подходит для выбора класса документа, маршрута обработки или категории отчётности.',
  extraction: 'Используется, когда нужно извлечь поля, реквизиты и значения из исходной таблицы или файла.',
  normalization: 'Приводит строки и столбцы к целевой структуре отчёта и единому формату данных.',
  hybrid: 'Комбинирует определение шаблона, извлечение данных и нормализацию в одном сценарии.',
};

const TEMPLATE_PRESET_CONFIGS: Record<TemplateType, Record<string, unknown>> = {
  classification: {
    strategy: 'classification',
    confidence_threshold: 0.8,
    use_title_features: true,
    use_header_features: true,
  },
  extraction: {
    strategy: 'extraction',
    extract_headers: true,
    extract_totals: true,
    allow_sparse_rows: false,
  },
  normalization: {
    strategy: 'normalization',
    normalize_headers: true,
    trim_values: true,
    drop_empty_rows: true,
  },
  hybrid: {
    strategy: 'hybrid',
    classification_first: true,
    normalize_after_mapping: true,
    confidence_threshold: 0.75,
  },
};

const TEMPLATE_PRESET_METRICS: Record<TemplateType, Record<string, unknown>> = {
  classification: {
    primary_metric: 'accuracy',
    target_threshold: 0.9,
    track_confidence: true,
  },
  extraction: {
    primary_metric: 'precision_recall',
    target_precision: 0.9,
    target_recall: 0.85,
  },
  normalization: {
    primary_metric: 'row_mapping_quality',
    target_quality_score: 0.9,
    validate_required_fields: true,
  },
  hybrid: {
    primary_metric: 'combined_quality',
    target_quality_score: 0.88,
    track_stage_scores: true,
  },
};

export function getTemplateTypeLabel(value: TemplateType) {
  return TEMPLATE_TYPE_LABELS[value] ?? value;
}

export function getTemplateTypeDescription(value: TemplateType) {
  return TEMPLATE_TYPE_DESCRIPTIONS[value] ?? 'Параметры этого типа можно настроить вручную.';
}

export function buildTemplatePreset(value: TemplateType) {
  return {
    config_json: TEMPLATE_PRESET_CONFIGS[value],
    metrics_json: TEMPLATE_PRESET_METRICS[value],
  };
}
