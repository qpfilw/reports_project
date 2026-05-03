import { useEffect, useMemo, useState } from 'react';
import { Badge, Button, Dropdown, Spinner } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { notificationsApi } from '../api/notifications';
import {
  getNotificationDisplayTitle,
  getNotificationTargetUrl,
  getNotificationTypeClassName,
} from '../lib/notificationLabels';
import { readUserSettings } from '../lib/userSettings';
import type { NotificationItem } from '../types/notification';
import bellIcon from '../../assets/icons/notification.png';

function formatDateTime(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('ru-RU');
}

export function NotificationsBell() {
  const navigate = useNavigate();
  const settings = readUserSettings();

  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isActionLoading, setIsActionLoading] = useState(false);

  useEffect(() => {
    let isMounted = true;

    const load = async () => {
      try {
        const data = await notificationsApi.list();
        if (isMounted) {
          setNotifications(data);
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

  const unreadCount = useMemo(() => {
    return notifications.filter((item) => !item.is_read).length;
  }, [notifications]);

  const latestNotifications = useMemo(() => {
    return notifications.slice(0, settings.tablePageSize);
  }, [notifications, settings.tablePageSize]);

  const handleOpenNotification = async (notification: NotificationItem) => {
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

  const handleMarkAllRead = async () => {
    try {
      setIsActionLoading(true);
      await notificationsApi.markAllRead(notifications);
      const updated = await notificationsApi.list();
      setNotifications(updated);
    } finally {
      setIsActionLoading(false);
    }
  };

  return (
    <Dropdown align="end" className="notification-bell-dropdown">
      <Dropdown.Toggle className="notification-bell-button" id="notifications-dropdown">
        <img src={bellIcon} alt="Уведомления" className="notification-bell-image" />
        {unreadCount > 0 ? <Badge pill bg="primary">{unreadCount}</Badge> : null}
      </Dropdown.Toggle>

      <Dropdown.Menu className="notification-dropdown-menu">
        <div className="notification-dropdown-header">
          <div className="notification-dropdown-title">Уведомления</div>

          <Button
            variant="link"
            className="notification-dropdown-link"
            disabled={isActionLoading || unreadCount === 0}
            onClick={() => void handleMarkAllRead()}
          >
            Прочитать все
          </Button>
        </div>

        {isLoading ? (
          <div className="notification-dropdown-empty">
            <Spinner animation="border" size="sm" />
          </div>
        ) : latestNotifications.length === 0 ? (
          <div className="notification-dropdown-empty">Уведомлений нет</div>
        ) : (
          latestNotifications.map((notification) => (
            <button
              key={notification.id}
              type="button"
              className={`notification-dropdown-item ${notification.is_read ? '' : 'notification-dropdown-item-unread'}`}
              onClick={() => void handleOpenNotification(notification)}
            >
              <div className="notification-dropdown-item-top">
                <span className={getNotificationTypeClassName(notification.type)}>
                    {getNotificationDisplayTitle(notification)}
                </span>
                <span className="notification-dropdown-date">
                  {formatDateTime(notification.created_at)}
                </span>
              </div>

              <div className="notification-dropdown-message">
                {notification.message}
              </div>
            </button>
          ))
        )}

        <Dropdown.Divider />

        <Button
          variant="link"
          className="notification-dropdown-footer-link"
          onClick={() => navigate('/notifications')}
        >
          Открыть все уведомления
        </Button>
      </Dropdown.Menu>
    </Dropdown>
  );
}