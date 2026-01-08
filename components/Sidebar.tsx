'use client';

import { useState, useRef } from 'react';
import { 
  Folder, 
  FileText, 
  Upload, 
  ChevronRight, 
  Plus,
  X,
  CheckCircle2,
  Clock,
  AlertCircle,
  Edit2,
  Trash2
} from 'lucide-react';
import { useFiles, UploadedFile as FilesContextUploadedFile } from '@/contexts/FilesContext';
import { useProjects } from '@/contexts/ProjectsContext';

interface SidebarProps {
  onCollapseChange?: (collapsed: boolean) => void;
}

export function Sidebar({ onCollapseChange }: SidebarProps = {} as SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const { files: uploadedFiles, uploadFiles, removeFile, isLoading } = useFiles();
  const { projects, activeProjectId, setActiveProjectId, createProject, updateProject, deleteProject } = useProjects();
  const [showCreateProject, setShowCreateProject] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [editingProjectId, setEditingProjectId] = useState<string | null>(null);
  const [editingProjectName, setEditingProjectName] = useState('');
  
  const handleToggle = () => {
    const newState = !isCollapsed;
    setIsCollapsed(newState);
    onCollapseChange?.(newState);
  };
  
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropZoneRef = useRef<HTMLDivElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    const validFiles = files.filter(
      (file) =>
        file.name.toLowerCase().endsWith('.xlsx') ||
        file.name.toLowerCase().endsWith('.xls') ||
        file.name.toLowerCase().endsWith('.csv')
    );
    
    if (validFiles.length > 0) {
      await uploadFiles(validFiles, activeProjectId);
    }
  };

  const handleFileInput = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files) {
      const fileArray = Array.from(files);
      const validFiles = fileArray.filter(
        (file) =>
          file.name.toLowerCase().endsWith('.xlsx') ||
          file.name.toLowerCase().endsWith('.xls') ||
          file.name.toLowerCase().endsWith('.csv')
      );
      
      if (validFiles.length > 0) {
        await uploadFiles(validFiles, activeProjectId);
      }
      
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) return;
    
    const project = await createProject(newProjectName.trim());
    if (project) {
      setNewProjectName('');
      setShowCreateProject(false);
    }
  };

  const handleDeleteProject = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('Êtes-vous sûr de vouloir supprimer ce projet ? Les fichiers associés ne seront pas supprimés.')) {
      await deleteProject(id);
    }
  };

  const handleStartEdit = (projectId: string, projectName: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingProjectId(projectId);
    setEditingProjectName(projectName);
  };

  const handleSaveEdit = async (projectId: string) => {
    if (!editingProjectName.trim()) return;
    
    try {
      await updateProject(projectId, editingProjectName.trim());
      setEditingProjectId(null);
      setEditingProjectName('');
    } catch (error) {
      console.error('Error updating project:', error);
    }
  };

  const getFileTypeIcon = (file: FilesContextUploadedFile) => {
    return <FileText className="w-4 h-4" strokeWidth={1.5} />;
  };

  const getStatusIcon = (file: FilesContextUploadedFile) => {
    switch (file.status) {
      case 'ready':
        return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" strokeWidth={1.5} />;
      case 'processing':
      case 'uploading':
        return <Clock className="w-3.5 h-3.5 text-[#D4AF37]" strokeWidth={1.5} />;
      case 'error':
        return <AlertCircle className="w-3.5 h-3.5 text-red-500" strokeWidth={1.5} />;
      default:
        return null;
    }
  };

  const formatDate = (date: Date) => {
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return "Aujourd'hui";
    } else if (diffDays === 1) {
      return 'Hier';
    } else if (diffDays < 7) {
      return `Il y a ${diffDays}j`;
    } else {
      return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
    }
  };

  const formatProjectDate = (dateString: string) => {
    const date = new Date(dateString);
    return formatDate(date);
  };

  return (
    <aside 
      className={`bg-white border-r border-[#E5E5E5] flex flex-col transition-all duration-200 fixed left-0 bottom-0 z-40 ${
        isCollapsed ? 'w-16' : 'w-64'
      }`}
      style={{ top: '49px' }}
    >
      {/* Header avec bouton collapse */}
      <div className="flex items-center justify-end p-4 border-b border-[#E5E5E5]">
        <button
          onClick={handleToggle}
          className="p-1.5 rounded-md hover:bg-[#F5F5F5] transition-colors text-[#737373] hover:text-[#1A1A1A]"
        >
          <ChevronRight 
            className={`w-4 h-4 transition-transform duration-200 ${isCollapsed ? 'rotate-180' : ''}`} 
            strokeWidth={1.5} 
          />
        </button>
      </div>

      {!isCollapsed && (
        <>
          {/* Section Projets */}
          <div className="flex-1 overflow-y-auto scrollbar-subtle">
            <div className="p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-[11px] font-medium text-[#737373] uppercase tracking-wider">
                  Projets
                </h3>
                <button 
                  onClick={() => setShowCreateProject(true)}
                  className="p-1 rounded-md hover:bg-[#F5F5F5] transition-colors text-[#737373] hover:text-[#1A1A1A]"
                >
                  <Plus className="w-3.5 h-3.5" strokeWidth={1.5} />
                </button>
              </div>
              
              {/* Formulaire de création */}
              {showCreateProject && (
                <div className="mb-2 p-2 bg-[#FAFAFA] rounded-md border border-[#E5E5E5]">
                  <input
                    type="text"
                    value={newProjectName}
                    onChange={(e) => setNewProjectName(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        handleCreateProject();
                      } else if (e.key === 'Escape') {
                        setShowCreateProject(false);
                        setNewProjectName('');
                      }
                    }}
                    placeholder="Nom du projet"
                    className="w-full px-2 py-1 text-sm border border-[#E5E5E5] rounded focus:outline-none focus:ring-1 focus:ring-[#D4AF37]"
                    autoFocus
                  />
                  <div className="flex gap-1 mt-2">
                    <button
                      onClick={handleCreateProject}
                      className="flex-1 px-2 py-1 text-xs bg-[#1A1A1A] text-white rounded hover:bg-[#2A2A2A]"
                    >
                      Créer
                    </button>
                    <button
                      onClick={() => {
                        setShowCreateProject(false);
                        setNewProjectName('');
                      }}
                      className="px-2 py-1 text-xs bg-white border border-[#E5E5E5] rounded hover:bg-[#FAFAFA]"
                    >
                      Annuler
                    </button>
                  </div>
                </div>
              )}
              
              <div className="space-y-1">
                {projects.length === 0 ? (
                  <p className="text-[11px] text-[#737373] text-center py-4">
                    Aucun projet
                  </p>
                ) : (
                  projects.map((project) => (
                    <div
                      key={project.id}
                      className={`w-full px-3 py-2 rounded-md transition-all duration-150 flex items-center gap-2 group ${
                        activeProjectId === project.id
                          ? 'bg-[#FAFAFA] text-[#1A1A1A]'
                          : 'text-[#737373] hover:bg-[#FAFAFA] hover:text-[#1A1A1A]'
                      }`}
                    >
                      <button
                        onClick={() => setActiveProjectId(project.id)}
                        className="flex-1 text-left flex items-center gap-2 min-w-0"
                      >
                        <Folder className={`w-4 h-4 flex-shrink-0 ${activeProjectId === project.id ? 'text-[#D4AF37]' : ''}`} strokeWidth={1.5} />
                        <div className="flex-1 min-w-0">
                          {editingProjectId === project.id ? (
                            <input
                              type="text"
                              value={editingProjectName}
                              onChange={(e) => setEditingProjectName(e.target.value)}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                  handleSaveEdit(project.id);
                                } else if (e.key === 'Escape') {
                                  setEditingProjectId(null);
                                  setEditingProjectName('');
                                }
                              }}
                              onClick={(e) => e.stopPropagation()}
                              className="w-full px-1 py-0.5 text-sm border border-[#D4AF37] rounded focus:outline-none"
                              autoFocus
                            />
                          ) : (
                            <>
                              <div className="text-sm font-medium truncate" style={{ letterSpacing: '-0.01em' }}>
                                {project.name}
                              </div>
                              <div className="text-[11px] text-[#737373] mt-0.5">
                                {formatProjectDate(project.created_at)}
                              </div>
                            </>
                          )}
                        </div>
                      </button>
                      {editingProjectId !== project.id && (
                        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button
                            onClick={(e) => handleStartEdit(project.id, project.name, e)}
                            className="p-1 rounded hover:bg-[#F5F5F5] text-[#737373] hover:text-[#1A1A1A]"
                            title="Modifier"
                          >
                            <Edit2 className="w-3 h-3" strokeWidth={1.5} />
                          </button>
                          <button
                            onClick={(e) => handleDeleteProject(project.id, e)}
                            className="p-1 rounded hover:bg-[#F5F5F5] text-[#737373] hover:text-red-500"
                            title="Supprimer"
                          >
                            <Trash2 className="w-3 h-3" strokeWidth={1.5} />
                          </button>
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Section Fichiers Sources */}
            <div className="p-4 border-t border-[#E5E5E5]">
              <h3 className="text-[11px] font-medium text-[#737373] uppercase tracking-wider mb-3">
                Fichiers Sources
                {activeProjectId && (
                  <span className="ml-2 text-[10px] normal-case text-[#737373]">
                    ({projects.find(p => p.id === activeProjectId)?.name})
                  </span>
                )}
              </h3>
              
              {!activeProjectId && (
                <p className="text-[11px] text-[#737373] text-center py-4">
                  Sélectionnez un projet pour voir les fichiers
                </p>
              )}
              
              <div className="space-y-1">
                {!activeProjectId ? null : uploadedFiles.length === 0 ? (
                  <p className="text-[11px] text-[#737373] text-center py-4">
                    Aucun fichier dans ce projet
                  </p>
                ) : (
                  uploadedFiles.map((file) => (
                    <div
                      key={file.id}
                      className="px-3 py-2 rounded-md hover:bg-[#FAFAFA] transition-colors duration-150 group relative"
                    >
                      <div className="flex items-center gap-2">
                        <div className="text-[#737373] group-hover:text-[#D4AF37] transition-colors">
                          {getFileTypeIcon(file)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-xs font-medium text-[#1A1A1A] truncate" style={{ letterSpacing: '-0.01em' }}>
                            {file.name}
                          </div>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className="text-[10px] text-[#737373]">{formatDate(file.uploadDate)}</span>
                            {getStatusIcon(file)}
                          </div>
                          {file.error && (
                            <div className="text-[10px] text-red-500 mt-1 truncate" title={file.error}>
                              {file.error}
                            </div>
                          )}
                        </div>
                        <button
                          onClick={() => removeFile(file.id)}
                          className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded hover:bg-[#F5F5F5] text-[#737373] hover:text-red-500"
                          title="Supprimer"
                        >
                          <X className="w-3 h-3" strokeWidth={1.5} />
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Zone Drag & Drop */}
            <div className="p-4 border-t border-[#E5E5E5]">
              <div
                ref={dropZoneRef}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-lg p-6 text-center transition-all duration-200 cursor-pointer ${
                  isDragging
                    ? 'border-[#D4AF37] bg-[#D4AF37]/5'
                    : 'border-[#E5E5E5] hover:border-[#D4AF37]/30 hover:bg-[#FAFAFA]'
                }`}
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload className={`w-6 h-6 mx-auto mb-2 transition-colors ${
                  isDragging ? 'text-[#D4AF37]' : 'text-[#737373]'
                }`} strokeWidth={1.5} />
                <p className="text-xs font-medium text-[#1A1A1A] mb-1" style={{ letterSpacing: '-0.01em' }}>
                  {isDragging ? 'Déposez vos fichiers' : 'Glisser-déposer'}
                </p>
                <p className="text-[10px] text-[#737373]">
                  ou cliquez pour parcourir
                </p>
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".xlsx,.xls,.csv"
                  onChange={handleFileInput}
                  className="hidden"
                />
              </div>
            </div>
          </div>
        </>
      )}

      {/* Version collapsed */}
      {isCollapsed && (
        <div className="flex-1 flex flex-col items-center py-4 gap-4">
          <button className="p-2 rounded-md hover:bg-[#F5F5F5] transition-colors text-[#737373] hover:text-[#1A1A1A]">
            <Folder className="w-5 h-5" strokeWidth={1.5} />
          </button>
          <button className="p-2 rounded-md hover:bg-[#F5F5F5] transition-colors text-[#737373] hover:text-[#1A1A1A]">
            <FileText className="w-5 h-5" strokeWidth={1.5} />
          </button>
          <button 
            className="p-2 rounded-md hover:bg-[#F5F5F5] transition-colors text-[#737373] hover:text-[#1A1A1A]"
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload className="w-5 h-5" strokeWidth={1.5} />
          </button>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".xlsx,.xls,.csv"
            onChange={handleFileInput}
            className="hidden"
          />
        </div>
      )}
    </aside>
  );
}
