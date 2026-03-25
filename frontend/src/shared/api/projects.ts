import { apiClient } from './client';
import type {
  AddProjectMemberPayload,
  CreateProjectPayload,
  Project,
  ProjectAvailableUser,
  ProjectDetail,
  ProjectMember,
  RequestProjectAccessPayload,
  UpdateProjectMemberPayload,
} from '../types/project';

export const projectsApi = {
  list: async () => {
    const response = await apiClient.get<Project[]>('/projects');
    return response.data;
  },

  getById: async (projectId: number) => {
    const response = await apiClient.get<ProjectDetail>(`/projects/${projectId}`);
    return response.data;
  },

  create: async (payload: CreateProjectPayload) => {
    const response = await apiClient.post<ProjectDetail>('/projects', payload);
    return response.data;
  },

  listMembers: async (projectId: number) => {
    const response = await apiClient.get<ProjectMember[]>(`/projects/${projectId}/members`);
    return response.data;
  },

  listAvailableUsers: async (projectId: number) => {
    const response = await apiClient.get<ProjectAvailableUser[]>(
      `/projects/${projectId}/available-users`,
    );
    return response.data;
  },

  addMember: async (projectId: number, payload: AddProjectMemberPayload) => {
    const response = await apiClient.post<ProjectMember>(
      `/projects/${projectId}/members`,
      payload,
    );
    return response.data;
  },

  updateMember: async (
    projectId: number,
    memberId: number,
    payload: UpdateProjectMemberPayload,
  ) => {
    const response = await apiClient.patch<ProjectMember>(
      `/projects/${projectId}/members/${memberId}`,
      payload,
    );
    return response.data;
  },

  removeMember: async (projectId: number, memberId: number) => {
    const response = await apiClient.delete<{ message: string }>(
      `/projects/${projectId}/members/${memberId}`,
    );
    return response.data;
  },

  requestAccess: async (projectId: number, payload: RequestProjectAccessPayload) => {
    const response = await apiClient.post<ProjectMember>(
      `/projects/${projectId}/access-request`,
      payload,
    );
    return response.data;
  },
};