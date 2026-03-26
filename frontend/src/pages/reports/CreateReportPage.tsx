import { useEffect, useMemo, useState } from 'react';
import { Alert, Button, Col, Form, Row, Spinner } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthProvider';
import { useProjectContext } from '../../features/projects/ProjectContext';
import { mlApi } from '../../shared/api/ml';
import { reportTypesApi } from '../../shared/api/reportTypes';
import { reportsApi } from '../../shared/api/reports';
import { readUserSettings, saveLastMlTemplateId } from '../../shared/lib/userSettings';
import type { ReportType } from '../../shared/types/report-type';
import type { MlTemplate } from '../../shared/types/template';
import { ContentCard } from '../../shared/ui/ContentCard';

interface CreateReportFormState {
  project_id: string;
  report_type_id: string;
  title: string;
  description: string;
  report_period_start: string;
  report_period_end: string;
  ml_template_id: string;
}

const initialForm: CreateReportFormState = {
  project_id: '',
  report_type_id: '',
  title: '',
  description: '',
  report_period_start: '',
  report_period_end: '',
  ml_template_id: '',
};

export default function CreateReportPage() {
  const { user } = useAuth();
  const { activeProjectId, projects } = useProjectContext();
  const navigate = useNavigate();
  const settings = readUserSettings();

  const [form, setForm] = useState<CreateReportFormState>(initialForm);
  const [reportTypes, setReportTypes] = useState<ReportType[]>([]);
  const [templates, setTemplates] = useState<MlTemplate[]>([]);

  const [isBootLoading, setIsBootLoading] = useState(true);
  const [isTemplatesLoading, setIsTemplatesLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  useEffect(() => {
    if (activeProjectId != null) {
      setForm((prev) => ({
        ...prev,
        project_id: String(activeProjectId),
      }));
    }
  }, [activeProjectId]);

  useEffect(() => {
    (async () => {
      try {
        setIsBootLoading(true);
        setError('');

        const reportTypesData = await reportTypesApi.list();
        setReportTypes(reportTypesData.filter((item) => item.is_active));
      } catch {
        setError('Не удалось загрузить данные для создания отчета.');
      } finally {
        setIsBootLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    if (!form.report_type_id) {
      setTemplates([]);
      setForm((prev) => ({ ...prev, ml_template_id: '' }));
      return;
    }

    (async () => {
      try {
        setIsTemplatesLoading(true);
        const templatesData = await mlApi.listTemplates(Number(form.report_type_id));
        setTemplates(templatesData);

        if (!settings.rememberLastMlTemplate) {
          return;
        }

        const rememberedTemplateId = settings.lastMlTemplateId;

        if (!rememberedTemplateId) {
          return;
        }

        const matchingTemplate = templatesData.find(
          (template) => String(template.id) === rememberedTemplateId,
        );

        if (matchingTemplate) {
          setForm((prev) => ({
            ...prev,
            ml_template_id: prev.ml_template_id || rememberedTemplateId,
          }));
        }
      } catch {
        setTemplates([]);
      } finally {
        setIsTemplatesLoading(false);
      }
    })();
  }, [form.report_type_id, settings.lastMlTemplateId, settings.rememberLastMlTemplate]);

  const selectedProject = useMemo(
    () => projects.find((item) => item.id === Number(form.project_id)) ?? null,
    [projects, form.project_id],
  );

  const selectedReportType = useMemo(
    () => reportTypes.find((item) => item.id === Number(form.report_type_id)) ?? null,
    [reportTypes, form.report_type_id],
  );

  const updateField = (key: keyof CreateReportFormState, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const validateForm = () => {
    if (!user) {
      return 'Пользователь не авторизован.';
    }

    if (!form.project_id) {
      return 'Сначала выбери проект.';
    }

    if (!form.report_type_id) {
      return 'Выбери тип отчетности.';
    }

    if (!form.title.trim()) {
      return 'Укажи название отчета.';
    }

    if (!form.report_period_start || !form.report_period_end) {
      return 'Укажи период отчета.';
    }

    if (form.report_period_start > form.report_period_end) {
      return 'Дата начала периода не может быть позже даты окончания.';
    }

    return '';
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError('');
    setSuccessMessage('');

    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    try {
      setIsSubmitting(true);

      const createdReport = await reportsApi.create({
        project_id: Number(form.project_id),
        report_type_id: Number(form.report_type_id),
        title: form.title.trim(),
        description: form.description.trim() || null,
        report_period_start: form.report_period_start,
        report_period_end: form.report_period_end,
        creator_id: user!.id,
        ml_template_id: form.ml_template_id ? Number(form.ml_template_id) : null,
      });

      if (settings.rememberLastMlTemplate) {
        saveLastMlTemplateId(form.ml_template_id || null);
      } else {
        saveLastMlTemplateId(null);
      }

      setSuccessMessage(`Отчет №${createdReport.id} успешно создан.`);
      setTimeout(() => {
        navigate(`/reports/${createdReport.id}/upload`);
      }, 700);
    } catch {
      setError('Не удалось создать отчет. Проверь введенные данные и права доступа.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isBootLoading) {
    return (
      <ContentCard
        header={
          <div className="section-header">
            <h2 className="section-title">Создание отчета</h2>
          </div>
        }
      >
        <div className="py-5 text-center">
          <Spinner animation="border" />
        </div>
      </ContentCard>
    );
  }

  return (
    <ContentCard
      header={
        <div className="section-header">
          <h2 className="section-title">Создание отчета</h2>
        </div>
      }
    >
      <div className="form-shell">
        {error ? <Alert variant="danger">{error}</Alert> : null}
        {successMessage ? <Alert variant="success">{successMessage}</Alert> : null}

        {activeProjectId == null ? (
          <Alert variant="warning">
            Сначала выбери проект. Создание отчета выполняется в контексте активного проекта.
          </Alert>
        ) : null}

        <Form onSubmit={handleSubmit}>
          <Row className="g-3">
            <Col md={6}>
              <Form.Group>
                <Form.Label>Проект</Form.Label>
                <Form.Select
                  value={form.project_id}
                  onChange={(e) => updateField('project_id', e.target.value)}
                  className="soft-input"
                  disabled={activeProjectId != null}
                >
                  <option value="">Выбрать проект</option>
                  {projects
                    .filter((item) => !item.is_archived)
                    .map((project) => (
                      <option key={project.id} value={project.id}>
                        {project.name} ({project.code})
                      </option>
                    ))}
                </Form.Select>
              </Form.Group>
            </Col>

            <Col md={6}>
              <Form.Group>
                <Form.Label>Тип отчетности</Form.Label>
                <Form.Select
                  value={form.report_type_id}
                  onChange={(e) => updateField('report_type_id', e.target.value)}
                  className="soft-input"
                >
                  <option value="">Выбрать тип</option>
                  {reportTypes.map((reportType) => (
                    <option key={reportType.id} value={reportType.id}>
                      {reportType.name}
                    </option>
                  ))}
                </Form.Select>
              </Form.Group>
            </Col>

            <Col md={12}>
              <Form.Group>
                <Form.Label>Название отчета</Form.Label>
                <Form.Control
                  value={form.title}
                  onChange={(e) => updateField('title', e.target.value)}
                  placeholder="Например: Ежемесячный финансовый отчет"
                  className="soft-input"
                />
              </Form.Group>
            </Col>

            <Col md={12}>
              <Form.Group>
                <Form.Label>Описание</Form.Label>
                <Form.Control
                  as="textarea"
                  rows={4}
                  value={form.description}
                  onChange={(e) => updateField('description', e.target.value)}
                  placeholder="Краткое описание содержания отчета"
                  className="soft-input soft-textarea"
                />
              </Form.Group>
            </Col>

            <Col md={6}>
              <Form.Group>
                <Form.Label>Период начала</Form.Label>
                <Form.Control
                  type="date"
                  value={form.report_period_start}
                  onChange={(e) => updateField('report_period_start', e.target.value)}
                  className="soft-input"
                />
              </Form.Group>
            </Col>

            <Col md={6}>
              <Form.Group>
                <Form.Label>Период окончания</Form.Label>
                <Form.Control
                  type="date"
                  value={form.report_period_end}
                  onChange={(e) => updateField('report_period_end', e.target.value)}
                  className="soft-input"
                />
              </Form.Group>
            </Col>

            <Col md={12}>
              <Form.Group>
                <Form.Label>ML-шаблон</Form.Label>
                <Form.Select
                  value={form.ml_template_id}
                  onChange={(e) => updateField('ml_template_id', e.target.value)}
                  className="soft-input"
                  disabled={!form.report_type_id || isTemplatesLoading}
                >
                  <option value="">
                    {!form.report_type_id
                      ? 'Сначала выбери тип отчетности'
                      : isTemplatesLoading
                        ? 'Загрузка шаблонов...'
                        : 'Без шаблона'}
                  </option>
                  {templates.map((template) => (
                    <option key={template.id} value={template.id}>
                      {template.name} ({template.version})
                      {template.is_default ? ' • по умолчанию' : ''}
                    </option>
                  ))}
                </Form.Select>
              </Form.Group>
            </Col>
          </Row>

          <div className="form-meta-grid">
            <div className="form-meta-card">
              <div className="form-meta-label">Выбранный проект</div>
              <div className="form-meta-value">
                {selectedProject ? `${selectedProject.name} (${selectedProject.code})` : '-'}
              </div>
            </div>

            <div className="form-meta-card">
              <div className="form-meta-label">Тип отчетности</div>
              <div className="form-meta-value">
                {selectedReportType ? selectedReportType.name : '-'}
              </div>
            </div>

            <div className="form-meta-card">
              <div className="form-meta-label">Создатель</div>
              <div className="form-meta-value">{user?.full_name ?? '-'}</div>
            </div>
          </div>

          <div className="action-dock action-dock-inline">
            <Button
              type="button"
              variant="light"
              className="secondary-pill-button"
              onClick={() => navigate('/reports')}
            >
              Отмена
            </Button>

            <Button
              type="submit"
              className="primary-pill-button"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Создаем...' : 'Создать отчет'}
            </Button>
          </div>
        </Form>
      </div>
    </ContentCard>
  );
}