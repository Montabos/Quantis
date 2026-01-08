'use client';

import { createContext, useContext, useState, ReactNode, useCallback, useEffect } from 'react';
import { createClient } from '@/lib/supabase/client';
import { useAuth } from './AuthContext';

export interface Project {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
}

interface ProjectsContextType {
  projects: Project[];
  activeProjectId: string | null;
  setActiveProjectId: (id: string | null) => void;
  createProject: (name: string) => Promise<Project | null>;
  updateProject: (id: string, name: string) => Promise<void>;
  deleteProject: (id: string) => Promise<void>;
  isLoading: boolean;
  refreshProjects: () => Promise<void>;
}

const ProjectsContext = createContext<ProjectsContextType | undefined>(undefined);

export function ProjectsProvider({ children }: { children: ReactNode }) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { user } = useAuth();
  const supabase = createClient();

  // Load projects from Supabase
  const loadProjects = useCallback(async () => {
    if (!user) {
      setProjects([]);
      setActiveProjectId(null);
      return;
    }

    setIsLoading(true);
    try {
      const { data, error } = await supabase
        .from('projects')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false });

      if (error) {
        console.error('Error loading projects:', error);
        return;
      }

      const loadedProjects = (data || []) as Project[];
      setProjects(loadedProjects);

      // Set first project as active if none is selected
      if (loadedProjects.length > 0 && !activeProjectId) {
        setActiveProjectId(loadedProjects[0].id);
      } else if (loadedProjects.length === 0) {
        setActiveProjectId(null);
      } else if (activeProjectId && !loadedProjects.find(p => p.id === activeProjectId)) {
        // If active project was deleted, select first one
        setActiveProjectId(loadedProjects[0].id);
      }
    } catch (error) {
      console.error('Error loading projects:', error);
    } finally {
      setIsLoading(false);
    }
  }, [user, supabase, activeProjectId]);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  const createProject = useCallback(async (name: string): Promise<Project | null> => {
    if (!user) return null;

    try {
      const { data, error } = await supabase
        .from('projects')
        .insert({
          user_id: user.id,
          name: name.trim(),
        })
        .select()
        .single();

      if (error) {
        console.error('Error creating project:', error);
        return null;
      }

      await loadProjects();
      setActiveProjectId(data.id);
      return data as Project;
    } catch (error) {
      console.error('Error creating project:', error);
      return null;
    }
  }, [user, supabase, loadProjects]);

  const updateProject = useCallback(async (id: string, name: string) => {
    if (!user) return;

    try {
      const { error } = await supabase
        .from('projects')
        .update({ name: name.trim() })
        .eq('id', id)
        .eq('user_id', user.id);

      if (error) {
        console.error('Error updating project:', error);
        throw error;
      }

      await loadProjects();
    } catch (error) {
      console.error('Error updating project:', error);
      throw error;
    }
  }, [user, supabase, loadProjects]);

  const deleteProject = useCallback(async (id: string) => {
    if (!user) return;

    try {
      const { error } = await supabase
        .from('projects')
        .delete()
        .eq('id', id)
        .eq('user_id', user.id);

      if (error) {
        console.error('Error deleting project:', error);
        throw error;
      }

      await loadProjects();
    } catch (error) {
      console.error('Error deleting project:', error);
      throw error;
    }
  }, [user, supabase, loadProjects]);

  return (
    <ProjectsContext.Provider
      value={{
        projects,
        activeProjectId,
        setActiveProjectId,
        createProject,
        updateProject,
        deleteProject,
        isLoading,
        refreshProjects: loadProjects,
      }}
    >
      {children}
    </ProjectsContext.Provider>
  );
}

export function useProjects() {
  const context = useContext(ProjectsContext);
  if (context === undefined) {
    throw new Error('useProjects must be used within a ProjectsProvider');
  }
  return context;
}

