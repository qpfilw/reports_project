import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react';
import { Alert, Button, Col, Form, Modal, Row, Spinner, Table } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthProvider';
import { reportTypesApi } from '../../shared/api/reportTypes';
import { templatesApi } from '../../shared/api/templates';
import { TEMPLATE_TYPE_OPTIONS, type CreateMlTemplatePayload, type MlTemplate, type MlTemplateDetail, type TemplateType, type UpdateMlTemplatePayload } from '../../shared/types/template';
import type { ReportType } from '../../shared/types/report-type';
import { ContentCard } from '../../shared/ui/ContentCard';

type FormMode = 'create' | 'edit';

interface TemplateFormState {
  code: string;
  name: string;
  description: string;
  template_type: TemplateType;
  target_report_type_id: string;
  department: string;
  config_json: string;
  metrics_json: string;
  model_path: string;
  version: string;
  is_default: boolean;
  is_active: boolean;
}

const initialFormState: TemplateFormState = {
  code: '',
  name: '',
  description: '',
  template_type: 'classification',
  target_report_type_id: '',
  department: '',
  config_json: '{\n  \n}',
  metrics_json: '{\n  \n}',
  model_path: '',
  version: '1.0',
  is_default: false,
  is_active: true,
};

function prettyJson(value: Record<string, unknown>) {
  return JSON.stringify(value ?? {}, null, 2);
}

function buildFormState(template?: MlTemplateDetail | null): TemplateFormState {
  if (!template) {
    return initialFormState;
  }

  return {
    code: template.code,
    name: template.name,
    description: template.description ?? '',
    template_type: template.template_type,
    target_report_type_id: template.target_report_type_id ? String(template.target_report_type_id) : '',
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
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('ru-RU');
}

function getTemplateTypeLabel(value: TemplateType) {
  return TEMPLATE_TYPE_OPTIONS.find((item) => item.value === value)?.label ?? value;
}

export default function AdminTemplatesPage() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [templates, setTemplates] = useState<MlTemplate[]>([]);
  const [reportTypes, setReportTypes] = useState<ReportType[]>([]);

  const [selectedTemplate, setSelectedTemplate] = useState<MlTemplateDetail | null>(null);
  const [formState, setFormState] = useState<TemplateFormState>(initialFormState);

  const [search, setSearch] = useState('');
  const [reportTypeFilter, setReportTypeFilter] = useState('all');
  const [activityFilter, setActivityFilter] = useState('all');

  const [formMode, setFormMode] = useState<FormMode>('create');
  const [showFormModal, setShowFormModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);

  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const loadTemplatesData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError('');

      const [templatesData, reportTypesData] = await Promise.all([
        templatesApi.list(),
        reportTypesApi.list(),
      ]);

      setTemplates(templatesData);
      setReportTypes(reportTypesData);
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

  const updateFormField = <K extends keyof TemplateFormState>(
    key: K,
    value: TemplateFormState[K],
  ) => {
    setFormState((prev) => ({ ...prev, [key]: value }));
  };

  const openCreateModal = () => {
    setFormMode('create');
    setFormState(initialFormState);
    setShowFormModal(true);
    setError('');
    setSuccessMessage('');
  };

  const openEditModal = async (templateId: number) => {
    try {
      setError('');
      const detail = await templatesApi.getById(templateId);
      setSelectedTemplate(detail);
      setFormMode('edit');
      setFormState(buildFormState(detail));
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

  const parseJsonField = (value: string, fieldLabel: string) => {
    try {
      return JSON.parse(value || '{}') as Record<string, unknown>;
    } catch {
      throw new Error(`Поле "${fieldLabel}" содержит некорректный JSON.`);
    }
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

      const configJson = parseJsonField(formState.config_json, 'Конфигурация');
      const metricsJson = parseJsonField(formState.metrics_json, 'Метрики');

      if (formMode === 'create') {
        const payload: CreateMlTemplatePayload = {
          code: formState.code.trim(),
          name: formState.name.trim(),
          description: formState.description.trim() || null,
          template_type: formState.template_type,
          target_report_type_id: formState.target_report_type_id
            ? Number(formState.target_report_type_id)
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
          department: formState.department.trim() || null,
          config_json: configJson,
          metrics_json: metricsJson,
          model_path: formState.model_path.trim() || null,
          version: formState.version.trim() || '1.0',
          is_default: formState.is_default,
          is_active: formState.is_active,
        };

        await templatesApi.update(selectedTemplate.id, payload);
        setSuccessMessage('ML-шаблон успешно обновлен.');
      }

      setShowFormModal(false);
      setSelectedTemplate(null);
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
                  <option value="all">Все типы отчетности</option>
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
                      <th>Тип отчетности</th>
                      <th>Версия</th>
                      <th>Статус</th>
                      <th>По умолчанию</th>
                      <th>Действия</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredTemplates.length === 0 ? (
                      <tr>
                        <td colSpan={9} className="text-center py-4">
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
                          <td>{template.target_report_type_id ? reportTypeMap.get(template.target_report_type_id)?.name ?? `#${template.target_report_type_id}` : '-'}</td>
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

      <Modal
        show={showFormModal}
        onHide={() => {
          setShowFormModal(false);
          setSelectedTemplate(null);
        }}
        size="lg"
        centered
      >
        <Modal.Header closeButton>
          <Modal.Title>
            {formMode === 'create' ? 'Создание ML-шаблона' : 'Редактирование ML-шаблона'}
          </Modal.Title>
        </Modal.Header>

        <Form onSubmit={handleSubmit}>
          <Modal.Body>
            <Row className="g-3">
              <Col md={6}>
                <Form.Group>
                  <Form.Label>Код</Form.Label>
                  <Form.Control
                    className="soft-input"
                    value={formState.code}
                    onChange={(event) => updateFormField('code', event.target.value)}
                  />
                </Form.Group>
              </Col>

              <Col md={6}>
                <Form.Group>
                  <Form.Label>Версия</Form.Label>
                  <Form.Control
                    className="soft-input"
                    value={formState.version}
                    onChange={(event) => updateFormField('version', event.target.value)}
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
                  <Form.Label>Тип шаблона</Form.Label>
                  <Form.Select
                    className="soft-input"
                    value={formState.template_type}
                    onChange={(event) =>
                      updateFormField('template_type', event.target.value as TemplateType)
                    }
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
                  <Form.Label>Тип отчетности</Form.Label>
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
                  <Form.Label>Отдел</Form.Label>
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
                  />
                </Form.Group>
              </Col>

              <Col md={6}>
                <Form.Group>
                  <Form.Label>config_json</Form.Label>
                  <Form.Control
                    as="textarea"
                    rows={8}
                    className="soft-input soft-textarea template-json-area"
                    value={formState.config_json}
                    onChange={(event) => updateFormField('config_json', event.target.value)}
                  />
                </Form.Group>
              </Col>

              <Col md={6}>
                <Form.Group>
                  <Form.Label>metrics_json</Form.Label>
                  <Form.Control
                    as="textarea"
                    rows={8}
                    className="soft-input soft-textarea template-json-area"
                    value={formState.metrics_json}
                    onChange={(event) => updateFormField('metrics_json', event.target.value)}
                  />
                </Form.Group>
              </Col>

              <Col md={6}>
                <Form.Check
                  type="switch"
                  id="template-is-default"
                  label="Шаблон по умолчанию"
                  checked={formState.is_default}
                  onChange={(event) => updateFormField('is_default', event.target.checked)}
                />
              </Col>

              <Col md={6}>
                <Form.Check
                  type="switch"
                  id="template-is-active"
                  label="Активный шаблон"
                  checked={formState.is_active}
                  onChange={(event) => updateFormField('is_active', event.target.checked)}
                />
              </Col>
            </Row>
          </Modal.Body>

          <Modal.Footer>
            <Button
              variant="light"
              className="secondary-pill-button"
              onClick={() => {
                setShowFormModal(false);
                setSelectedTemplate(null);
              }}
            >
              Отмена
            </Button>

            <Button type="submit" className="primary-pill-button" disabled={isSubmitting}>
              {isSubmitting ? 'Сохранение...' : formMode === 'create' ? 'Создать' : 'Сохранить'}
            </Button>
          </Modal.Footer>
        </Form>
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
                <div className="form-meta-label">Тип</div>
                <div className="form-meta-value">{getTemplateTypeLabel(selectedTemplate.template_type)}</div>
              </div>

              <div className="form-meta-card">
                <div className="form-meta-label">Версия</div>
                <div className="form-meta-value">{selectedTemplate.version}</div>
              </div>

              <div className="form-meta-card">
                <div className="form-meta-label">Тип отчетности</div>
                <div className="form-meta-value">
                  {selectedTemplate.target_report_type_id
                    ? reportTypeMap.get(selectedTemplate.target_report_type_id)?.name ?? `#${selectedTemplate.target_report_type_id}`
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
                <div className="form-meta-label">config_json</div>
                <pre className="template-json-preview">
                  {prettyJson(selectedTemplate.config_json)}
                </pre>
              </div>

              <div className="form-meta-card template-detail-wide">
                <div className="form-meta-label">metrics_json</div>
                <pre className="template-json-preview">
                  {prettyJson(selectedTemplate.metrics_json)}
                </pre>
              </div>

              <div className="form-meta-card template-detail-wide">
                <div className="form-meta-label">Служебная информация</div>
                <div className="result-info-list">
                  <div><strong>ID:</strong> {selectedTemplate.id}</div>
                  <div><strong>created_at:</strong> {formatDateTime(selectedTemplate.created_at)}</div>
                  <div><strong>updated_at:</strong> {formatDateTime(selectedTemplate.updated_at)}</div>
                  <div><strong>model_path:</strong> {selectedTemplate.model_path ?? '-'}</div>
                  <div><strong>department:</strong> {selectedTemplate.department ?? '-'}</div>
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