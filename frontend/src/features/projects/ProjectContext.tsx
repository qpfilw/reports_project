import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from 'react';
import { useAuth } from '../auth/AuthProvider';
import { projectsApi } from '../../shared/api/projects';
import { storage } from '../../shared/lib/storage';
import type { Project } from '../../shared/types/project';

interface ProjectContextValue {
  projects: Project[];
  activeProjectId: number | null;
  activeProject: Project | null;
  isLoading: boolean;
  setActiveProjectId: (projectId: number | null) => void;
  clearActiveProject: () => void;
  reloadProjects: () => Promise<void>;
}

const ProjectContext = createContext<ProjectContextValue | null>(null);

export function ProjectProvider({ children }: PropsWithChildren) {
  const { isAuthenticated } = useAuth();

  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProjectId, setActiveProjectIdState] = useState<number | null>(() => {
    const raw = storage.getActiveProject();
    if (!raw) return null;

    const parsed = Number(raw);
    return Number.isNaN(parsed) ? null : parsed;
  });
  const [isLoading, setIsLoading] = useState(true);

  const reloadProjects = useCallback(async () => {
    if (!isAuthenticated) {
      setProjects([]);
      setActiveProjectIdState(null);
      storage.removeActiveProject();
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      const data = await projectsApi.list();
      setProjects(data);

      const exists = data.some((project) => project.id === activeProjectId);

      if (activeProjectId != null && !exists) {
        setActiveProjectIdState(null);
        storage.removeActiveProject();
      }
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated, activeProjectId]);

  useEffect(() => {
    void reloadProjects();
  }, [reloadProjects]);

  const setActiveProjectId = useCallback((projectId: number | null) => {
    setActiveProjectIdState(projectId);

    if (projectId == null) {
      storage.removeActiveProject();
      return;
    }

    storage.setActiveProject(String(projectId));
  }, []);

  const clearActiveProject = useCallback(() => {
    setActiveProjectId(null);
  }, [setActiveProjectId]);

  const activeProject = useMemo(() => {
    if (activeProjectId == null) return null;
    return projects.find((project) => project.id === activeProjectId) ?? null;
  }, [projects, activeProjectId]);

  const value = useMemo<ProjectContextValue>(
    () => ({
      projects,
      activeProjectId,
      activeProject,
      isLoading,
      setActiveProjectId,
      clearActiveProject,
      reloadProjects,
    }),
    [
      projects,
      activeProjectId,
      activeProject,
      isLoading,
      setActiveProjectId,
      clearActiveProject,
      reloadProjects,
    ],
  );

  return <ProjectContext.Provider value={value}>{children}</ProjectContext.Provider>;
}

export function useProjectContext() {
  const context = useContext(ProjectContext);

  if (!context) {
    throw new Error('useProjectContext must be used inside ProjectProvider');
  }

  return context;
}