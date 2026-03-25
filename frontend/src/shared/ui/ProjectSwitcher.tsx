import { Form } from 'react-bootstrap';
import { useProjectContext } from '../../features/projects/ProjectContext';

export function ProjectSwitcher() {
  const {
    projects,
    activeProjectId,
    isLoading,
    setActiveProjectId,
  } = useProjectContext();

  const visibleProjects = projects.filter((project) => !project.is_archived);

  return (
    <div className="project-switcher-wrap">
      <Form.Select
        className="project-switcher-select"
        value={activeProjectId ?? ''}
        disabled={isLoading}
        onChange={(event) => {
          const value = event.target.value;

          if (!value) {
            setActiveProjectId(null);
            return;
          }

          setActiveProjectId(Number(value));
        }}
      >
        <option value="">Проект не выбран</option>
        {visibleProjects.map((project) => (
          <option key={project.id} value={project.id}>
            {project.name} ({project.code})
          </option>
        ))}
      </Form.Select>
    </div>
  );
}