import { useEffect, useMemo, useRef, useState } from 'react';
import { Form, Spinner } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthProvider';
import { projectsApi } from '../api/projects';
import { reportsApi } from '../api/reports';
import { getReportStatusLabel } from '../lib/reportStatus';
import type { Project } from '../types/project';
import type { Report } from '../types/report';
import { NotificationsBell } from './NotificationsBell';
import { ProjectSwitcher } from './ProjectSwitcher';

type SearchResultType = 'section' | 'settings' | 'project' | 'report';

interface SearchResultItem {
  id: string;
  title: string;
  subtitle: string;
  route: string;
  searchText: string;
  type: SearchResultType;
}

function getTypeLabel(type: SearchResultType) {
  switch (type) {
    case 'section':
      return 'Раздел';
    case 'settings':
      return 'Настройка';
    case 'project':
      return 'Проект';
    case 'report':
      return 'Отчёт';
    default:
      return type;
  }
}

function normalizeText(value: string) {
  return value.trim().toLowerCase();
}

function scoreSearchResult(item: SearchResultItem, query: string) {
  const normalizedTitle = item.title.toLowerCase();
  const normalizedSubtitle = item.subtitle.toLowerCase();

  if (normalizedTitle.startsWith(query)) return 0;
  if (normalizedTitle.includes(query)) return 1;
  if (normalizedSubtitle.includes(query)) return 2;
  if (item.searchText.includes(query)) return 3;
  return 4;
}

function buildProjectItems(projects: Project[]): SearchResultItem[] {
  return projects.map((project) => ({
    id: `project-${project.id}`,
    title: project.name,
    subtitle: `${project.code} · ${project.is_archived ? 'архивный проект' : 'проект'}`,
    route: `/projects/${project.id}`,
    searchText: [project.name, project.code, project.description ?? '', project.is_archived ? 'архив' : 'активный']
      .join(' ')
      .toLowerCase(),
    type: 'project',
  }));
}

function buildReportItems(reports: Report[]): SearchResultItem[] {
  return reports.map((report) => ({
    id: `report-${report.id}`,
    title: report.title,
    subtitle: `Отчёт #${report.id} · ${getReportStatusLabel(report.status)}`,
    route: `/reports/${report.id}/edit`,
    searchText: [
      report.title,
      report.description ?? '',
      `отчёт ${report.id}`,
      getReportStatusLabel(report.status),
      report.report_period_start,
      report.report_period_end,
    ]
      .join(' ')
      .toLowerCase(),
    type: 'report',
  }));
}

export function TopSearchBar() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const containerRef = useRef<HTMLDivElement | null>(null);
  const hasLoadedRef = useRef(false);

  const [query, setQuery] = useState('');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isLoadingData, setIsLoadingData] = useState(false);
  const [searchError, setSearchError] = useState('');
  const [projectItems, setProjectItems] = useState<SearchResultItem[]>([]);
  const [reportItems, setReportItems] = useState<SearchResultItem[]>([]);

  const staticItems = useMemo<SearchResultItem[]>(() => {
    const items: SearchResultItem[] = [
      {
        id: 'section-dashboard',
        title: 'Главная панель',
        subtitle: 'Главная страница системы',
        route: '/dashboard',
        searchText: 'главная панель dashboard домашняя страница home',
        type: 'section',
      },
      {
        id: 'section-projects',
        title: 'Проекты',
        subtitle: 'Список и карточки проектов',
        route: '/projects',
        searchText: 'проекты карточка проекта список проектов',
        type: 'section',
      },
      {
        id: 'section-reports',
        title: 'Отчётность',
        subtitle: 'Реестр отчётов и обработка',
        route: '/reports',
        searchText: 'отчёт отчетность список отчетов реестр обработка',
        type: 'section',
      },
      {
        id: 'section-analytics',
        title: 'Аналитика',
        subtitle: 'Графики, KPI и дашборды',
        route: '/analytics',
        searchText: 'аналитика графики dashboard kpi дашборд',
        type: 'section',
      },
      {
        id: 'section-notifications',
        title: 'Уведомления',
        subtitle: 'Список уведомлений и статусы',
        route: '/notifications',
        searchText: 'уведомления события статусы уведомление',
        type: 'section',
      },
      {
        id: 'section-profile',
        title: 'Профиль пользователя',
        subtitle: 'Личная информация и пароль',
        route: '/profile',
        searchText: 'профиль пользователь аккаунт пароль настройки профиля',
        type: 'section',
      },
      {
        id: 'settings-interface',
        title: 'Настройки интерфейса',
        subtitle: 'Автообновление, активный проект и таблицы',
        route: '/settings#settings-interface',
        searchText: 'настройки интерфейс автообновление активный проект таблицы',
        type: 'settings',
      },
      {
        id: 'settings-analytics',
        title: 'Настройки аналитики',
        subtitle: 'Период, стартовый вид и дашборды',
        route: '/settings#settings-analytics',
        searchText: 'настройки аналитика период стартовый вид дашборды',
        type: 'settings',
      },
      {
        id: 'settings-reports',
        title: 'Настройки отчётов и обработки',
        subtitle: 'Экспорт, приоритет и ML-шаблоны',
        route: '/settings#settings-reports',
        searchText: 'настройки отчеты обработка экспорт приоритет ml шаблон',
        type: 'settings',
      },
      {
        id: 'settings-notifications',
        title: 'Настройки уведомлений',
        subtitle: 'Фильтрация непрочитанных и автопометка',
        route: '/settings#settings-notifications',
        searchText: 'настройки уведомления непрочитанные автопометка',
        type: 'settings',
      },
      {
        id: 'settings-summary',
        title: 'Сводка пользовательских предпочтений',
        subtitle: 'Итог сохранённых настроек',
        route: '/settings#settings-summary',
        searchText: 'настройки сводка предпочтения итог сохраненные параметры',
        type: 'settings',
      },
    ];

    if (user?.role.code === 'admin') {
      items.push(
        {
          id: 'section-admin',
          title: 'Панель администратора',
          subtitle: 'Пользователи, заявки и шаблоны',
          route: '/admin',
          searchText: 'администратор admin пользователи заявки роли шаблоны',
          type: 'section',
        },
        {
          id: 'section-admin-audit',
          title: 'Журнал аудита',
          subtitle: 'История действий в системе',
          route: '/admin/audit',
          searchText: 'аудит журнал история действий лог',
          type: 'section',
        },
      );
    }

    return items;
  }, [user?.role.code]);

  const ensureSearchDataLoaded = async () => {
    if (hasLoadedRef.current || isLoadingData) {
      return;
    }

    try {
      setIsLoadingData(true);
      setSearchError('');

      const [projects, reports] = await Promise.all([projectsApi.list(), reportsApi.list()]);
      setProjectItems(buildProjectItems(projects));
      setReportItems(buildReportItems(reports));
      hasLoadedRef.current = true;
    } catch {
      setSearchError('Не удалось загрузить данные для глобального поиска.');
    } finally {
      setIsLoadingData(false);
    }
  };

  useEffect(() => {
    const handlePointerDown = (event: MouseEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handlePointerDown);
    document.addEventListener('keydown', handleEscape);

    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
      document.removeEventListener('keydown', handleEscape);
    };
  }, []);

  const results = useMemo(() => {
    const normalizedQuery = normalizeText(query);
    const mergedItems = [...staticItems, ...projectItems, ...reportItems];

    if (!normalizedQuery) {
      return staticItems.slice(0, 6);
    }

    return mergedItems
      .filter((item) => item.searchText.includes(normalizedQuery))
      .sort((a, b) => scoreSearchResult(a, normalizedQuery) - scoreSearchResult(b, normalizedQuery))
      .slice(0, 12);
  }, [projectItems, query, reportItems, staticItems]);

  const handleSelectResult = (route: string) => {
    setQuery('');
    setIsDropdownOpen(false);
    navigate(route);
  };

  return (
    <div className="top-search-wrap">
      <div className="top-search-row">
        <div ref={containerRef} className="top-search-box">
          <Form.Control
            type="search"
            placeholder="Найти проект, отчёт, настройку или раздел"
            className="top-search-input"
            value={query}
            onFocus={() => {
              setIsDropdownOpen(true);
              void ensureSearchDataLoaded();
            }}
            onChange={(event) => {
              setQuery(event.target.value);
              setIsDropdownOpen(true);
              void ensureSearchDataLoaded();
            }}
          />

          {isDropdownOpen ? (
            <div className="global-search-dropdown">
              <div className="global-search-header">
                <div className="global-search-title">Глобальный поиск</div>
                {isLoadingData ? (
                  <div className="global-search-loading">
                    <Spinner animation="border" size="sm" />
                    <span>Загрузка</span>
                  </div>
                ) : null}
              </div>

              {searchError ? <div className="global-search-empty">{searchError}</div> : null}

              {!searchError && results.length === 0 ? (
                <div className="global-search-empty">Ничего не найдено.</div>
              ) : null}

              {!searchError && results.length > 0 ? (
                <div className="global-search-results">
                  {results.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      className="global-search-item"
                      onClick={() => handleSelectResult(item.route)}
                    >
                      <div className="global-search-item-top">
                        <span className="global-search-item-title">{item.title}</span>
                        <span className="global-search-item-type">{getTypeLabel(item.type)}</span>
                      </div>
                      <div className="global-search-item-subtitle">{item.subtitle}</div>
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
          ) : null}
        </div>

        <div className="top-bar-actions">
          <ProjectSwitcher />
          <NotificationsBell />
        </div>
      </div>
    </div>
  );
}
