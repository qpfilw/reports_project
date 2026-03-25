import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type FormEvent,
} from 'react';
import { Alert, Button, Col, Form, Modal, Row, Spinner, Table } from 'react-bootstrap';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthProvider';
import { exportsApi } from '../../shared/api/exports';
import { processingApi } from '../../shared/api/processing';
import { projectsApi } from '../../shared/api/projects';
import { reportsApi } from '../../shared/api/reports';
import { resultsApi } from '../../shared/api/results';
import {
  getReportStatusClassName,
  getReportStatusLabel,
} from '../../shared/lib/reportStatus';
import type { ExportArtifactDetail, ExportFormat } from '../../shared/types/export';
import type { ProcessingTaskDetail } from '../../shared/types/processing';
import {
  getProjectRoleLabel,
  type ProjectMember,
} from '../../shared/types/project';
import type {
  ReportDetail,
  ReportStatus,
} from '../../shared/types/report';
import type { NormalizedDataset, NormalizedDatasetDetail } from '../../shared/types/result';
import { ContentCard } from '../../shared/ui/ContentCard';

type WorkflowActionType =
  | 'submit-review'
  | 'submit-approval'
  | 'approve'
  | 'reject'
  | 'rework';

const WORKFLOW_ACTION_META: Record<
  WorkflowActionType,
  {
    title: string;
    buttonLabel: string;
    placeholder: string;
    commentRequired: boolean;
    successMessage: string;
  }
> = {
  'submit-review': {
    title: 'Отправка на рассмотрение',
    buttonLabel: 'Отправить на рассмотрение',
    placeholder: 'Комментарий для менеджера',
    commentRequired: false,
    successMessage: 'Отчёт отправлен на рассмотрение.',
  },
  'submit-approval': {
    title: 'Передача на утверждение',
    buttonLabel: 'Передать на утверждение',
    placeholder: 'Комментарий к этапу утверждения',
    commentRequired: false,
    successMessage: 'Отчёт передан на утверждение.',
  },
  approve: {
    title: 'Утверждение отчёта',
    buttonLabel: 'Утвердить',
    placeholder: 'Комментарий к утверждению',
    commentRequired: false,
    successMessage: 'Отчёт утверждён.',
  },
  reject: {
    title: 'Отклонение отчёта',
    buttonLabel: 'Отклонить',
    placeholder: 'Укажи причину отклонения',
    commentRequired: true,
    successMessage: 'Отчёт отклонён.',
  },
  rework: {
    title: 'Возврат в доработку',
    buttonLabel: 'Вернуть в доработку',
    placeholder: 'Укажи комментарий по доработке',
    commentRequired: true,
    successMessage: 'Отчёт возвращён в доработку.',
  },
};

function formatDateTime(value?: string | null) {
  if (!value) return '-';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('ru-RU');
}

function formatBytes(value: number) {
  if (value < 1024) return `${value} Б`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} КБ`;
  return `${(value / (1024 * 1024)).toFixed(2)} МБ`;
}

function getAvailableWorkflowActions(
  status: ReportStatus,
  canOperateFlow: boolean,
  canManageApprovalFlow: boolean,
): WorkflowActionType[] {
  const actions: WorkflowActionType[] = [];

  if ((status === 'processed' || status === 'rework') && canOperateFlow) {
    actions.push('submit-review');
  }

  if (status === 'on_review' && canManageApprovalFlow) {
    actions.push('submit-approval');
  }

  if (status === 'on_approval' && canManageApprovalFlow) {
    actions.push('approve');
  }

  if ((status === 'on_review' || status === 'on_approval') && canManageApprovalFlow) {
    actions.push('reject');
  }

  if ((status === 'rejected' || status === 'failed') && canOperateFlow) {
    actions.push('rework');
  }

  return actions;
}

export default function ReportResultPage() {
  const { reportId } = useParams<{ reportId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const numericReportId = Number(reportId);

  const [report, setReport] = useState<ReportDetail | null>(null);
  const [taskDetail, setTaskDetail] = useState<ProcessingTaskDetail | null>(null);
  const [resultDetail, setResultDetail] = useState<NormalizedDatasetDetail | null>(null);
  const [exports, setExports] = useState<ExportArtifactDetail[]>([]);
  const [projectMembers, setProjectMembers] = useState<ProjectMember[]>([]);

  const [isLoading, setIsLoading] = useState(true);
  const [isExportLoading, setIsExportLoading] = useState(false);
  const [isWorkflowSubmitting, setIsWorkflowSubmitting] = useState(false);

  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const [showWorkflowModal, setShowWorkflowModal] = useState(false);
  const [workflowAction, setWorkflowAction] = useState<WorkflowActionType | null>(null);
  const [workflowComment, setWorkflowComment] = useState('');

  const previewColumns = useMemo(() => {
    if (!resultDetail?.preview_json?.length) {
      return [];
    }

    return Array.from(
      new Set(resultDetail.preview_json.flatMap((row) => Object.keys(row))),
    );
  }, [resultDetail]);

  const currentMembership = useMemo(() => {
    if (!user) {
      return null;
    }

    return (
      projectMembers.find(
        (member) =>
          member.user_id === user.id && member.access_status === 'approved',
      ) ?? null
    );
  }, [projectMembers, user]);

  const canManageApprovalFlow = useMemo(() => {
    const memberRole = currentMembership?.member_role;

    return (
      user?.role.code === 'admin' ||
      user?.role.code === 'manager' ||
      memberRole === 'owner' ||
      memberRole === 'manager'
    );
  }, [currentMembership, user]);

  const canOperateFlow = useMemo(() => {
    const memberRole = currentMembership?.member_role;

    return (
      canManageApprovalFlow ||
      user?.role.code === 'operator' ||
      memberRole === 'editor'
    );
  }, [canManageApprovalFlow, currentMembership, user]);

  const availableWorkflowActions = useMemo(() => {
    if (!report) {
      return [];
    }

    return getAvailableWorkflowActions(
      report.status,
      canOperateFlow,
      canManageApprovalFlow,
    );
  }, [report, canOperateFlow, canManageApprovalFlow]);

  const workflowCandidates = useMemo(() => {
    return projectMembers.filter(
      (member) =>
        member.access_status === 'approved' &&
        (member.member_role === 'owner' || member.member_role === 'manager'),
    );
  }, [projectMembers]);

  const loadPageData = useCallback(async () => {
    if (!reportId || Number.isNaN(numericReportId)) {
      setError('Некорректный идентификатор отчета.');
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError('');

      const reportData = await reportsApi.getById(numericReportId);

      const [tasks, results, exportList, membersData] = await Promise.all([
        processingApi.listTasks(),
        resultsApi.list(),
        exportsApi.list(),
        projectsApi.listMembers(reportData.project_id),
      ]);

      setReport(reportData);
      setProjectMembers(membersData);

      const latestTask = [...tasks]
        .filter((item) => item.report_id === numericReportId)
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())[0];

      const latestResult: NormalizedDataset | undefined = [...results]
        .filter((item) => item.report_id === numericReportId)
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())[0];

      if (latestTask) {
        const fullTask = await processingApi.getTask(latestTask.id);
        setTaskDetail(fullTask);
      } else {
        setTaskDetail(null);
      }

      if (latestResult) {
        const fullResult = await resultsApi.getById(latestResult.id);
        setResultDetail(fullResult);
      } else {
        setResultDetail(null);
      }

      const relatedExports = exportList
        .filter(
          (item) =>
            item.report_id === numericReportId ||
            (latestTask ? item.processing_task_id === latestTask.id : false),
        )
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

      setExports(relatedExports as ExportArtifactDetail[]);
    } catch {
      setError('Не удалось загрузить результат обработки.');
    } finally {
      setIsLoading(false);
    }
  }, [reportId, numericReportId]);

  useEffect(() => {
    void loadPageData();
  }, [loadPageData]);

  const handleRunExport = async (format: ExportFormat) => {
    if (!taskDetail || !report) {
      setError('Невозможно выполнить экспорт: задача обработки не найдена.');
      return;
    }

    try {
      setIsExportLoading(true);
      setError('');
      const createdExport = await exportsApi.run({
        processing_task_id: taskDetail.id,
        report_id: report.id,
        format,
      });

      setExports((prev) => [createdExport, ...prev]);
    } catch {
      setError('Не удалось сформировать экспорт.');
    } finally {
      setIsExportLoading(false);
    }
  };

  const handleDownload = async (exportId: number, format: ExportFormat) => {
    try {
      const blob = await exportsApi.download(exportId);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `report-export-${exportId}.${format}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      setError('Не удалось скачать экспортный файл.');
    }
  };

  const openWorkflowModal = (action: WorkflowActionType) => {
    setWorkflowAction(action);
    setWorkflowComment('');
    setError('');
    setSuccessMessage('');

    if (action === 'submit-review') {
      setWorkflowTargetUserId(
        report?.current_assignee?.id != null
          ? String(report.current_assignee.id)
          : workflowCandidates[0]?.user_id != null
            ? String(workflowCandidates[0].user_id)
            : '',
      );
    } else if (action === 'submit-approval') {
      setWorkflowTargetUserId(
        report?.approver?.id != null
          ? String(report.approver.id)
          : workflowCandidates[0]?.user_id != null
            ? String(workflowCandidates[0].user_id)
            : '',
      );
    } else {
      setWorkflowTargetUserId('');
    }

    setShowWorkflowModal(true);
  };

  const [workflowTargetUserId, setWorkflowTargetUserId] = useState('');

  const handleWorkflowSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!report || !workflowAction) {
      return;
    }

    const actionMeta = WORKFLOW_ACTION_META[workflowAction];
    const trimmedComment = workflowComment.trim();

    if (actionMeta.commentRequired && !trimmedComment) {
      setError('Для этого действия необходимо указать комментарий.');
      return;
    }

    if (
      (workflowAction === 'submit-review' || workflowAction === 'submit-approval') &&
      !workflowTargetUserId
    ) {
      setError('Необходимо выбрать ответственного пользователя.');
      return;
    }

    try {
      setIsWorkflowSubmitting(true);
      setError('');
      setSuccessMessage('');

      switch (workflowAction) {
        case 'submit-review':
          await reportsApi.submitForReview(report.id, {
            last_comment: trimmedComment || null,
            current_assignee_id: Number(workflowTargetUserId),
          });
          break;

        case 'submit-approval':
          await reportsApi.submitForApproval(report.id, {
            last_comment: trimmedComment || null,
            approver_id: Number(workflowTargetUserId),
          });
          break;

        case 'approve':
          await reportsApi.approve(report.id, {
            last_comment: trimmedComment || null,
          });
          break;

        case 'reject':
          await reportsApi.reject(report.id, {
            last_comment: trimmedComment || null,
          });
          break;

        case 'rework':
          await reportsApi.sendToRework(report.id, {
            last_comment: trimmedComment || null,
          });
          break;
      }

      await loadPageData();
      setShowWorkflowModal(false);
      setWorkflowAction(null);
      setWorkflowComment('');
      setWorkflowTargetUserId('');
      setSuccessMessage(actionMeta.successMessage);
    } catch {
      setError('Не удалось выполнить действие по согласованию отчёта.');
    } finally {
      setIsWorkflowSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <ContentCard
        header={
          <div className="section-header">
            <h2 className="section-title">Результат обработки</h2>
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
          <div className="section-header">
            <h2 className="section-title">Результат обработки</h2>
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
    <>
      <ContentCard
        header={
          <div className="toolbar-row">
            <div className="toolbar-left">
              <h2 className="section-title mb-0">Результат обработки</h2>
            </div>

            <div className="toolbar-actions">
              <Button className="secondary-pill-button" onClick={() => navigate('/reports')}>
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
              <div className="form-meta-label">Название отчета</div>
              <div className="form-meta-value">{report.title}</div>
            </div>

            <div className="form-meta-card">
              <div className="form-meta-label">Статус</div>
              <div className="form-meta-value">
                <span className={getReportStatusClassName(report.status)}>
                  {getReportStatusLabel(report.status)}
                </span>
              </div>
            </div>

            <div className="form-meta-card">
              <div className="form-meta-label">Период</div>
              <div className="form-meta-value">
                {report.report_period_start} - {report.report_period_end}
              </div>
            </div>
          </div>

          <div className="form-meta-card mb-4">
            <div className="toolbar-row">
              <div className="toolbar-left">
                <div className="form-meta-label mb-0">Согласование отчёта</div>
              </div>

              <div className="workflow-action-group">
                {availableWorkflowActions.map((action) => (
                  <Button
                    key={action}
                    className={
                      action === 'approve'
                        ? 'primary-pill-button workflow-action-button'
                        : 'secondary-pill-button workflow-action-button'
                    }
                    onClick={() => openWorkflowModal(action)}
                  >
                    {WORKFLOW_ACTION_META[action].buttonLabel}
                  </Button>
                ))}
              </div>
            </div>

            <Row className="g-4 mt-1">
              <Col lg={6}>
                <div className="workflow-meta-grid">
                  <div>
                    <div className="form-meta-label">Создатель</div>
                    <div className="form-meta-value">{report.creator.full_name}</div>
                  </div>
                  <div>
                    <div className="form-meta-label">Тип отчётности</div>
                    <div className="form-meta-value">{report.report_type.name}</div>
                  </div>
                  <div>
                    <div className="form-meta-label">Назначено на рассмотрение</div>
                    <div className="form-meta-value">
                      {report.current_assignee?.full_name ?? '-'}
                    </div>
                  </div>
                  <div>
                    <div className="form-meta-label">Утверждающий</div>
                    <div className="form-meta-value">
                      {report.approver?.full_name ?? '-'}
                    </div>
                  </div>
                </div>
              </Col>

              <Col lg={6}>
                <div className="workflow-meta-grid">
                  <div>
                    <div className="form-meta-label">Отправлено</div>
                    <div className="form-meta-value">{formatDateTime(report.submitted_at)}</div>
                  </div>
                  <div>
                    <div className="form-meta-label">Утверждено</div>
                    <div className="form-meta-value">{formatDateTime(report.approved_at)}</div>
                  </div>
                  <div>
                    <div className="form-meta-label">Отклонено</div>
                    <div className="form-meta-value">{formatDateTime(report.rejected_at)}</div>
                  </div>
                  <div>
                    <div className="form-meta-label">ML-шаблон</div>
                    <div className="form-meta-value">{report.ml_template?.name ?? '-'}</div>
                  </div>
                </div>
              </Col>
            </Row>

            <div className="report-workflow-note">
              <strong>Последний комментарий:</strong>{' '}
              {report.last_comment ?? 'Комментарий отсутствует.'}
            </div>

            {availableWorkflowActions.length === 0 ? (
              <div className="report-workflow-note">
                Для текущего статуса и твоих прав действий согласования сейчас нет.
              </div>
            ) : null}
          </div>

          <Row className="g-4 mb-4">
            <Col lg={6}>
              <div className="form-meta-card h-100">
                <div className="form-meta-label">Информация об обработке</div>

                <div className="result-info-list">
                  <div><strong>ID задачи:</strong> {taskDetail?.id ?? '-'}</div>
                  <div><strong>Статус задачи:</strong> {taskDetail?.status ?? '-'}</div>
                  <div><strong>Прогресс:</strong> {taskDetail?.progress ?? 0}%</div>
                  <div>
                    <strong>Качество:</strong>{' '}
                    {taskDetail?.quality_score != null
                      ? `${Math.round(taskDetail.quality_score * 100)}%`
                      : '-'}
                  </div>
                  <div><strong>Предупреждений:</strong> {taskDetail?.warning_count ?? 0}</div>
                  <div><strong>Ошибок:</strong> {taskDetail?.error_count ?? 0}</div>
                  <div><strong>Запущено:</strong> {formatDateTime(taskDetail?.started_at)}</div>
                  <div><strong>Завершено:</strong> {formatDateTime(taskDetail?.finished_at)}</div>
                </div>
              </div>
            </Col>

            <Col lg={6}>
              <div className="form-meta-card h-100">
                <div className="form-meta-label">Итог нормализации</div>

                <div className="result-info-list">
                  <div><strong>ID результата:</strong> {resultDetail?.id ?? '-'}</div>
                  <div><strong>Количество строк:</strong> {resultDetail?.rows_count ?? '-'}</div>
                  <div><strong>Дата формирования:</strong> {formatDateTime(resultDetail?.created_at)}</div>
                  <div><strong>Расположение данных:</strong> {resultDetail?.data_location ?? '-'}</div>
                </div>
              </div>
            </Col>
          </Row>

          <div className="form-meta-card mb-4">
            <div className="form-meta-label">Сводка обработки</div>

            {!resultDetail ? (
              <div className="form-meta-value">Нормализованный результат пока отсутствует.</div>
            ) : Object.keys(resultDetail.summary_json ?? {}).length === 0 ? (
              <div className="form-meta-value">Сводные данные отсутствуют.</div>
            ) : (
              <div className="result-summary-grid">
                {Object.entries(resultDetail.summary_json).map(([key, value]) => (
                  <div key={key} className="result-summary-item">
                    <div className="result-summary-key">{key}</div>
                    <div className="result-summary-value">{String(value)}</div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="form-meta-card mb-4">
            <div className="form-meta-label">Предпросмотр нормализованных данных</div>

            {!resultDetail || resultDetail.preview_json.length === 0 ? (
              <div className="form-meta-value">Предпросмотр данных отсутствует.</div>
            ) : (
              <div className="table-wrap">
                <Table borderless responsive className="prototype-table">
                  <thead>
                    <tr>
                      {previewColumns.map((column) => (
                        <th key={column}>{column}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {resultDetail.preview_json.map((row, index) => (
                      <tr key={index}>
                        {previewColumns.map((column) => (
                          <td key={`${index}-${column}`}>{String(row[column] ?? '')}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </div>
            )}
          </div>

          <Row className="g-4 mb-4">
            <Col lg={6}>
              <div className="form-meta-card h-100">
                <div className="form-meta-label">Логи обработки</div>

                                {!taskDetail || taskDetail.logs.length === 0 ? (
                  <div className="form-meta-value">Логи отсутствуют.</div>
                ) : (
                  <div className="task-log-list">
                    {taskDetail.logs.map((log) => (
                      <div key={log.id} className="task-log-item">
                        <div className="task-log-top">
                          <strong>{log.stage}</strong>
                          <span>{formatDateTime(log.created_at)}</span>
                        </div>
                        <div>{log.message}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </Col>

            <Col lg={6}>
              <div className="form-meta-card h-100">
                <div className="form-meta-label">Ошибки обработки</div>

                {!taskDetail || taskDetail.errors.length === 0 ? (
                  <div className="form-meta-value">Ошибки отсутствуют.</div>
                ) : (
                  <div className="task-log-list">
                    {taskDetail.errors.map((item) => (
                      <div key={item.id} className="task-log-item">
                        <div className="task-log-top">
                          <strong>{item.error_code}</strong>
                          <span>{item.error_type}</span>
                        </div>
                        <div>{item.details ?? item.source_value ?? 'Без подробностей'}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </Col>
          </Row>

          <div className="form-meta-card mb-4">
            <div className="toolbar-row">
              <div className="toolbar-left">
                <div className="form-meta-label mb-0">Экспорт результата</div>
              </div>

              <div className="result-export-actions">
                <Button
                  className="secondary-pill-button"
                  disabled={isExportLoading || !taskDetail}
                  onClick={() => handleRunExport('csv')}
                >
                  CSV
                </Button>
                <Button
                  className="secondary-pill-button"
                  disabled={isExportLoading || !taskDetail}
                  onClick={() => handleRunExport('xlsx')}
                >
                  XLSX
                </Button>
                <Button
                  className="secondary-pill-button"
                  disabled={isExportLoading || !taskDetail}
                  onClick={() => handleRunExport('pdf')}
                >
                  PDF
                </Button>
              </div>
            </div>

            {exports.length === 0 ? (
              <div className="form-meta-value mt-3">Экспортные артефакты пока отсутствуют.</div>
            ) : (
              <div className="table-wrap mt-3">
                <Table borderless responsive className="prototype-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Формат</th>
                      <th>Размер</th>
                      <th>Создан</th>
                      <th>Действие</th>
                    </tr>
                  </thead>
                  <tbody>
                    {exports.map((item) => (
                      <tr key={item.id}>
                        <td>{item.id}</td>
                        <td>{item.format.toUpperCase()}</td>
                        <td>{formatBytes(item.file_size)}</td>
                        <td>{formatDateTime(item.created_at)}</td>
                        <td>
                          <Button
                            size="sm"
                            className="primary-pill-button result-download-button"
                            onClick={() => handleDownload(item.id, item.format)}
                          >
                            Скачать
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </div>
            )}
          </div>
        </div>
      </ContentCard>

      <Modal
        show={showWorkflowModal}
        onHide={() => {
          setShowWorkflowModal(false);
          setWorkflowAction(null);
          setWorkflowComment('');
          setWorkflowTargetUserId('');
        }}
        centered
      >
        <Modal.Header closeButton>
          <Modal.Title>
            {workflowAction ? WORKFLOW_ACTION_META[workflowAction].title : 'Действие'}
          </Modal.Title>
        </Modal.Header>

        <Form onSubmit={handleWorkflowSubmit}>
          <Modal.Body>
            {workflowAction && report ? (
              <Row className="g-3">
                <Col md={12}>
                  <div className="workflow-modal-report-name">
                    <strong>Отчёт:</strong> {report.title}
                  </div>
                </Col>

                {workflowAction === 'submit-review' || workflowAction === 'submit-approval' ? (
                  <Col md={12}>
                    <Form.Group>
                      <Form.Label>
                        {workflowAction === 'submit-review'
                          ? 'Назначить на рассмотрение'
                          : 'Назначить утверждающего'}
                      </Form.Label>

                      <Form.Select
                        className="soft-input"
                        value={workflowTargetUserId}
                        onChange={(event) => setWorkflowTargetUserId(event.target.value)}
                      >
                        {workflowCandidates.length === 0 ? (
                          <option value="">Нет доступных пользователей</option>
                        ) : (
                          workflowCandidates.map((member) => (
                            <option key={member.id} value={member.user_id}>
                              {member.user.full_name} - {getProjectRoleLabel(member.member_role)}
                            </option>
                          ))
                        )}
                      </Form.Select>
                    </Form.Group>
                  </Col>
                ) : null}

                <Col md={12}>
                  <Form.Group>
                    <Form.Label>Комментарий</Form.Label>
                    <Form.Control
                      as="textarea"
                      rows={4}
                      className="soft-input soft-textarea"
                      value={workflowComment}
                      onChange={(event) => setWorkflowComment(event.target.value)}
                      placeholder={WORKFLOW_ACTION_META[workflowAction].placeholder}
                    />
                  </Form.Group>
                </Col>

                <Col md={12}>
                  <div className="report-workflow-note mb-0">
                    <strong>Текущий статус:</strong> {getReportStatusLabel(report.status)}
                  </div>
                </Col>
              </Row>
            ) : null}
          </Modal.Body>

          <Modal.Footer>
            <Button
              className="secondary-pill-button"
              onClick={() => {
                setShowWorkflowModal(false);
                setWorkflowAction(null);
                setWorkflowComment('');
                setWorkflowTargetUserId('');
              }}
            >
              Отмена
            </Button>

            <Button
              type="submit"
              className={
                workflowAction === 'approve'
                  ? 'primary-pill-button'
                  : workflowAction === 'reject'
                    ? 'secondary-pill-button approval-danger-button'
                    : 'primary-pill-button'
              }
              disabled={isWorkflowSubmitting || !workflowAction}
            >
              {isWorkflowSubmitting
                ? 'Сохранение...'
                : workflowAction
                  ? WORKFLOW_ACTION_META[workflowAction].buttonLabel
                  : 'Подтвердить'}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>
    </>
  );
}