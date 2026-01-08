'use client';

import { TabsProvider } from '@/contexts/TabsContext';
import { FilesProvider } from '@/contexts/FilesContext';
import { ProjectsProvider } from '@/contexts/ProjectsContext';
import { AuthProvider } from '@/contexts/AuthContext';

export function TabsProviderWrapper({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <ProjectsProvider>
        <FilesProvider>
          <TabsProvider>{children}</TabsProvider>
        </FilesProvider>
      </ProjectsProvider>
    </AuthProvider>
  );
}

