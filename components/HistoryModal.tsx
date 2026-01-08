'use client';

import { useState, useEffect } from 'react';
import { X, RotateCcw, Trash2, Clock } from 'lucide-react';
import { useTabs, DecisionTab } from '@/contexts/TabsContext';
import { useProjects } from '@/contexts/ProjectsContext';

interface HistoryModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function HistoryModal({ isOpen, onClose }: HistoryModalProps) {
  const { getClosedTabsForProject, reopenTab, permanentlyDeleteTab } = useTabs();
  const { activeProjectId } = useProjects();
  const [closedTabs, setClosedTabs] = useState<DecisionTab[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && activeProjectId) {
      loadClosedTabs();
    }
  }, [isOpen, activeProjectId]);

  const loadClosedTabs = async () => {
    if (!activeProjectId) return;
    
    setIsLoading(true);
    try {
      const tabs = await getClosedTabsForProject(activeProjectId);
      setClosedTabs(tabs);
    } catch (error) {
      console.error('Error loading closed tabs:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReopen = async (tabId: string) => {
    try {
      await reopenTab(tabId);
      onClose();
    } catch (error) {
      console.error('Error reopening tab:', error);
    }
  };

  const handleDelete = async (tabId: string) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer définitivement cette analyse ?')) {
      return;
    }
    
    setDeletingId(tabId);
    try {
      await permanentlyDeleteTab(tabId);
      await loadClosedTabs(); // Reload to update the list
    } catch (error) {
      console.error('Error deleting tab:', error);
      alert('Erreur lors de la suppression. Veuillez réessayer.');
    } finally {
      setDeletingId(null);
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/20 backdrop-blur-sm z-50"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div 
          className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[80vh] flex flex-col"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="px-6 py-4 border-b border-[#E5E5E5] flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-[#D4AF37]/10 border border-[#D4AF37]/20 flex items-center justify-center">
                <Clock className="w-4 h-4 text-[#D4AF37]" strokeWidth={2} />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-[#1A1A1A]" style={{ letterSpacing: '-0.01em' }}>
                  Historique des analyses
                </h2>
                <p className="text-xs text-[#737373] font-medium">
                  Analyses fermées pour ce projet
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-md hover:bg-[#F5F5F5] transition-colors text-[#737373] hover:text-[#1A1A1A]"
            >
              <X className="w-4 h-4" strokeWidth={2} />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <div className="text-sm text-[#737373]">Chargement...</div>
              </div>
            ) : closedTabs.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="w-12 h-12 rounded-lg bg-[#F5F5F5] flex items-center justify-center mb-4">
                  <Clock className="w-6 h-6 text-[#737373]" strokeWidth={1.5} />
                </div>
                <p className="text-sm text-[#737373] font-medium mb-1">
                  Aucune analyse fermée
                </p>
                <p className="text-xs text-[#737373]">
                  Les analyses que vous fermez apparaîtront ici
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {closedTabs.map((tab) => (
                  <div
                    key={tab.id}
                    className="bg-white border border-[#E5E5E5] rounded-lg p-4 hover:border-[#D4AF37]/30 transition-all group"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <h3 className="text-sm font-semibold text-[#1A1A1A] mb-1 truncate" style={{ letterSpacing: '-0.01em' }}>
                          {tab.label}
                        </h3>
                        <p className="text-xs text-[#737373] line-clamp-2 mb-3">
                          {tab.query}
                        </p>
                        {tab.analysisResult?.decision_summary?.description && (
                          <p className="text-xs text-[#6B7280] line-clamp-2">
                            {tab.analysisResult.decision_summary.description}
                          </p>
                        )}
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <button
                          onClick={() => handleReopen(tab.id)}
                          className="p-2 rounded-md hover:bg-[#D4AF37]/10 hover:text-[#D4AF37] transition-colors text-[#737373]"
                          title="Rouvrir l'onglet"
                        >
                          <RotateCcw className="w-4 h-4" strokeWidth={2} />
                        </button>
                        <button
                          onClick={() => handleDelete(tab.id)}
                          disabled={deletingId === tab.id}
                          className="p-2 rounded-md hover:bg-red-50 hover:text-red-600 transition-colors text-[#737373] disabled:opacity-50"
                          title="Supprimer définitivement"
                        >
                          <Trash2 className="w-4 h-4" strokeWidth={2} />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-[#E5E5E5] flex items-center justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-md bg-[#1A1A1A] text-white text-sm font-medium hover:bg-[#2A2A2A] transition-colors"
            >
              Fermer
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

