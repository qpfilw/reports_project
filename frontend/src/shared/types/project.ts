export interface Project {
  id: number;
  name: string;
  code: string;
  description: string | null;
  owner_id: number;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}