import { useEffect, useMemo, useState } from 'react';
import { Alert, Button, Form, Modal, Spinner, Table } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthProvider';
import { useProjectContext } from '../../features/projects/ProjectContext';
import { reportsApi } from '../../shared/api/reports';
import {
  getReportStatusClassName,
  getReportStatusLabel,
  reportStatusOptions,
} from '../../shared/lib/reportStatus';
import { readUserSettings } from '../../shared/lib/userSettings';
import type { Report } from '../../shared/types/report';
import { ContentCard } from '../../shared/ui/ContentCard';

function formatDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString('ru-RU');
}

function canArchiveReport(report: Report) {
  return (
    !report.is_archived &&
    (report.status === 'approved' || report.status === 'rejected' || report.status === 'failed')
  );
}

export default function ReportsPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { activeProjectId, activeProject } = useProjectContext();
  const settings = readUserSettings();

  const [reports, setReports] = useState<Report[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(true);
  const [isArchiveSubmitting, setIsArchiveSubmitting] = useState(false);

  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const [showArchiveModal, setShowArchiveModal] = useState(false);
  const [archiveComment, setArchiveComment] = useState('');

  const canAccessApprovalQueue = user?.role.code === 'admin' || user?.role.code === 'manager';

  const loadReports = async () => {
    try {
      setIsLoading(true);
      setError('');
      const data = await reportsApi.list();
      setReports(data);
    } catch {
      setError('Не удалось загрузить список отчетов.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadReports();
  }, []);

  useEffect(() => {
    setSelectedIds([]);
  }, [activeProjectId, statusFilter]);

  const projectReports = useMemo(() => {
    if (activeProjectId == null) {
      return [];
    }

    return reports.filter((report) => report.project_id === activeProjectId);
  }, [reports, activeProjectId]);

  const filteredReports = useMemo(() => {
    if (statusFilter === 'all') {
      return projectReports;
    }

    return projectReports.filter((report) => report.status === statusFilter);
  }, [projectReports, statusFilter]);

  const visibleReports = useMemo(() => {
    return filteredReports.slice(0, settings.tablePageSize);
  }, [filteredReports, settings.tablePageSize]);

  const selectedReports = useMemo(
    () => reports.filter((report) => selectedIds.includes(report.id)),
    [reports, selectedIds],
  );

  const selectedSingleReport = selectedReports.length === 1 ? selectedReports[0] : null;

  const canEditSelected =
    selectedSingleReport != null &&
    selectedSingleReport.status !== 'archived' &&
    !selectedSingleReport.is_archived;

  const canArchiveSelected =
    selectedReports.length > 0 && selectedReports.every((report) => canArchiveReport(report));

  const toggleOne = (reportId: number) => {
    setSelectedIds((prev) =>
      prev.includes(reportId) ? prev.filter((id) => id !== reportId) : [...prev, reportId],
    );
  };

  const toggleAll = () => {
    if (filteredReports.length === 0) {
      return;
    }

    const visibleIds = visibleReports.map((report) => report.id);
    const allSelected = visibleIds.every((id) => selectedIds.includes(id));

    setSelectedIds((prev) => {
      if (allSelected) {
        return prev.filter((id) => !visibleIds.includes(id));
      }

      return Array.from(new Set([...prev, ...visibleIds]));
    });
  };

  const handleArchiveReports = async () => {
    if (!canArchiveSelected || selectedReports.length === 0) {
      return;
    }

    try {
      setIsArchiveSubmitting(true);
      setError('');
      setSuccessMessage('');

      const trimmedComment = archiveComment.trim();

      const results = await Promise.allSettled(
        selectedReports.map((report) => reportsApi.archive(report.id, trimmedComment || null)),
      );

      const successCount = results.filter((item) => item.status === 'fulfilled').length;
      const failedCount = results.length - successCount;

      await loadReports();
      setSelectedIds([]);
      setShowArchiveModal(false);
      setArchiveComment('');

      if (failedCount === 0) {
        setSuccessMessage(
          successCount === 1
            ? 'Отчет успешно архивирован.'
            : `Отчеты успешно архивированы: ${successCount}.`,
        );
      } else {
        setError(
          `Часть архивирования завершилась с ошибкой. Успешно: ${successCount}, с ошибкой: ${failedCount}.`,
        );
      }
    } catch {
      setError('Не удалось архивировать выбранные отчеты.');
    } finally {
      setIsArchiveSubmitting(false);
    }
  };

  return (
    <>
      <ContentCard
        header={
          <div className="toolbar-row">
            <div className="toolbar-left">
              <div>
                <h2 className="section-title">Отчётность</h2>
                <div className="section-subtitle">
                  {activeProject ? `Активный проект: ${activeProject.name}` : 'Выберите активный проект для работы с отчётами'}
                </div>
              </div>

              {activeProjectId != null ? (
                <Form.Select
                  className="soft-select"
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  {reportStatusOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </Form.Select>
              ) : null}
            </div>

            <div className="reports-toolbar-actions">
              {canAccessApprovalQueue ? (
                <Button className="secondary-pill-button" onClick={() => navigate('/reports/approval')}>
                  Согласование
                </Button>
              ) : null}

              <Button
                className="primary-pill-button"
                onClick={() =>
                  activeProjectId == null ? navigate('/projects') : navigate('/reports/create')
                }
              >
                {activeProjectId == null ? 'Выбрать проект' : 'Создать отчет'}
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

        {!isLoading && !error && activeProjectId == null ? (
          <div className="page-empty-state">
            <div className="page-empty-state-title">Сначала выбери проект</div>
            <div className="page-empty-state-text">
              Отчеты, результаты обработки и действия доступны только в контексте выбранного проекта.
            </div>
            <Button className="primary-pill-button mt-3" onClick={() => navigate('/projects')}>
              Перейти к проектам
            </Button>
          </div>
        ) : null}

        {!isLoading && !error && activeProjectId != null ? (
          <>
            <div className="table-wrap">
              <Table borderless responsive className="prototype-table">
                <thead>
                  <tr>
                    <th className="checkbox-col">
                      <Form.Check
                        checked={
                          visibleReports.length > 0 &&
                          visibleReports.every((report) => selectedIds.includes(report.id))
                        }
                        onChange={toggleAll}
                      />
                    </th>
                    <th>ID</th>
                    <th>Название</th>
                    <th>Статус</th>
                    <th>Период начала</th>
                    <th>Период конца</th>
                    <th>Версия</th>
                    <th>Комментарий</th>
                  </tr>
                </thead>
                <tbody>
                  {visibleReports.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="text-center py-4">
                        Отчеты в выбранном проекте не найдены
                      </td>
                    </tr>
                  ) : (
                    visibleReports.map((report) => (
                      <tr
                        key={report.id}
                        className="table-row-clickable"
                        onClick={() => navigate(`/reports/${report.id}/result`)}
                      >
                        <td className="checkbox-col" onClick={(event) => event.stopPropagation()}>
                          <Form.Check
                            checked={selectedIds.includes(report.id)}
                            onChange={() => toggleOne(report.id)}
                          />
                        </td>
                        <td>{report.id}</td>
                        <td>{report.title}</td>
                        <td>
                          <span className={getReportStatusClassName(report.status)}>
                            {getReportStatusLabel(report.status)}
                          </span>
                        </td>
                        <td>{formatDate(report.report_period_start)}</td>
                        <td>{formatDate(report.report_period_end)}</td>
                        <td>{report.version}</td>
                        <td className="approval-comment-cell">{report.last_comment ?? '—'}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </Table>
            </div>

            <div className="action-dock">
              <Button
                className="primary-pill-button"
                disabled={!canEditSelected}
                onClick={() => {
                  if (selectedSingleReport) {
                    navigate(`/reports/${selectedSingleReport.id}/edit`);
                  }
                }}
              >
                Редактировать
              </Button>

              <Button
                className="primary-pill-button"
                disabled={!canArchiveSelected}
                onClick={() => {
                  setArchiveComment('');
                  setShowArchiveModal(true);
                }}
              >
                Архивировать
              </Button>
            </div>
          </>
        ) : null}
      </ContentCard>

      <Modal
        show={showArchiveModal}
        onHide={() => {
          setShowArchiveModal(false);
          setArchiveComment('');
        }}
        centered
      >
        <Modal.Header closeButton>
          <Modal.Title>Архивирование отчетов</Modal.Title>
        </Modal.Header>

        <Modal.Body>
          <div className="archive-warning-text">
            {selectedReports.length === 1
              ? 'Выбранный отчет будет переведен в архив.'
              : `Будут архивированы отчеты: ${selectedReports.length}.`}
          </div>

          <Form.Group className="mt-3">
            <Form.Label>Комментарий</Form.Label>
            <Form.Control
              as="textarea"
              rows={4}
              className="soft-input soft-textarea"
              value={archiveComment}
              onChange={(event) => setArchiveComment(event.target.value)}
              placeholder="Например: отчет завершен и переведен в архив"
            />
          </Form.Group>
        </Modal.Body>

        <Modal.Footer>
          <Button
            className="secondary-pill-button"
            onClick={() => {
              setShowArchiveModal(false);
              setArchiveComment('');
            }}
          >
            Отмена
          </Button>

          <Button
            className="primary-pill-button"
            onClick={() => void handleArchiveReports()}
            disabled={isArchiveSubmitting}
          >
            {isArchiveSubmitting ? 'Архивирование...' : 'Архивировать'}
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
}