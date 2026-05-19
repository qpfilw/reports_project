import { useCallback, useEffect, useMemo, useState, type ChangeEvent, type FormEvent } from 'react';
import { Alert, Button, Col, Form, Modal, Row, Spinner, Table } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthProvider';
import { reportTypesApi } from '../../shared/api/reportTypes';
import { processingScriptsApi } from '../../shared/api/processingScripts';
import { templatesApi } from '../../shared/api/templates';
import {
  buildTemplatePreset,
  getTemplateTypeDescription,
  getTemplateTypeLabel,
} from '../../shared/lib/templateLabels';
import type { ReportType } from '../../shared/types/report-type';
import type { ProcessingScript, ValidateProcessingScriptResult } from '../../shared/types/processing-script';
import {
  TEMPLATE_TYPE_OPTIONS,
  type CreateMlTemplatePayload,
  type MlTemplate,
  type MlTemplateDetail,
  type TemplateType,
  type UpdateMlTemplatePayload,
} from '../../shared/types/template';
import { ContentCard } from '../../shared/ui/ContentCard';

type FormMode = 'create' | 'edit';

interface TemplateFormState {
  code: string;
  name: string;
  description: string;
  template_type: TemplateType;
  target_report_type_id: string;
  processing_script_id: string;
  department: string;
  config_json: string;
  metrics_json: string;
  model_path: string;
  version: string;
  is_default: boolean;
  is_active: boolean;
}

interface JsonValidationState {
  isValid: boolean;
  message: string;
}

interface ScriptFormState {
  code: string;
  name: string;
  description: string;
  target_report_type_id: string;
  script_code: string;
  version: string;
  is_default: boolean;
  is_active: boolean;
}

interface ReportTypeFormState {
  code: string;
  name: string;
  description: string;
  schema_version: string;
  is_active: boolean;
}

const INITIAL_TEMPLATE_TYPE: TemplateType = 'classification';

const DEMO_PROCESSING_SCRIPT = `from openpyxl import load_workbook


def _to_number(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _read_limits(path):
    if not path:
        return {}

    workbook = load_workbook(path, read_only=True, data_only=True)
    sheet = workbook[workbook.sheetnames[0]]
    rows = list(sheet.iter_rows(values_only=True))
    workbook.close()

    if not rows:
        return {}

    headers = [str(value).strip() if value is not None else '' for value in rows[0]]
    try:
        category_index = headers.index('Категория расходов')
        limit_index = headers.index('Лимит')
    except ValueError:
        return {}

    limits = {}
    for values in rows[1:]:
        category = values[category_index] if category_index < len(values) else None
        limit = values[limit_index] if limit_index < len(values) else 0
        if category:
            limits[str(category).strip()] = _to_number(limit)
    return limits


def process(context):
    rows = context.get('rows') or []
    files = context.get('files') or {}
    by_role = files.get('by_role') or {}
    limits_file = by_role.get('limits') or by_role.get('reference') or {}
    limits = _read_limits(limits_file.get('path'))

    processed_rows = []
    exceeded_limit_count = 0
    high_risk_count = 0

    for row in rows:
        next_row = dict(row)
        category = str(next_row.get('Категория расходов') or '').strip()
        total = _to_number(next_row.get('Итого с НДС'))
        status = str(next_row.get('Статус оплаты') or '').strip()
        limit = limits.get(category, 100000.0)
        deviation = round(total - limit, 2)
        exceeded = deviation > 0

        if exceeded and total >= 300000:
            risk = 'Высокий'
            control = 'Требует срочного контроля'
        elif exceeded or status in {'Ожидает оплаты', 'Частично оплачено'}:
            risk = 'Средний'
            control = 'Требует контроля' if status != 'Частично оплачено' else 'Требует сверки оплаты'
        else:
            risk = 'Низкий'
            control = 'Без замечаний'

        next_row['Лимит по категории'] = limit
        next_row['Отклонение от лимита'] = deviation
        next_row['Превышен лимит'] = 'Да' if exceeded else 'Нет'
        next_row['Результат контроля'] = control
        next_row['Уровень риска'] = risk
        next_row['Требуется согласование'] = 'Да' if risk in {'Средний', 'Высокий'} else 'Нет'

        exceeded_limit_count += 1 if exceeded else 0
        high_risk_count += 1 if risk == 'Высокий' else 0
        processed_rows.append(next_row)

    return {
        'rows': processed_rows,
        'summary': {
            'exceeded_limit_count': exceeded_limit_count,
            'high_risk_count': high_risk_count,
            'processed_rows': len(processed_rows),
        },
        'warnings': [],
    }
`;

const INITIAL_SCRIPT_FORM: ScriptFormState = {
  code: 'expense_control_script',
  name: 'Контроль расходных операций',
  description: 'Скрипт добавляет контрольные признаки по сумме операции и статусу оплаты.',
  target_report_type_id: '',
  script_code: DEMO_PROCESSING_SCRIPT,
  version: '1.0',
  is_default: false,
  is_active: true,
};

const INITIAL_REPORT_TYPE_FORM: ReportTypeFormState = {
  code: '',
  name: '',
  description: '',
  schema_version: '1.0',
  is_active: true,
};

function prettyJson(value: Record<string, unknown>) {
  return JSON.stringify(value ?? {}, null, 2);
}

function createInitialFormState(templateType: TemplateType = INITIAL_TEMPLATE_TYPE): TemplateFormState {
  const preset = buildTemplatePreset(templateType);

  return {
    code: '',
    name: '',
    description: '',
    template_type: templateType,
    target_report_type_id: '',
    processing_script_id: '',
    department: '',
    config_json: prettyJson(preset.config_json),
    metrics_json: prettyJson(preset.metrics_json),
    model_path: '',
    version: '1.0',
    is_default: false,
    is_active: true,
  };
}

function buildFormState(template?: MlTemplateDetail | null): TemplateFormState {
  if (!template) {
    return createInitialFormState();
  }

  return {
    code: template.code,
    name: template.name,
    description: template.description ?? '',
    template_type: template.template_type,
    target_report_type_id: template.target_report_type_id ? String(template.target_report_type_id) : '',
    processing_script_id: template.processing_script_id ? String(template.processing_script_id) : '',
    department: template.department ?? '',
    config_json: prettyJson(template.config_json),
    metrics_json: prettyJson(template.metrics_json),
    model_path: template.model_path ?? '',
    version: template.version,
    is_default: template.is_default,
    is_active: template.is_active,
  };
}

function formatDateTime(value?: string | null) {
  if (!value) return '-';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString('ru-RU');
}

function parseJsonField(value: string, fieldLabel: string) {
  try {
    return JSON.parse(value || '{}') as Record<string, unknown>;
  } catch {
    throw new Error(`Поле «${fieldLabel}» содержит некорректный JSON.`);
  }
}

function getJsonValidationState(value: string, fieldLabel: string): JsonValidationState {
  try {
    JSON.parse(value || '{}');
    return {
      isValid: true,
      message: `${fieldLabel}: корректный JSON`,
    };
  } catch {
    return {
      isValid: false,
      message: `${fieldLabel}: обнаружена ошибка в структуре JSON`,
    };
  }
}

export default function AdminTemplatesPage() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [templates, setTemplates] = useState<MlTemplate[]>([]);
  const [reportTypes, setReportTypes] = useState<ReportType[]>([]);
  const [processingScripts, setProcessingScripts] = useState<ProcessingScript[]>([]);

  const [selectedTemplate, setSelectedTemplate] = useState<MlTemplateDetail | null>(null);
  const [formState, setFormState] = useState<TemplateFormState>(createInitialFormState());

  const [search, setSearch] = useState('');
  const [reportTypeFilter, setReportTypeFilter] = useState('all');
  const [activityFilter, setActivityFilter] = useState('all');

  const [formMode, setFormMode] = useState<FormMode>('create');
  const [showFormModal, setShowFormModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);
  const [showScriptModal, setShowScriptModal] = useState(false);
  const [scriptFormMode, setScriptFormMode] = useState<FormMode>('create');
  const [selectedScriptId, setSelectedScriptId] = useState<number | null>(null);
  const [scriptForm, setScriptForm] = useState<ScriptFormState>(INITIAL_SCRIPT_FORM);
  const [scriptValidation, setScriptValidation] = useState<ValidateProcessingScriptResult | null>(null);
  const [showReportTypeModal, setShowReportTypeModal] = useState(false);
  const [reportTypeFormMode, setReportTypeFormMode] = useState<FormMode>('create');
  const [selectedReportTypeId, setSelectedReportTypeId] = useState<number | null>(null);
  const [reportTypeForm, setReportTypeForm] = useState<ReportTypeFormState>(INITIAL_REPORT_TYPE_FORM);

  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmittingScript, setIsSubmittingScript] = useState(false);
  const [isSubmittingReportType, setIsSubmittingReportType] = useState(false);
  const [isValidatingScript, setIsValidatingScript] = useState(false);

  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const loadTemplatesData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError('');

      const [templatesData, reportTypesData, scriptsData] = await Promise.all([
        templatesApi.list(),
        reportTypesApi.list(),
        processingScriptsApi.list(),
      ]);

      setTemplates(templatesData);
      setReportTypes(reportTypesData);
      setProcessingScripts(scriptsData);
    } catch {
      setError('Не удалось загрузить ML-шаблоны.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadTemplatesData();
  }, [loadTemplatesData]);

  const reportTypeMap = useMemo(() => {
    return new Map(reportTypes.map((item) => [item.id, item]));
  }, [reportTypes]);

  const processingScriptMap = useMemo(() => {
    return new Map(processingScripts.map((item) => [item.id, item]));
  }, [processingScripts]);

  const filteredTemplates = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();

    return templates.filter((template) => {
      const matchesSearch =
        !normalizedSearch ||
        template.code.toLowerCase().includes(normalizedSearch) ||
        template.name.toLowerCase().includes(normalizedSearch) ||
        (template.description ?? '').toLowerCase().includes(normalizedSearch);

      const matchesReportType =
        reportTypeFilter === 'all' ||
        String(template.target_report_type_id ?? '') === reportTypeFilter;

      const matchesActivity =
        activityFilter === 'all' ||
        (activityFilter === 'active' && template.is_active) ||
        (activityFilter === 'inactive' && !template.is_active);

      return matchesSearch && matchesReportType && matchesActivity;
    });
  }, [templates, search, reportTypeFilter, activityFilter]);

  const configValidation = useMemo(
    () => getJsonValidationState(formState.config_json, 'Конфигурация шаблона'),
    [formState.config_json],
  );
  const metricsValidation = useMemo(
    () => getJsonValidationState(formState.metrics_json, 'Метрики и контроль качества'),
    [formState.metrics_json],
  );

  const updateFormField = <K extends keyof TemplateFormState>(
    key: K,
    value: TemplateFormState[K],
  ) => {
    setFormState((prev) => ({ ...prev, [key]: value }));
  };

  const closeFormModal = () => {
    setShowFormModal(false);
    setSelectedTemplate(null);
    setShowAdvancedSettings(false);
  };

  const applyRecommendedPreset = (templateType: TemplateType) => {
    const preset = buildTemplatePreset(templateType);
    setFormState((prev) => ({
      ...prev,
      template_type: templateType,
      config_json: prettyJson(preset.config_json),
      metrics_json: prettyJson(preset.metrics_json),
    }));
  };

  const openCreateModal = () => {
    setFormMode('create');
    setFormState(createInitialFormState());
    setShowAdvancedSettings(false);
    setShowFormModal(true);
    setError('');
    setSuccessMessage('');
  };

  const openCreateScriptModal = () => {
    setScriptFormMode('create');
    setSelectedScriptId(null);
    setScriptForm({
      ...INITIAL_SCRIPT_FORM,
      target_report_type_id: formState.target_report_type_id || '',
    });
    setScriptValidation(null);
    setShowScriptModal(true);
    setError('');
    setSuccessMessage('');
  };

  const openEditScriptModal = async (scriptId: number) => {
    try {
      setError('');
      setSuccessMessage('');
      setScriptValidation(null);
      const script = await processingScriptsApi.getById(scriptId);
      setScriptFormMode('edit');
      setSelectedScriptId(script.id);
      setScriptForm({
        code: script.code,
        name: script.name,
        description: script.description ?? '',
        target_report_type_id: script.target_report_type_id ? String(script.target_report_type_id) : '',
        script_code: script.script_code,
        version: script.version,
        is_default: script.is_default,
        is_active: script.is_active,
      });
      setShowScriptModal(true);
    } catch {
      setError('Не удалось загрузить скрипт обработки для редактирования.');
    }
  };

  const closeScriptModal = () => {
    setShowScriptModal(false);
    setScriptForm(INITIAL_SCRIPT_FORM);
    setScriptFormMode('create');
    setSelectedScriptId(null);
    setScriptValidation(null);
  };

  const openCreateReportTypeModal = () => {
    setReportTypeFormMode('create');
    setSelectedReportTypeId(null);
    setReportTypeForm(INITIAL_REPORT_TYPE_FORM);
    setShowReportTypeModal(true);
    setError('');
    setSuccessMessage('');
  };

  const openEditReportTypeModal = async (reportTypeId: number) => {
    try {
      setError('');
      setSuccessMessage('');
      const reportType = await reportTypesApi.getById(reportTypeId);
      setReportTypeFormMode('edit');
      setSelectedReportTypeId(reportType.id);
      setReportTypeForm({
        code: reportType.code,
        name: reportType.name,
        description: reportType.description ?? '',
        schema_version: reportType.schema_version,
        is_active: reportType.is_active,
      });
      setShowReportTypeModal(true);
    } catch {
      setError('Не удалось загрузить тип отчётности для редактирования.');
    }
  };

  const closeReportTypeModal = () => {
    setShowReportTypeModal(false);
    setReportTypeForm(INITIAL_REPORT_TYPE_FORM);
    setReportTypeFormMode('create');
    setSelectedReportTypeId(null);
  };

  const handleSaveReportType = async () => {
    const code = reportTypeForm.code.trim();
    const name = reportTypeForm.name.trim();

    if (!code || !name) {
      setError('Укажи код и название типа отчётности.');
      return;
    }

    try {
      setIsSubmittingReportType(true);
      setError('');
      setSuccessMessage('');

      if (reportTypeFormMode === 'create') {
        const createdReportType = await reportTypesApi.create({
          code,
          name,
          description: reportTypeForm.description.trim() || null,
          schema_version: reportTypeForm.schema_version.trim() || '1.0',
          is_active: reportTypeForm.is_active,
        });

        await loadTemplatesData();
        updateFormField('target_report_type_id', String(createdReportType.id));
        setScriptForm((prev) => ({
          ...prev,
          target_report_type_id: String(createdReportType.id),
        }));
        closeReportTypeModal();
        setSuccessMessage('Тип отчётности успешно создан и выбран в форме.');
      } else {
        if (selectedReportTypeId == null) {
          setError('Тип отчётности для редактирования не выбран.');
          return;
        }

        const updatedReportType = await reportTypesApi.update(selectedReportTypeId, {
          code,
          name,
          description: reportTypeForm.description.trim() || null,
          schema_version: reportTypeForm.schema_version.trim() || '1.0',
          is_active: reportTypeForm.is_active,
        });

        await loadTemplatesData();
        updateFormField('target_report_type_id', String(updatedReportType.id));
        setSuccessMessage('Тип отчётности успешно обновлён.');
        closeReportTypeModal();
      }
    } catch {
      setError(
        reportTypeFormMode === 'create'
          ? 'Не удалось создать тип отчётности. Проверь уникальность кода и заполнение обязательных полей.'
          : 'Не удалось обновить тип отчётности. Проверь уникальность кода и заполнение обязательных полей.',
      );
    } finally {
      setIsSubmittingReportType(false);
    }
  };


  const handleValidateScript = async () => {
    try {
      setIsValidatingScript(true);
      setScriptValidation(null);
      const result = await processingScriptsApi.validate({
        script_code: scriptForm.script_code,
        sample_context: {
          rows: [
            {
              'Категория расходов': 'IT',
              'Итого с НДС': 350000,
              'Статус оплаты': 'Ожидает оплаты',
            },
          ],
          files: { main: null, additional: [], by_role: {} },
          params: {},
        },
      });
      setScriptValidation(result);
    } catch {
      setScriptValidation({
        is_valid: false,
        message: 'Не удалось проверить скрипт.',
        output_row: null,
        added_columns: [],
        error: 'Проверь доступность backend API.',
      });
    } finally {
      setIsValidatingScript(false);
    }
  };

  const handleScriptFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const nextFile = event.currentTarget.files?.[0] ?? null;
    if (!nextFile) return;

    if (!nextFile.name.endsWith('.py')) {
      setError('Можно загрузить только Python-файл с расширением .py.');
      return;
    }

    const content = await nextFile.text();
    setScriptForm((prev) => ({
      ...prev,
      script_code: content,
      code: prev.code || nextFile.name.replace(/\.py$/i, ''),
      name: prev.name || nextFile.name.replace(/\.py$/i, ''),
    }));
    setScriptValidation(null);
  };

  const handleSaveScript = async () => {
    if (!scriptForm.code.trim() || !scriptForm.name.trim() || !scriptForm.script_code.trim()) {
      setError('Укажи код, название и тело скрипта.');
      return;
    }

    try {
      setIsSubmittingScript(true);
      setError('');
      setSuccessMessage('');

      if (scriptFormMode === 'create') {
        const createdScript = await processingScriptsApi.create({
          code: scriptForm.code.trim(),
          name: scriptForm.name.trim(),
          description: scriptForm.description.trim() || null,
          target_report_type_id: scriptForm.target_report_type_id ? Number(scriptForm.target_report_type_id) : null,
          script_code: scriptForm.script_code,
          version: scriptForm.version.trim() || '1.0',
          is_default: scriptForm.is_default,
          is_active: scriptForm.is_active,
          created_by: user?.id ?? null,
        });
        await loadTemplatesData();
        updateFormField('processing_script_id', String(createdScript.id));
        setSuccessMessage('Скрипт обработки успешно создан и выбран в форме шаблона.');
      } else {
        if (selectedScriptId == null) {
          setError('Скрипт для редактирования не выбран.');
          return;
        }

        const updatedScript = await processingScriptsApi.update(selectedScriptId, {
          code: scriptForm.code.trim(),
          name: scriptForm.name.trim(),
          description: scriptForm.description.trim() || null,
          target_report_type_id: scriptForm.target_report_type_id ? Number(scriptForm.target_report_type_id) : null,
          script_code: scriptForm.script_code,
          version: scriptForm.version.trim() || '1.0',
          is_default: scriptForm.is_default,
          is_active: scriptForm.is_active,
          validation_json: null,
        });
        await loadTemplatesData();
        updateFormField('processing_script_id', String(updatedScript.id));
        setSuccessMessage('Скрипт обработки успешно обновлён.');
      }

      closeScriptModal();
    } catch {
      setError(
        scriptFormMode === 'create'
          ? 'Не удалось создать скрипт обработки. Проверь код и уникальность версии.'
          : 'Не удалось обновить скрипт обработки. Проверь код, тело скрипта и уникальность версии.',
      );
    } finally {
      setIsSubmittingScript(false);
    }
  };

  const openEditModal = async (templateId: number) => {
    try {
      setError('');
      const detail = await templatesApi.getById(templateId);
      setSelectedTemplate(detail);
      setFormMode('edit');
      setFormState(buildFormState(detail));
      setShowAdvancedSettings(true);
      setShowFormModal(true);
    } catch {
      setError('Не удалось загрузить данные шаблона для редактирования.');
    }
  };

  const openDetailModal = async (templateId: number) => {
    try {
      setError('');
      const detail = await templatesApi.getById(templateId);
      setSelectedTemplate(detail);
      setShowDetailModal(true);
    } catch {
      setError('Не удалось загрузить данные шаблона.');
    }
  };

  const handleTemplateTypeChange = (templateType: TemplateType) => {
    if (formMode === 'create') {
      applyRecommendedPreset(templateType);
      return;
    }

    updateFormField('template_type', templateType);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    setSuccessMessage('');

    if (!formState.code.trim()) {
      setError('Укажи код шаблона.');
      return;
    }

    if (!formState.name.trim()) {
      setError('Укажи название шаблона.');
      return;
    }

    try {
      setIsSubmitting(true);

      const configJson = parseJsonField(formState.config_json, 'Конфигурация шаблона');
      const metricsJson = parseJsonField(formState.metrics_json, 'Метрики и контроль качества');

      if (formMode === 'create') {
        const payload: CreateMlTemplatePayload = {
          code: formState.code.trim(),
          name: formState.name.trim(),
          description: formState.description.trim() || null,
          template_type: formState.template_type,
          target_report_type_id: formState.target_report_type_id
            ? Number(formState.target_report_type_id)
            : null,
          processing_script_id: formState.processing_script_id
            ? Number(formState.processing_script_id)
            : null,
          department: formState.department.trim() || null,
          config_json: configJson,
          metrics_json: metricsJson,
          model_path: formState.model_path.trim() || null,
          version: formState.version.trim() || '1.0',
          is_default: formState.is_default,
          is_active: formState.is_active,
          created_by: user?.id ?? null,
        };

        await templatesApi.create(payload);
        setSuccessMessage('ML-шаблон успешно создан.');
      } else {
        if (!selectedTemplate) {
          setError('Шаблон для редактирования не выбран.');
          return;
        }

        const payload: UpdateMlTemplatePayload = {
          code: formState.code.trim(),
          name: formState.name.trim(),
          description: formState.description.trim() || null,
          template_type: formState.template_type,
          target_report_type_id: formState.target_report_type_id
            ? Number(formState.target_report_type_id)
            : null,
          processing_script_id: formState.processing_script_id
            ? Number(formState.processing_script_id)
            : null,
          department: formState.department.trim() || null,
          config_json: configJson,
          metrics_json: metricsJson,
          model_path: formState.model_path.trim() || null,
          version: formState.version.trim() || '1.0',
          is_default: formState.is_default,
          is_active: formState.is_active,
        };

        await templatesApi.update(selectedTemplate.id, payload);
        setSuccessMessage('ML-шаблон успешно обновлён.');
      }

      closeFormModal();
      await loadTemplatesData();
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Не удалось сохранить ML-шаблон.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <ContentCard
        header={
          <div className="toolbar-row">
            <div className="toolbar-left">
              <h2 className="section-title mb-0">ML-шаблоны</h2>
            </div>

            <div className="admin-header-actions">
              <Button className="secondary-pill-button" onClick={() => navigate('/admin')}>
                Назад
              </Button>
              <Button className="secondary-pill-button" onClick={openCreateReportTypeModal}>
                Создать тип отчётности
              </Button>
              <Button className="secondary-pill-button" onClick={openCreateScriptModal}>
                Создать скрипт обработки
              </Button>
              <Button className="primary-pill-button" onClick={openCreateModal}>
                Создать шаблон
              </Button>
            </div>
          </div>
        }
      >
        {isLoading ? (
          <div className="py-5 text-center">
            <Spinner animation="border" />
          </div>
        ) : null}

        {!isLoading && error ? <Alert variant="danger">{error}</Alert> : null}
        {!isLoading && successMessage ? <Alert variant="success">{successMessage}</Alert> : null}

        {!isLoading ? (
          <>
            <div className="admin-section-card mb-4">
              <div className="template-toolbar-filters">
                <Form.Control
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  className="soft-input"
                  placeholder="Поиск по коду, названию или описанию"
                />

                <Form.Select
                  className="soft-select"
                  value={reportTypeFilter}
                  onChange={(event) => setReportTypeFilter(event.target.value)}
                >
                  <option value="all">Все типы отчётности</option>
                  {reportTypes.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name}
                    </option>
                  ))}
                </Form.Select>

                <Form.Select
                  className="soft-select"
                  value={activityFilter}
                  onChange={(event) => setActivityFilter(event.target.value)}
                >
                  <option value="all">Все состояния</option>
                  <option value="active">Только активные</option>
                  <option value="inactive">Только неактивные</option>
                </Form.Select>
              </div>
            </div>

            <div className="admin-section-card">
              <div className="table-wrap">
                <Table borderless responsive className="prototype-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Код</th>
                      <th>Название</th>
                      <th>Тип</th>
                      <th>Тип отчётности</th>
                      <th>Скрипт</th>
                      <th>Версия</th>
                      <th>Статус</th>
                      <th>По умолчанию</th>
                      <th>Действия</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredTemplates.length === 0 ? (
                      <tr>
                        <td colSpan={10} className="text-center py-4">
                          ML-шаблоны не найдены
                        </td>
                      </tr>
                    ) : (
                      filteredTemplates.map((template) => (
                        <tr key={template.id}>
                          <td>{template.id}</td>
                          <td>{template.code}</td>
                          <td>{template.name}</td>
                          <td>{getTemplateTypeLabel(template.template_type)}</td>
                          <td>
                            {template.target_report_type_id ? (
                              <button
                                type="button"
                                className="template-table-link"
                                onClick={() => void openEditReportTypeModal(template.target_report_type_id as number)}
                                title="Редактировать тип отчётности"
                              >
                                {reportTypeMap.get(template.target_report_type_id)?.name ?? `#${template.target_report_type_id}`}
                              </button>
                            ) : (
                              '-'
                            )}
                          </td>
                          <td>
                            {template.processing_script_id ? (
                              <button
                                type="button"
                                className="template-table-link"
                                onClick={() => void openEditScriptModal(template.processing_script_id as number)}
                                title="Редактировать скрипт обработки"
                              >
                                {processingScriptMap.get(template.processing_script_id)?.name ?? `#${template.processing_script_id}`}
                              </button>
                            ) : (
                              '-'
                            )}
                          </td>
                          <td>{template.version}</td>
                          <td>
                            <span className={template.is_active ? 'status-badge status-badge-success' : 'status-badge status-badge-muted'}>
                              {template.is_active ? 'Активен' : 'Неактивен'}
                            </span>
                          </td>
                          <td>
                            {template.is_default ? (
                              <span className="template-chip template-chip-default">Да</span>
                            ) : (
                              <span className="template-chip template-chip-plain">Нет</span>
                            )}
                          </td>
                          <td className="table-action-cell">
                            <div className="admin-action-group">
                              <Button
                                size="sm"
                                className="secondary-pill-button admin-small-button"
                                onClick={() => void openDetailModal(template.id)}
                              >
                                Просмотр
                              </Button>

                              <Button
                                size="sm"
                                className="primary-pill-button admin-small-button"
                                onClick={() => void openEditModal(template.id)}
                              >
                                Редактировать
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </Table>
              </div>
            </div>
          </>
        ) : null}
      </ContentCard>

      <Modal show={showFormModal} onHide={closeFormModal} size="lg" centered>
        <Modal.Header closeButton>
          <Modal.Title>
            {formMode === 'create' ? 'Создание ML-шаблона' : 'Редактирование ML-шаблона'}
          </Modal.Title>
        </Modal.Header>

        <Form onSubmit={handleSubmit}>
          <Modal.Body>
            <div className="template-helper-panel mb-4">
              <div className="template-helper-title">Как заполнить шаблон</div>
              <div className="template-helper-text">
                Сначала укажи основные сведения о шаблоне, затем выбери тип обработки. После выбора типа можно
                подставить рекомендуемый пример конфигурации и при необходимости уточнить расширенные параметры.
              </div>
            </div>

            <div className="template-type-grid mb-4">
              {TEMPLATE_TYPE_OPTIONS.map((item) => {
                const isActive = formState.template_type === item.value;

                return (
                  <button
                    key={item.value}
                    type="button"
                    className={`template-type-card ${isActive ? 'template-type-card-active' : ''}`}
                    onClick={() => handleTemplateTypeChange(item.value)}
                  >
                    <div className="template-type-card-title">{item.label}</div>
                    <div className="template-type-card-text">{getTemplateTypeDescription(item.value)}</div>
                  </button>
                );
              })}
            </div>

            <div className="template-form-section mb-4">
              <div className="template-form-section-title">Основные сведения</div>
              <Row className="g-3">
                <Col md={6}>
                  <Form.Group>
                    <Form.Label>Код шаблона</Form.Label>
                    <Form.Control
                      className="soft-input"
                      value={formState.code}
                      onChange={(event) => updateFormField('code', event.target.value)}
                    />
                    <Form.Text className="text-muted">
                      Краткий технический идентификатор без пробелов. Используется в API и логах.
                    </Form.Text>
                  </Form.Group>
                </Col>

                <Col md={6}>
                  <Form.Group>
                    <Form.Label>Версия</Form.Label>
                    <Form.Control
                      className="soft-input"
                      value={formState.version}
                      onChange={(event) => updateFormField('version', event.target.value)}
                      placeholder="1.0"
                    />
                  </Form.Group>
                </Col>

                <Col md={12}>
                  <Form.Group>
                    <Form.Label>Название</Form.Label>
                    <Form.Control
                      className="soft-input"
                      value={formState.name}
                      onChange={(event) => updateFormField('name', event.target.value)}
                    />
                  </Form.Group>
                </Col>

                <Col md={6}>
                  <Form.Group>
                    <Form.Label>Тип обработки</Form.Label>
                    <Form.Select
                      className="soft-input"
                      value={formState.template_type}
                      onChange={(event) => handleTemplateTypeChange(event.target.value as TemplateType)}
                    >
                      {TEMPLATE_TYPE_OPTIONS.map((item) => (
                        <option key={item.value} value={item.value}>
                          {item.label}
                        </option>
                      ))}
                    </Form.Select>
                  </Form.Group>
                </Col>

                <Col md={6}>
                  <Form.Group>
                    <div className="template-field-header">
                      <Form.Label>Тип отчётности</Form.Label>
                      <button type="button" className="template-inline-link" onClick={openCreateReportTypeModal}>
                        Создать тип
                      </button>
                    </div>
                    <Form.Select
                      className="soft-input"
                      value={formState.target_report_type_id}
                      onChange={(event) => updateFormField('target_report_type_id', event.target.value)}
                    >
                      <option value="">Не задан</option>
                      {reportTypes.map((item) => (
                        <option key={item.id} value={item.id}>
                          {item.name}
                        </option>
                      ))}
                    </Form.Select>
                  </Form.Group>
                </Col>

                <Col md={6}>
                  <Form.Group>
                    <div className="template-field-header">
                      <Form.Label>Скрипт постобработки</Form.Label>
                      <button type="button" className="template-inline-link" onClick={openCreateScriptModal}>
                        Создать скрипт
                      </button>
                    </div>
                    <Form.Select
                      className="soft-input"
                      value={formState.processing_script_id}
                      onChange={(event) => updateFormField('processing_script_id', event.target.value)}
                    >
                      <option value="">Не задан</option>
                      {processingScripts
                        .filter((item) => !formState.target_report_type_id || String(item.target_report_type_id ?? '') === formState.target_report_type_id || item.target_report_type_id == null)
                        .map((item) => (
                          <option key={item.id} value={item.id}>
                            {item.name} v{item.version}
                          </option>
                        ))}
                    </Form.Select>
                    <Form.Text className="text-muted">
                      Скрипт применяется после нормализации и может добавить новые расчётные колонки.
                    </Form.Text>
                  </Form.Group>
                </Col>

                <Col md={6}>
                  <Form.Group>
                    <Form.Label>Подразделение</Form.Label>
                    <Form.Control
                      className="soft-input"
                      value={formState.department}
                      onChange={(event) => updateFormField('department', event.target.value)}
                    />
                  </Form.Group>
                </Col>

                <Col md={6}>
                  <Form.Group>
                    <Form.Label>Путь к модели</Form.Label>
                    <Form.Control
                      className="soft-input"
                      value={formState.model_path}
                      onChange={(event) => updateFormField('model_path', event.target.value)}
                    />
                    <Form.Text className="text-muted">
                      Поле необязательно. Заполняй его только если шаблон связан с конкретным ML-артефактом.
                    </Form.Text>
                  </Form.Group>
                </Col>

                <Col md={12}>
                  <Form.Group>
                    <Form.Label>Описание</Form.Label>
                    <Form.Control
                      as="textarea"
                      rows={3}
                      className="soft-input soft-textarea"
                      value={formState.description}
                      onChange={(event) => updateFormField('description', event.target.value)}
                      placeholder="Кратко опиши, для какой отчётности и сценария предназначен этот шаблон"
                    />
                  </Form.Group>
                </Col>
              </Row>
            </div>

            <div className="template-form-section mb-4">
              <div className="template-form-section-header">
                <div>
                  <div className="template-form-section-title mb-1">Расширенные параметры</div>
                  <div className="template-form-section-text">
                    Здесь можно задать конфигурацию обработки и параметры оценки качества. Для большинства сценариев
                    достаточно подставить рекомендуемый пример и при необходимости скорректировать его.
                  </div>
                </div>

                <div className="template-advanced-actions">
                  <Button
                    type="button"
                    className="secondary-pill-button"
                    onClick={() => setShowAdvancedSettings((prev) => !prev)}
                  >
                    {showAdvancedSettings ? 'Скрыть расширенные поля' : 'Показать расширенные поля'}
                  </Button>

                  <Button
                    type="button"
                    className="secondary-pill-button"
                    onClick={() => applyRecommendedPreset(formState.template_type)}
                  >
                    Подставить пример
                  </Button>
                </div>
              </div>

              <div className="template-json-status-grid mb-3">
                <div className={`template-json-status ${configValidation.isValid ? 'template-json-status-valid' : 'template-json-status-invalid'}`}>
                  {configValidation.message}
                </div>
                <div className={`template-json-status ${metricsValidation.isValid ? 'template-json-status-valid' : 'template-json-status-invalid'}`}>
                  {metricsValidation.message}
                </div>
              </div>

              {showAdvancedSettings ? (
                <Row className="g-3">
                  <Col md={6}>
                    <Form.Group>
                      <Form.Label>Конфигурация шаблона</Form.Label>
                      <Form.Control
                        as="textarea"
                        rows={9}
                        className="soft-input soft-textarea template-json-area"
                        value={formState.config_json}
                        onChange={(event) => updateFormField('config_json', event.target.value)}
                      />
                      <Form.Text className="text-muted">
                        Здесь задаются рабочие параметры обработки: стратегия, пороги, правила чтения и нормализации.
                      </Form.Text>
                    </Form.Group>
                  </Col>

                  <Col md={6}>
                    <Form.Group>
                      <Form.Label>Метрики и контроль качества</Form.Label>
                      <Form.Control
                        as="textarea"
                        rows={9}
                        className="soft-input soft-textarea template-json-area"
                        value={formState.metrics_json}
                        onChange={(event) => updateFormField('metrics_json', event.target.value)}
                      />
                      <Form.Text className="text-muted">
                        Укажи, какие показатели качества нужно отслеживать и какие пороговые значения считаются допустимыми.
                      </Form.Text>
                    </Form.Group>
                  </Col>
                </Row>
              ) : (
                <div className="template-collapsed-note">
                  Выбрано: <strong>{getTemplateTypeLabel(formState.template_type)}</strong>. Рекомендуемый пример можно
                  подставить одной кнопкой и открыть расширенные поля только при необходимости.
                </div>
              )}
            </div>

            <Row className="g-3">
              <Col md={6}>
                <Form.Check
                  type="switch"
                  id="template-is-default"
                  label="Использовать как шаблон по умолчанию"
                  checked={formState.is_default}
                  onChange={(event) => updateFormField('is_default', event.target.checked)}
                />
              </Col>

              <Col md={6}>
                <Form.Check
                  type="switch"
                  id="template-is-active"
                  label="Шаблон активен"
                  checked={formState.is_active}
                  onChange={(event) => updateFormField('is_active', event.target.checked)}
                />
              </Col>
            </Row>
          </Modal.Body>

          <Modal.Footer>
            <Button type="button" className="secondary-pill-button" onClick={closeFormModal}>
              Отмена
            </Button>

            <Button type="submit" className="primary-pill-button" disabled={isSubmitting}>
              {isSubmitting ? 'Сохранение...' : formMode === 'create' ? 'Создать шаблон' : 'Сохранить изменения'}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>



      <Modal show={showScriptModal} onHide={closeScriptModal} size="lg" centered>
        <Modal.Header closeButton>
          <Modal.Title>{scriptFormMode === 'create' ? 'Создание скрипта обработки' : 'Редактирование скрипта обработки'}</Modal.Title>
        </Modal.Header>

        <Modal.Body>
          <div className="template-helper-panel mb-4">
            <div className="template-helper-title">Скрипт постобработки</div>
            <div className="template-helper-text">
              Скрипт выполняется после технической нормализации и получает расширенный контекст: строки отчёта, путь к основному файлу,
              дополнительные файлы и параметры задачи. Скрипт должен содержать функцию process(context), а внутри неё можно использовать
              любые вспомогательные функции и доступные в окружении Python-библиотеки.
            </div>
          </div>

          <Row className="g-3">
            <Col md={6}>
              <Form.Group>
                <Form.Label>Код скрипта</Form.Label>
                <Form.Control
                  className="soft-input"
                  value={scriptForm.code}
                  onChange={(event) => setScriptForm((prev) => ({ ...prev, code: event.target.value }))}
                  placeholder="expense_control_script"
                />
              </Form.Group>
            </Col>

            <Col md={6}>
              <Form.Group>
                <Form.Label>Версия</Form.Label>
                <Form.Control
                  className="soft-input"
                  value={scriptForm.version}
                  onChange={(event) => setScriptForm((prev) => ({ ...prev, version: event.target.value }))}
                  placeholder="1.0"
                />
              </Form.Group>
            </Col>

            <Col md={12}>
              <Form.Group>
                <Form.Label>Название</Form.Label>
                <Form.Control
                  className="soft-input"
                  value={scriptForm.name}
                  onChange={(event) => setScriptForm((prev) => ({ ...prev, name: event.target.value }))}
                  placeholder="Контроль расходных операций"
                />
              </Form.Group>
            </Col>

            <Col md={6}>
              <Form.Group>
                <div className="template-field-header">
                  <Form.Label>Тип отчётности</Form.Label>
                  <button type="button" className="template-inline-link" onClick={openCreateReportTypeModal}>
                    Создать тип
                  </button>
                </div>
                <Form.Select
                  className="soft-input"
                  value={scriptForm.target_report_type_id}
                  onChange={(event) => setScriptForm((prev) => ({ ...prev, target_report_type_id: event.target.value }))}
                >
                  <option value="">Без привязки</option>
                  {reportTypes.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name}
                    </option>
                  ))}
                </Form.Select>
              </Form.Group>
            </Col>

            <Col md={6}>
              <div className="template-script-switches">
                <Form.Check
                  type="switch"
                  id="script-active"
                  label="Скрипт активен"
                  checked={scriptForm.is_active}
                  onChange={(event) => setScriptForm((prev) => ({ ...prev, is_active: event.target.checked }))}
                />
                <Form.Check
                  type="switch"
                  id="script-default"
                  label="Использовать по умолчанию для типа отчётности"
                  checked={scriptForm.is_default}
                  onChange={(event) => setScriptForm((prev) => ({ ...prev, is_default: event.target.checked }))}
                />
              </div>
            </Col>

            <Col md={12}>
              <Form.Group>
                <Form.Label>Описание</Form.Label>
                <Form.Control
                  as="textarea"
                  rows={2}
                  className="soft-input soft-textarea"
                  value={scriptForm.description}
                  onChange={(event) => setScriptForm((prev) => ({ ...prev, description: event.target.value }))}
                />
              </Form.Group>
            </Col>

            <Col md={12}>
              <Form.Group>
                <Form.Label>Загрузить .py-файл скрипта</Form.Label>
                <Form.Control
                  type="file"
                  className="soft-input"
                  accept=".py"
                  onChange={handleScriptFileChange}
                />
                <Form.Text className="text-muted">
                  Можно загрузить локально подготовленный и протестированный Python-файл.
                </Form.Text>
              </Form.Group>
            </Col>

            <Col md={12}>
              <Form.Group>
                <Form.Label>Python-код</Form.Label>
                <Form.Control
                  as="textarea"
                  rows={18}
                  className="soft-input soft-textarea template-code-editor"
                  value={scriptForm.script_code}
                  onChange={(event) => setScriptForm((prev) => ({ ...prev, script_code: event.target.value }))}
                />
                <Form.Text className="text-muted">
                  Точка входа: process(context). Скрипт запускается в отдельном процессе и может работать с context["rows"],
                  context["files"]["main"] и context["files"]["by_role"].
                </Form.Text>
              </Form.Group>
            </Col>

            {scriptValidation ? (
              <Col md={12}>
                <Alert variant={scriptValidation.is_valid ? 'success' : 'danger'} className="mb-0">
                  <div>{scriptValidation.message}</div>
                  {scriptValidation.error ? <div>{scriptValidation.error}</div> : null}
                  {scriptValidation.added_columns.length > 0 ? (
                    <div>Добавляемые колонки: {scriptValidation.added_columns.join(', ')}</div>
                  ) : null}
                </Alert>
              </Col>
            ) : null}
          </Row>
        </Modal.Body>

        <Modal.Footer>
          <Button className="secondary-pill-button" onClick={closeScriptModal}>
            Отмена
          </Button>
          <Button
            type="button"
            className="secondary-pill-button"
            disabled={isValidatingScript}
            onClick={() => void handleValidateScript()}
          >
            {isValidatingScript ? 'Проверка...' : 'Проверить скрипт'}
          </Button>
          <Button
            type="button"
            className="primary-pill-button"
            disabled={isSubmittingScript}
            onClick={() => void handleSaveScript()}
          >
            {isSubmittingScript ? 'Сохранение...' : scriptFormMode === 'create' ? 'Создать скрипт' : 'Сохранить изменения'}
          </Button>
        </Modal.Footer>
      </Modal>


      <Modal show={showReportTypeModal} onHide={closeReportTypeModal} centered>
        <Modal.Header closeButton>
          <Modal.Title>{reportTypeFormMode === 'create' ? 'Создание типа отчётности' : 'Редактирование типа отчётности'}</Modal.Title>
        </Modal.Header>

        <Modal.Body>
          <div className="template-helper-panel mb-4">
            <div className="template-helper-title">Тип отчётности</div>
            <div className="template-helper-text">
              Тип отчётности используется при создании отчёта и настройке ML-шаблона. Он помогает связать шаблон,
              скрипт обработки и конкретный вид отчётных данных.
            </div>
          </div>

          <Row className="g-3">
            <Col md={6}>
              <Form.Group>
                <Form.Label>Код типа отчётности</Form.Label>
                <Form.Control
                  className="soft-input"
                  value={reportTypeForm.code}
                  onChange={(event) => setReportTypeForm((prev) => ({ ...prev, code: event.target.value }))}
                />
                <Form.Text className="text-muted">
                  Технический код без пробелов. Используется в API, шаблонах и логах.
                </Form.Text>
              </Form.Group>
            </Col>

            <Col md={6}>
              <Form.Group>
                <Form.Label>Версия схемы</Form.Label>
                <Form.Control
                  className="soft-input"
                  value={reportTypeForm.schema_version}
                  onChange={(event) => setReportTypeForm((prev) => ({ ...prev, schema_version: event.target.value }))}
                  placeholder="1.0"
                />
              </Form.Group>
            </Col>

            <Col md={12}>
              <Form.Group>
                <Form.Label>Название</Form.Label>
                <Form.Control
                  className="soft-input"
                  value={reportTypeForm.name}
                  onChange={(event) => setReportTypeForm((prev) => ({ ...prev, name: event.target.value }))}
                />
              </Form.Group>
            </Col>

            <Col md={12}>
              <Form.Group>
                <Form.Label>Описание</Form.Label>
                <Form.Control
                  as="textarea"
                  rows={3}
                  className="soft-input soft-textarea"
                  value={reportTypeForm.description}
                  onChange={(event) => setReportTypeForm((prev) => ({ ...prev, description: event.target.value }))}
                  placeholder="Кратко опиши назначение типа отчётности"
                />
              </Form.Group>
            </Col>

            <Col md={12}>
              <Form.Check
                type="switch"
                id="report-type-active"
                label="Тип отчётности активен"
                checked={reportTypeForm.is_active}
                onChange={(event) => setReportTypeForm((prev) => ({ ...prev, is_active: event.target.checked }))}
              />
            </Col>
          </Row>
        </Modal.Body>

        <Modal.Footer>
          <Button className="secondary-pill-button" onClick={closeReportTypeModal}>
            Отмена
          </Button>
          <Button
            type="button"
            className="primary-pill-button"
            disabled={isSubmittingReportType}
            onClick={() => void handleSaveReportType()}
          >
            {isSubmittingReportType ? 'Сохранение...' : reportTypeFormMode === 'create' ? 'Создать тип' : 'Сохранить изменения'}
          </Button>
        </Modal.Footer>
      </Modal>

      <Modal
        show={showDetailModal}
        onHide={() => {
          setShowDetailModal(false);
          setSelectedTemplate(null);
        }}
        size="lg"
        centered
      >
        <Modal.Header closeButton>
          <Modal.Title>Детали ML-шаблона</Modal.Title>
        </Modal.Header>

        <Modal.Body>
          {!selectedTemplate ? (
            <div className="text-center py-4">
              <Spinner animation="border" />
            </div>
          ) : (
            <div className="template-detail-grid">
              <div className="form-meta-card">
                <div className="form-meta-label">Название</div>
                <div className="form-meta-value">{selectedTemplate.name}</div>
              </div>

              <div className="form-meta-card">
                <div className="form-meta-label">Код</div>
                <div className="form-meta-value">{selectedTemplate.code}</div>
              </div>

              <div className="form-meta-card">
                <div className="form-meta-label">Тип обработки</div>
                <div className="form-meta-value">{getTemplateTypeLabel(selectedTemplate.template_type)}</div>
              </div>

              <div className="form-meta-card">
                <div className="form-meta-label">Версия</div>
                <div className="form-meta-value">{selectedTemplate.version}</div>
              </div>

              <div className="form-meta-card">
                <div className="form-meta-label">Тип отчётности</div>
                <div className="form-meta-value">
                  {selectedTemplate.target_report_type_id
                    ? reportTypeMap.get(selectedTemplate.target_report_type_id)?.name ?? `#${selectedTemplate.target_report_type_id}`
                    : '-'}
                </div>
              </div>

              <div className="form-meta-card">
                <div className="form-meta-label">Скрипт постобработки</div>
                <div className="form-meta-value">
                  {selectedTemplate.processing_script_id
                    ? processingScriptMap.get(selectedTemplate.processing_script_id)?.name ?? `#${selectedTemplate.processing_script_id}`
                    : '-'}
                </div>
              </div>

              <div className="form-meta-card">
                <div className="form-meta-label">Создатель</div>
                <div className="form-meta-value">{selectedTemplate.creator?.full_name ?? '-'}</div>
              </div>

              <div className="form-meta-card">
                <div className="form-meta-label">Статус</div>
                <div className="form-meta-value">
                  <span className={selectedTemplate.is_active ? 'status-badge status-badge-success' : 'status-badge status-badge-muted'}>
                    {selectedTemplate.is_active ? 'Активен' : 'Неактивен'}
                  </span>
                </div>
              </div>

              <div className="form-meta-card">
                <div className="form-meta-label">По умолчанию</div>
                <div className="form-meta-value">{selectedTemplate.is_default ? 'Да' : 'Нет'}</div>
              </div>

              <div className="form-meta-card template-detail-wide">
                <div className="form-meta-label">Описание</div>
                <div className="form-meta-value">{selectedTemplate.description ?? '-'}</div>
              </div>

              <div className="form-meta-card template-detail-wide">
                <div className="form-meta-label">Конфигурация шаблона</div>
                <pre className="template-json-preview">{prettyJson(selectedTemplate.config_json)}</pre>
              </div>

              <div className="form-meta-card template-detail-wide">
                <div className="form-meta-label">Метрики и контроль качества</div>
                <pre className="template-json-preview">{prettyJson(selectedTemplate.metrics_json)}</pre>
              </div>

              <div className="form-meta-card template-detail-wide">
                <div className="form-meta-label">Служебная информация</div>
                <div className="result-info-list">
                  <div><strong>ID:</strong> {selectedTemplate.id}</div>
                  <div><strong>Создан:</strong> {formatDateTime(selectedTemplate.created_at)}</div>
                  <div><strong>Обновлён:</strong> {formatDateTime(selectedTemplate.updated_at)}</div>
                  <div><strong>Путь к модели:</strong> {selectedTemplate.model_path ?? '-'}</div>
                  <div><strong>Подразделение:</strong> {selectedTemplate.department ?? '-'}</div>
                </div>
              </div>
            </div>
          )}
        </Modal.Body>

        <Modal.Footer>
          <Button
            className="secondary-pill-button"
            onClick={() => {
              setShowDetailModal(false);
              setSelectedTemplate(null);
            }}
          >
            Закрыть
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
}
