import { useEffect, useMemo, useState } from 'react';
import { Alert, Button, Col, ProgressBar, Row, Spinner, Table } from 'react-bootstrap';
import { useNavigate, useParams } from 'react-router-dom';
import { mlApi } from '../../shared/api/ml';
import { processingApi } from '../../shared/api/processing';
import { tasksApi } from '../../shared/api/tasks';
import { readUserSettings } from '../../shared/lib/userSettings';
import type { MlPipelineResult } from '../../shared/types/ml-pipeline';
import type {
  ProcessingTaskDetail,
  TaskProgressResponse,
} from '../../shared/types/processing';
import { ContentCard } from '../../shared/ui/ContentCard';

function formatDateTime(value?: string | null) {
  if (!value) return '-';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('ru-RU');
}

function getStatusLabel(status: string) {
  switch (status) {
    case 'queued':
      return 'В очереди';
    case 'running':
      return 'Выполняется';
    case 'success':
      return 'Успешно';
    case 'failed':
      return 'Ошибка';
    case 'retry':
      return 'Повтор';
    case 'cancelled':
      return 'Отменена';
    default:
      return status;
  }
}

const POLLABLE_STATUSES = new Set(['queued', 'running', 'retry']);

export default function TaskDetailsPage() {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const settings = readUserSettings();
  const numericTaskId = Number(taskId);

  const [task, setTask] = useState<ProcessingTaskDetail | null>(null);
  const [progress, setProgress] = useState<TaskProgressResponse | null>(null);
  const [pipelineResult, setPipelineResult] = useState<MlPipelineResult | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [isActionLoading, setIsActionLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!numericTaskId) {
      setError('Некорректный идентификатор задачи.');
      return;
    }

    (async () => {
      try {
        setIsLoading(true);
        setError('');

        const [taskData, progressData] = await Promise.all([
          processingApi.getTask(numericTaskId),
          tasksApi.getProgress(numericTaskId),
        ]);

        setTask(taskData);
        setProgress(progressData);

        try {
          const pipeline = await mlApi.getPipelineResult(numericTaskId);
          setPipelineResult(pipeline);
        } catch {
          setPipelineResult(null);
        }
      } catch {
        setError('Не удалось загрузить данные задачи.');
      } finally {
        setIsLoading(false);
      }
    })();
  }, [numericTaskId]);

  useEffect(() => {
    if (!settings.autoRefresh || !progress || !POLLABLE_STATUSES.has(progress.status)) {
      return;
    }

    const interval = window.setInterval(async () => {
      try {
        const nextProgress = await tasksApi.getProgress(numericTaskId);
        setProgress(nextProgress);

        if (!POLLABLE_STATUSES.has(nextProgress.status)) {
          const freshTask = await processingApi.getTask(numericTaskId);
          setTask(freshTask);

          try {
            const pipeline = await mlApi.getPipelineResult(numericTaskId);
            setPipelineResult(pipeline);
          } catch {
            setPipelineResult(null);
          }

          window.clearInterval(interval);
        }
      } catch {
        window.clearInterval(interval);
      }
    }, 3000);

    return () => window.clearInterval(interval);
  }, [numericTaskId, progress, settings.autoRefresh]);

  const canRetry = useMemo(() => {
    return progress?.status === 'failed';
  }, [progress]);

  const canCancel = useMemo(() => {
    return progress ? POLLABLE_STATUSES.has(progress.status) : false;
  }, [progress]);

  const handleRetry = async () => {
    try {
      setIsActionLoading(true);
      const updatedTask = await tasksApi.retry(numericTaskId);
      setTask(updatedTask);
      setProgress({
        task_id: updatedTask.id,
        status: updatedTask.status,
        progress: updatedTask.progress,
        warning_count: updatedTask.warning_count,
        error_count: updatedTask.error_count,
        started_at: updatedTask.started_at,
        finished_at: updatedTask.finished_at,
        error_summary: updatedTask.error_summary,
      });
    } catch {
      setError('Не удалось отправить задачу на повторную обработку.');
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleCancel = async () => {
    try {
      setIsActionLoading(true);
      const updatedTask = await tasksApi.cancel(numericTaskId);
      setTask(updatedTask);
      setProgress({
        task_id: updatedTask.id,
        status: updatedTask.status,
        progress: updatedTask.progress,
        warning_count: updatedTask.warning_count,
        error_count: updatedTask.error_count,
        started_at: updatedTask.started_at,
        finished_at: updatedTask.finished_at,
        error_summary: updatedTask.error_summary,
      });
    } catch {
      setError('Не удалось отменить задачу.');
    } finally {
      setIsActionLoading(false);
    }
  };

  if (isLoading) {
    return (
      <ContentCard
        header={
          <div className="section-header">
            <h2 className="section-title">Мониторинг задачи обработки</h2>
          </div>
        }
      >
        <div className="py-5 text-center">
          <Spinner animation="border" />
        </div>
      </ContentCard>
    );
  }

  if (!task || !progress) {
    return (
      <ContentCard
        header={
          <div className="section-header">
            <h2 className="section-title">Мониторинг задачи обработки</h2>
          </div>
        }
      >
        <Alert variant="danger" className="mb-0">
          {error || 'Задача не найдена.'}
        </Alert>
      </ContentCard>
    );
  }

  return (
    <ContentCard
      header={
        <div className="toolbar-row">
          <div className="toolbar-left">
            <h2 className="section-title mb-0">Мониторинг задачи обработки</h2>
          </div>

          <Button className="secondary-pill-button" onClick={() => navigate('/reports')}>
            К отчетам
          </Button>
        </div>
      }
    >
      <div className="form-shell">
        {error ? <Alert variant="danger">{error}</Alert> : null}

        <div className="form-meta-grid mb-4">
          <div className="form-meta-card">
            <div className="form-meta-label">ID задачи</div>
            <div className="form-meta-value">#{task.id}</div>
          </div>

          <div className="form-meta-card">
            <div className="form-meta-label">Статус</div>
            <div className="form-meta-value">{getStatusLabel(progress.status)}</div>
          </div>

          <div className="form-meta-card">
            <div className="form-meta-label">Отчет</div>
            <div className="form-meta-value">{task.report.title}</div>
          </div>
        </div>

        <div className="task-progress-card mb-4">
          <div className="task-progress-header">
            <div className="form-meta-label mb-2">Прогресс выполнения</div>
            <div className="task-progress-value">{progress.progress}%</div>
          </div>

          <ProgressBar now={progress.progress} />

          <div className="task-progress-meta">
            <span>Предупреждений: {progress.warning_count}</span>
            <span>Ошибок: {progress.error_count}</span>
            <span>Запуск: {formatDateTime(progress.started_at)}</span>
            <span>Завершение: {formatDateTime(progress.finished_at)}</span>
          </div>

          {progress.error_summary ? (
            <Alert variant="warning" className="mt-3 mb-0">
              {progress.error_summary}
            </Alert>
          ) : null}
        </div>

        <Row className="g-4">
          <Col lg={6}>
            <div className="form-meta-card h-100">
              <div className="form-meta-label">Логи обработки</div>

              {task.logs.length === 0 ? (
                <div className="form-meta-value">Логи пока отсутствуют.</div>
              ) : (
                <div className="task-log-list">
                  {task.logs.map((log) => (
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
              <div className="form-meta-label">Результат ML-контура</div>

              <div className="task-ml-list">
                <div>
                  <strong>Выбранный шаблон:</strong>{' '}
                  {pipelineResult?.selected_template?.name ?? '-'}
                </div>
                <div>
                  <strong>Качество:</strong>{' '}
                  {pipelineResult?.quality_score != null
                    ? `${Math.round(pipelineResult.quality_score * 100)}%`
                    : '-'}
                </div>
                <div>
                  <strong>Подтверждение маппинга:</strong>{' '}
                  {pipelineResult?.mapping_confirmation_required ? 'Требуется' : 'Не требуется'}
                </div>
                <div>
                  <strong>Аномалий:</strong> {pipelineResult?.anomalies.length ?? 0}
                </div>
              </div>
            </div>
          </Col>
        </Row>

        <div className="mt-4">
          <div className="table-wrap">
            <Table borderless responsive className="prototype-table">
              <thead>
                <tr>
                  <th>Код ошибки</th>
                  <th>Тип</th>
                  <th>Поле</th>
                  <th>Строка</th>
                  <th>Описание</th>
                </tr>
              </thead>
              <tbody>
                {task.errors.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="text-center py-4">
                      Ошибки обработки отсутствуют
                    </td>
                  </tr>
                ) : (
                  task.errors.map((item) => (
                    <tr key={item.id}>
                      <td>{item.error_code}</td>
                      <td>{item.error_type}</td>
                      <td>{item.field_path ?? '-'}</td>
                      <td>{item.row_number ?? '-'}</td>
                      <td>{item.details ?? item.source_value ?? '-'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </Table>
          </div>
        </div>

        <div className="action-dock action-dock-inline">
          <Button
            className="secondary-pill-button"
            disabled={!canRetry || isActionLoading}
            onClick={handleRetry}
          >
            Повторить
          </Button>

          <Button
            className="primary-pill-button"
            disabled={!canCancel || isActionLoading}
            onClick={handleCancel}
          >
            Отменить
          </Button>
        </div>
      </div>
    </ContentCard>
  );
}