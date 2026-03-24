import { useEffect, useMemo, useState } from 'react';
import { Alert, Button, Col, Form, Row, Spinner, Table } from 'react-bootstrap';
import { Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  ArcElement,
  BarElement,
  CategoryScale,
  Legend,
  LinearScale,
  Tooltip,
} from 'chart.js';
import { useNavigate } from 'react-router-dom';
import { exportsApi } from '../../shared/api/exports';
import { reportsApi } from '../../shared/api/reports';
import { resultsApi } from '../../shared/api/results';
import { getReportStatusLabel, reportStatusOptions } from '../../shared/lib/reportStatus';
import type { ExportArtifact } from '../../shared/types/export';
import type { Report } from '../../shared/types/report';
import type { NormalizedDataset } from '../../shared/types/result';
import { ContentCard } from '../../shared/ui/ContentCard';

ChartJS.register(ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend);

function formatDateTime(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('ru-RU');
}

function formatRows(value: number) {
  return new Intl.NumberFormat('ru-RU').format(value);
}

export default function AnalyticsPage() {
  const navigate = useNavigate();

  const [reports, setReports] = useState<Report[]>([]);
  const [results, setResults] = useState<NormalizedDataset[]>([]);
  const [exports, setExports] = useState<ExportArtifact[]>([]);

  const [statusFilter, setStatusFilter] = useState('all');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        setIsLoading(true);
        setError('');

        const [reportsData, resultsData, exportsData] = await Promise.all([
          reportsApi.list(),
          resultsApi.list(),
          exportsApi.list(),
        ]);

        setReports(reportsData);
        setResults(resultsData);
        setExports(exportsData);
      } catch {
        setError('Не удалось загрузить аналитические данные.');
      } finally {
        setIsLoading(false);
      }
    })();
  }, []);

  const filteredReports = useMemo(() => {
    if (statusFilter === 'all') {
      return reports;
    }

    return reports.filter((report) => report.status === statusFilter);
  }, [reports, statusFilter]);

  const filteredReportIds = useMemo(() => new Set(filteredReports.map((item) => item.id)), [filteredReports]);

  const filteredResults = useMemo(() => {
    return results.filter((item) => filteredReportIds.has(item.report_id));
  }, [results, filteredReportIds]);

  const totalRows = useMemo(() => {
    return filteredResults.reduce((acc, item) => acc + item.rows_count, 0);
  }, [filteredResults]);

  const processedReportsCount = useMemo(() => {
    return filteredReports.filter((item) => item.status === 'processed').length;
  }, [filteredReports]);

  const filteredExportsCount = useMemo(() => {
    return exports.filter((item) => item.report_id != null && filteredReportIds.has(item.report_id)).length;
  }, [exports, filteredReportIds]);

  const statusChartData = useMemo(() => {
    const counters = new Map<string, number>();

    filteredReports.forEach((report) => {
      counters.set(report.status, (counters.get(report.status) ?? 0) + 1);
    });

    const labels = Array.from(counters.keys()).map((status) => getReportStatusLabel(status));
    const values = Array.from(counters.values());

    return {
      labels,
      datasets: [
        {
          label: 'Количество отчетов',
          data: values,
        },
      ],
    };
  }, [filteredReports]);

  const rowsChartData = useMemo(() => {
    const reportTitleById = new Map<number, string>();
    filteredReports.forEach((report) => {
      reportTitleById.set(report.id, report.title);
    });

    const topResults = [...filteredResults]
      .sort((a, b) => b.rows_count - a.rows_count)
      .slice(0, 6);

    return {
      labels: topResults.map((item) => reportTitleById.get(item.report_id) ?? `Отчет #${item.report_id}`),
      datasets: [
        {
          label: 'Количество строк',
          data: topResults.map((item) => item.rows_count),
        },
      ],
    };
  }, [filteredReports, filteredResults]);

  const latestResults = useMemo(() => {
    return [...filteredResults]
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      .slice(0, 8);
  }, [filteredResults]);

  const reportTitleMap = useMemo(() => {
    return new Map(reports.map((item) => [item.id, item.title]));
  }, [reports]);

  return (
    <ContentCard
      header={
        <div className="toolbar-row">
          <div className="toolbar-left">
            <h2 className="section-title mb-0">Аналитика</h2>

            <Form.Select
              className="soft-select"
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value)}
            >
              {reportStatusOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Form.Select>
          </div>

          <Button className="primary-pill-button" onClick={() => navigate('/reports')}>
            К отчетам
          </Button>
        </div>
      }
    >
      {isLoading ? (
        <div className="py-5 text-center">
          <Spinner animation="border" />
        </div>
      ) : null}

      {!isLoading && error ? <Alert variant="danger">{error}</Alert> : null}

      {!isLoading && !error ? (
        <>
          <Row className="g-3 mb-4">
            <Col md={3}>
              <div className="metric-card">
                <div className="metric-label">Всего отчетов</div>
                <div className="metric-value">{filteredReports.length}</div>
              </div>
            </Col>

            <Col md={3}>
              <div className="metric-card">
                <div className="metric-label">Обработано</div>
                <div className="metric-value">{processedReportsCount}</div>
              </div>
            </Col>

            <Col md={3}>
              <div className="metric-card">
                <div className="metric-label">Строк нормализации</div>
                <div className="metric-value">{formatRows(totalRows)}</div>
              </div>
            </Col>

            <Col md={3}>
              <div className="metric-card">
                <div className="metric-label">Экспортов</div>
                <div className="metric-value">{filteredExportsCount}</div>
              </div>
            </Col>
          </Row>

          <Row className="g-4 mb-4">
            <Col lg={5}>
              <div className="analytics-card">
                <div className="analytics-card-title">Распределение по статусам</div>
                <div className="analytics-chart-wrap">
                  <Doughnut data={statusChartData} />
                </div>
              </div>
            </Col>

            <Col lg={7}>
              <div className="analytics-card">
                <div className="analytics-card-title">Обработанные строки по отчетам</div>
                <div className="analytics-chart-wrap">
                  <Bar data={rowsChartData} />
                </div>
              </div>
            </Col>
          </Row>

          <div className="analytics-card">
            <div className="analytics-card-title">Последние результаты обработки</div>

            <div className="table-wrap">
              <Table borderless responsive className="prototype-table">
                <thead>
                  <tr>
                    <th>ID результата</th>
                    <th>Отчет</th>
                    <th>Строк</th>
                    <th>Дата формирования</th>
                    <th>Действие</th>
                  </tr>
                </thead>
                <tbody>
                  {latestResults.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="text-center py-4">
                        Данные для аналитики отсутствуют
                      </td>
                    </tr>
                  ) : (
                    latestResults.map((item) => (
                      <tr key={item.id}>
                        <td>{item.id}</td>
                        <td>{reportTitleMap.get(item.report_id) ?? `Отчет #${item.report_id}`}</td>
                        <td>{formatRows(item.rows_count)}</td>
                        <td>{formatDateTime(item.created_at)}</td>
                        <td>
                          <Button
                            size="sm"
                            className="primary-pill-button analytics-open-button"
                            onClick={() => navigate(`/reports/${item.report_id}/result`)}
                          >
                            Открыть
                          </Button>
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
  );
}