import { useCallback, useEffect, useMemo, useState } from 'react';
import { Alert, Button, Col, Form, Row, Spinner, Table } from 'react-bootstrap';
import { adminApi } from '../../shared/api/admin';
import { rolesApi } from '../../shared/api/roles';
import { usersApi } from '../../shared/api/users';
import { getAccessStatusLabel, getRoleLabel } from '../../shared/lib/adminLabels';
import type { RoleCode, Role } from '../../shared/types/auth';
import type {
  AdminOverview,
  AdminPendingUser,
  AdminProjectAccessRequest,
  AdminUserListItem,
} from '../../shared/types/admin';
import { ContentCard } from '../../shared/ui/ContentCard';
import { useNavigate } from 'react-router-dom';

const APPROVE_ROLE_OPTIONS: RoleCode[] = ['viewer', 'operator', 'manager'];

function formatDateTime(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('ru-RU');
}

export default function AdminPage() {
  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [pendingUsers, setPendingUsers] = useState<AdminPendingUser[]>([]);
  const [users, setUsers] = useState<AdminUserListItem[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [accessRequests, setAccessRequests] = useState<AdminProjectAccessRequest[]>([]);

  const [userRoleFilter, setUserRoleFilter] = useState('all');
  const [pendingRoleSelections, setPendingRoleSelections] = useState<Record<number, RoleCode>>({});
  const [userRoleSelections, setUserRoleSelections] = useState<Record<number, RoleCode>>({});

  const [isLoading, setIsLoading] = useState(true);
  const [actionLoadingKey, setActionLoadingKey] = useState('');
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

    const loadAdminData = useCallback(async () => {
    try {
        setIsLoading(true);
        setError('');

        const [overviewData, pendingData, usersData, rolesData, accessData] = await Promise.all([
        adminApi.overview(),
        adminApi.pendingUsers(),
        usersApi.list(),
        rolesApi.list(),
        adminApi.projectAccessRequests('requested'),
        ]);

        setOverview(overviewData);
        setPendingUsers(pendingData);
        setUsers(usersData);
        setRoles(rolesData);
        setAccessRequests(accessData);

        setPendingRoleSelections(
        Object.fromEntries(
            pendingData.map((user) => [user.id, 'viewer' as RoleCode]),
        ),
        );

        const roleById = new Map(rolesData.map((role) => [role.id, role.code]));
        setUserRoleSelections(
        Object.fromEntries(
            usersData.map((user) => [user.id, (roleById.get(user.role_id) ?? 'viewer') as RoleCode]),
        ),
        );
    } catch {
        setError('Не удалось загрузить административные данные.');
    } finally {
        setIsLoading(false);
    }
    }, []);

  useEffect(() => {
    void loadAdminData();
  }, [loadAdminData]);

  const roleById = useMemo(() => {
    return new Map(roles.map((role) => [role.id, role]));
  }, [roles]);

  const filteredUsers = useMemo(() => {
    if (userRoleFilter === 'all') {
      return users;
    }

    return users.filter((user) => roleById.get(user.role_id)?.code === userRoleFilter);
  }, [users, userRoleFilter, roleById]);

    const runAction = async (
    key: string,
    action: () => Promise<unknown>,
    successText: string,
    ) => {
    try {
        setActionLoadingKey(key);
        setError('');
        setSuccessMessage('');
        await action();
        setSuccessMessage(successText);
        await loadAdminData();
    } catch {
        setError('Не удалось выполнить административное действие.');
    } finally {
        setActionLoadingKey('');
    }
    };

    const navigate = useNavigate();

  return (
      <ContentCard
        header={
        <div className="toolbar-row">
            <div className="toolbar-left">
            <h2 className="section-title mb-0">Панель администратора</h2>
            </div>

            <div className="admin-header-actions">
            <Button className="secondary-pill-button" onClick={() => navigate('/admin/templates')}>
                ML-шаблоны
            </Button>
            <Button className="secondary-pill-button" onClick={() => void loadAdminData()}>
                Обновить
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

      {!isLoading && overview ? (
        <>
          <Row className="g-3 mb-4">
            <Col md={3}>
              <div className="metric-card">
                <div className="metric-label">Пользователей</div>
                <div className="metric-value">{overview.total_users}</div>
              </div>
            </Col>

            <Col md={3}>
              <div className="metric-card">
                <div className="metric-label">Ожидают одобрения</div>
                <div className="metric-value">{overview.pending_users}</div>
              </div>
            </Col>

            <Col md={3}>
              <div className="metric-card">
                <div className="metric-label">Заблокировано</div>
                <div className="metric-value">{overview.blocked_users}</div>
              </div>
            </Col>

            <Col md={3}>
              <div className="metric-card">
                <div className="metric-label">Заявок доступа</div>
                <div className="metric-value">{overview.pending_project_access_requests}</div>
              </div>
            </Col>
          </Row>

          <div className="admin-section-card mb-4">
            <div className="admin-section-header">
              <div className="admin-section-title">Новые пользователи</div>
            </div>

            <div className="table-wrap">
              <Table borderless responsive className="prototype-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>ФИО</th>
                    <th>Email</th>
                    <th>Отдел</th>
                    <th>Должность</th>
                    <th>Роль после одобрения</th>
                    <th>Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {pendingUsers.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="text-center py-4">
                        Новых заявок нет
                      </td>
                    </tr>
                  ) : (
                    pendingUsers.map((user) => (
                      <tr key={user.id}>
                        <td>{user.id}</td>
                        <td>{user.full_name}</td>
                        <td>{user.email}</td>
                        <td>{user.department ?? '—'}</td>
                        <td>{user.position ?? '—'}</td>
                        <td>
                          <Form.Select
                            className="admin-inline-select"
                            value={pendingRoleSelections[user.id] ?? 'viewer'}
                            onChange={(event) =>
                              setPendingRoleSelections((prev) => ({
                                ...prev,
                                [user.id]: event.target.value as RoleCode,
                              }))
                            }
                          >
                            {APPROVE_ROLE_OPTIONS.map((roleCode) => (
                              <option key={roleCode} value={roleCode}>
                                {getRoleLabel(roleCode)}
                              </option>
                            ))}
                          </Form.Select>
                        </td>
                        <td>
                          <div className="admin-action-group">
                            <Button
                              size="sm"
                              className="primary-pill-button admin-small-button"
                              disabled={actionLoadingKey === `approve-${user.id}`}
                              onClick={() =>
                                void runAction(
                                  `approve-${user.id}`,
                                  () => adminApi.approveUser(user.id, pendingRoleSelections[user.id] ?? 'viewer'),
                                  'Пользователь успешно одобрен.',
                                )
                              }
                            >
                              Одобрить
                            </Button>

                            <Button
                              size="sm"
                              className="secondary-pill-button admin-small-button"
                              disabled={actionLoadingKey === `reject-${user.id}`}
                              onClick={() =>
                                void runAction(
                                  `reject-${user.id}`,
                                  () => adminApi.rejectUser(user.id),
                                  'Регистрация пользователя отклонена.',
                                )
                              }
                            >
                              Отклонить
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </Table>
            </div>
          </div>

          <div className="admin-section-card mb-4">
            <div className="toolbar-row admin-table-toolbar">
              <div className="toolbar-left">
                <div className="admin-section-title">Пользователи системы</div>
              </div>

              <Form.Select
                className="soft-select"
                value={userRoleFilter}
                onChange={(event) => setUserRoleFilter(event.target.value)}
              >
                <option value="all">Все роли</option>
                {roles.map((role) => (
                  <option key={role.id} value={role.code}>
                    {role.name}
                  </option>
                ))}
              </Form.Select>
            </div>

            <div className="table-wrap">
              <Table borderless responsive className="prototype-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>ФИО</th>
                    <th>Email</th>
                    <th>Роль</th>
                    <th>Активность</th>
                    <th>Блокировка</th>
                    <th>Последний вход</th>
                    <th>Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredUsers.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="text-center py-4">
                        Пользователи не найдены
                      </td>
                    </tr>
                  ) : (
                    filteredUsers.map((user) => {
                      const role = roleById.get(user.role_id);
                      const selectedRole = userRoleSelections[user.id] ?? (role?.code as RoleCode | undefined) ?? 'viewer';

                      return (
                        <tr key={user.id}>
                          <td>{user.id}</td>
                          <td>{user.full_name}</td>
                          <td>{user.email}</td>
                          <td>
                            <div className="admin-role-cell">
                              <span>{role?.name ?? '—'}</span>
                              <Form.Select
                                className="admin-inline-select"
                                value={selectedRole}
                                onChange={(event) =>
                                  setUserRoleSelections((prev) => ({
                                    ...prev,
                                    [user.id]: event.target.value as RoleCode,
                                  }))
                                }
                              >
                                {roles.map((item) => (
                                  <option key={item.id} value={item.code}>
                                    {item.name}
                                  </option>
                                ))}
                              </Form.Select>
                            </div>
                          </td>
                          <td>{user.is_active ? 'Активен' : 'Неактивен'}</td>
                          <td>{user.is_blocked ? 'Да' : 'Нет'}</td>
                          <td>{formatDateTime(user.last_login_at)}</td>
                          <td>
                            <div className="admin-action-group">
                              <Button
                                size="sm"
                                className="secondary-pill-button admin-small-button"
                                disabled={actionLoadingKey === `role-${user.id}`}
                                onClick={() =>
                                  void runAction(
                                    `role-${user.id}`,
                                    () => adminApi.assignUserRole(user.id, selectedRole),
                                    'Роль пользователя обновлена.',
                                  )
                                }
                              >
                                Сменить роль
                              </Button>

                              {user.is_blocked ? (
                                <Button
                                  size="sm"
                                  className="primary-pill-button admin-small-button"
                                  disabled={actionLoadingKey === `unblock-${user.id}`}
                                  onClick={() =>
                                    void runAction(
                                      `unblock-${user.id}`,
                                      () => adminApi.unblockUser(user.id),
                                      'Пользователь разблокирован.',
                                    )
                                  }
                                >
                                  Разблокировать
                                </Button>
                              ) : (
                                <Button
                                  size="sm"
                                  className="secondary-pill-button admin-small-button"
                                  disabled={actionLoadingKey === `block-${user.id}`}
                                  onClick={() =>
                                    void runAction(
                                      `block-${user.id}`,
                                      () => adminApi.blockUser(user.id),
                                      'Пользователь заблокирован.',
                                    )
                                  }
                                >
                                  Заблокировать
                                </Button>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </Table>
            </div>
          </div>

          <div className="admin-section-card">
            <div className="admin-section-header">
              <div className="admin-section-title">Запросы доступа к проектам</div>
            </div>

            <div className="table-wrap">
              <Table borderless responsive className="prototype-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Проект</th>
                    <th>Пользователь</th>
                    <th>Роль в проекте</th>
                    <th>Статус</th>
                    <th>Запрошено</th>
                    <th>Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {accessRequests.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="text-center py-4">
                        Запросов доступа нет
                      </td>
                    </tr>
                  ) : (
                    accessRequests.map((item) => (
                      <tr key={item.id}>
                        <td>{item.id}</td>
                        <td>
                          {item.project.name} ({item.project.code})
                        </td>
                        <td>{item.user.full_name}</td>
                        <td>{item.member_role}</td>
                        <td>{getAccessStatusLabel(item.access_status)}</td>
                        <td>{formatDateTime(item.requested_at)}</td>
                        <td>
                          <div className="admin-action-group">
                            <Button
                              size="sm"
                              className="primary-pill-button admin-small-button"
                              disabled={actionLoadingKey === `access-approve-${item.id}`}
                              onClick={() =>
                                void runAction(
                                  `access-approve-${item.id}`,
                                  () => adminApi.approveProjectAccess(item.id),
                                  'Запрос доступа одобрен.',
                                )
                              }
                            >
                              Одобрить
                            </Button>

                            <Button
                              size="sm"
                              className="secondary-pill-button admin-small-button"
                              disabled={actionLoadingKey === `access-reject-${item.id}`}
                              onClick={() =>
                                void runAction(
                                  `access-reject-${item.id}`,
                                  () => adminApi.rejectProjectAccess(item.id),
                                  'Запрос доступа отклонен.',
                                )
                              }
                            >
                              Отклонить
                            </Button>
                          </div>
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