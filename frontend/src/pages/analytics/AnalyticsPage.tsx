import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { Alert, Button, Col, Form, Modal, Row, Spinner, Table } from 'react-bootstrap';
import { Bar, Doughnut } from 'react-chartjs-2';
import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Tooltip,
} from 'chart.js';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthProvider';
import { useProjectContext } from '../../features/projects/ProjectContext';
import { analyticsApi } from '../../shared/api/analytics';
import { exportsApi } from '../../shared/api/exports';
import { reportsApi } from '../../shared/api/reports';
import { resultsApi } from '../../shared/api/results';
import { getReportStatusLabel, reportStatusOptions } from '../../shared/lib/reportStatus';
import type {
  AnalyticsOverview,
  CreateDashboardPayload,
  Dashboard,
  DashboardSourceType,
  DashboardType,
  DashboardWidgetKey,
  UpdateDashboardPayload,
} from '../../shared/types/analytics';
import {
  DASHBOARD_TYPE_OPTIONS,
  DASHBOARD_WIDGET_OPTIONS,
  getDashboardSourceTypeLabel,
  getDashboardTypeLabel,
} from '../../shared/types/analytics';
import type { ExportArtifact } from '../../shared/types/export';
import type { Report } from '../../shared/types/report';
import type { NormalizedDataset } from '../../shared/types/result';
import { ContentCard } from '../../shared/ui/ContentCard';

ChartJS.register(ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend);

const DEFAULT_WIDGETS: DashboardWidgetKey[] = [
  'overviewMetrics',
  'statusDistribution',
  'periodDynamics',
  'rowsByReport',
  'summaryMetrics',
  'latestResults',
];

interface DashboardFormState {
  name: string;
  description: string;
  dashboardType: DashboardType;
  sourceType: DashboardSourceType;
  isShared: boolean;
  isDefault: boolean;
  widgets: DashboardWidgetKey[];
}

const initialDashboardForm: DashboardFormState = {
  name: '',
  description: '',
  dashboardType: 'personal',
  sourceType: 'project_aggregate',
  isShared: false,
  isDefault: false,
  widgets: DEFAULT_WIDGETS,
};

function formatDateTime(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('ru-RU');
}

function formatRows(value: number) {
  return new Intl.NumberFormat('ru-RU').format(value);
}

function formatPercent(value?: number | null) {
  if (value == null) return '—';
  return `${Math.round(value * 100)}%`;
}

function extractWidgetKeys(configJson: Record<string, unknown>): DashboardWidgetKey[] {
  const widgets = configJson.widgets;

  if (!Array.isArray(widgets)) {
    return DEFAULT_WIDGETS;
  }

  return widgets.filter(
    (item): item is DashboardWidgetKey =>
      typeof item === 'string' && DEFAULT_WIDGETS.includes(item as DashboardWidgetKey),
  );
}

function getDashboardSavedStatusFilter(dashboard: Dashboard): string {
  const value = dashboard.filters_json?.statusFilter;
  return typeof value === 'string' ? value : 'all';
}

export default function AnalyticsPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { activeProjectId, activeProject } = useProjectContext();

  const [reports, setReports] = useState<Report[]>([]);
  const [results, setResults] = useState<NormalizedDataset[]>([]);
  const [exports, setExports] = useState<ExportArtifact[]>([]);
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [dashboards, setDashboards] = useState<Dashboard[]>([]);

  const [statusFilter, setStatusFilter] = useState('all');
  const [activeWidgetKeys, setActiveWidgetKeys] = useState<DashboardWidgetKey[]>(DEFAULT_WIDGETS);
  const [appliedDashboardId, setAppliedDashboardId] = useState<number | null>(null);

  const [showDashboardModal, setShowDashboardModal] = useState(false);
  const [editingDashboard, setEditingDashboard] = useState<Dashboard | null>(null);
  const [dashboardForm, setDashboardForm] = useState<DashboardFormState>(initialDashboardForm);

  const [showDeleteDashboardModal, setShowDeleteDashboardModal] = useState(false);
  const [deletingDashboard, setDeletingDashboard] = useState<Dashboard | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [isSavingDashboard, setIsSavingDashboard] = useState(false);
  const [isDeletingDashboard, setIsDeletingDashboard] = useState(false);

  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [dashboardError, setDashboardError] = useState('');

  const canManageDashboards = user?.role.code === 'admin' || user?.role.code === 'manager';

  const dashboardStorageKey =
    activeProjectId != null ? `analytics-active-dashboard:${activeProjectId}` : null;

  const loadCoreAnalytics = async () => {
    const [reportsData, resultsData, exportsData] = await Promise.all([
      reportsApi.list(),
      resultsApi.list(),
      exportsApi.list(),
    ]);

    setReports(reportsData);
    setResults(resultsData);
    setExports(exportsData);
  };

  const loadDashboardServerData = async () => {
    if (!canManageDashboards) {
      setOverview(null);
      setDashboards([]);
      return;
    }

    try {
      const [overviewData, dashboardsData] = await Promise.all([
        analyticsApi.getOverview(),
        analyticsApi.listDashboards(),
      ]);

      setOverview(overviewData);
      setDashboards(dashboardsData);
      setDashboardError('');
    } catch {
      setOverview(null);
      setDashboards([]);
      setDashboardError('Не удалось загрузить сохранённые дашборды или KPI overview.');
    }
  };

  useEffect(() => {
    (async () => {
      try {
        setIsLoading(true);
        setError('');
        setSuccessMessage('');

        await loadCoreAnalytics();
        await loadDashboardServerData();
      } catch {
        setError('Не удалось загрузить аналитические данные.');
      } finally {
        setIsLoading(false);
      }
    })();
  }, [canManageDashboards]);

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

  const filteredReportIds = useMemo(() => {
    return new Set(filteredReports.map((item) => item.id));
  }, [filteredReports]);

  const filteredResults = useMemo(() => {
    return results.filter((item) => filteredReportIds.has(item.report_id));
  }, [results, filteredReportIds]);

  const filteredExports = useMemo(() => {
    return exports.filter(
      (item) => item.report_id != null && filteredReportIds.has(item.report_id),
    );
  }, [exports, filteredReportIds]);

  const projectDashboards = useMemo(() => {
    if (activeProjectId == null) {
      return [];
    }

    return dashboards.filter((dashboard) => dashboard.project_id === activeProjectId);
  }, [dashboards, activeProjectId]);

  const totalRows = useMemo(() => {
    return filteredResults.reduce((acc, item) => acc + item.rows_count, 0);
  }, [filteredResults]);

  const processedReportsCount = useMemo(() => {
    return filteredReports.filter((item) => item.status === 'processed').length;
  }, [filteredReports]);

  const reportTitleMap = useMemo(() => {
    return new Map(reports.map((item) => [item.id, item.title]));
  }, [reports]);

  const periodRowsChartData = useMemo(() => {
    const reportMap = new Map(filteredReports.map((item) => [item.id, item]));
    const counters = new Map<string, number>();

    filteredResults.forEach((result) => {
      const report = reportMap.get(result.report_id);
      if (!report) return;

      const periodKey = report.report_period_start.slice(0, 7);
      counters.set(periodKey, (counters.get(periodKey) ?? 0) + result.rows_count);
    });

    const sortedEntries = Array.from(counters.entries()).sort(([a], [b]) => a.localeCompare(b));

    return {
      labels: sortedEntries.map(([key]) => key),
      datasets: [
        {
          label: 'Строки нормализации',
          data: sortedEntries.map(([, value]) => value),
        },
      ],
    };
  }, [filteredReports, filteredResults]);

  const statusChartData = useMemo(() => {
    const counters = new Map<string, number>();

    filteredReports.forEach((report) => {
      counters.set(report.status, (counters.get(report.status) ?? 0) + 1);
    });

    return {
      labels: Array.from(counters.keys()).map((status) => getReportStatusLabel(status)),
      datasets: [
        {
          label: 'Количество отчётов',
          data: Array.from(counters.values()),
        },
      ],
    };
  }, [filteredReports]);

  const rowsChartData = useMemo(() => {
    const topResults = [...filteredResults]
      .sort((a, b) => b.rows_count - a.rows_count)
      .slice(0, 6);

    return {
      labels: topResults.map(
        (item) => reportTitleMap.get(item.report_id) ?? `Отчёт #${item.report_id}`,
      ),
      datasets: [
        {
          label: 'Количество строк',
          data: topResults.map((item) => item.rows_count),
        },
      ],
    };
  }, [filteredResults, reportTitleMap]);

  const aggregatedSummaryMetrics = useMemo(() => {
    const totals = new Map<string, number>();

    filteredResults.forEach((result) => {
      Object.entries(result.summary_json ?? {}).forEach(([key, value]) => {
        if (typeof value === 'number' && Number.isFinite(value)) {
          totals.set(key, (totals.get(key) ?? 0) + value);
        }
      });
    });

    return Array.from(totals.entries())
      .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
      .slice(0, 8)
      .map(([key, value]) => ({ key, value }));
  }, [filteredResults]);

  const summaryMetricsChartData = useMemo(() => {
    return {
      labels: aggregatedSummaryMetrics.map((item) => item.key),
      datasets: [
        {
          label: 'Суммарное значение',
          data: aggregatedSummaryMetrics.map((item) => item.value),
        },
      ],
    };
  }, [aggregatedSummaryMetrics]);

  const latestResults = useMemo(() => {
    return [...filteredResults]
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      .slice(0, 8);
  }, [filteredResults]);

  const activeDashboard = useMemo(() => {
    if (appliedDashboardId == null) {
      return null;
    }

    return projectDashboards.find((item) => item.id === appliedDashboardId) ?? null;
  }, [projectDashboards, appliedDashboardId]);

  const localMetricCards = useMemo(() => {
    const cards = [
      { key: 'reports', label: 'Всего отчётов', value: filteredReports.length },
      { key: 'processed', label: 'Обработано', value: processedReportsCount },
      { key: 'rows', label: 'Строк нормализации', value: formatRows(totalRows) },
      { key: 'exports', label: 'Экспортов', value: filteredExports.length },
    ];

    if (overview) {
      cards.push(
        {
          key: 'tasks',
          label: 'Всего задач',
          value: overview.total_tasks,
        },
        {
          key: 'quality',
          label: 'Среднее качество',
          value: formatPercent(overview.average_quality_score),
        },
      );
    }

    if (canManageDashboards) {
      cards.push({
        key: 'dashboards',
        label: 'Сохранённых дашбордов',
        value: projectDashboards.length,
      });
    }

    return cards;
  }, [
    filteredReports.length,
    processedReportsCount,
    totalRows,
    filteredExports.length,
    overview,
    canManageDashboards,
    projectDashboards.length,
  ]);

  const isWidgetVisible = (widget: DashboardWidgetKey) => activeWidgetKeys.includes(widget);

  const resetDashboardBuilder = () => {
    setEditingDashboard(null);
    setDashboardForm(initialDashboardForm);
    setShowDashboardModal(false);
  };

  const openCreateDashboardModal = () => {
    setEditingDashboard(null);
    setDashboardForm({
      ...initialDashboardForm,
      widgets: activeWidgetKeys.length > 0 ? activeWidgetKeys : DEFAULT_WIDGETS,
    });
    setDashboardError('');
    setShowDashboardModal(true);
  };

  const openEditDashboardModal = (dashboard: Dashboard) => {
    setEditingDashboard(dashboard);
    setDashboardForm({
      name: dashboard.name,
      description: dashboard.description ?? '',
      dashboardType: dashboard.dashboard_type,
      sourceType: dashboard.source_type,
      isShared: dashboard.is_shared,
      isDefault: dashboard.is_default,
      widgets: extractWidgetKeys(dashboard.config_json),
    });
    setDashboardError('');
    setShowDashboardModal(true);
  };

  const handleWidgetToggle = (widget: DashboardWidgetKey, checked: boolean) => {
    setDashboardForm((prev) => ({
      ...prev,
      widgets: checked
        ? Array.from(new Set([...prev.widgets, widget]))
        : prev.widgets.filter((item) => item !== widget),
    }));
  };

  const applyDashboard = (dashboard: Dashboard) => {
    setAppliedDashboardId(dashboard.id);

    const nextWidgets = extractWidgetKeys(dashboard.config_json);
    setActiveWidgetKeys(nextWidgets.length > 0 ? nextWidgets : DEFAULT_WIDGETS);

    const savedStatusFilter = getDashboardSavedStatusFilter(dashboard);
    setStatusFilter(savedStatusFilter);

    if (dashboardStorageKey) {
      localStorage.setItem(dashboardStorageKey, String(dashboard.id));
    }
  };

  const clearAppliedDashboard = () => {
    setAppliedDashboardId(null);
    setActiveWidgetKeys(DEFAULT_WIDGETS);
    setStatusFilter('all');

    if (dashboardStorageKey) {
      localStorage.removeItem(dashboardStorageKey);
    }
  };

  useEffect(() => {
    if (activeProjectId == null) {
      setAppliedDashboardId(null);
      setActiveWidgetKeys(DEFAULT_WIDGETS);
      setStatusFilter('all');
      return;
    }

    if (projectDashboards.length === 0) {
      setAppliedDashboardId(null);
      setActiveWidgetKeys(DEFAULT_WIDGETS);
      setStatusFilter('all');
      return;
    }

    const storedDashboardIdRaw = dashboardStorageKey
      ? localStorage.getItem(dashboardStorageKey)
      : null;
    const storedDashboardId = storedDashboardIdRaw ? Number(storedDashboardIdRaw) : null;

    const storedDashboard =
      storedDashboardId != null
        ? projectDashboards.find((item) => item.id === storedDashboardId) ?? null
        : null;

    const defaultDashboard = projectDashboards.find((item) => item.is_default) ?? null;
    const targetDashboard = storedDashboard ?? defaultDashboard;

    if (!targetDashboard) {
      setAppliedDashboardId(null);
      setActiveWidgetKeys(DEFAULT_WIDGETS);
      setStatusFilter('all');
      return;
    }

    const nextWidgets = extractWidgetKeys(targetDashboard.config_json);
    setAppliedDashboardId(targetDashboard.id);
    setActiveWidgetKeys(nextWidgets.length > 0 ? nextWidgets : DEFAULT_WIDGETS);
    setStatusFilter(getDashboardSavedStatusFilter(targetDashboard));

    if (dashboardStorageKey) {
      localStorage.setItem(dashboardStorageKey, String(targetDashboard.id));
    }
  }, [activeProjectId, projectDashboards, dashboardStorageKey]);

  const handleSaveDashboard = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!user || activeProjectId == null) {
      setDashboardError('Невозможно сохранить дашборд без выбранного проекта.');
      return;
    }

    if (!dashboardForm.name.trim()) {
      setDashboardError('Укажи название дашборда.');
      return;
    }

    if (dashboardForm.widgets.length === 0) {
      setDashboardError('Выбери хотя бы один виджет.');
      return;
    }

    try {
      setIsSavingDashboard(true);
      setDashboardError('');
      setSuccessMessage('');

      const commonPayload = {
        name: dashboardForm.name.trim(),
        description: dashboardForm.description.trim() || null,
        dashboard_type: dashboardForm.dashboardType,
        source_type: dashboardForm.sourceType,
        config_json: {
          widgets: dashboardForm.widgets,
          reportCount: filteredReports.length,
          resultCount: filteredResults.length,
        },
        filters_json: {
          statusFilter,
        },
        layout_json: {
          order: dashboardForm.widgets,
        },
        metrics_json: {
          summaryMetricKeys: aggregatedSummaryMetrics.map((item) => item.key),
        },
        is_shared: dashboardForm.isShared,
        is_default: dashboardForm.isDefault,
      };

      if (editingDashboard) {
        const payload: UpdateDashboardPayload = {
          ...commonPayload,
          last_generated_at: new Date().toISOString(),
        };

        const updated = await analyticsApi.updateDashboard(editingDashboard.id, payload);

        setDashboards((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));

        if (updated.is_default || appliedDashboardId === updated.id) {
          applyDashboard(updated);
        }

        setSuccessMessage(`Дашборд "${updated.name}" обновлён.`);
      } else {
        const payload: CreateDashboardPayload = {
          project_id: activeProjectId,
          owner_id: user.id,
          ...commonPayload,
        };

        const created = await analyticsApi.createDashboard(payload);

        setDashboards((prev) => [created, ...prev]);

        if (created.is_default) {
          applyDashboard(created);
        }

        setSuccessMessage(`Дашборд "${created.name}" создан.`);
      }

      setShowDashboardModal(false);
      setEditingDashboard(null);
      setDashboardForm(initialDashboardForm);
    } catch {
      setDashboardError('Не удалось сохранить конфигурацию дашборда.');
    } finally {
      setIsSavingDashboard(false);
    }
  };

  const openDeleteDashboardModal = (dashboard: Dashboard) => {
    setDeletingDashboard(dashboard);
    setDashboardError('');
    setShowDeleteDashboardModal(true);
  };

  const handleDeleteDashboard = async () => {
    if (!deletingDashboard) {
      return;
    }

    try {
      setIsDeletingDashboard(true);
      setDashboardError('');
      setSuccessMessage('');

      await analyticsApi.deleteDashboard(deletingDashboard.id);

      setDashboards((prev) => prev.filter((item) => item.id !== deletingDashboard.id));

      if (appliedDashboardId === deletingDashboard.id) {
        setAppliedDashboardId(null);
        setActiveWidgetKeys(DEFAULT_WIDGETS);
        setStatusFilter('all');

        if (dashboardStorageKey) {
          localStorage.removeItem(dashboardStorageKey);
        }
      }

      setSuccessMessage(`Дашборд "${deletingDashboard.name}" удалён.`);
      setDeletingDashboard(null);
      setShowDeleteDashboardModal(false);
    } catch {
      setDashboardError('Не удалось удалить дашборд.');
    } finally {
      setIsDeletingDashboard(false);
    }
  };

  return (
    <>
      <ContentCard
        header={
          <div className="toolbar-row">
            <div className="toolbar-left">
              <h2 className="section-title mb-0">
                {activeProject ? `Аналитика · ${activeProject.name}` : 'Аналитика'}
              </h2>

              {activeProjectId != null ? (
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
              ) : null}
            </div>

            <div className="analytics-header-actions">
              {canManageDashboards && activeProjectId != null ? (
                <Button className="secondary-pill-button" onClick={openCreateDashboardModal}>
                  Создать дашборд
                </Button>
              ) : null}

              <Button
                className="primary-pill-button"
                onClick={() =>
                  activeProjectId == null ? navigate('/projects') : navigate('/reports')
                }
              >
                {activeProjectId == null ? 'Выбрать проект' : 'К отчётам'}
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
        {!isLoading && dashboardError ? <Alert variant="warning">{dashboardError}</Alert> : null}

        {!isLoading && !error && activeProjectId == null ? (
          <div className="page-empty-state">
            <div className="page-empty-state-title">Сначала выбери проект</div>
            <div className="page-empty-state-text">
              Аналитика и дашборды строятся только по данным выбранного проекта.
            </div>
            <Button className="primary-pill-button mt-3" onClick={() => navigate('/projects')}>
              Перейти к проектам
            </Button>
          </div>
        ) : null}

        {!isLoading && !error && activeProjectId != null ? (
          <>
            {activeDashboard ? (
              <div className="dashboard-applied-banner">
                <div>
                  <div className="dashboard-applied-title">
                    Применён дашборд: {activeDashboard.name}
                  </div>
                  <div className="dashboard-applied-text">
                    {activeDashboard.description || 'Описание отсутствует.'}
                  </div>
                </div>

                <Button className="secondary-pill-button" onClick={clearAppliedDashboard}>
                  Сбросить
                </Button>
              </div>
            ) : null}

            {isWidgetVisible('overviewMetrics') ? (
              <Row className="g-3 mb-4">
                {localMetricCards.map((card) => (
                  <Col key={card.key} md={6} xl={3}>
                    <div className="metric-card">
                      <div className="metric-label">{card.label}</div>
                      <div className="metric-value">{card.value}</div>
                    </div>
                  </Col>
                ))}
              </Row>
            ) : null}

            <Row className="g-4 mb-4">
              {isWidgetVisible('statusDistribution') ? (
                <Col lg={5}>
                  <div className="analytics-card h-100">
                    <div className="analytics-card-title">Распределение по статусам</div>
                    <div className="analytics-chart-wrap">
                      <Doughnut data={statusChartData} />
                    </div>
                  </div>
                </Col>
              ) : null}

              {isWidgetVisible('periodDynamics') ? (
                <Col lg={isWidgetVisible('statusDistribution') ? 7 : 12}>
                  <div className="analytics-card h-100">
                    <div className="analytics-card-title">Динамика по периодам</div>
                    <div className="analytics-chart-wrap">
                      <Bar data={periodRowsChartData} />
                    </div>
                  </div>
                </Col>
              ) : null}
            </Row>

            <Row className="g-4 mb-4">
              {isWidgetVisible('rowsByReport') ? (
                <Col lg={6}>
                  <div className="analytics-card h-100">
                    <div className="analytics-card-title">Объём данных по отчётам</div>
                    <div className="analytics-chart-wrap">
                      <Bar data={rowsChartData} />
                    </div>
                  </div>
                </Col>
              ) : null}

              {isWidgetVisible('summaryMetrics') ? (
                <Col lg={isWidgetVisible('rowsByReport') ? 6 : 12}>
                  <div className="analytics-card h-100">
                    <div className="analytics-card-title">
                      Сводные показатели по summary_json
                    </div>

                    {aggregatedSummaryMetrics.length === 0 ? (
                      <div className="analytics-empty">
                        В summary_json пока нет числовых показателей для построения графика.
                      </div>
                    ) : (
                      <>
                        <div className="analytics-chart-wrap">
                          <Bar data={summaryMetricsChartData} />
                        </div>

                        <div className="analytics-mini-list">
                          {aggregatedSummaryMetrics.map((item) => (
                            <div key={item.key} className="analytics-mini-item">
                              <span>{item.key}</span>
                              <strong>{formatRows(item.value)}</strong>
                            </div>
                          ))}
                        </div>
                      </>
                    )}
                  </div>
                </Col>
              ) : null}
            </Row>

            {isWidgetVisible('latestResults') ? (
              <div className="analytics-card mb-4">
                <div className="analytics-card-title">Последние результаты обработки</div>

                <div className="table-wrap">
                  <Table borderless responsive className="prototype-table">
                    <thead>
                      <tr>
                        <th>ID результата</th>
                        <th>Отчёт</th>
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
                            <td>{reportTitleMap.get(item.report_id) ?? `Отчёт #${item.report_id}`}</td>
                            <td>{formatRows(item.rows_count)}</td>
                            <td>{formatDateTime(item.created_at)}</td>
                            <td>
                              <Button
                                size="sm"
                                className="primary-pill-button"
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
            ) : null}

            {canManageDashboards ? (
              <div className="analytics-card">
                <div className="analytics-card-title">Сохранённые дашборды</div>

                {projectDashboards.length === 0 ? (
                  <div className="analytics-empty">
                    Для выбранного проекта пока нет сохранённых дашбордов.
                  </div>
                ) : (
                  <div className="saved-dashboard-grid">
                    {projectDashboards.map((dashboard) => (
                      <div key={dashboard.id} className="saved-dashboard-card">
                        <div className="saved-dashboard-top">
                          <div>
                            <div className="saved-dashboard-title">{dashboard.name}</div>
                            <div className="saved-dashboard-subtitle">
                              {getDashboardTypeLabel(dashboard.dashboard_type)} ·{' '}
                              {getDashboardSourceTypeLabel(dashboard.source_type)}
                            </div>
                          </div>

                          <div className="saved-dashboard-badges">
                            {dashboard.is_default ? (
                              <span className="status-badge status-badge-info">По умолчанию</span>
                            ) : null}
                            {dashboard.is_shared ? (
                              <span className="status-badge status-badge-success">Общий</span>
                            ) : null}
                          </div>
                        </div>

                        <div className="saved-dashboard-description">
                          {dashboard.description || 'Описание отсутствует.'}
                        </div>

                        <div className="saved-dashboard-meta">
                          <div>
                            <strong>Обновлён:</strong> {formatDateTime(dashboard.updated_at)}
                          </div>
                          <div>
                            <strong>Последняя генерация:</strong>{' '}
                            {formatDateTime(dashboard.last_generated_at)}
                          </div>
                        </div>

                        <div className="saved-dashboard-actions">
                          <Button
                            className="secondary-pill-button"
                            onClick={() => applyDashboard(dashboard)}
                          >
                            Применить
                          </Button>

                          <Button
                            className="primary-pill-button"
                            onClick={() => openEditDashboardModal(dashboard)}
                          >
                            Редактировать
                          </Button>

                          <Button
                            className="secondary-pill-button dashboard-delete-button"
                            onClick={() => openDeleteDashboardModal(dashboard)}
                          >
                            Удалить
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : null}
          </>
        ) : null}
      </ContentCard>

      <Modal
        show={showDashboardModal}
        onHide={resetDashboardBuilder}
        centered
        className="projects-modal"
      >
        <Modal.Header closeButton>
          <Modal.Title>
            {editingDashboard ? 'Редактирование дашборда' : 'Создание дашборда'}
          </Modal.Title>
        </Modal.Header>

        <Form onSubmit={handleSaveDashboard}>
          <Modal.Body>
            <Row className="g-3">
              <Col md={12}>
                <Form.Group>
                  <Form.Label>Название</Form.Label>
                  <Form.Control
                    className="soft-input"
                    value={dashboardForm.name}
                    onChange={(event) =>
                      setDashboardForm((prev) => ({ ...prev, name: event.target.value }))
                    }
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
                    value={dashboardForm.description}
                    onChange={(event) =>
                      setDashboardForm((prev) => ({ ...prev, description: event.target.value }))
                    }
                  />
                </Form.Group>
              </Col>

              <Col md={6}>
                <Form.Group>
                  <Form.Label>Тип дашборда</Form.Label>
                  <Form.Select
                    className="soft-input"
                    value={dashboardForm.dashboardType}
                    onChange={(event) =>
                      setDashboardForm((prev) => ({
                        ...prev,
                        dashboardType: event.target.value as DashboardType,
                      }))
                    }
                  >
                    {DASHBOARD_TYPE_OPTIONS.map((item) => (
                      <option key={item.value} value={item.value}>
                        {item.label}
                      </option>
                    ))}
                  </Form.Select>
                </Form.Group>
              </Col>

              <Col md={6}>
                <Form.Group>
                  <Form.Label>Источник</Form.Label>
                  <Form.Select
                    className="soft-input"
                    value={dashboardForm.sourceType}
                    onChange={(event) =>
                      setDashboardForm((prev) => ({
                        ...prev,
                        sourceType: event.target.value as DashboardSourceType,
                      }))
                    }
                  >
                    <option value="project_aggregate">Сводный по проекту</option>
                  </Form.Select>
                </Form.Group>
              </Col>

              <Col md={12}>
                <div className="dashboard-builder-block">
                  <div className="dashboard-builder-title">Виджеты</div>

                  <div className="dashboard-widget-check-grid">
                    {DASHBOARD_WIDGET_OPTIONS.map((item) => (
                      <Form.Check
                        key={item.value}
                        type="checkbox"
                        id={`dashboard-widget-${item.value}`}
                        label={item.label}
                        checked={dashboardForm.widgets.includes(item.value)}
                        onChange={(event) =>
                          handleWidgetToggle(item.value, event.target.checked)
                        }
                        className="dashboard-widget-check"
                      />
                    ))}
                  </div>
                </div>
              </Col>

              <Col md={6}>
                <Form.Check
                  type="switch"
                  id="dashboard-shared"
                  label="Сделать общим"
                  checked={dashboardForm.isShared}
                  onChange={(event) =>
                    setDashboardForm((prev) => ({ ...prev, isShared: event.target.checked }))
                  }
                />
              </Col>

              <Col md={6}>
                <Form.Check
                  type="switch"
                  id="dashboard-default"
                  label="Сделать по умолчанию"
                  checked={dashboardForm.isDefault}
                  onChange={(event) =>
                    setDashboardForm((prev) => ({ ...prev, isDefault: event.target.checked }))
                  }
                />
              </Col>
            </Row>
          </Modal.Body>

          <Modal.Footer>
            <Button type="button" className="secondary-pill-button" onClick={resetDashboardBuilder}>
              Отмена
            </Button>
            <Button type="submit" className="primary-pill-button" disabled={isSavingDashboard}>
              {isSavingDashboard
                ? 'Сохранение...'
                : editingDashboard
                  ? 'Сохранить'
                  : 'Создать'}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>

      <Modal
        show={showDeleteDashboardModal}
        onHide={() => {
          setShowDeleteDashboardModal(false);
          setDeletingDashboard(null);
        }}
        centered
      >
        <Modal.Header closeButton>
          <Modal.Title>Удаление дашборда</Modal.Title>
        </Modal.Header>

        <Modal.Body>
          {deletingDashboard ? (
            <div className="archive-warning-text">
              Удалить дашборд <strong>{deletingDashboard.name}</strong>?
            </div>
          ) : null}
        </Modal.Body>

        <Modal.Footer>
          <Button
            className="secondary-pill-button"
            onClick={() => {
              setShowDeleteDashboardModal(false);
              setDeletingDashboard(null);
            }}
          >
            Отмена
          </Button>

          <Button
            className="secondary-pill-button dashboard-delete-button"
            onClick={() => void handleDeleteDashboard()}
            disabled={isDeletingDashboard}
          >
            {isDeletingDashboard ? 'Удаление...' : 'Удалить'}
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
}