import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Alert,
  Button,
  Col,
  Form,
  Modal,
  Row,
  Spinner,
  Table,
} from 'react-bootstrap';
import { ContentCard } from '../../shared/ui/ContentCard';
import { auditApi } from '../../shared/api/audit';
import { adminApi } from '../../shared/api/admin';
import { usersApi } from '../../shared/api/users';
import { projectsApi } from '../../shared/api/projects';
import { getAuditActionLabel, getAuditEntityLabel } from '../../shared/lib/auditLabels';
import { readUserSettings } from '../../shared/lib/userSettings';
import type { AuditAction, AuditEntityType, AuditLog, AuditLogDetail } from '../../shared/types/audit';


function formatDateTime(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('ru-RU');
}

function stringifyJson(value: Record<string, unknown> | null) {
  if (!value) return '—';
  return JSON.stringify(value, null, 2);
}

const actionOptions: AuditAction[] = [
  'create',
  'update',
  'delete',
  'submit',
  'approve',
  'reject',
  'process_start',
  'process_retry',
  'process_finish',
  'login',
  'logout',
  'export',
];

const entityOptions: AuditEntityType[] = [
  'user',
  'project',
  'report',
  'report_upload',
  'template',
  'task',
  'dashboard',
];

export default function AdminAuditPage() {
  const navigate = useNavigate();
  const pageSize = readUserSettings().tablePageSize;

  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [selectedAudit, setSelectedAudit] = useState<AuditLogDetail | null>(null);
  const [selectedAuditId, setSelectedAuditId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [error, setError] = useState('');
  const [detailError, setDetailError] = useState('');
  const [totalAuditCount, setTotalAuditCount] = useState<number | null>(null);

  const [search, setSearch] = useState('');
  const [actionFilter, setActionFilter] = useState<'all' | AuditAction>('all');
  const [entityFilter, setEntityFilter] = useState<'all' | AuditEntityType>('all');

  const [userNames, setUserNames] = useState<Record<number, string>>({});
  const [projectNames, setProjectNames] = useState<Record<number, string>>({});

  const loadAuditData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError('');

      const [logsData, overviewData, usersData, projectsData] = await Promise.all([
        auditApi.list(),
        adminApi.overview(),
        usersApi.list(),
        projectsApi.list(),
      ]);

      setLogs(logsData);
      setTotalAuditCount(overviewData.total_audit_logs);
      setUserNames(
        Object.fromEntries(usersData.map((item) => [item.id, item.full_name || item.email])),
      );
      setProjectNames(
        Object.fromEntries(projectsData.map((item) => [item.id, item.name])),
      );
    } catch {
      setError('Не удалось загрузить журнал аудита.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadAuditData();
  }, [loadAuditData]);

  const filteredLogs = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();

    return logs.filter((item) => {
      if (actionFilter !== 'all' && item.action !== actionFilter) {
        return false;
      }

      if (entityFilter !== 'all' && item.entity_type !== entityFilter) {
        return false;
      }

      if (!normalizedSearch) {
        return true;
      }

      const userText = item.user_id ? userNames[item.user_id] ?? `Пользователь #${item.user_id}` : '';
      const projectText = item.project_id ? projectNames[item.project_id] ?? `Проект #${item.project_id}` : '';
      const haystack = [
        String(item.id),
        getAuditActionLabel(item.action),
        getAuditEntityLabel(item.entity_type),
        String(item.entity_id ?? ''),
        String(item.user_id ?? ''),
        String(item.project_id ?? ''),
        item.ip_address ?? '',
        userText,
        projectText,
      ]
        .join(' ')
        .toLowerCase();

      return haystack.includes(normalizedSearch);
    });
  }, [logs, search, actionFilter, entityFilter, userNames, projectNames]);

  const visibleLogs = useMemo(() => filteredLogs.slice(0, pageSize), [filteredLogs, pageSize]);

  const openDetail = async (auditId: number) => {
    try {
      setSelectedAuditId(auditId);
      setIsModalOpen(true);
      setIsDetailLoading(true);
      setDetailError('');
      const detail = await auditApi.getById(auditId);
      setSelectedAudit(detail);
    } catch {
      setDetailError('Не удалось загрузить подробности записи аудита.');
      setSelectedAudit(null);
    } finally {
      setIsDetailLoading(false);
    }
  };

  const closeDetail = () => {
    setIsModalOpen(false);
    setSelectedAudit(null);
    setSelectedAuditId(null);
    setDetailError('');
  };

  return (
    <>
      <ContentCard
        header={
          <div className="toolbar-row">
            <div className="toolbar-left">
              <h2 className="section-title mb-0">Журнал аудита</h2>
            </div>

            <div className="admin-header-actions">
              <Button className="secondary-pill-button" onClick={() => navigate('/admin')}>
                Назад
              </Button>
              <Button className="secondary-pill-button" onClick={() => void loadAuditData()}>
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

        {!isLoading ? (
          <>
            <Row className="g-3 mb-4">
              <Col md={4}>
                <div className="metric-card">
                  <div className="metric-label">Всего записей</div>
                  <div className="metric-value">{totalAuditCount ?? logs.length}</div>
                </div>
              </Col>
              <Col md={4}>
                <div className="metric-card">
                  <div className="metric-label">Загружено на страницу</div>
                  <div className="metric-value">{logs.length}</div>
                </div>
              </Col>
              <Col md={4}>
                <div className="metric-card">
                  <div className="metric-label">После фильтрации</div>
                  <div className="metric-value">{filteredLogs.length}</div>
                </div>
              </Col>
            </Row>

            <div className="admin-section-card mb-4">
              <div className="toolbar-row admin-table-toolbar mb-3">
                <div className="toolbar-left">
                  <div className="admin-section-title">Последние действия в системе</div>
                </div>
              </div>

              <Row className="g-3 mb-3">
                <Col lg={4}>
                  <Form.Control
                    className="soft-input"
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    placeholder="Поиск по ID, пользователю, проекту, IP"
                  />
                </Col>

                <Col md={4} lg={3}>
                  <Form.Select
                    className="soft-select w-100"
                    value={actionFilter}
                    onChange={(event) => setActionFilter(event.target.value as 'all' | AuditAction)}
                  >
                    <option value="all">Все действия</option>
                    {actionOptions.map((action) => (
                      <option key={action} value={action}>
                        {getAuditActionLabel(action)}
                      </option>
                    ))}
                  </Form.Select>
                </Col>

                <Col md={4} lg={3}>
                  <Form.Select
                    className="soft-select w-100"
                    value={entityFilter}
                    onChange={(event) => setEntityFilter(event.target.value as 'all' | AuditEntityType)}
                  >
                    <option value="all">Все сущности</option>
                    {entityOptions.map((entity) => (
                      <option key={entity} value={entity}>
                        {getAuditEntityLabel(entity)}
                      </option>
                    ))}
                  </Form.Select>
                </Col>

                <Col md={4} lg={2}>
                  <div className="audit-page-limit-note">Показывается до {pageSize} строк</div>
                </Col>
              </Row>

              <div className="table-wrap">
                <Table borderless responsive className="prototype-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Дата и время</th>
                      <th>Действие</th>
                      <th>Сущность</th>
                      <th>Пользователь</th>
                      <th>Проект</th>
                      <th>IP</th>
                      <th>Детали</th>
                    </tr>
                  </thead>
                  <tbody>
                    {visibleLogs.length === 0 ? (
                      <tr>
                        <td colSpan={8} className="text-center py-4">
                          Записи журнала не найдены
                        </td>
                      </tr>
                    ) : (
                      visibleLogs.map((item) => (
                        <tr key={item.id}>
                          <td>{item.id}</td>
                          <td>{formatDateTime(item.created_at)}</td>
                          <td>{getAuditActionLabel(item.action)}</td>
                          <td>
                            {getAuditEntityLabel(item.entity_type)}
                            {item.entity_id != null ? ` #${item.entity_id}` : ''}
                          </td>
                          <td>
                            {item.user_id != null
                              ? userNames[item.user_id] ?? `Пользователь #${item.user_id}`
                              : 'Системное действие'}
                          </td>
                          <td>
                            {item.project_id != null
                              ? projectNames[item.project_id] ?? `Проект #${item.project_id}`
                              : '—'}
                          </td>
                          <td>{item.ip_address ?? '—'}</td>
                          <td>
                            <Button
                              size="sm"
                              className="secondary-pill-button admin-small-button"
                              onClick={() => void openDetail(item.id)}
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

      <Modal show={isModalOpen} onHide={closeDetail} size="lg" centered>
        <Modal.Header closeButton>
          <Modal.Title>Запись аудита #{selectedAuditId ?? '—'}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {isDetailLoading ? (
            <div className="py-5 text-center">
              <Spinner animation="border" />
            </div>
          ) : null}

          {!isDetailLoading && detailError ? <Alert variant="danger">{detailError}</Alert> : null}

          {!isDetailLoading && !detailError && selectedAudit ? (
            <div className="audit-detail-grid">
              <div><strong>Дата и время:</strong> {formatDateTime(selectedAudit.created_at)}</div>
              <div><strong>Действие:</strong> {getAuditActionLabel(selectedAudit.action)}</div>
              <div><strong>Сущность:</strong> {getAuditEntityLabel(selectedAudit.entity_type)}</div>
              <div><strong>ID сущности:</strong> {selectedAudit.entity_id ?? '—'}</div>
              <div>
                <strong>Пользователь:</strong>{' '}
                {selectedAudit.user?.full_name ?? (selectedAudit.user_id != null ? `#${selectedAudit.user_id}` : 'Системное действие')}
              </div>
              <div>
                <strong>Проект:</strong>{' '}
                {selectedAudit.project?.name ?? (selectedAudit.project_id != null ? `#${selectedAudit.project_id}` : '—')}
              </div>
              <div><strong>IP-адрес:</strong> {selectedAudit.ip_address ?? '—'}</div>
              <div><strong>User-Agent:</strong> {selectedAudit.user_agent ?? '—'}</div>

              <div className="audit-json-block">
                <div className="audit-json-title">Состояние до изменения</div>
                <pre className="audit-json-pre">{stringifyJson(selectedAudit.before_json)}</pre>
              </div>

              <div className="audit-json-block">
                <div className="audit-json-title">Состояние после изменения</div>
                <pre className="audit-json-pre">{stringifyJson(selectedAudit.after_json)}</pre>
              </div>
            </div>
          ) : null}
        </Modal.Body>
      </Modal>
    </>
  );
}
