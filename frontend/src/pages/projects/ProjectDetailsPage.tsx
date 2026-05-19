import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { Alert, Button, Col, Form, Modal, Row, Spinner, Table } from 'react-bootstrap';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthProvider';
import { useProjectContext } from '../../features/projects/ProjectContext';
import { projectsApi } from '../../shared/api/projects';
import {
  getProjectAccessStatusLabel,
  getProjectRoleLabel,
  PROJECT_MEMBER_ROLE_OPTIONS,
  type ProjectAvailableUser,
  type ProjectDetail,
  type ProjectMember,
  type ProjectMemberRole,
} from '../../shared/types/project';
import { ContentCard } from '../../shared/ui/ContentCard';

function formatDateTime(value?: string | null) {
  if (!value) return '-';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString('ru-RU');
}

export default function ProjectDetailsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { activeProjectId, setActiveProjectId, reloadProjects } = useProjectContext();

  const numericProjectId = Number(projectId);

  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [members, setMembers] = useState<ProjectMember[]>([]);

  const [requestedRole, setRequestedRole] = useState<ProjectMemberRole>('viewer');
  const [requestNote, setRequestNote] = useState('');
  const [showRequestModal, setShowRequestModal] = useState(false);
  const [isRequestSubmitting, setIsRequestSubmitting] = useState(false);

  const [showAddMemberModal, setShowAddMemberModal] = useState(false);
  const [availableUsers, setAvailableUsers] = useState<ProjectAvailableUser[]>([]);
  const [selectedUserId, setSelectedUserId] = useState('');
  const [selectedMemberRole, setSelectedMemberRole] = useState<ProjectMemberRole>('viewer');
  const [memberNote, setMemberNote] = useState('');
  const [isAvailableUsersLoading, setIsAvailableUsersLoading] = useState(false);
  const [isAddMemberSubmitting, setIsAddMemberSubmitting] = useState(false);

  const [showEditMemberModal, setShowEditMemberModal] = useState(false);
  const [editingMember, setEditingMember] = useState<ProjectMember | null>(null);
  const [editingRole, setEditingRole] = useState<ProjectMemberRole>('viewer');
  const [editingNote, setEditingNote] = useState('');
  const [isEditMemberSubmitting, setIsEditMemberSubmitting] = useState(false);

  const [showDeleteMemberModal, setShowDeleteMemberModal] = useState(false);
  const [deletingMember, setDeletingMember] = useState<ProjectMember | null>(null);
  const [isDeleteMemberSubmitting, setIsDeleteMemberSubmitting] = useState(false);

  const [isLoading, setIsLoading] = useState(true);

  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const loadProjectData = async () => {
    if (!projectId || Number.isNaN(numericProjectId)) {
      setError('Некорректный идентификатор проекта.');
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError('');

      const [projectData, membersData] = await Promise.all([
        projectsApi.getById(numericProjectId),
        projectsApi.listMembers(numericProjectId),
      ]);

      setProject(projectData);
      setMembers(membersData);
    } catch {
      setError('Не удалось загрузить данные проекта.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadProjectData();
  }, [projectId, numericProjectId]);

  const currentMembership = useMemo(() => {
    if (!user) return null;
    return members.find((member) => member.user_id === user.id) ?? null;
  }, [members, user]);

  const approvedMembers = useMemo(() => {
    return members.filter((member) => member.access_status === 'approved');
  }, [members]);

  const canRequestAccess = useMemo(() => {
    if (!user) return false;
    if (!currentMembership) return true;
    return currentMembership.access_status === 'rejected';
  }, [user, currentMembership]);

  const canManageMembers = useMemo(() => {
    if (!user || !project) return false;
    return user.role.code === 'admin' || user.id === project.owner_id;
  }, [user, project]);

  const canArchiveProject = useMemo(() => {
    if (!user || !project) return false;
    return user.role.code === 'admin' || user.id === project.owner_id;
  }, [user, project]);


  const handleToggleArchive = async () => {
    if (!project) {
      setError('Проект не найден.');
      return;
    }

    if (!canArchiveProject) {
      setError('Архивировать проект может только владелец или администратор.');
      return;
    }

    const nextArchivedState = !project.is_archived;
    const actionLabel = nextArchivedState ? 'архивировать' : 'восстановить';

    if (!window.confirm(`Подтвердить действие: ${actionLabel} проект "${project.name}"?`)) {
      return;
    }

    try {
      setError('');
      setSuccessMessage('');

      const updatedProject = await projectsApi.update(project.id, {
          is_archived: nextArchivedState,
        });

        setProject(updatedProject);

        const refreshedMembers = await projectsApi.listMembers(project.id);
        setMembers(refreshedMembers);

        await reloadProjects();

      setSuccessMessage(
        nextArchivedState
          ? `Проект "${project.name}" перенесён в архив.`
          : `Проект "${project.name}" восстановлен из архива.`,
      );
    } catch {
      setError('Не удалось изменить статус проекта.');
    }
  };

  const handleRequestAccess = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!project) {
      setError('Проект не найден.');
      return;
    }

    try {
      setIsRequestSubmitting(true);
      setError('');
      setSuccessMessage('');

      const createdRequest = await projectsApi.requestAccess(project.id, {
        member_role: requestedRole,
        request_note: requestNote.trim() || null,
      });

      setMembers((prev) => {
        const filtered = prev.filter((member) => member.user_id !== createdRequest.user_id);
        return [createdRequest, ...filtered];
      });

      setShowRequestModal(false);
      setRequestNote('');
      setRequestedRole('viewer');
      setSuccessMessage('Запрос на доступ к проекту отправлен.');
    } catch {
      setError('Не удалось отправить запрос на доступ.');
    } finally {
      setIsRequestSubmitting(false);
    }
  };

  const handleOpenAddMemberModal = async () => {
    if (!project) return;

    try {
      setError('');
      setSuccessMessage('');
      setIsAvailableUsersLoading(true);

      const users = await projectsApi.listAvailableUsers(project.id);
      setAvailableUsers(users);
      setSelectedUserId(users.length > 0 ? String(users[0].id) : '');
      setSelectedMemberRole('viewer');
      setMemberNote('');
      setShowAddMemberModal(true);
    } catch {
      setError('Не удалось загрузить список доступных пользователей.');
    } finally {
      setIsAvailableUsersLoading(false);
    }
  };

  const handleAddMember = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!project) {
      setError('Проект не найден.');
      return;
    }

    if (!selectedUserId) {
      setError('Выбери пользователя для добавления.');
      return;
    }

    try {
      setIsAddMemberSubmitting(true);
      setError('');
      setSuccessMessage('');

      const createdMember = await projectsApi.addMember(project.id, {
        user_id: Number(selectedUserId),
        member_role: selectedMemberRole,
        request_note: memberNote.trim() || null,
      });

      setMembers((prev) => [createdMember, ...prev]);
      setAvailableUsers((prev) => prev.filter((item) => item.id !== createdMember.user_id));
      setShowAddMemberModal(false);
      setSelectedUserId('');
      setSelectedMemberRole('viewer');
      setMemberNote('');
      setSuccessMessage(`Участник "${createdMember.user.full_name}" добавлен в проект.`);
    } catch {
      setError('Не удалось добавить участника в проект.');
    } finally {
      setIsAddMemberSubmitting(false);
    }
  };

  const openEditMemberModal = (member: ProjectMember) => {
    setEditingMember(member);
    setEditingRole(member.member_role);
    setEditingNote(member.review_note ?? '');
    setShowEditMemberModal(true);
  };

  const handleEditMember = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!project || !editingMember) {
      setError('Участник проекта не найден.');
      return;
    }

    try {
      setIsEditMemberSubmitting(true);
      setError('');
      setSuccessMessage('');

      const updatedMember = await projectsApi.updateMember(project.id, editingMember.id, {
        member_role: editingRole,
        review_note: editingNote.trim() || null,
      });

      setMembers((prev) =>
        prev.map((member) => (member.id === updatedMember.id ? updatedMember : member)),
      );

      setShowEditMemberModal(false);
      setEditingMember(null);
      setEditingNote('');
      setSuccessMessage(`Роль участника "${updatedMember.user.full_name}" обновлена.`);
    } catch {
      setError('Не удалось изменить роль участника.');
    } finally {
      setIsEditMemberSubmitting(false);
    }
  };

  const openDeleteMemberModal = (member: ProjectMember) => {
    setDeletingMember(member);
    setShowDeleteMemberModal(true);
  };

  const handleDeleteMember = async () => {
    if (!project || !deletingMember) {
      setError('Участник проекта не найден.');
      return;
    }

    try {
      setIsDeleteMemberSubmitting(true);
      setError('');
      setSuccessMessage('');

      await projectsApi.removeMember(project.id, deletingMember.id);

      setMembers((prev) => prev.filter((member) => member.id !== deletingMember.id));
      setShowDeleteMemberModal(false);
      setSuccessMessage(`Участник "${deletingMember.user.full_name}" удалён из проекта.`);
      setDeletingMember(null);
    } catch {
      setError('Не удалось удалить участника из проекта.');
    } finally {
      setIsDeleteMemberSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <ContentCard
        header={
          <div className="section-header">
            <h2 className="section-title">Карточка проекта</h2>
          </div>
        }
      >
        <div className="py-5 text-center">
          <Spinner animation="border" />
        </div>
      </ContentCard>
    );
  }

  if (!project) {
    return (
      <ContentCard
        header={
          <div className="section-header">
            <h2 className="section-title">Карточка проекта</h2>
          </div>
        }
      >
        <Alert variant="danger" className="mb-0">
          {error || 'Проект не найден.'}
        </Alert>
      </ContentCard>
    );
  }

  return (
    <>
      <ContentCard
        header={
          <div className="toolbar-row">
            <div className="toolbar-left">
              <h2 className="section-title mb-0">Карточка проекта</h2>
            </div>

            <div className="admin-header-actions">
              <Button className="secondary-pill-button" onClick={() => navigate('/projects')}>
                К проектам
              </Button>

              <Button
                className={
                  activeProjectId === project.id
                    ? 'secondary-pill-button'
                    : 'primary-pill-button'
                }
                onClick={() => setActiveProjectId(project.id)}
              >
                {activeProjectId === project.id ? 'Активный проект' : 'Сделать активным'}
              </Button>

              {canArchiveProject ? (
                <Button
                  className="secondary-pill-button"
                  onClick={() => void handleToggleArchive()}
                >
                  {project.is_archived ? 'Восстановить проект' : 'Архивировать проект'}
                </Button>
              ) : null}

              {canRequestAccess ? (
                <Button className="primary-pill-button" onClick={() => setShowRequestModal(true)}>
                  Запросить доступ
                </Button>
              ) : null}
            </div>
          </div>
        }
      >
        {error ? <Alert variant="danger">{error}</Alert> : null}
        {successMessage ? <Alert variant="success" className="app-soft-alert app-soft-alert-success">{successMessage}</Alert> : null}

        <div className="form-meta-grid mb-4">
          <div className="form-meta-card">
            <div className="form-meta-label">Название</div>
            <div className="form-meta-value">{project.name}</div>
          </div>

          <div className="form-meta-card">
            <div className="form-meta-label">Код</div>
            <div className="form-meta-value">{project.code}</div>
          </div>

          <div className="form-meta-card">
            <div className="form-meta-label">Статус</div>
            <div className="form-meta-value">
              <span
                className={
                  project.is_archived
                    ? 'status-badge status-badge-muted'
                    : 'status-badge status-badge-success'
                }
              >
                {project.is_archived ? 'Архивный' : 'Активный'}
              </span>
            </div>
          </div>
        </div>

        <Row className="g-4 mb-4">
          <Col lg={7}>
            <div className="form-meta-card h-100">
              <div className="form-meta-label">Описание</div>
              <div className="form-meta-value">
                {project.description ?? 'Описание не указано.'}
              </div>
            </div>
          </Col>

          <Col lg={5}>
            <div className="form-meta-card h-100">
              <div className="form-meta-label">Служебная информация</div>

              <div className="result-info-list">
                <div>
                  <strong>Владелец:</strong> {project.owner?.full_name ?? '-'}
                </div>
                <div>
                  <strong>Создан:</strong> {formatDateTime(project.created_at)}
                </div>
                <div>
                  <strong>Обновлен:</strong> {formatDateTime(project.updated_at)}
                </div>
                <div>
                  <strong>Мой доступ:</strong>{' '}
                  {currentMembership
                    ? `${getProjectRoleLabel(currentMembership.member_role)} / ${getProjectAccessStatusLabel(currentMembership.access_status)}`
                    : 'Нет доступа'}
                </div>
                <div>
                  <strong>Участников с доступом:</strong> {approvedMembers.length}
                </div>
              </div>
            </div>
          </Col>
        </Row>

        <div className="admin-section-card">
          <div className="admin-section-header">
            <div className="admin-section-title">Участники проекта</div>

            {canManageMembers ? (
              <div className="project-members-header-actions">
                <Button
                  className="primary-pill-button"
                  onClick={handleOpenAddMemberModal}
                  disabled={isAvailableUsersLoading}
                >
                  {isAvailableUsersLoading ? 'Загрузка...' : 'Добавить участника'}
                </Button>
              </div>
            ) : null}
          </div>

          <div className="table-wrap">
            <Table borderless responsive className="prototype-table">
              <thead>
                <tr>
                  <th>ФИО</th>
                  <th>Email</th>
                  <th>Роль</th>
                  <th>Статус доступа</th>
                  <th>Запрошено</th>
                  <th>Рассмотрено</th>
                  <th>Действия</th>
                </tr>
              </thead>
              <tbody>
                {members.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="text-center py-4">
                      Участники проекта отсутствуют
                    </td>
                  </tr>
                ) : (
                  members.map((member) => {
                    const isOwnerRow = member.user_id === project.owner_id;
                    const canManageThisMember = canManageMembers && !isOwnerRow;

                    return (
                      <tr key={member.id}>
                        <td>{member.user.full_name}</td>
                        <td>{member.user.email}</td>
                        <td>{getProjectRoleLabel(member.member_role)}</td>
                        <td>
                          <span
                            className={
                              member.access_status === 'approved'
                                ? 'status-badge status-badge-success'
                                : member.access_status === 'requested'
                                  ? 'status-badge status-badge-info'
                                  : 'status-badge status-badge-danger'
                            }
                          >
                            {getProjectAccessStatusLabel(member.access_status)}
                          </span>
                        </td>
                        <td>{formatDateTime(member.requested_at)}</td>
                        <td>{formatDateTime(member.reviewed_at)}</td>
                        <td>
                          <div className="table-action-center">
                            {isOwnerRow ? (
                              <span className="text-muted">Недоступно</span>
                            ) : canManageThisMember ? (
                              <div className="project-member-actions">
                                <Button
                                  size="sm"
                                  className="secondary-pill-button project-member-action-button"
                                  onClick={() => openEditMemberModal(member)}
                                >
                                  Изменить роль
                                </Button>

                                <Button
                                  size="sm"
                                  className="secondary-pill-button project-member-action-button project-member-remove-button"
                                  onClick={() => openDeleteMemberModal(member)}
                                >
                                  Удалить
                                </Button>
                              </div>
                            ) : (
                              <span className="text-muted">-</span>
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
      </ContentCard>

      <Modal show={showRequestModal} onHide={() => setShowRequestModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Запрос доступа к проекту</Modal.Title>
        </Modal.Header>

        <Form onSubmit={handleRequestAccess}>
          <Modal.Body>
            <Row className="g-3">
              <Col md={12}>
                <Form.Group>
                  <Form.Label>Запрашиваемая роль</Form.Label>
                  <Form.Select
                    className="soft-input"
                    value={requestedRole}
                    onChange={(event) =>
                      setRequestedRole(event.target.value as ProjectMemberRole)
                    }
                  >
                    {PROJECT_MEMBER_ROLE_OPTIONS.map((item) => (
                      <option key={item.value} value={item.value}>
                        {item.label}
                      </option>
                    ))}
                  </Form.Select>
                </Form.Group>
              </Col>

              <Col md={12}>
                <Form.Group>
                  <Form.Label>Комментарий</Form.Label>
                  <Form.Control
                    as="textarea"
                    rows={4}
                    className="soft-input soft-textarea"
                    value={requestNote}
                    onChange={(event) => setRequestNote(event.target.value)}
                  />
                </Form.Group>
              </Col>
            </Row>
          </Modal.Body>

          <Modal.Footer>
            <Button className="secondary-pill-button" onClick={() => setShowRequestModal(false)}>
              Отмена
            </Button>
            <Button type="submit" className="primary-pill-button" disabled={isRequestSubmitting}>
              {isRequestSubmitting ? 'Отправка...' : 'Отправить запрос'}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>

      <Modal show={showAddMemberModal} onHide={() => setShowAddMemberModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Добавление участника</Modal.Title>
        </Modal.Header>

        <Form onSubmit={handleAddMember}>
          <Modal.Body>
            {availableUsers.length === 0 ? (
              <Alert variant="light" className="mb-0">
                Все доступные пользователи уже добавлены в проект.
              </Alert>
            ) : (
              <Row className="g-3">
                <Col md={12}>
                  <Form.Group>
                    <Form.Label>Пользователь</Form.Label>
                    <Form.Select
                      className="soft-input"
                      value={selectedUserId}
                      onChange={(event) => setSelectedUserId(event.target.value)}
                    >
                      {availableUsers.map((item) => (
                        <option key={item.id} value={item.id}>
                          {item.full_name} - {item.email}
                        </option>
                      ))}
                    </Form.Select>
                  </Form.Group>
                </Col>

                <Col md={12}>
                  <Form.Group>
                    <Form.Label>Роль в проекте</Form.Label>
                    <Form.Select
                      className="soft-input"
                      value={selectedMemberRole}
                      onChange={(event) =>
                        setSelectedMemberRole(event.target.value as ProjectMemberRole)
                      }
                    >
                      {PROJECT_MEMBER_ROLE_OPTIONS.map((item) => (
                        <option key={item.value} value={item.value}>
                          {item.label}
                        </option>
                      ))}
                    </Form.Select>
                  </Form.Group>
                </Col>

                <Col md={12}>
                  <Form.Group>
                    <Form.Label>Комментарий</Form.Label>
                    <Form.Control
                      as="textarea"
                      rows={4}
                      className="soft-input soft-textarea"
                      value={memberNote}
                      onChange={(event) => setMemberNote(event.target.value)}
                    />
                  </Form.Group>
                </Col>
              </Row>
            )}
          </Modal.Body>

          <Modal.Footer>
            <Button className="secondary-pill-button" onClick={() => setShowAddMemberModal(false)}>
              Закрыть
            </Button>
            <Button
              type="submit"
              className="primary-pill-button"
              disabled={isAddMemberSubmitting || availableUsers.length === 0}
            >
              {isAddMemberSubmitting ? 'Добавление...' : 'Добавить'}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>

      <Modal
        show={showEditMemberModal}
        onHide={() => {
          setShowEditMemberModal(false);
          setEditingMember(null);
        }}
        centered
      >
        <Modal.Header closeButton>
          <Modal.Title>Редактирование роли</Modal.Title>
        </Modal.Header>

        <Form onSubmit={handleEditMember}>
          <Modal.Body>
            <Row className="g-3">
              <Col md={12}>
                <Form.Group>
                  <Form.Label>Участник</Form.Label>
                  <Form.Control
                    className="soft-input"
                    value={
                      editingMember
                        ? `${editingMember.user.full_name} - ${editingMember.user.email}`
                        : ''
                    }
                    readOnly
                  />
                </Form.Group>
              </Col>

              <Col md={12}>
                <Form.Group>
                  <Form.Label>Новая роль</Form.Label>
                  <Form.Select
                    className="soft-input"
                    value={editingRole}
                    onChange={(event) => setEditingRole(event.target.value as ProjectMemberRole)}
                  >
                    {PROJECT_MEMBER_ROLE_OPTIONS.map((item) => (
                      <option key={item.value} value={item.value}>
                        {item.label}
                      </option>
                    ))}
                  </Form.Select>
                </Form.Group>
              </Col>

              <Col md={12}>
                <Form.Group>
                  <Form.Label>Комментарий</Form.Label>
                  <Form.Control
                    as="textarea"
                    rows={4}
                    className="soft-input soft-textarea"
                    value={editingNote}
                    onChange={(event) => setEditingNote(event.target.value)}
                  />
                </Form.Group>
              </Col>
            </Row>
          </Modal.Body>

          <Modal.Footer>
            <Button
              className="secondary-pill-button"
              onClick={() => {
                setShowEditMemberModal(false);
                setEditingMember(null);
              }}
            >
              Отмена
            </Button>
            <Button type="submit" className="primary-pill-button" disabled={isEditMemberSubmitting}>
              {isEditMemberSubmitting ? 'Сохранение...' : 'Сохранить'}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>

      <Modal
        show={showDeleteMemberModal}
        onHide={() => {
          setShowDeleteMemberModal(false);
          setDeletingMember(null);
        }}
        centered
      >
        <Modal.Header closeButton>
          <Modal.Title>Удаление участника</Modal.Title>
        </Modal.Header>

        <Modal.Body>
          {deletingMember ? (
            <p className="mb-0">
              Удалить участника <strong>{deletingMember.user.full_name}</strong> из проекта?
            </p>
          ) : null}
        </Modal.Body>

        <Modal.Footer>
          <Button
            className="secondary-pill-button"
            onClick={() => {
              setShowDeleteMemberModal(false);
              setDeletingMember(null);
            }}
          >
            Отмена
          </Button>
          <Button
            className="secondary-pill-button project-member-remove-button"
            onClick={() => void handleDeleteMember()}
            disabled={isDeleteMemberSubmitting}
          >
            {isDeleteMemberSubmitting ? 'Удаление...' : 'Удалить'}
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
}