'use client';

import { X, CheckCircle2, Loader2, AlertCircle, Circle, Sparkles } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useAnalysisProgress, AnalysisStatus, MissingData } from '@/hooks/useAnalysisProgress';
import { useFiles } from '@/contexts/FilesContext';
import { useProjects } from '@/contexts/ProjectsContext';
import { useTabs } from '@/contexts/TabsContext';

interface AnalysisModalProps {
  question: string;
  isOpen: boolean;
  onClose: () => void;
}

export function AnalysisModal({ question, isOpen, onClose }: AnalysisModalProps) {
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const { status, isLoading, error, refresh } = useAnalysisProgress(analysisId);
  const { getReadyFiles } = useFiles();
  const { activeProjectId } = useProjects();
  const { refreshAnalyses, setActiveTab, decisionTabs } = useTabs();

  // Start analysis when modal opens
  useEffect(() => {
    if (isOpen && !analysisId && activeProjectId) {
      startAnalysis();
    }
  }, [isOpen, analysisId, activeProjectId]);

  // When analysis completes, refresh analyses and open the tab
  useEffect(() => {
    const openTabWhenReady = async () => {
      if (status?.status === 'completed' && status.result && analysisId) {
        const tabId = `analysis-${analysisId}`;
        const tabExists = decisionTabs.some(tab => tab.id === tabId && tab.analysisResult);
        
        if (tabExists) {
          console.log(`[AnalysisModal] Tab ${tabId} is ready with analysisResult, setting as active`);
          setActiveTab(tabId);
        } else {
          // Tab not ready yet, refresh analyses
          console.log(`[AnalysisModal] Tab ${tabId} not ready yet, refreshing analyses...`);
          await refreshAnalyses();
        }
      }
    };

    openTabWhenReady();
  }, [status?.status, status?.result, analysisId, decisionTabs, refreshAnalyses, setActiveTab]);

  const startAnalysis = async () => {
    if (!activeProjectId) {
      return;
    }

    try {
      const readyFiles = getReadyFiles();
      const fileIds = readyFiles.map((f) => f.backendId || f.id).filter(Boolean);

      const response = await fetch('/api/decisions/analyze/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question,
          file_ids: fileIds.length > 0 ? fileIds : undefined,
          project_id: activeProjectId,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Failed to start analysis' }));
        throw new Error(errorData.error || 'Failed to start analysis');
      }

      const data = await response.json();
      setAnalysisId(data.analysis_id);
    } catch (err) {
      console.error('Error starting analysis:', err);
    }
  };

  const handleClose = async () => {
    if (status?.status === 'completed' && status.result && analysisId) {
      console.log(`[AnalysisModal] Closing modal, refreshing analyses for analysis ${analysisId}`);
      console.log(`[AnalysisModal] Result data keys:`, status.result ? Object.keys(status.result) : 'none');
      
      // Refresh analyses to load the new one from Supabase
      await refreshAnalyses();
      
      // Small delay to ensure tabs are updated
      await new Promise(resolve => setTimeout(resolve, 200));
      
      // Verify the tab exists before setting it as active
      const tabId = `analysis-${analysisId}`;
      const tabExists = decisionTabs.some(tab => tab.id === tabId);
      console.log(`[AnalysisModal] Tab ${tabId} exists:`, tabExists);
      console.log(`[AnalysisModal] Available tabs:`, decisionTabs.map(t => t.id));
      
      if (tabExists) {
        console.log(`[AnalysisModal] Setting active tab to ${tabId}`);
        setActiveTab(tabId);
      } else {
        console.warn(`[AnalysisModal] Tab ${tabId} not found after refresh, trying again...`);
        // Try refreshing one more time
        await refreshAnalyses();
        await new Promise(resolve => setTimeout(resolve, 200));
        const tabExistsAfterRetry = decisionTabs.some(tab => tab.id === tabId);
        if (tabExistsAfterRetry) {
          setActiveTab(tabId);
        } else {
          console.error(`[AnalysisModal] Tab ${tabId} still not found after retry`);
        }
      }
    }
    setAnalysisId(null);
    onClose();
  };

  const handleContinue = async (providedData: Record<string, any>) => {
    if (!analysisId) return;

    try {
      const response = await fetch(`/api/decisions/analyze/${analysisId}/continue`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ missing_data: providedData }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Failed to continue analysis' }));
        throw new Error(errorData.error || 'Failed to continue analysis');
      }

      // Refresh status to pick up the change
      setTimeout(() => {
        refresh();
      }, 1000);
    } catch (err) {
      console.error('Error continuing analysis:', err);
      alert('Erreur lors de la reprise de l\'analyse. Veuillez réessayer.');
    }
  };

  if (!isOpen) return null;

  const getStepIcon = (stepStatus: string) => {
    switch (stepStatus) {
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-emerald-600" />;
      case 'in_progress':
        return <Loader2 className="w-4 h-4 text-[#D4AF37] animate-spin" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-600" />;
      default:
        return <Circle className="w-4 h-4 text-[#E5E5E5]" />;
    }
  };

  const getStepLabel = (stepName: string) => {
    const labels: Record<string, string> = {
      analyzing_question: 'Analyse de la question',
      checking_files: 'Vérification des fichiers disponibles',
      analyzing_structure: 'Analyse de la structure des données',
      calculating_metrics: 'Calcul des métriques clés',
      generating_scenarios: 'Génération des scénarios',
      creating_recommendations: 'Création des recommandations',
    };
    return labels[stepName] || stepName;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Overlay */}
      <div
        className="absolute inset-0 bg-black/20 backdrop-blur-sm"
        onClick={status?.status === 'completed' ? handleClose : undefined}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-lg shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col border border-[#E5E5E5]">
        {/* Header */}
        <div className="flex items-start justify-between px-6 py-4 border-b border-[#E5E5E5]">
          <div className="flex-1 pr-4">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 rounded-lg bg-[#D4AF37]/10 border border-[#D4AF37]/20 flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-[#D4AF37]" strokeWidth={2} />
              </div>
              <h2 className="text-lg font-semibold text-[#1A1A1A]" style={{ letterSpacing: '-0.01em' }}>
                Analyse en cours
              </h2>
            </div>
            <p className="text-sm text-[#737373] leading-relaxed">{question}</p>
          </div>
          {status?.status === 'completed' && (
            <button
              onClick={handleClose}
              className="flex-shrink-0 w-8 h-8 rounded-md hover:bg-[#F5F5F5] flex items-center justify-center transition-colors"
              aria-label="Fermer"
            >
              <X className="w-4 h-4 text-[#737373]" />
            </button>
          )}
        </div>

        {/* Progress Bar */}
        {status && (
          <div className="px-6 py-4 border-b border-[#E5E5E5]">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-[#737373]">Progression</span>
              <span className="text-xs font-medium text-[#737373]">{status.progress}%</span>
            </div>
            <div className="h-2 bg-[#F5F5F5] rounded-full overflow-hidden">
              <div
                className="h-full bg-[#D4AF37] transition-all duration-300 ease-out"
                style={{ width: `${status.progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-red-900">Erreur</p>
                  <p className="text-sm text-red-700 mt-1">{error}</p>
                </div>
              </div>
            </div>
          )}

          {status?.status === 'waiting_for_data' && (
            <MissingDataForm missingData={status.missing_data} onContinue={handleContinue} />
          )}

          {status?.status === 'completed' && status.result && (
            <AnalysisPreview result={status.result} />
          )}

          {/* Steps Timeline */}
          {status && status.steps.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-[#1A1A1A] mb-4">Étapes de l'analyse</h3>
              <div className="relative">
                {/* Timeline line */}
                <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-[#E5E5E5]" />
                
                <div className="space-y-4">
                  {status.steps.map((step, index) => {
                    const isActive = step.status === 'in_progress';
                    const isCompleted = step.status === 'completed';
                    const isPending = step.status === 'pending';
                    const isError = step.status === 'error';
                    
                    return (
                      <div key={step.name || index} className="relative flex items-start gap-4">
                        {/* Timeline dot */}
                        <div className="relative z-10 flex-shrink-0">
                          <div
                            className={`w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300 ${
                              isActive
                                ? 'bg-[#D4AF37] shadow-lg shadow-[#D4AF37]/30'
                                : isCompleted
                                ? 'bg-emerald-500'
                                : isError
                                ? 'bg-red-500'
                                : 'bg-[#E5E5E5]'
                            }`}
                          >
                            {getStepIcon(step.status)}
                          </div>
                        </div>
                        
                        {/* Step content */}
                        <div
                          className={`flex-1 min-w-0 pb-4 transition-all duration-300 ${
                            isActive
                              ? 'translate-x-0'
                              : 'translate-x-0'
                          }`}
                        >
                          <div
                            className={`p-4 rounded-lg border transition-all duration-300 ${
                              isActive
                                ? 'bg-[#D4AF37]/5 border-[#D4AF37]/30 shadow-sm'
                                : isCompleted
                                ? 'bg-emerald-50/50 border-emerald-200/50'
                                : isError
                                ? 'bg-red-50/50 border-red-200/50'
                                : 'bg-[#FAFAFA] border-[#E5E5E5]'
                            }`}
                          >
                            <div className="flex items-start justify-between gap-2">
                              <div className="flex-1 min-w-0">
                                <p
                                  className={`text-sm font-medium transition-colors ${
                                    isActive
                                      ? 'text-[#D4AF37]'
                                      : isCompleted
                                      ? 'text-emerald-700'
                                      : isError
                                      ? 'text-red-700'
                                      : 'text-[#737373]'
                                  }`}
                                >
                                  {step.label || getStepLabel(step.name)}
                                </p>
                                {step.message && (
                                  <p className="text-xs text-[#737373] mt-1.5 leading-relaxed">
                                    {step.message}
                                  </p>
                                )}
                                {!step.message && isActive && (
                                  <p className="text-xs text-[#737373] mt-1.5 italic">
                                    En cours...
                                  </p>
                                )}
                              </div>
                              {isActive && (
                                <Loader2 className="w-4 h-4 text-[#D4AF37] animate-spin flex-shrink-0" />
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-[#E5E5E5] flex items-center justify-between">
          {status?.status === 'completed' && (
            <button
              onClick={handleClose}
              className="px-4 py-2 bg-[#D4AF37] text-white rounded-md text-sm font-medium hover:bg-[#B8941F] transition-colors"
            >
              Voir le rapport complet
            </button>
          )}
          {status?.status === 'error' && (
            <button
              onClick={handleClose}
              className="px-4 py-2 bg-[#F5F5F5] text-[#1A1A1A] rounded-md text-sm font-medium hover:bg-[#E5E5E5] transition-colors"
            >
              Fermer
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function MissingDataForm({
  missingData,
  onContinue,
}: {
  missingData: MissingData[];
  onContinue: (data: Record<string, any>) => void;
}) {
  const [formData, setFormData] = useState<Record<string, any>>({});

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onContinue(formData);
  };

  return (
    <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
      <h3 className="text-sm font-semibold text-amber-900 mb-3">Données supplémentaires requises</h3>
      <form onSubmit={handleSubmit} className="space-y-4">
        {missingData.map((item) => (
          <div key={item.id}>
            <label className="block text-sm font-medium text-[#1A1A1A] mb-1">
              {item.description}
              {item.required && <span className="text-red-600 ml-1">*</span>}
            </label>
            <input
              type={item.type === 'number' ? 'number' : 'text'}
              required={item.required}
              value={formData[item.id] || ''}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  [item.id]: item.type === 'number' ? parseFloat(e.target.value) : e.target.value,
                }))
              }
              className="w-full px-3 py-2 border border-[#E5E5E5] rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-[#D4AF37] focus:border-transparent"
              placeholder={`Entrez ${item.description.toLowerCase()}`}
            />
          </div>
        ))}
        <button
          type="submit"
          className="w-full px-4 py-2 bg-[#D4AF37] text-white rounded-md text-sm font-medium hover:bg-[#B8941F] transition-colors"
        >
          Continuer l'analyse
        </button>
      </form>
    </div>
  );
}

function AnalysisPreview({ result }: { result: any }) {
  return (
    <div className="mb-6 space-y-4">
      <h3 className="text-sm font-semibold text-[#1A1A1A] mb-3">Aperçu des résultats</h3>
      
      {result.decision_summary?.description && (
        <div className="p-4 bg-[#D4AF37]/5 border border-[#D4AF37]/20 rounded-lg">
          <p className="text-sm text-[#1A1A1A]">{result.decision_summary.description}</p>
        </div>
      )}

      {result.key_metrics && Object.keys(result.key_metrics).length > 0 && (
        <div className="p-4 bg-[#FAFAFA] border border-[#E5E5E5] rounded-lg">
          <h4 className="text-xs font-semibold text-[#737373] uppercase mb-2">Métriques clés</h4>
          <div className="space-y-1">
            {Object.entries(result.key_metrics).slice(0, 3).map(([key, metric]: [string, any]) => (
              <div key={key} className="flex justify-between text-sm">
                <span className="text-[#737373]">{key.replace(/_/g, ' ')}</span>
                <span className="text-[#1A1A1A] font-medium">
                  {typeof metric.value === 'number' ? metric.value.toLocaleString('fr-FR') : metric.value}
                  {metric.unit || ''}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

