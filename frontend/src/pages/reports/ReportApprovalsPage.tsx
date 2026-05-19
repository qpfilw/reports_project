import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type FormEvent,
} from 'react';
import { Alert, Button, Form, Modal, Spinner, Table } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthProvider';
import { useProjectContext } from '../../features/projects/ProjectContext';
import { projectsApi } from '../../shared/api/projects';
import { reportsApi } from '../../shared/api/reports';
import {
  getReportStatusClassName,
  getReportStatusLabel,
} from '../../shared/lib/reportStatus';
import type { ProjectMember } from '../../shared/types/project';
import type { Report } from '../../shared/types/report';
import { ContentCard } from '../../shared/ui/ContentCard';

type ApprovalActionType = 'submit-approval' | 'approve' | 'reject';

const APPROVAL_ACTION_META: Record<
  ApprovalActionType,
  {
    title: string;
    buttonLabel: string;
    placeholder: string;
    commentRequired: boolean;
    successMessage: string;
  }
> = {
  'submit-approval': {
    title: 'Передача отчёта на утверждение',
    buttonLabel: 'Передать',
    placeholder: 'Комментарий для этапа утверждения',
    commentRequired: false,
    successMessage: 'Отчёт передан на утверждение.',
  },
  approve: {
    title: 'Утверждение отчёта',
    buttonLabel: 'Утвердить',
    placeholder: 'Комментарий к утверждению',
    commentRequired: false,
    successMessage: 'Отчёт успешно утверждён.',
  },
  reject: {
    title: 'Отклонение отчёта',
    buttonLabel: 'Отклонить',
    placeholder: 'Укажи причину отклонения',
    commentRequired: true,
    successMessage: 'Отчёт отклонён.',
  },
};

function formatDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString('ru-RU');
}

function getMemberDisplayName(userId: number | null, members: ProjectMember[]) {
  if (userId == null) {
    return '—';
  }

  const member = members.find((item) => item.user_id === userId);
  return member?.user.full_name ?? 'Пользователь';
}

export default function ReportApprovalsPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { activeProjectId, activeProject } = useProjectContext();

  const [reports, setReports] = useState<Report[]>([]);
  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'on_review' | 'on_approval'>('all');

  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const [showActionModal, setShowActionModal] = useState(false);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [selectedAction, setSelectedAction] = useState<ApprovalActionType | null>(null);
  const [comment, setComment] = useState('');

  const loadApprovals = useCallback(async () => {
    if (activeProjectId == null) {
      setReports([]);
      setMembers([]);
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError('');

      const [reportsData, membersData] = await Promise.all([
        reportsApi.list(),
        projectsApi.listMembers(activeProjectId),
      ]);

      setReports(reportsData.filter((item) => item.project_id === activeProjectId));
      setMembers(membersData);
    } catch {
      setError('Не удалось загрузить очередь согласования.');
    } finally {
      setIsLoading(false);
    }
  }, [activeProjectId]);

  useEffect(() => {
    void loadApprovals();
  }, [loadApprovals]);

  const currentMembership = useMemo(() => {
    if (!user) {
      return null;
    }

    return (
      members.find(
        (member) =>
          member.user_id === user.id && member.access_status === 'approved',
      ) ?? null
    );
  }, [members, user]);

  const canManageApprovalFlow = useMemo(() => {
    const memberRole = currentMembership?.member_role;

    return (
      user?.role.code === 'admin' ||
      user?.role.code === 'manager' ||
      memberRole === 'owner' ||
      memberRole === 'manager'
    );
  }, [currentMembership, user]);

  const approvalReports = useMemo(() => {
    return reports.filter(
      (report) =>
        report.status === 'on_review' || report.status === 'on_approval',
    );
  }, [reports]);

  const filteredReports = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();

    return approvalReports.filter((report) => {
      const creatorName = getMemberDisplayName(report.creator_id, members).toLowerCase();
      const matchesStatus =
        statusFilter === 'all' ? true : report.status === statusFilter;

      const matchesSearch =
        !normalizedSearch ||
        report.title.toLowerCase().includes(normalizedSearch) ||
        creatorName.includes(normalizedSearch) ||
        (report.last_comment ?? '').toLowerCase().includes(normalizedSearch);

      return matchesStatus && matchesSearch;
    });
  }, [approvalReports, members, search, statusFilter]);

  const openActionModal = (action: ApprovalActionType, report: Report) => {
    setSelectedAction(action);
    setSelectedReport(report);
    setComment('');
    setError('');
    setSuccessMessage('');
    setShowActionModal(true);
  };

  const handleActionSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!selectedAction || !selectedReport) {
      return;
    }

    const actionMeta = APPROVAL_ACTION_META[selectedAction];
    const trimmedComment = comment.trim();

    if (actionMeta.commentRequired && !trimmedComment) {
      setError('Для этого действия необходимо указать комментарий.');
      return;
    }

    try {
      setIsSubmitting(true);
      setError('');
      setSuccessMessage('');

      switch (selectedAction) {
        case 'submit-approval':
          await reportsApi.submitForApproval(selectedReport.id, {
            last_comment: trimmedComment || null,
            approver_id: user?.id ?? null,
          });
          break;

        case 'approve':
          await reportsApi.approve(selectedReport.id, {
            last_comment: trimmedComment || null,
          });
          break;

        case 'reject':
          await reportsApi.reject(selectedReport.id, {
            last_comment: trimmedComment || null,
          });
          break;
      }

      await loadApprovals();
      setShowActionModal(false);
      setSelectedAction(null);
      setSelectedReport(null);
      setComment('');
      setSuccessMessage(actionMeta.successMessage);
    } catch {
      setError('Не удалось выполнить действие согласования.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <ContentCard
        header={
          <div className="section-header">
            <h2 className="section-title">Согласование отчётов</h2>
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
    <>
      <ContentCard
        header={
          <div className="toolbar-row">
            <div className="toolbar-left">
              <div>
                <h2 className="section-title mb-0">Согласование отчётов</h2>
                <div className="section-subtitle">
                  {activeProject
                    ? `Активный проект: ${activeProject.name}`
                    : 'Выберите активный проект для очереди согласования'}
                </div>
              </div>

              {activeProjectId != null ? (
                <>
                  <Form.Control
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    className="soft-input approvals-search-input"
                    placeholder="Поиск по названию, инициатору или комментарию"
                  />

                  <Form.Select
                    className="soft-select"
                    value={statusFilter}
                    onChange={(event) =>
                      setStatusFilter(
                        event.target.value as 'all' | 'on_review' | 'on_approval',
                      )
                    }
                  >
                    <option value="all">Все этапы</option>
                    <option value="on_review">На рассмотрении</option>
                    <option value="on_approval">На утверждении</option>
                  </Form.Select>
                </>
              ) : null}
            </div>

            <div className="toolbar-actions">
              <Button
                className="secondary-pill-button"
                onClick={() => navigate('/reports')}
              >
                К отчетам
              </Button>
            </div>
          </div>
        }
      >
        {error ? <Alert variant="danger">{error}</Alert> : null}
        {successMessage ? <Alert variant="success">{successMessage}</Alert> : null}

        {activeProjectId == null ? (
          <div className="page-empty-state">
            <div className="page-empty-state-title">Сначала выбери проект</div>
            <div className="page-empty-state-text">
              Очередь согласования формируется только в контексте выбранного проекта.
            </div>
            <Button className="primary-pill-button mt-3" onClick={() => navigate('/projects')}>
              Перейти к проектам
            </Button>
          </div>
        ) : !canManageApprovalFlow ? (
          <Alert variant="warning" className="mb-0">
            У тебя нет прав на согласование отчётов в выбранном проекте.
          </Alert>
        ) : (
          <div className="table-wrap">
            <Table borderless responsive className="prototype-table">
              <thead>
                <tr>
                  <th>Название</th>
                  <th>Инициатор</th>
                  <th>Период</th>
                  <th>Статус</th>
                  <th>Комментарий</th>
                  <th>Действия</th>
                </tr>
              </thead>
              <tbody>
                {filteredReports.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-4">
                      В очереди согласования отчётов нет
                    </td>
                  </tr>
                ) : (
                  filteredReports.map((report) => (
                    <tr
                      key={report.id}
                      className="table-row-clickable"
                      onClick={() => navigate(`/reports/${report.id}/result`)}
                    >
                      <td>{report.title}</td>
                      <td>{getMemberDisplayName(report.creator_id, members)}</td>
                      <td>
                        {formatDate(report.report_period_start)} —{' '}
                        {formatDate(report.report_period_end)}
                      </td>
                      <td>
                        <span className={getReportStatusClassName(report.status)}>
                          {getReportStatusLabel(report.status)}
                        </span>
                      </td>
                      <td>
                        <div className="approvals-comment">
                          {report.last_comment ?? '—'}
                        </div>
                      </td>
                      <td onClick={(event) => event.stopPropagation()}>
                        <div className="approvals-table-actions">
                          {report.status === 'on_review' ? (
                            <>
                              <Button
                                size="sm"
                                className="secondary-pill-button approvals-action-button"
                                onClick={() => openActionModal('submit-approval', report)}
                              >
                                На утверждение
                              </Button>

                              <Button
                                size="sm"
                                className="secondary-pill-button approvals-action-button"
                                onClick={() => openActionModal('reject', report)}
                              >
                                Отклонить
                              </Button>
                            </>
                          ) : null}

                          {report.status === 'on_approval' ? (
                            <>
                              <Button
                                size="sm"
                                className="primary-pill-button approvals-action-button"
                                onClick={() => openActionModal('approve', report)}
                              >
                                Утвердить
                              </Button>

                              <Button
                                size="sm"
                                className="secondary-pill-button approvals-action-button"
                                onClick={() => openActionModal('reject', report)}
                              >
                                Отклонить
                              </Button>
                            </>
                          ) : null}

                          <Button
                            size="sm"
                            className="secondary-pill-button approvals-open-button"
                            onClick={() => navigate(`/reports/${report.id}/result`)}
                          >
                            Открыть
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </Table>
          </div>
        )}
      </ContentCard>

      <Modal
        show={showActionModal}
        onHide={() => {
          setShowActionModal(false);
          setSelectedAction(null);
          setSelectedReport(null);
          setComment('');
        }}
        centered
      >
        <Modal.Header closeButton>
          <Modal.Title>
            {selectedAction ? APPROVAL_ACTION_META[selectedAction].title : 'Действие'}
          </Modal.Title>
        </Modal.Header>

        <Form onSubmit={handleActionSubmit}>
          <Modal.Body>
            <div className="mb-3">
              <div className="form-meta-label">Отчёт</div>
              <div className="form-meta-value">{selectedReport?.title ?? '—'}</div>
            </div>

            <Form.Group>
              <Form.Label>Комментарий</Form.Label>
              <Form.Control
                as="textarea"
                rows={4}
                className="soft-input soft-textarea workflow-comment-input"
                value={comment}
                onChange={(event) => setComment(event.target.value)}
                placeholder={
                  selectedAction
                    ? APPROVAL_ACTION_META[selectedAction].placeholder
                    : 'Комментарий'
                }
              />
            </Form.Group>
          </Modal.Body>

          <Modal.Footer>
            <Button
              className="secondary-pill-button"
              onClick={() => {
                setShowActionModal(false);
                setSelectedAction(null);
                setSelectedReport(null);
                setComment('');
              }}
            >
              Отмена
            </Button>
            <Button
              type="submit"
              className="primary-pill-button"
              disabled={isSubmitting}
            >
              {isSubmitting
                ? 'Сохранение...'
                : selectedAction
                  ? APPROVAL_ACTION_META[selectedAction].buttonLabel
                  : 'Сохранить'}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>
    </>
  );
}