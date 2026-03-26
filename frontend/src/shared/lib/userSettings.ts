import type { ExportFormat } from '../types/export';

export type AnalyticsDefaultView = 'overviewMetrics' | 'statusDistribution' | 'periodDynamics';
export type AnalyticsDefaultPeriod = '30d' | '90d' | '180d' | '365d';
export type ProcessingPriority = '1' | '3' | '5';

export const USER_SETTINGS_KEYS = {
  autoRefresh: 'reportrt.settings.autoRefresh',
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
  rememberActiveProject: 'reportrt.settings.rememberActiveProject',
  lastMlTemplateId: 'reportrt.settings.lastMlTemplateId',
} as const;

export interface UserSettingsSnapshot {
  autoRefresh: boolean;
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
  rememberActiveProject: boolean;
  lastMlTemplateId: string | null;
}

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

export function readUserSettings(): UserSettingsSnapshot {
  return {
    autoRefresh: readBoolean(USER_SETTINGS_KEYS.autoRefresh, true),
    tablePageSize: readNumber(USER_SETTINGS_KEYS.tablePageSize, 10),
    analyticsDefaultPeriod: readString<AnalyticsDefaultPeriod>(
      USER_SETTINGS_KEYS.analyticsDefaultPeriod,
      '90d',
    ),
    analyticsDefaultView: readString<AnalyticsDefaultView>(
      USER_SETTINGS_KEYS.analyticsDefaultView,
      'overviewMetrics',
    ),
    analyticsOnlyActiveProject: readBoolean(
      USER_SETTINGS_KEYS.analyticsOnlyActiveProject,
      true,
    ),
    analyticsShowSavedDashboards: readBoolean(
      USER_SETTINGS_KEYS.analyticsShowSavedDashboards,
      true,
    ),
    defaultExportFormat: readString<ExportFormat>(
      USER_SETTINGS_KEYS.defaultExportFormat,
      'xlsx',
    ),
    defaultProcessingPriority: readString<ProcessingPriority>(
      USER_SETTINGS_KEYS.defaultProcessingPriority,
      '3',
    ),
    rememberLastMlTemplate: readBoolean(
      USER_SETTINGS_KEYS.rememberLastMlTemplate,
      true,
    ),
    notificationsUnreadOnly: readBoolean(
      USER_SETTINGS_KEYS.notificationsUnreadOnly,
      false,
    ),
    autoMarkNotificationsRead: readBoolean(
      USER_SETTINGS_KEYS.autoMarkNotificationsRead,
      true,
    ),
    rememberActiveProject: readBoolean(
      USER_SETTINGS_KEYS.rememberActiveProject,
      true,
    ),
    lastMlTemplateId: localStorage.getItem(USER_SETTINGS_KEYS.lastMlTemplateId),
  };
}

export function saveLastMlTemplateId(templateId: string | null) {
  if (!templateId) {
    localStorage.removeItem(USER_SETTINGS_KEYS.lastMlTemplateId);
    return;
  }

  localStorage.setItem(USER_SETTINGS_KEYS.lastMlTemplateId, templateId);
}