import { useEffect, useMemo, useState, type ChangeEvent, type FormEvent } from 'react';
import { Alert, Button, Col, Form, Row, Spinner } from 'react-bootstrap';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthProvider';
import { mlApi } from '../../shared/api/ml';
import { processingApi } from '../../shared/api/processing';
import { projectsApi } from '../../shared/api/projects';
import { reportTypesApi } from '../../shared/api/reportTypes';
import { reportsApi } from '../../shared/api/reports';
import { readUserSettings, saveLastMlTemplateId } from '../../shared/lib/userSettings';
import type { ProjectMember } from '../../shared/types/project';
import type { ReportDetail } from '../../shared/types/report';
import type { ReportType } from '../../shared/types/report-type';
import type { MlTemplate } from '../../shared/types/template';
import { ContentCard } from '../../shared/ui/ContentCard';

interface EditReportFormState {
  report_type_id: string;
  title: string;
  description: string;
  report_period_start: string;
  report_period_end: string;
  current_assignee_id: string;
  approver_id: string;
  ml_template_id: string;
  version: string;
  last_comment: string;
}

const initialForm: EditReportFormState = {
  report_type_id: '',
  title: '',
  description: '',
  report_period_start: '',
  report_period_end: '',
  current_assignee_id: '',
  approver_id: '',
  ml_template_id: '',
  version: '1',
  last_comment: '',
};

function normalizeDate(value?: string | null) {
  if (!value) return '';
  return value.slice(0, 10);
}

export default function EditReportPage() {
  const { reportId } = useParams<{ reportId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const settings = readUserSettings();

  const numericReportId = Number(reportId);

  const [report, setReport] = useState<ReportDetail | null>(null);
  const [form, setForm] = useState<EditReportFormState>(initialForm);

  const [reportTypes, setReportTypes] = useState<ReportType[]>([]);
  const [projectMembers, setProjectMembers] = useState<ProjectMember[]>([]);
  const [templates, setTemplates] = useState<MlTemplate[]>([]);

  const [reprocessFile, setReprocessFile] = useState<File | null>(null);
  const [reprocessComment, setReprocessComment] = useState('');
  const [reprocessPriority, setReprocessPriority] = useState<string>(
    settings.defaultProcessingPriority,
  );

  const [isLoading, setIsLoading] = useState(true);
  const [isTemplatesLoading, setIsTemplatesLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isRelaunching, setIsRelaunching] = useState(false);

  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const approvedMembers = useMemo(
    () => projectMembers.filter((member) => member.access_status === 'approved'),
    [projectMembers],
  );

  const approverCandidates = useMemo(
    () =>
      approvedMembers.filter(
        (member) => member.member_role === 'owner' || member.member_role === 'manager',
      ),
    [approvedMembers],
  );

  const canRelaunchProcessing = report?.status === 'rework' || report?.status === 'failed';

  useEffect(() => {
    (async () => {
      if (!reportId || Number.isNaN(numericReportId)) {
        setError('Некорректный идентификатор отчета.');
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setError('');

        const reportData = await reportsApi.getById(numericReportId);
        const [reportTypesData, membersData] = await Promise.all([
          reportTypesApi.list(),
          projectsApi.listMembers(reportData.project_id),
        ]);

        setReport(reportData);
        setReportTypes(reportTypesData.filter((item) => item.is_active));
        setProjectMembers(membersData);

        setForm({
          report_type_id: String(reportData.report_type_id),
          title: reportData.title,
          description: reportData.description ?? '',
          report_period_start: normalizeDate(reportData.report_period_start),
          report_period_end: normalizeDate(reportData.report_period_end),
          current_assignee_id: reportData.current_assignee_id
            ? String(reportData.current_assignee_id)
            : '',
          approver_id: reportData.approver_id ? String(reportData.approver_id) : '',
          ml_template_id: reportData.ml_template_id ? String(reportData.ml_template_id) : '',
          version: String(reportData.version),
          last_comment: reportData.last_comment ?? '',
        });
      } catch {
        setError('Не удалось загрузить данные отчета для редактирования.');
      } finally {
        setIsLoading(false);
      }
    })();
  }, [reportId, numericReportId]);

  useEffect(() => {
    if (!form.report_type_id) {
      setTemplates([]);
      return;
    }

    (async () => {
      try {
        setIsTemplatesLoading(true);
        const templatesData = await mlApi.listTemplates(Number(form.report_type_id));
        setTemplates(templatesData);

        if (!settings.rememberLastMlTemplate || form.ml_template_id) {
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
          setForm((prev) => ({ ...prev, ml_template_id: rememberedTemplateId }));
        }
      } catch {
        setTemplates([]);
      } finally {
        setIsTemplatesLoading(false);
      }
    })();
  }, [
    form.ml_template_id,
    form.report_type_id,
    settings.lastMlTemplateId,
    settings.rememberLastMlTemplate,
  ]);

  const updateField = (key: keyof EditReportFormState, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleReprocessFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const nextFile = event.currentTarget.files?.[0] ?? null;
    setReprocessFile(nextFile);
  };

  const validateForm = () => {
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

    if (!form.version || Number(form.version) < 1) {
      return 'Версия отчета должна быть не меньше 1.';
    }

    return '';
  };

  const persistReportChanges = async () => {
    if (!report) {
      setError('Отчет не найден.');
      return null;
    }

    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return null;
    }

    const updated = await reportsApi.update(report.id, {
      report_type_id: Number(form.report_type_id),
      title: form.title.trim(),
      description: form.description.trim() || null,
      report_period_start: form.report_period_start,
      report_period_end: form.report_period_end,
      current_assignee_id: form.current_assignee_id ? Number(form.current_assignee_id) : null,
      approver_id: form.approver_id ? Number(form.approver_id) : null,
      ml_template_id: form.ml_template_id ? Number(form.ml_template_id) : null,
      version: Number(form.version),
      last_comment: form.last_comment.trim() || null,
    });

    setReport(updated);

    if (settings.rememberLastMlTemplate) {
      saveLastMlTemplateId(updated.ml_template_id ? String(updated.ml_template_id) : null);
    } else {
      saveLastMlTemplateId(null);
    }

    return updated;
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    setSuccessMessage('');

    try {
      setIsSubmitting(true);

      const updated = await persistReportChanges();
      if (!updated) {
        return;
      }

      setSuccessMessage('Изменения отчета успешно сохранены.');

      setTimeout(() => {
        navigate(`/reports/${updated.id}/result`);
      }, 700);
    } catch {
      setError('Не удалось сохранить изменения отчета.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSaveAndRelaunch = async () => {
    setError('');
    setSuccessMessage('');

    if (!report || !user) {
      setError('Не удалось определить отчет или пользователя.');
      return;
    }

    if (!canRelaunchProcessing) {
      setError('Повторная загрузка доступна только для отчетов на доработке или с ошибкой.');
      return;
    }

    if (!reprocessFile) {
      setError('Сначала выбери новый файл для повторной обработки.');
      return;
    }

    try {
      setIsRelaunching(true);

      const updated = await persistReportChanges();
      if (!updated) {
        return;
      }

      const upload = await reportsApi.uploadFile(
        updated.id,
        reprocessFile,
        reprocessComment.trim() || undefined,
        );

      const task = await processingApi.launchTask({
        report_id: updated.id,
        report_upload_id: upload.id,
        ml_template_id: updated.ml_template_id ?? null,
        created_by: user.id,
        priority: Number(reprocessPriority),
        params_json: {},
      });

      navigate(`/tasks/${task.id}`);
    } catch {
      setError('Не удалось сохранить изменения, загрузить файл и перезапустить обработку.');
    } finally {
      setIsRelaunching(false);
    }
  };

  if (isLoading) {
    return (
      <ContentCard
        header={
          <div className="toolbar-row">
            <div className="toolbar-left">
              <h2 className="section-title mb-0">Редактирование отчета</h2>
            </div>
          </div>
        }
      >
        <div className="py-5 text-center">
          <Spinner animation="border" />
        </div>
      </ContentCard>
    );
  }

  if (!report) {
    return (
      <ContentCard
        header={
          <div className="toolbar-row">
            <div className="toolbar-left">
              <h2 className="section-title mb-0">Редактирование отчета</h2>
            </div>
          </div>
        }
      >
        <Alert variant="danger" className="mb-0">
          {error || 'Отчет не найден.'}
        </Alert>
      </ContentCard>
    );
  }

  return (
    <ContentCard
      header={
        <div className="toolbar-row">
          <div className="toolbar-left">
            <h2 className="section-title mb-0">Редактирование отчета</h2>
          </div>

          <div className="toolbar-actions">
            <Button
              className="secondary-pill-button"
              onClick={() => navigate(`/reports/${report.id}/result`)}
            >
              Назад
            </Button>
          </div>
        </div>
      }
    >
      <div className="form-shell">
        {error ? <Alert variant="danger">{error}</Alert> : null}
        {successMessage ? <Alert variant="success">{successMessage}</Alert> : null}

        <div className="form-meta-grid mb-4">
          <div className="form-meta-card">
            <div className="form-meta-label">ID отчета</div>
            <div className="form-meta-value">{report.id}</div>
          </div>

          <div className="form-meta-card">
            <div className="form-meta-label">Проект</div>
            <div className="form-meta-value">{report.project_id}</div>
          </div>

          <div className="form-meta-card">
            <div className="form-meta-label">Текущий статус</div>
            <div className="form-meta-value">{report.status}</div>
          </div>
        </div>

        <Form onSubmit={handleSubmit}>
          <Row className="g-3">
            <Col md={6}>
              <Form.Group>
                <Form.Label>Тип отчетности</Form.Label>
                <Form.Select
                  value={form.report_type_id}
                  onChange={(event) => {
                    updateField('report_type_id', event.target.value);
                    updateField('ml_template_id', '');
                  }}
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

            <Col md={6}>
              <Form.Group>
                <Form.Label>ML-шаблон</Form.Label>
                <Form.Select
                  value={form.ml_template_id}
                  onChange={(event) => updateField('ml_template_id', event.target.value)}
                  className="soft-input"
                  disabled={!form.report_type_id || isTemplatesLoading}
                >
                  <option value="">
                    {isTemplatesLoading ? 'Загрузка шаблонов...' : 'Без шаблона'}
                  </option>
                  {templates.map((template) => (
                    <option key={template.id} value={template.id}>
                      {template.name}
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
                  onChange={(event) => updateField('title', event.target.value)}
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
                  onChange={(event) => updateField('description', event.target.value)}
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
                  onChange={(event) => updateField('report_period_start', event.target.value)}
                  className="soft-input"
                />
              </Form.Group>
            </Col>

            <Col md={6}>
              <Form.Group>
                <Form.Label>Период конца</Form.Label>
                <Form.Control
                  type="date"
                  value={form.report_period_end}
                  onChange={(event) => updateField('report_period_end', event.target.value)}
                  className="soft-input"
                />
              </Form.Group>
            </Col>

            <Col md={6}>
              <Form.Group>
                <Form.Label>Назначить на рассмотрение</Form.Label>
                <Form.Select
                  value={form.current_assignee_id}
                  onChange={(event) => updateField('current_assignee_id', event.target.value)}
                  className="soft-input"
                >
                  <option value="">Не назначено</option>
                  {approvedMembers.map((member) => (
                    <option key={member.id} value={member.user_id}>
                      {member.user.full_name}
                    </option>
                  ))}
                </Form.Select>
              </Form.Group>
            </Col>

            <Col md={6}>
              <Form.Group>
                <Form.Label>Утверждающий</Form.Label>
                <Form.Select
                  value={form.approver_id}
                  onChange={(event) => updateField('approver_id', event.target.value)}
                  className="soft-input"
                >
                  <option value="">Не назначен</option>
                  {approverCandidates.map((member) => (
                    <option key={member.id} value={member.user_id}>
                      {member.user.full_name}
                    </option>
                  ))}
                </Form.Select>
              </Form.Group>
            </Col>

            <Col md={4}>
              <Form.Group>
                <Form.Label>Версия</Form.Label>
                <Form.Control
                  type="number"
                  min={1}
                  value={form.version}
                  onChange={(event) => updateField('version', event.target.value)}
                  className="soft-input"
                />
              </Form.Group>
            </Col>

            <Col md={8}>
              <Form.Group>
                <Form.Label>Последний комментарий</Form.Label>
                <Form.Control
                  value={form.last_comment}
                  onChange={(event) => updateField('last_comment', event.target.value)}
                  className="soft-input"
                  placeholder="Комментарий к изменению отчета"
                />
              </Form.Group>
            </Col>
          </Row>

          {canRelaunchProcessing ? (
            <div className="form-meta-card mt-4">
              <div className="form-meta-label">Повторная загрузка и обработка</div>

              <div className="archive-warning-text mb-3">
                Для отчётов со статусом <strong>на доработке</strong> или <strong>ошибка</strong>
                можно сохранить изменения, загрузить новый файл и сразу запустить повторную
                обработку.
              </div>

              <Row className="g-3">
                <Col md={12}>
                  <Form.Group>
                    <Form.Label>Файл отчета</Form.Label>
                    <Form.Control
                      type="file"
                      accept=".xlsx,.xls,.csv"
                      onChange={handleReprocessFileChange}
                      className="soft-input"
                    />
                  </Form.Group>
                </Col>

                <Col md={8}>
                  <Form.Group>
                    <Form.Label>Комментарий к загрузке</Form.Label>
                    <Form.Control
                      value={reprocessComment}
                      onChange={(event) => setReprocessComment(event.target.value)}
                      className="soft-input"
                      placeholder="Например: загружена исправленная версия файла"
                    />
                  </Form.Group>
                </Col>

                <Col md={4}>
                  <Form.Group>
                    <Form.Label>Приоритет</Form.Label>
                    <Form.Select
                      value={reprocessPriority}
                      onChange={(event) => setReprocessPriority(event.target.value)}
                      className="soft-input"
                    >
                      <option value="1">1 — низкий</option>
                      <option value="3">3 — обычный</option>
                      <option value="5">5 — повышенный</option>
                    </Form.Select>
                  </Form.Group>
                </Col>
              </Row>

              <div className="form-actions-row mt-4">
                <Button
                  type="button"
                  className="primary-pill-button"
                  onClick={() => void handleSaveAndRelaunch()}
                  disabled={isRelaunching}
                >
                  {isRelaunching
                    ? 'Сохранение и запуск...'
                    : 'Сохранить, загрузить и запустить заново'}
                </Button>
              </div>
            </div>
          ) : null}

          <div className="form-actions-row mt-4">
            <Button
              type="button"
              className="secondary-pill-button"
              onClick={() => navigate(`/reports/${report.id}/result`)}
            >
              Отмена
            </Button>

            <Button type="submit" className="primary-pill-button" disabled={isSubmitting}>
              {isSubmitting ? 'Сохранение...' : 'Сохранить изменения'}
            </Button>
          </div>
        </Form>
      </div>
    </ContentCard>
  );
}