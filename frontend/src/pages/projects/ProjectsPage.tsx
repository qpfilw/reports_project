import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { Alert, Button, Col, Form, Modal, Row, Spinner, Table } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthProvider';
import { useProjectContext } from '../../features/projects/ProjectContext';
import { projectsApi } from '../../shared/api/projects';
import type { CreateProjectPayload, Project } from '../../shared/types/project';
import { ContentCard } from '../../shared/ui/ContentCard';

interface ProjectFormState {
  name: string;
  code: string;
  description: string;
}

const initialFormState: ProjectFormState = {
  name: '',
  code: '',
  description: '',
};

export default function ProjectsPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { reloadProjects } = useProjectContext();

  const [projects, setProjects] = useState<Project[]>([]);
  const [search, setSearch] = useState('');
  const [isArchivedVisible, setIsArchivedVisible] = useState(false);

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [formState, setFormState] = useState<ProjectFormState>(initialFormState);

  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const canCreateProject = user?.role.code === 'admin' || user?.role.code === 'manager';

  const loadProjects = async () => {
    try {
      setIsLoading(true);
      setError('');
      const data = await projectsApi.list();
      setProjects(data);
    } catch {
      setError('Не удалось загрузить список проектов.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadProjects();
  }, []);

  const filteredProjects = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();

    return projects.filter((project) => {
      const matchesArchive = isArchivedVisible ? true : !project.is_archived;
      const matchesSearch =
        !normalizedSearch ||
        project.name.toLowerCase().includes(normalizedSearch) ||
        project.code.toLowerCase().includes(normalizedSearch) ||
        (project.description ?? '').toLowerCase().includes(normalizedSearch);

      return matchesArchive && matchesSearch;
    });
  }, [projects, search, isArchivedVisible]);


  const handleToggleArchive = async (project: Project) => {
    if (!user) {
      setError('Пользователь не авторизован.');
      return;
    }

    const canManageProject = user.role.code === 'admin' || user.id === project.owner_id;

    if (!canManageProject) {
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

      setProjects((prev) =>
        prev.map((item) => (item.id === updatedProject.id ? updatedProject : item)),
      );

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

  const handleCreateProject = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    setSuccessMessage('');

    if (!user) {
      setError('Пользователь не авторизован.');
      return;
    }

    if (!formState.name.trim()) {
      setError('Укажи название проекта.');
      return;
    }

    if (!formState.code.trim()) {
      setError('Укажи код проекта.');
      return;
    }

    try {
      setIsSubmitting(true);

      const payload: CreateProjectPayload = {
        name: formState.name.trim(),
        code: formState.code.trim(),
        description: formState.description.trim() || null,
        owner_id: user.id,
      };

      const created = await projectsApi.create(payload);

      await Promise.all([loadProjects(), reloadProjects()]);

      setShowCreateModal(false);
      setFormState(initialFormState);
      setSuccessMessage(`Проект "${created.name}" успешно создан.`);
    } catch {
      setError('Не удалось создать проект.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <ContentCard
        header={
          <div className="toolbar-row">
            <div className="toolbar-left toolbar-left-wrap">
              <h2 className="section-title mb-0">Проекты</h2>

              <Form.Control
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                className="soft-input projects-search-input"
                placeholder="Поиск по названию, коду или описанию"
              />

              <Form.Check
                type="switch"
                id="show-archived-projects"
                label="Показывать архивные"
                className="projects-archive-switch"
                checked={isArchivedVisible}
                onChange={(event) => setIsArchivedVisible(event.target.checked)}
              />
            </div>

            {canCreateProject ? (
              <Button className="primary-pill-button" onClick={() => setShowCreateModal(true)}>
                Создать проект
              </Button>
            ) : null}
          </div>
        }
      >
        {isLoading ? (
          <div className="py-5 text-center">
            <Spinner animation="border" />
          </div>
        ) : null}

        {!isLoading && error ? <Alert variant="danger">{error}</Alert> : null}
        {!isLoading && successMessage ? <Alert variant="success" className="app-soft-alert app-soft-alert-success">{successMessage}</Alert> : null}

        {!isLoading && !error ? (
          <div className="table-wrap">
            <Table borderless responsive className="prototype-table">
              <thead>
                <tr>
                  <th>Код</th>
                  <th>Название</th>
                  <th>Описание</th>
                  <th>Статус</th>
                  <th>Действие</th>
                </tr>
              </thead>
              <tbody>
                {filteredProjects.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="text-center py-4">
                      Проекты не найдены
                    </td>
                  </tr>
                ) : (
                  filteredProjects.map((project) => (
                    <tr
                      key={project.id}
                      className="table-row-clickable"
                      onClick={() => navigate(`/projects/${project.id}`)}
                    >
                      <td>{project.code}</td>
                      <td>{project.name}</td>
                      <td>{project.description ?? '-'}</td>
                      <td className="table-cell-center table-status-cell">
                        <span
                          className={
                            project.is_archived
                              ? 'status-badge status-badge-muted'
                              : 'status-badge status-badge-success'
                          }
                        >
                          {project.is_archived ? 'Архивный' : 'Активный'}
                        </span>
                      </td>
                      <td className="table-action-cell" onClick={(event) => event.stopPropagation()}>
                        <div className="table-action-center projects-action-row">
                          <Button
                            size="sm"
                            className="primary-pill-button projects-open-button"
                            onClick={() => navigate(`/projects/${project.id}`)}
                          >
                            Открыть
                          </Button>

                          {user?.role.code === 'admin' || user?.id === project.owner_id ? (
                            <Button
                              size="sm"
                              className="secondary-pill-button projects-archive-button"
                              onClick={() => void handleToggleArchive(project)}
                            >
                              {project.is_archived ? 'Восстановить' : 'Архивировать'}
                            </Button>
                          ) : null}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </Table>
          </div>
        ) : null}
      </ContentCard>

      <Modal
        show={showCreateModal}
        onHide={() => setShowCreateModal(false)}
        centered
        className="projects-modal"
      >
        <Modal.Header closeButton>
          <Modal.Title>Создание проекта</Modal.Title>
        </Modal.Header>

        <Form onSubmit={handleCreateProject}>
          <Modal.Body>
            <Row className="g-3">
              <Col md={12}>
                <Form.Group>
                  <Form.Label>Название проекта</Form.Label>
                  <Form.Control
                    className="soft-input"
                    value={formState.name}
                    onChange={(event) =>
                      setFormState((prev) => ({ ...prev, name: event.target.value }))
                    }
                  />
                </Form.Group>
              </Col>

              <Col md={12}>
                <Form.Group>
                  <Form.Label>Код проекта</Form.Label>
                  <Form.Control
                    className="soft-input"
                    value={formState.code}
                    onChange={(event) =>
                      setFormState((prev) => ({ ...prev, code: event.target.value }))
                    }
                  />
                </Form.Group>
              </Col>

              <Col md={12}>
                <Form.Group>
                  <Form.Label>Описание</Form.Label>
                  <Form.Control
                    as="textarea"
                    rows={4}
                    className="soft-input soft-textarea"
                    value={formState.description}
                    onChange={(event) =>
                      setFormState((prev) => ({ ...prev, description: event.target.value }))
                    }
                  />
                </Form.Group>
              </Col>
            </Row>
          </Modal.Body>

          <Modal.Footer>
            <Button
              type="button"
              className="secondary-pill-button"
              onClick={() => setShowCreateModal(false)}
            >
              Отмена
            </Button>
            <Button type="submit" className="primary-pill-button" disabled={isSubmitting}>
              {isSubmitting ? 'Создание...' : 'Создать'}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>
    </>
  );
}