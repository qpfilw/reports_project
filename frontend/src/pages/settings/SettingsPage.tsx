import { useEffect, useState } from 'react';
import { Alert, Button, Form } from 'react-bootstrap';
import { storage } from '../../shared/lib/storage';
import { saveLastMlTemplateId } from '../../shared/lib/userSettings';
import { ContentCard } from '../../shared/ui/ContentCard';
import type { ExportFormat } from '../../shared/types/export';

const STORAGE_KEYS = {
  compactMode: 'reportrt.settings.compactMode',
  autoRefresh: 'reportrt.settings.autoRefresh',
  showRussianDates: 'reportrt.settings.showRussianDates',
  tablePageSize: 'reportrt.settings.tablePageSize',
  analyticsDefaultPeriod: 'reportrt.settings.analyticsDefaultPeriod',
  analyticsDefaultView: 'reportrt.settings.analyticsDefaultView',
  analyticsOnlyActiveProject: 'reportrt.settings.analyticsOnlyActiveProject',
  analyticsShowSavedDashboards: 'reportrt.settings.analyticsShowSavedDashboards',
  defaultExportFormat: 'reportrt.settings.defaultExportFormat',
  defaultProcessingPriority: 'reportrt.settings.defaultProcessingPriority',
  rememberLastMlTemplate: 'reportrt.settings.rememberLastMlTemplate',
  notificationsUnreadOnly: 'reportrt.settings.notificationsUnreadOnly',
  autoMarkNotificationsRead: 'reportrt.settings.autoMarkNotificationsRead',
  projectScopedBadges: 'reportrt.settings.projectScopedBadges',
  rememberActiveProject: 'reportrt.settings.rememberActiveProject',
} as const;

type AnalyticsDefaultView = 'overviewMetrics' | 'statusDistribution' | 'periodDynamics';
type AnalyticsDefaultPeriod = '30d' | '90d' | '180d' | '365d';
type ProcessingPriority = '1' | '3' | '5';

const ANALYTICS_PERIOD_LABELS: Record<AnalyticsDefaultPeriod, string> = {
  '30d': '30 дней',
  '90d': '90 дней',
  '180d': '180 дней',
  '365d': '365 дней',
};

interface SettingsState {
  compactMode: boolean;
  autoRefresh: boolean;
  showRussianDates: boolean;
  tablePageSize: number;
  analyticsDefaultPeriod: AnalyticsDefaultPeriod;
  analyticsDefaultView: AnalyticsDefaultView;
  analyticsOnlyActiveProject: boolean;
  analyticsShowSavedDashboards: boolean;
  defaultExportFormat: ExportFormat;
  defaultProcessingPriority: ProcessingPriority;
  rememberLastMlTemplate: boolean;
  notificationsUnreadOnly: boolean;
  autoMarkNotificationsRead: boolean;
  projectScopedBadges: boolean;
  rememberActiveProject: boolean;
}

const DEFAULT_SETTINGS: SettingsState = {
  compactMode: false,
  autoRefresh: true,
  showRussianDates: true,
  tablePageSize: 10,
  analyticsDefaultPeriod: '90d',
  analyticsDefaultView: 'overviewMetrics',
  analyticsOnlyActiveProject: true,
  analyticsShowSavedDashboards: true,
  defaultExportFormat: 'xlsx',
  defaultProcessingPriority: '3',
  rememberLastMlTemplate: true,
  notificationsUnreadOnly: false,
  autoMarkNotificationsRead: true,
  projectScopedBadges: true,
  rememberActiveProject: true,
};

function readBoolean(key: string, fallback: boolean) {
  const value = localStorage.getItem(key);
  if (value == null) return fallback;
  return value === 'true';
}

function readNumber(key: string, fallback: number) {
  const raw = localStorage.getItem(key);
  const parsed = raw ? Number(raw) : NaN;
  return Number.isFinite(parsed) ? parsed : fallback;
}

function readString<T extends string>(key: string, fallback: T): T {
  const value = localStorage.getItem(key);
  return (value as T | null) ?? fallback;
}

function persistSettings(settings: SettingsState) {
  localStorage.setItem(STORAGE_KEYS.compactMode, String(settings.compactMode));
  localStorage.setItem(STORAGE_KEYS.autoRefresh, String(settings.autoRefresh));
  localStorage.setItem(STORAGE_KEYS.showRussianDates, String(settings.showRussianDates));
  localStorage.setItem(STORAGE_KEYS.tablePageSize, String(settings.tablePageSize));
  localStorage.setItem(STORAGE_KEYS.analyticsDefaultPeriod, settings.analyticsDefaultPeriod);
  localStorage.setItem(STORAGE_KEYS.analyticsDefaultView, settings.analyticsDefaultView);
  localStorage.setItem(
    STORAGE_KEYS.analyticsOnlyActiveProject,
    String(settings.analyticsOnlyActiveProject),
  );
  localStorage.setItem(
    STORAGE_KEYS.analyticsShowSavedDashboards,
    String(settings.analyticsShowSavedDashboards),
  );
  localStorage.setItem(STORAGE_KEYS.defaultExportFormat, settings.defaultExportFormat);
  localStorage.setItem(
    STORAGE_KEYS.defaultProcessingPriority,
    settings.defaultProcessingPriority,
  );
  localStorage.setItem(
    STORAGE_KEYS.rememberLastMlTemplate,
    String(settings.rememberLastMlTemplate),
  );
  localStorage.setItem(
    STORAGE_KEYS.notificationsUnreadOnly,
    String(settings.notificationsUnreadOnly),
  );
  localStorage.setItem(
    STORAGE_KEYS.autoMarkNotificationsRead,
    String(settings.autoMarkNotificationsRead),
  );
  localStorage.setItem(STORAGE_KEYS.projectScopedBadges, String(settings.projectScopedBadges));
  localStorage.setItem(STORAGE_KEYS.rememberActiveProject, String(settings.rememberActiveProject));

  if (!settings.rememberActiveProject) {
    storage.removeActiveProject();
  }

  if (!settings.rememberLastMlTemplate) {
    saveLastMlTemplateId(null);
  }
}

function removeAllStoredSettings() {
  Object.values(STORAGE_KEYS).forEach((key) => localStorage.removeItem(key));
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<SettingsState>(DEFAULT_SETTINGS);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    try {
      const loaded: SettingsState = {
        compactMode: readBoolean(
          STORAGE_KEYS.compactMode,
          DEFAULT_SETTINGS.compactMode,
        ),
        autoRefresh: readBoolean(
          STORAGE_KEYS.autoRefresh,
          DEFAULT_SETTINGS.autoRefresh,
        ),
        showRussianDates: readBoolean(
          STORAGE_KEYS.showRussianDates,
          DEFAULT_SETTINGS.showRussianDates,
        ),
        tablePageSize: readNumber(
          STORAGE_KEYS.tablePageSize,
          DEFAULT_SETTINGS.tablePageSize,
        ),
        analyticsDefaultPeriod: readString<AnalyticsDefaultPeriod>(
          STORAGE_KEYS.analyticsDefaultPeriod,
          DEFAULT_SETTINGS.analyticsDefaultPeriod,
        ),
        analyticsDefaultView: readString<AnalyticsDefaultView>(
          STORAGE_KEYS.analyticsDefaultView,
          DEFAULT_SETTINGS.analyticsDefaultView,
        ),
        analyticsOnlyActiveProject: readBoolean(
          STORAGE_KEYS.analyticsOnlyActiveProject,
          DEFAULT_SETTINGS.analyticsOnlyActiveProject,
        ),
        analyticsShowSavedDashboards: readBoolean(
          STORAGE_KEYS.analyticsShowSavedDashboards,
          DEFAULT_SETTINGS.analyticsShowSavedDashboards,
        ),
        defaultExportFormat: readString<ExportFormat>(
          STORAGE_KEYS.defaultExportFormat,
          DEFAULT_SETTINGS.defaultExportFormat,
        ),
        defaultProcessingPriority: readString<ProcessingPriority>(
          STORAGE_KEYS.defaultProcessingPriority,
          DEFAULT_SETTINGS.defaultProcessingPriority,
        ),
        rememberLastMlTemplate: readBoolean(
          STORAGE_KEYS.rememberLastMlTemplate,
          DEFAULT_SETTINGS.rememberLastMlTemplate,
        ),
        notificationsUnreadOnly: readBoolean(
          STORAGE_KEYS.notificationsUnreadOnly,
          DEFAULT_SETTINGS.notificationsUnreadOnly,
        ),
        autoMarkNotificationsRead: readBoolean(
          STORAGE_KEYS.autoMarkNotificationsRead,
          DEFAULT_SETTINGS.autoMarkNotificationsRead,
        ),
        projectScopedBadges: readBoolean(
          STORAGE_KEYS.projectScopedBadges,
          DEFAULT_SETTINGS.projectScopedBadges,
        ),
        rememberActiveProject: readBoolean(
          STORAGE_KEYS.rememberActiveProject,
          DEFAULT_SETTINGS.rememberActiveProject,
        ),
      };

      setSettings(loaded);
    } catch {
      setError('Не удалось прочитать сохранённые настройки.');
    }
  }, []);

  const updateSetting = <K extends keyof SettingsState>(key: K, value: SettingsState[K]) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
    setSaved(false);
  };

  const handleSave = () => {
    try {
      persistSettings(settings);
      setSaved(true);
      setError('');
      window.setTimeout(() => setSaved(false), 1800);
    } catch {
      setError('Не удалось сохранить настройки.');
    }
  };

  const handleReset = () => {
    removeAllStoredSettings();
    setSettings(DEFAULT_SETTINGS);
    setSaved(false);
    setError('');
  };

  return (
    <ContentCard
      header={
        <div className="toolbar-row">
          <div className="toolbar-left">
            <h2 className="section-title mb-0">Настройки</h2>
          </div>

          <div className="settings-header-actions">
            <Button className="secondary-pill-button" onClick={handleReset}>
              Сбросить
            </Button>
            <Button className="primary-pill-button" onClick={handleSave}>
              {saved ? 'Сохранено' : 'Сохранить'}
            </Button>
          </div>
        </div>
      }
    >
      <div className="form-shell">
        {error ? <Alert variant="danger">{error}</Alert> : null}
        {saved ? <Alert variant="success">Настройки успешно сохранены.</Alert> : null}

        <div className="settings-grid">
          <div className="form-meta-card">
            <div className="form-meta-label">Интерфейс</div>

            <div className="settings-option-list">
              <Form.Check
                type="switch"
                id="auto-refresh"
                label="Автообновление статусов и уведомлений"
                checked={settings.autoRefresh}
                onChange={(event) => updateSetting('autoRefresh', event.target.checked)}
              />

              <Form.Check
                type="switch"
                id="remember-active-project"
                label="Запоминать активный проект между сессиями"
                checked={settings.rememberActiveProject}
                onChange={(event) =>
                  updateSetting('rememberActiveProject', event.target.checked)
                }
              />

              <Form.Group>
                <Form.Label>Количество строк в таблицах</Form.Label>
                <Form.Select
                  className="soft-input settings-select"
                  value={String(settings.tablePageSize)}
                  onChange={(event) =>
                    updateSetting('tablePageSize', Number(event.target.value))
                  }
                >
                  <option value="10">10 строк</option>
                  <option value="20">20 строк</option>
                  <option value="50">50 строк</option>
                </Form.Select>
              </Form.Group>
            </div>
          </div>

          <div className="form-meta-card">
            <div className="form-meta-label">Аналитика и дашборды</div>

            <div className="settings-option-list">
              <Form.Group>
                <Form.Label>Период аналитики по умолчанию</Form.Label>
                <Form.Select
                  className="soft-input settings-select"
                  value={settings.analyticsDefaultPeriod}
                  onChange={(event) =>
                    updateSetting(
                      'analyticsDefaultPeriod',
                      event.target.value as AnalyticsDefaultPeriod,
                    )
                  }
                >
                  <option value="30d">30 дней</option>
                  <option value="90d">90 дней</option>
                  <option value="180d">180 дней</option>
                  <option value="365d">365 дней</option>
                </Form.Select>
              </Form.Group>

              <Form.Group>
                <Form.Label>Стартовый вид аналитики</Form.Label>
                <Form.Select
                  className="soft-input settings-select"
                  value={settings.analyticsDefaultView}
                  onChange={(event) =>
                    updateSetting(
                      'analyticsDefaultView',
                      event.target.value as AnalyticsDefaultView,
                    )
                  }
                >
                  <option value="overviewMetrics">Ключевые показатели</option>
                  <option value="statusDistribution">Статусное распределение</option>
                  <option value="periodDynamics">Динамика по периодам</option>
                </Form.Select>
              </Form.Group>

              <Form.Check
                type="switch"
                id="analytics-only-project"
                label="Открывать аналитику только в контексте активного проекта"
                checked={settings.analyticsOnlyActiveProject}
                onChange={(event) =>
                  updateSetting('analyticsOnlyActiveProject', event.target.checked)
                }
              />

              <Form.Check
                type="switch"
                id="analytics-saved-dashboards"
                label="Показывать сохранённые дашборды по умолчанию"
                checked={settings.analyticsShowSavedDashboards}
                onChange={(event) =>
                  updateSetting('analyticsShowSavedDashboards', event.target.checked)
                }
              />
            </div>
          </div>

          <div className="form-meta-card">
            <div className="form-meta-label">Отчёты и обработка</div>

            <div className="settings-option-list">
              <Form.Group>
                <Form.Label>Формат экспорта по умолчанию</Form.Label>
                <Form.Select
                  className="soft-input settings-select"
                  value={settings.defaultExportFormat}
                  onChange={(event) =>
                    updateSetting(
                      'defaultExportFormat',
                      event.target.value as ExportFormat,
                    )
                  }
                >
                  <option value="xlsx">XLSX</option>
                  <option value="csv">CSV</option>
                  <option value="pdf">PDF</option>
                </Form.Select>
              </Form.Group>

              <Form.Group>
                <Form.Label>Приоритет обработки по умолчанию</Form.Label>
                <Form.Select
                  className="soft-input settings-select"
                  value={settings.defaultProcessingPriority}
                  onChange={(event) =>
                    updateSetting(
                      'defaultProcessingPriority',
                      event.target.value as ProcessingPriority,
                    )
                  }
                >
                  <option value="1">Низкий</option>
                  <option value="3">Обычный</option>
                  <option value="5">Повышенный</option>
                </Form.Select>
              </Form.Group>

              <Form.Check
                type="switch"
                id="remember-last-template"
                label="Подставлять последний использованный ML-шаблон"
                checked={settings.rememberLastMlTemplate}
                onChange={(event) =>
                  updateSetting('rememberLastMlTemplate', event.target.checked)
                }
              />
            </div>
          </div>

          <div className="form-meta-card">
            <div className="form-meta-label">Уведомления</div>

            <div className="settings-option-list">
              <Form.Check
                type="switch"
                id="notifications-unread-only"
                label="Показывать сначала только непрочитанные"
                checked={settings.notificationsUnreadOnly}
                onChange={(event) =>
                  updateSetting('notificationsUnreadOnly', event.target.checked)
                }
              />

              <Form.Check
                type="switch"
                id="auto-mark-read"
                label="Автоматически помечать уведомление прочитанным после перехода"
                checked={settings.autoMarkNotificationsRead}
                onChange={(event) =>
                  updateSetting('autoMarkNotificationsRead', event.target.checked)
                }
              />
            </div>
          </div>
          <div className="form-meta-card">
            <div className="form-meta-label">Сводка текущих предпочтений</div>

            <div className="settings-summary-list">
              <div className="settings-summary-item">
                <span>Таблицы</span>
                <strong>{settings.tablePageSize} строк</strong>
              </div>
              <div className="settings-summary-item">
                <span>Период аналитики</span>
                <strong>{ANALYTICS_PERIOD_LABELS[settings.analyticsDefaultPeriod]}</strong>
              </div>
              <div className="settings-summary-item">
                <span>Экспорт</span>
                <strong>{settings.defaultExportFormat.toUpperCase()}</strong>
              </div>
              <div className="settings-summary-item">
                <span>Приоритет обработки</span>
                <strong>{settings.defaultProcessingPriority}</strong>
              </div>
              <div className="settings-summary-item">
                <span>Активный проект</span>
                <strong>{settings.rememberActiveProject ? 'Запоминается' : 'Не сохраняется'}</strong>
              </div>
            </div>
          </div>
        </div>
      </div>
    </ContentCard>
  );
}