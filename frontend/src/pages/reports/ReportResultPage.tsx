import { useEffect, useMemo, useState } from 'react';
import { Alert, Button, Col, Row, Spinner, Table } from 'react-bootstrap';
import { useNavigate, useParams } from 'react-router-dom';
import { exportsApi } from '../../shared/api/exports';
import { processingApi } from '../../shared/api/processing';
import { reportsApi } from '../../shared/api/reports';
import { resultsApi } from '../../shared/api/results';
import { getReportStatusClassName, getReportStatusLabel } from '../../shared/lib/reportStatus';
import type { ExportArtifactDetail, ExportFormat } from '../../shared/types/export';
import type { ProcessingTaskDetail } from '../../shared/types/processing';
import type { Report } from '../../shared/types/report';
import type { NormalizedDataset, NormalizedDatasetDetail } from '../../shared/types/result';
import { ContentCard } from '../../shared/ui/ContentCard';

function formatDateTime(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('ru-RU');
}

function formatBytes(value: number) {
  if (value < 1024) return `${value} Б`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} КБ`;
  return `${(value / (1024 * 1024)).toFixed(2)} МБ`;
}

export default function ReportResultPage() {
  const { reportId } = useParams<{ reportId: string }>();
  const navigate = useNavigate();

  const numericReportId = Number(reportId);

  const [report, setReport] = useState<Report | null>(null);
  const [taskDetail, setTaskDetail] = useState<ProcessingTaskDetail | null>(null);
  const [resultDetail, setResultDetail] = useState<NormalizedDatasetDetail | null>(null);
  const [exports, setExports] = useState<ExportArtifactDetail[]>([]);

  const [isLoading, setIsLoading] = useState(true);
  const [isExportLoading, setIsExportLoading] = useState(false);
  const [error, setError] = useState('');

  const previewColumns = useMemo(() => {
    if (!resultDetail?.preview_json?.length) {
      return [];
    }

    return Array.from(
      new Set(resultDetail.preview_json.flatMap((row) => Object.keys(row))),
    );
  }, [resultDetail]);

  useEffect(() => {
    if (!reportId || Number.isNaN(numericReportId)) {
      setError('Некорректный идентификатор отчета.');
      setIsLoading(false);
      return;
    }

    (async () => {
      try {
        setIsLoading(true);
        setError('');

        const [reportData, tasks, results, exportList] = await Promise.all([
          reportsApi.getById(numericReportId),
          processingApi.listTasks(),
          resultsApi.list(),
          exportsApi.list(),
        ]);

        setReport(reportData);

        const latestTask = [...tasks]
          .filter((item) => item.report_id === numericReportId)
          .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())[0];

        const latestResult: NormalizedDataset | undefined = [...results]
          .filter((item) => item.report_id === numericReportId)
          .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())[0];

        if (latestTask) {
          const fullTask = await processingApi.getTask(latestTask.id);
          setTaskDetail(fullTask);
        }

        if (latestResult) {
          const fullResult = await resultsApi.getById(latestResult.id);
          setResultDetail(fullResult);
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
    })();
  }, [reportId, numericReportId]);

  const handleRunExport = async (format: ExportFormat) => {
    if (!taskDetail || !report) {
      setError('Невозможно выполнить экспорт: задача обработки не найдена.');
      return;
    }

    try {
      setIsExportLoading(true);
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
    <ContentCard
      header={
        <div className="toolbar-row">
          <div className="toolbar-left">
            <h2 className="section-title mb-0">Результат обработки</h2>
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
              {report.report_period_start} — {report.report_period_end}
            </div>
          </div>
        </div>

        <Row className="g-4 mb-4">
          <Col lg={6}>
            <div className="form-meta-card h-100">
              <div className="form-meta-label">Информация об обработке</div>

              <div className="result-info-list">
                <div><strong>ID задачи:</strong> {taskDetail?.id ?? '—'}</div>
                <div><strong>Статус задачи:</strong> {taskDetail?.status ?? '—'}</div>
                <div><strong>Прогресс:</strong> {taskDetail?.progress ?? 0}%</div>
                <div><strong>Качество:</strong> {taskDetail?.quality_score != null ? `${Math.round(taskDetail.quality_score * 100)}%` : '—'}</div>
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
                <div><strong>ID результата:</strong> {resultDetail?.id ?? '—'}</div>
                <div><strong>Количество строк:</strong> {resultDetail?.rows_count ?? '—'}</div>
                <div><strong>Дата формирования:</strong> {formatDateTime(resultDetail?.created_at)}</div>
                <div><strong>Расположение данных:</strong> {resultDetail?.data_location ?? '—'}</div>
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
  );
}