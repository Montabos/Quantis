'use client';

import { createContext, useContext, useState, ReactNode, useCallback, useEffect } from 'react';
import { createClient } from '@/lib/supabase/client';
import { useAuth } from './AuthContext';
import { useProjects } from './ProjectsContext';

export interface FileMetadata {
  columns?: string[];
  numRows?: number;
  numColumns?: number;
  fileType?: string; // 'cash_flow', 'balance_sheet', etc.
  detectedDocumentType?: string;
}

export interface UploadedFile {
  id: string;
  name: string;
  originalName: string;
  type: 'excel' | 'csv';
  size: number;
  uploadDate: Date;
  status: 'uploading' | 'processing' | 'ready' | 'error';
  metadata?: FileMetadata;
  backendId?: string; // ID côté backend après upload (now the DB ID)
  error?: string;
}

interface FilesContextType {
  files: UploadedFile[];
  uploadFiles: (files: File[]) => Promise<void>;
  removeFile: (fileId: string) => Promise<void>;
  getFiles: () => UploadedFile[];
  getFileById: (fileId: string) => UploadedFile | undefined;
  getReadyFiles: () => UploadedFile[];
  isLoading: boolean;
  refreshFiles: () => Promise<void>;
}

const FilesContext = createContext<FilesContextType | undefined>(undefined);

export function FilesProvider({ children }: { children: ReactNode }) {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const { user } = useAuth();
  const { activeProjectId } = useProjects();
  const supabase = createClient();

  // Load files from Supabase when user is authenticated
  const loadFiles = useCallback(async () => {
    if (!user) {
      setFiles([]);
      return;
    }

    setIsLoading(true);
    try {
      // Require active project - files must belong to a project
      if (!activeProjectId) {
        setFiles([]);
        setIsLoading(false);
        return;
      }

      const { data, error } = await supabase
        .from('files')
        .select('*')
        .eq('user_id', user.id)
        .eq('project_id', activeProjectId)
        .order('created_at', { ascending: false });

      if (error) {
        console.error('Error loading files:', error);
        return;
      }

      const mappedFiles: UploadedFile[] = (data || []).map((file) => ({
        id: file.id,
        name: file.original_name, // Use original_name for display
        originalName: file.original_name,
        type: file.file_type as 'excel' | 'csv',
        size: file.size,
        uploadDate: new Date(file.created_at),
        status: file.status as 'uploading' | 'processing' | 'ready' | 'error',
        metadata: file.metadata as FileMetadata | undefined,
        backendId: file.id,
        error: file.error || undefined,
      }));

      setFiles(mappedFiles);
    } catch (error) {
      console.error('Error loading files:', error);
    } finally {
      setIsLoading(false);
    }
  }, [user, supabase, activeProjectId]);

  useEffect(() => {
    loadFiles();
  }, [loadFiles]);

  const uploadFiles = useCallback(async (fileList: File[], projectId?: string | null) => {
    if (!user) {
      console.error('User not authenticated');
      return;
    }

    if (!projectId) {
      console.error('No project selected. Please select a project before uploading files.');
      alert('Veuillez sélectionner un projet avant d\'uploader des fichiers.');
      return;
    }

    setIsLoading(true);
    
    const newFiles: UploadedFile[] = fileList.map((file) => {
      const id = `file-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      const isExcel = file.name.toLowerCase().endsWith('.xlsx') || file.name.toLowerCase().endsWith('.xls');
      
      return {
        id,
        name: file.name,
        originalName: file.name,
        type: isExcel ? 'excel' : 'csv',
        size: file.size,
        uploadDate: new Date(),
        status: 'uploading' as const,
      };
    });

    // Add files to state immediately with uploading status
    setFiles((prev) => [...prev, ...newFiles]);

    try {
      // Upload each file sequentially to avoid race conditions
      const uploadResults = [];
      for (let i = 0; i < newFiles.length; i++) {
        const fileData = newFiles[i];
        const file = fileList[i];
        if (!file) continue;

          const formData = new FormData();
          formData.append('file', file);
          if (projectId) {
            formData.append('project_id', projectId);
          }

          try {
            // Update status to processing
            setFiles((prev) =>
              prev.map((f) =>
                f.id === fileData.id ? { ...f, status: 'processing' } : f
              )
            );

            const response = await fetch('/api/files/upload', {
              method: 'POST',
              body: formData,
            });

          if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: 'Upload failed' }));
            throw new Error(errorData.error || 'Upload failed');
          }

          const result = await response.json();
          uploadResults.push({ success: true, result });
        } catch (error) {
          // Update file with error status
          setFiles((prev) =>
            prev.map((f) =>
              f.id === fileData.id
                ? {
                    ...f,
                    status: 'error' as const,
                    error: error instanceof Error ? error.message : 'Upload failed',
                  }
                : f
            )
          );
          uploadResults.push({ success: false, error });
        }
      }

      // Reload files from database once after all uploads are complete
      if (uploadResults.some(r => r.success)) {
        await loadFiles();
      }
    } catch (error) {
      console.error('Error uploading files:', error);
    } finally {
      setIsLoading(false);
    }
  }, [user, loadFiles, activeProjectId]);

  const removeFile = useCallback(async (fileId: string) => {
    try {
      const response = await fetch(`/api/files/${fileId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete file');
      }

      // Reload files from database
      await loadFiles();
    } catch (error) {
      console.error('Error deleting file:', error);
      throw error;
    }
  }, [loadFiles]);

  const getFiles = useCallback(() => {
    return files;
  }, [files]);

  const getFileById = useCallback(
    (fileId: string) => {
      return files.find((f) => f.id === fileId);
    },
    [files]
  );

  const getReadyFiles = useCallback(() => {
    return files.filter((f) => f.status === 'ready');
  }, [files]);

  return (
    <FilesContext.Provider
      value={{
        files,
        uploadFiles,
        removeFile,
        getFiles,
        getFileById,
        getReadyFiles,
        isLoading,
        refreshFiles: loadFiles,
      }}
    >
      {children}
    </FilesContext.Provider>
  );
}

export function useFiles() {
  const context = useContext(FilesContext);
  if (context === undefined) {
    throw new Error('useFiles must be used within a FilesProvider');
  }
  return context;
}




