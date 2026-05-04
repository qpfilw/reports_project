import { useEffect, useMemo, useState } from 'react';
import { Alert, Button, Spinner, Table } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { notificationsApi } from '../../shared/api/notifications';
import {
  getNotificationCompactLabel,
  getNotificationDisplayTitle,
  getNotificationTargetUrl,
  getNotificationTypeClassName,
} from '../../shared/lib/notificationLabels';
import { readUserSettings } from '../../shared/lib/userSettings';
import type { NotificationItem } from '../../shared/types/notification';
import { ContentCard } from '../../shared/ui/ContentCard';

function formatDateTime(value?: string | null) {
  if (!value) return '-';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString('ru-RU');
}

export default function NotificationsPage() {
  const navigate = useNavigate();
  const settings = readUserSettings();

  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isActionLoading, setIsActionLoading] = useState(false);
  const [filter, setFilter] = useState<'all' | 'unread' | 'read'>(
    settings.notificationsUnreadOnly ? 'unread' : 'all',
  );
  const [error, setError] = useState('');

  useEffect(() => {
    let isMounted = true;

    const load = async () => {
      try {
        if (isMounted) {
          setIsLoading(true);
          setError('');
        }

        const data = await notificationsApi.list();

        if (isMounted) {
          setNotifications(data);
        }
      } catch {
        if (isMounted) {
          setError('Не удалось загрузить уведомления.');
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    void load();

    if (!settings.autoRefresh) {
      return () => {
        isMounted = false;
      };
    }

    const interval = window.setInterval(() => {
      void load();
    }, 20000);

    return () => {
      isMounted = false;
      window.clearInterval(interval);
    };
  }, [settings.autoRefresh]);

  const filteredNotifications = useMemo(() => {
    if (filter === 'unread') {
      return notifications.filter((item) => !item.is_read);
    }

    if (filter === 'read') {
      return notifications.filter((item) => item.is_read);
    }

    return notifications;
  }, [notifications, filter]);

  const visibleNotifications = useMemo(() => {
    return filteredNotifications.slice(0, settings.tablePageSize);
  }, [filteredNotifications, settings.tablePageSize]);

  const handleOpen = async (notification: NotificationItem) => {
    try {
      if (settings.autoMarkNotificationsRead && !notification.is_read) {
        const updated = await notificationsApi.markRead(notification.id);
        setNotifications((prev) =>
          prev.map((item) => (item.id === updated.id ? updated : item)),
        );
      }
    } finally {
      navigate(getNotificationTargetUrl(notification));
    }
  };

  const handleMarkRead = async (notificationId: number) => {
    try {
      setIsActionLoading(true);
      const updated = await notificationsApi.markRead(notificationId);
      setNotifications((prev) =>
        prev.map((item) => (item.id === updated.id ? updated : item)),
      );
    } catch {
      setError('Не удалось отметить уведомление как прочитанное.');
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      setIsActionLoading(true);
      await notificationsApi.markAllRead(notifications);
      const data = await notificationsApi.list();
      setNotifications(data);
    } catch {
      setError('Не удалось отметить все уведомления как прочитанные.');
    } finally {
      setIsActionLoading(false);
    }
  };

  return (
    <ContentCard
      header={
        <div className="toolbar-row">
          <div className="toolbar-left">
            <h2 className="section-title mb-0">Уведомления</h2>

            <div className="notifications-filter-group">
              <Button
                className={filter === 'all' ? 'primary-pill-button notifications-filter-button' : 'secondary-pill-button notifications-filter-button'}
                onClick={() => setFilter('all')}
              >
                Все
              </Button>
              <Button
                className={filter === 'unread' ? 'primary-pill-button notifications-filter-button' : 'secondary-pill-button notifications-filter-button'}
                onClick={() => setFilter('unread')}
              >
                Непрочитанные
              </Button>
              <Button
                className={filter === 'read' ? 'primary-pill-button notifications-filter-button' : 'secondary-pill-button notifications-filter-button'}
                onClick={() => setFilter('read')}
              >
                Прочитанные
              </Button>
            </div>
          </div>

          <Button
            className="secondary-pill-button"
            disabled={isActionLoading || notifications.every((item) => item.is_read)}
            onClick={() => void handleMarkAllRead()}
          >
            Прочитать все
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
        <div className="table-wrap">
          <Table borderless responsive className="prototype-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Тип</th>
                <th>Заголовок</th>
                <th>Сообщение</th>
                <th>Статус</th>
                <th>Создано</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              {visibleNotifications.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-4">
                    Уведомления не найдены
                  </td>
                </tr>
              ) : (
                visibleNotifications.map((notification) => (
                  <tr
                    key={notification.id}
                    className={`table-row-clickable ${notification.is_read ? '' : 'notification-table-row-unread'}`}
                    onClick={() => void handleOpen(notification)}
                  >
                    <td>{notification.id}</td>
                    <td>
                        <span className={`${getNotificationTypeClassName(notification.type)} notification-type-badge-table`}>
                            {getNotificationCompactLabel(notification.type)}
                        </span>
                    </td>
                    <td>{getNotificationDisplayTitle(notification)}</td>
                    <td>{notification.message}</td>
                    <td>
                      <span className={notification.is_read ? 'status-badge status-badge-muted' : 'status-badge status-badge-info'}>
                        {notification.is_read ? 'Прочитано' : 'Новое'}
                      </span>
                    </td>
                    <td>{formatDateTime(notification.created_at)}</td>
                    <td onClick={(event) => event.stopPropagation()}>
                      {!notification.is_read ? (
                        <Button
                          size="sm"
                          className="secondary-pill-button notifications-action-button"
                          disabled={isActionLoading}
                          onClick={() => void handleMarkRead(notification.id)}
                        >
                          Прочитать
                        </Button>
                      ) : (
                        <Button
                          size="sm"
                          className="primary-pill-button notifications-action-button"
                          onClick={() => void handleOpen(notification)}
                        >
                          Открыть
                        </Button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </Table>
        </div>
      ) : null}
    </ContentCard>
  );
}