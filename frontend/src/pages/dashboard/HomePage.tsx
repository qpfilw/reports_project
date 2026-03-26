import { useEffect, useMemo, useState } from 'react';
import { Alert, Col, Row, Spinner } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthProvider';
import { useProjectContext } from '../../features/projects/ProjectContext';
import { processingApi } from '../../shared/api/processing';
import { reportsApi } from '../../shared/api/reports';
import type { ProcessingTask } from '../../shared/types/processing';
import type { Report } from '../../shared/types/report';
import { ContentCard } from '../../shared/ui/ContentCard';

const quickActions = [
  { title: 'Проекты', text: 'Создание проектов, состав участников и выбор активного контекста.', to: '/projects' },
  { title: 'Отчётность', text: 'Создание отчётов, загрузка файлов и контроль жизненного цикла.', to: '/reports' },
  { title: 'Аналитика', text: 'Сводные показатели, диаграммы, дашборды и просмотр результатов.', to: '/analytics' },
  { title: 'Уведомления', text: 'Статусы задач, согласование и важные системные события.', to: '/notifications' },
];

function isWithinLastDay(value?: string | null) {
  if (!value) return false;

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return false;
  }

  return Date.now() - date.getTime() <= 24 * 60 * 60 * 1000;
}

export default function HomePage() {
  const { user } = useAuth();
  const { activeProjectId, activeProject } = useProjectContext();

  const [reports, setReports] = useState<Report[]>([]);
  const [tasks, setTasks] = useState<ProcessingTask[]>([]);
  const [isLoadingStats, setIsLoadingStats] = useState(true);
  const [statsError, setStatsError] = useState('');

  useEffect(() => {
    if (user?.role.code === 'pending') {
      return;
    }

    const loadStats = async () => {
      try {
        setIsLoadingStats(true);
        setStatsError('');

        const [reportsData, tasksData] = await Promise.all([
          reportsApi.list(),
          processingApi.listTasks(),
        ]);

        setReports(reportsData);
        setTasks(tasksData);
      } catch {
        setStatsError('Не удалось загрузить сводные показатели главной страницы.');
      } finally {
        setIsLoadingStats(false);
      }
    };

    void loadStats();
  }, [user?.role.code]);

  const reportIdsByProject = useMemo(() => {
    const ids = new Set<number>();

    reports.forEach((report) => {
      if (activeProjectId == null || report.project_id === activeProjectId) {
        ids.add(report.id);
      }
    });

    return ids;
  }, [reports, activeProjectId]);

  const filteredReports = useMemo(() => {
    return reports.filter((report) => {
      if (activeProjectId != null && report.project_id !== activeProjectId) {
        return false;
      }

      return true;
    });
  }, [reports, activeProjectId]);

  const filteredTasks = useMemo(() => {
    return tasks.filter((task) => reportIdsByProject.has(task.report_id));
  }, [tasks, reportIdsByProject]);

  const reportsInWork = useMemo(() => {
    return filteredReports.filter(
      (report) =>
        !report.is_archived &&
        !['approved', 'rejected', 'archived'].includes(report.status),
    ).length;
  }, [filteredReports]);

  const tasksInQueue = useMemo(() => {
    return filteredTasks.filter((task) => ['queued', 'running', 'retry'].includes(task.status)).length;
  }, [filteredTasks]);

  const errorsLastDay = useMemo(() => {
    return filteredTasks.reduce((total, task) => {
      const relevantDate = task.finished_at ?? task.started_at ?? task.created_at;
      if (!isWithinLastDay(relevantDate)) {
        return total;
      }

      return total + (task.error_count ?? 0);
    }, 0);
  }, [filteredTasks]);

  if (user?.role.code === 'pending') {
    return (
      <ContentCard
        header={
          <div className="section-header">
            <h2 className="section-title">Главная</h2>
          </div>
        }
      >
        <Alert variant="info" className="mb-4">
          Учётная запись ожидает подтверждения администратора. После одобрения откроется доступ к
          проектам, отчётности, аналитике и уведомлениям.
        </Alert>

        <Row className="g-3">
          <Col lg={7}>
            <div className="admin-section-card h-100">
              <div className="admin-section-title mb-3">Что доступно сейчас</div>
              <ul className="landing-help-list mb-0">
                <li>Просмотр информации о платформе и порядка работы.</li>
                <li>Редактирование профиля и смена пароля.</li>
                <li>Ожидание решения администратора по регистрации.</li>
              </ul>
            </div>
          </Col>

          <Col lg={5}>
            <div className="admin-section-card h-100 d-flex flex-column justify-content-between">
              <div>
                <div className="admin-section-title mb-3">Следующие шаги</div>
                <div className="landing-card-text mb-3">
                  Проверьте корректность личных данных и дождитесь подтверждения учётной записи.
                  После этого система откроет основной рабочий контур.
                </div>
              </div>

              <div className="d-flex gap-2 flex-wrap">
                <Link to="/profile" className="btn primary-pill-button">
                  Профиль
                </Link>
                <Link to="/settings" className="btn secondary-pill-button">
                  Настройки
                </Link>
              </div>
            </div>
          </Col>
        </Row>
      </ContentCard>
    );
  }

  return (
    <ContentCard
      header={
        <div className="section-header section-header-with-subtitle">
          <div>
            <h2 className="section-title">Главная</h2>
            <div className="section-subtitle">
              {activeProject ? `Показатели по проекту «${activeProject.name}»` : 'Сводные показатели по всем доступным проектам'}
            </div>
          </div>
        </div>
      }
    >
      {statsError ? <Alert variant="danger">{statsError}</Alert> : null}

      <Row className="g-3 mb-4">
        <Col md={4}>
          <div className="metric-card">
            <div className="metric-label">Отчётов в работе</div>
            <div className="metric-value">{isLoadingStats ? <Spinner animation="border" size="sm" /> : reportsInWork}</div>
          </div>
        </Col>
        <Col md={4}>
          <div className="metric-card">
            <div className="metric-label">Задач в очереди</div>
            <div className="metric-value">{isLoadingStats ? <Spinner animation="border" size="sm" /> : tasksInQueue}</div>
          </div>
        </Col>
        <Col md={4}>
          <div className="metric-card">
            <div className="metric-label">Ошибок за сутки</div>
            <div className="metric-value">{isLoadingStats ? <Spinner animation="border" size="sm" /> : errorsLastDay}</div>
          </div>
        </Col>
      </Row>

      <Row className="g-3">
        {quickActions.map((item) => (
          <Col md={6} xl={3} key={item.title}>
            <div className="admin-section-card h-100 d-flex flex-column justify-content-between">
              <div>
                <div className="admin-section-title mb-2">{item.title}</div>
                <div className="landing-card-text">{item.text}</div>
              </div>

              <div className="mt-3">
                <Link to={item.to} className="btn secondary-pill-button">
                  Открыть раздел
                </Link>
              </div>
            </div>
          </Col>
        ))}
      </Row>
    </ContentCard>
  );
}
